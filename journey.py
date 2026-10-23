"""12-step journey for one customer + property, built ONLY from Gold columns (gold_customer_profile + gold_property_profile).
Steps the Gold tables cannot answer (quote, underwriting decision, endorsements, FNOL date) are returned with status "gap" instead of invented values."""
import pandas as pd

STEPS = [
    (1, "Customer", "Who is applying for / owning the insurance?"),
    (2, "Property", "Which property is being insured?"),
    (3, "Property Location", "Country → State → County → Community → ZIP"),
    (4, "Geography + Exposure", "Where is the property and what hazards / value are associated with it?"),
    (5, "Quote / Application", "Coverage and pricing are proposed based on the property and risk."),
    (6, "Underwriting", "Insurer evaluates the risk → Accept or Decline"),
    (7, "Policy Bind & Issue", "Coverage, premium and insured exposure become active."),
    (8, "Active Policy Management", "Endorsements, changes and other policy events."),
    (9, "Loss Event → FNOL → Claim", "Report loss → assess damage → reserve → payment → close claim."),
    (10, "Loss History", "Closed claims become part of the property's / customer's history."),
    (11, "Mitigation → Risk Updated", "Improvements can reduce or change the assessed risk."),
    (12, "Renewal", "Updated risk and history drive the decision → Renew / Non-renew"),
]
PHASES = [("Know the risk", 1, 4), ("Sell", 5, 7), ("Serve", 8, 10), ("Improve & renew", 11, 12)]
# which Gold object answers each step (shown in the app so the lineage is visible)
SOURCE = {1: "gold_customer_profile", 2: "gold_property_profile", 3: "gold_property_profile", 4: "gold_property_profile", 5: None, 6: None,
          7: "gold_property_profile / gold_policy_report", 8: None, 9: "gold_property_profile / gold_claim_report", 10: "gold_property_profile",
          11: "gold_property_profile", 12: "gold_customer_profile"}


def ok(x):
    return x is not None and not pd.isna(x)


def d(x):
    return "—" if not ok(x) else pd.Timestamp(x).strftime("%Y-%m-%d")


def usd(x):
    return "—" if not ok(x) else f"${float(x):,.0f}"


def build(C, P, as_of):
    """C: customer row (Series), P: property row (Series). Returns list of dict(step,title,lines,date,status,source)."""
    out = []

    def add(n, lines, date=None, status="done"):
        out.append({"step": n, "title": STEPS[n - 1][1], "lines": lines, "date": date if ok(date) else None, "status": status, "source": SOURCE[n]})

    name = f"{C.first_name} {C.last_name}"
    add(1, [f"{name} · customer_id = {C.customer_id}",
            f"{C.customer_status.title()} policyholder since {pd.Timestamp(C.customer_since).year} · owns {int(C.properties)} insured propert{'y' if C.properties == 1 else 'ies'} · agent {C.agent_name}"],
        C.customer_since)
    add(2, [f"{P.address_line} · property_id = {P.property_id}",
            f"Construction band {P.construction_date_band}" + (" · elevated building" if P.elevated else " · not elevated")])
    add(3, [f"USA → {P.state} → {P.county} County → {P.city}", f"ZIP {P.zip_code}"])
    sfha = str(P.flood_zone)[:1] in "AV"
    lines4 = [f"Flood Zone {P.flood_zone} ({'high-risk SFHA' if sfha else 'lower-risk'}) → {P.construction_date_band} · Community CRS Class {int(P.crs_class)}",
              f"County: #{int(P.county_rank)} by insured value ({P.county_share_of_portfolio:.1%} of portfolio) · {int(P.county_declared_disasters_window)} declared disasters in window"
              + (f" · last in {int(P.county_last_declared_year)}" if ok(P.county_last_declared_year) else "")]
    if ok(P.assessed_risk_score):
        lines4.append(f"Assessed risk score {P.assessed_risk_score:.0f} ({P.assessed_risk_band})")
    add(4, lines4)
    add(5, ["No quote or application table exists in the Gold layer.", "Pricing that resulted from the quote is visible in step 7 (active premium and coverage)."], None, "gap")
    add(6, ["No underwriting decision (accept / decline) exists in the Gold layer.",
            f"Risk on file for this property: {('score %.0f (%s)' % (P.assessed_risk_score, P.assessed_risk_band)) if ok(P.assessed_risk_score) else 'not assessed'}"], None, "gap")
    if ok(P.active_policy_id):
        add(7, [f"Policy {P.active_policy_id} · expires {d(P.policy_expiration_date)} · {int(P.policy_terms)} policy term{'s' if P.policy_terms != 1 else ''} to date",
                f"Building {usd(P.active_building_coverage)} + contents {usd(P.active_contents_coverage)} · active premium {usd(P.active_premium)} (incl. fees)"], None)
    else:
        add(7, [f"No active policy on {d(as_of)} · {int(P.policy_terms)} past term{'s' if P.policy_terms != 1 else ''}"], None, "stop")
    add(8, ["Endorsements and mid-term changes are not in the Gold layer."], None, "gap")
    if P.claims_total > 0:
        add(9, [f"{int(P.claims_total)} claim{'s' if P.claims_total != 1 else ''} on this property · {int(P.claims_open)} open · {usd(P.claims_paid_total)} paid",
                f"Last date of loss {d(P.last_loss_date)} (FNOL date is not in Gold)"], P.last_loss_date)
        add(10, [f"Property record: total claims = {int(P.claims_total)}",
                 "Flagged repetitive loss (nfip_rl = true)" if P.nfip_rl else f"Not flagged repetitive loss (nfip_rl = false: {int(P.claims_total)} claim{'s' if P.claims_total != 1 else ''})"], P.last_loss_date)
    else:
        add(9, ["No loss events on this property"], None, "none")
        add(10, ["Property record: 0 claims, nfip_rl = false"], None, "none")
    if P.mitigation_count > 0:
        add(11, [f"{int(P.mitigation_count)} mitigation action{'s' if P.mitigation_count != 1 else ''} recorded on this property",
                 f"County context: {int(P.county_hma_projects)} HMA projects · {usd(P.county_hma_obligated)} obligated"])
    else:
        add(11, ["No mitigation recorded", f"County context: {int(P.county_hma_projects)} HMA projects · {usd(P.county_hma_obligated)} obligated"], None, "none")
    if ok(P.policy_expiration_date):
        days = (pd.Timestamp(P.policy_expiration_date) - pd.Timestamp(as_of)).days
        flag = "renewal due within 60 days" if days <= 60 else "renewal not yet due"
        pend = " · renewal decision PENDING" if C.renewal_pending and days == C.days_to_renewal else ""
        add(12, [f"Next renewal {d(P.policy_expiration_date)} ({days} days) · {flag}{pend}"], P.policy_expiration_date)
    else:
        add(12, ["No active term to renew"], None, "none")
    return out
