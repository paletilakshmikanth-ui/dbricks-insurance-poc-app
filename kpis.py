"""Insurance KPIs computed from the four Gold tables. Pure pandas (no Streamlit) so it can be tested on its own.

Definitions used everywhere in the dashboard
  earned premium   written premium x share of the policy term that has elapsed by the as-of date
  paid loss ratio  claims paid / earned premium        (paid only: the Gold tables carry no reserves, so this is NOT an incurred loss ratio)
  credibility Z    sqrt(min(1, policy-years / full-credibility policy-years))   (limited-fluctuation credibility)
  adjusted LR      Z x own loss ratio + (1 - Z) x portfolio loss ratio          (what to rank customers by: small books are pulled to the portfolio)
"""
import numpy as np
import pandas as pd

SLA_DAYS = 60            # an open claim older than this is "past SLA" (editable on the Claims Desk page)
FULL_CRED_YEARS = 10     # policy-years of history at which a customer's own loss ratio is fully credible (editable on the Loss Ratios page)
AGE_BINS = [-1, 30, 60, 90, 10 ** 6]
AGE_LABELS = ["0-30 d", "31-60 d", "61-90 d", "90+ d"]


def has(df, *cols):
    """True when every column exists and holds at least one value (optional Gold columns come back empty when Gold lacks them)."""
    return all(c in df.columns and df[c].notna().any() for c in cols)


def safe_div(a, b):
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    out = np.full(np.broadcast(a, b).shape, np.nan)
    np.divide(a, b, out=out, where=(b != 0) & ~np.isnan(b))
    return out if out.ndim else float(out)


# ------------------------------------------------------------------ premium and exposure
def earned_terms(PO, as_of):
    """One row per policy term with earned premium and policy-years to the as-of date."""
    t = PO.copy()
    eff, exp = t.policy_effective_date, t.policy_termination_date
    length = (exp - eff).dt.days.clip(lower=1)
    elapsed = (as_of - eff).dt.days.clip(lower=0)
    share = np.minimum(elapsed / length, 1.0).where(eff.notna() & exp.notna(), 0.0)
    return t.assign(earned_premium=t.total_insurance_premium.fillna(0) * share, policy_years=share * length / 365.25)


def yearly(PO, CL, as_of):
    """Portfolio by calendar year: earned premium (pro-rata across years), claims paid by year of loss, loss ratio, and the cumulative loss ratio.
    The cumulative line is the one that settles down as years are added; single years swing with catastrophe events."""
    t = earned_terms(PO, as_of)
    t = t[t.policy_effective_date.notna() & t.policy_termination_date.notna()]
    rows = []
    for y in range(int(t.policy_effective_date.dt.year.min()), int(as_of.year) + 1):
        a = pd.Timestamp(y, 1, 1)
        lo, hi = t.policy_effective_date.clip(lower=a), t.policy_termination_date.clip(upper=min(pd.Timestamp(y + 1, 1, 1), as_of))
        days = (hi - lo).dt.days.clip(lower=0)
        length = (t.policy_termination_date - t.policy_effective_date).dt.days.clip(lower=1)
        rows.append((y, float((t.total_insurance_premium.fillna(0) * days / length).sum())))
    out = pd.DataFrame(rows, columns=["year", "earned_premium"]).set_index("year")
    paid = CL.groupby(CL.date_of_loss.dt.year).agg(paid=("paid", "sum"), claims=("claim_id", "count"))
    out = out.join(paid, how="left").fillna({"paid": 0.0, "claims": 0}).reset_index()
    out["loss_ratio"] = safe_div(out.paid, out.earned_premium)
    out["cum_loss_ratio"] = safe_div(out.paid.cumsum(), out.earned_premium.cumsum())
    return out[out.earned_premium > 0]


def window_lr(PO, CL, as_of, days):
    """Loss ratio over the trailing window: claims with date of loss in the window / premium earned in the window."""
    start = as_of - pd.Timedelta(days=days)
    t = PO[PO.policy_effective_date.notna() & PO.policy_termination_date.notna()]
    length = (t.policy_termination_date - t.policy_effective_date).dt.days.clip(lower=1)
    lo, hi = t.policy_effective_date.clip(lower=start), t.policy_termination_date.clip(upper=as_of)
    prem = (t.total_insurance_premium.fillna(0) * (hi - lo).dt.days.clip(lower=0) / length).sum()
    paid = CL[(CL.date_of_loss > start) & (CL.date_of_loss <= as_of)].paid.sum()
    return float(safe_div(paid, prem)), float(paid), float(prem)


# ------------------------------------------------------------------ property-level loss ratio frame (everything else is a group-by on this)
def property_lr(P, PO, CL, as_of):
    """Returns (frame, mode). One row per property with earned premium, paid, claims, policy-years and the property's dimensions.
    mode 'exact'  : policy_report carries property_id, so premium and claims are summed over every policy term.
    mode 'approx' : it does not, so premium is estimated as current premium x number of terms (lapsed properties have none), claims from the profile."""
    dims = ["property_id", "customer_id", "state", "county", "city", "flood_zone", "construction_date_band", "elevated", "assessed_risk_band", "assessed_risk_score", "latitude", "longitude"]
    base = P[[c for c in dims if c in P.columns]].copy()
    if has(PO, "property_id"):
        T = earned_terms(PO, as_of)
        prem = T.groupby("property_id").agg(earned_premium=("earned_premium", "sum"), policy_years=("policy_years", "sum"), terms=("policy_id", "count"))
        pmap = PO.drop_duplicates("policy_id").set_index("policy_id").property_id
        c = CL.assign(property_id=CL.policy_id.map(pmap))
        clm = c.groupby("property_id").agg(paid=("paid", "sum"), claims=("claim_id", "count"))
        df = base.merge(prem, on="property_id", how="left").merge(clm, on="property_id", how="left")
        mode = "exact"
    else:
        df = base.merge(P[["property_id", "active_premium", "policy_terms", "claims_paid_total", "claims_total"]], on="property_id", how="left")
        df = df.assign(earned_premium=df.active_premium.fillna(0) * df.policy_terms.fillna(0), policy_years=df.policy_terms.fillna(0), terms=df.policy_terms.fillna(0),
                       paid=df.claims_paid_total.fillna(0), claims=df.claims_total.fillna(0)).drop(columns=["active_premium", "policy_terms", "claims_paid_total", "claims_total"])
        mode = "approx"
    for c_ in ("earned_premium", "policy_years", "terms", "paid", "claims"):
        df[c_] = df[c_].fillna(0)
    return df, mode


def credibility(years, full=FULL_CRED_YEARS):
    return np.sqrt(np.minimum(1.0, np.asarray(years, dtype=float) / max(full, 1e-9)))


def by_dim(PL, dim, full=FULL_CRED_YEARS, portfolio_lr=None):
    """Loss ratio table for any dimension (customer_id, state, county, flood_zone, assessed_risk_band, agent_name ...)."""
    g = PL.groupby(dim, dropna=False).agg(properties=("property_id", "nunique"), earned_premium=("earned_premium", "sum"), paid=("paid", "sum"), claims=("claims", "sum"),
                                         policy_years=("policy_years", "sum")).reset_index()
    port = safe_div(PL.paid.sum(), PL.earned_premium.sum()) if portfolio_lr is None else portfolio_lr
    g["loss_ratio"] = safe_div(g.paid, g.earned_premium)
    g["credibility"] = credibility(g.policy_years, full)
    g["adj_loss_ratio"] = np.where(np.isnan(g.loss_ratio), np.nan, g.credibility * np.nan_to_num(g.loss_ratio) + (1 - g.credibility) * port)
    g["frequency"] = safe_div(g.claims, g.policy_years)
    g["severity"] = safe_div(g.paid, g.claims)
    return g


# ------------------------------------------------------------------ claim operations
def claim_ops(CL, PO, P, C, as_of, sla=SLA_DAYS):
    """Claim-level frame for the Claims Desk / Management pages. Needs claim_status, date_reported and date_closed (optional Gold columns)."""
    d = CL.copy()
    if has(d, "claim_status"):
        d["status"] = d.claim_status.fillna("UNKNOWN").str.upper()
    else:
        d["status"] = np.where(d.paid > 0, "CLOSED", "OPEN")       # fallback only: paid > 0 is treated as settled
    rep = d.date_reported if has(d, "date_reported") else d.date_of_loss
    d["is_open"] = d.status.eq("OPEN")
    d["days_open"] = np.where(d.is_open, (as_of - rep).dt.days, np.nan)
    d["days_to_close"] = (d.date_closed - rep).dt.days if has(d, "date_closed") else np.nan
    d["days_to_report"] = (rep - d.date_of_loss).dt.days
    d["age_bucket"] = pd.cut(d.days_open, AGE_BINS, labels=AGE_LABELS)
    d["past_sla"] = d.is_open & (d.days_open > sla)
    pol = PO.drop_duplicates("policy_id").set_index("policy_id")
    d["policy_effective_date"] = d.policy_id.map(pol.policy_effective_date)
    d["loss_within_30d_of_inception"] = (d.date_of_loss - d.policy_effective_date).dt.days.between(0, 30)     # NFIP has a 30-day waiting period
    d["coverage"] = d.total_building_insurance_coverage.fillna(0) + d.total_contents_insurance_coverage.fillna(0)
    d["coverage_used"] = safe_div(d.paid, d.coverage)
    if has(PO, "property_id"):
        d["property_id"] = d.policy_id.map(pol.property_id)
        d["customer_id"] = d.policy_id.map(pol.customer_id)
        pr = P.drop_duplicates("property_id").set_index("property_id")
        for col in ("address_line", "city", "county", "flood_zone", "assessed_risk_band", "nfip_rl", "mitigation_count", "elevated"):
            if col in pr.columns:
                d[col] = d.property_id.map(pr[col])
        d["claims_on_property"] = d.groupby("property_id").claim_id.transform("count")
        d["customer"] = d.customer_id.map(dict(zip(C.customer_id, C.first_name.fillna("") + " " + C.last_name.fillna(""))))
    return d


def ops_summary(D):
    """Headline operational numbers from claim_ops()."""
    closed = D[D.days_to_close.notna()]
    opn = D[D.is_open]
    return dict(open=int(len(opn)), open_avg_age=float(opn.days_open.mean()) if len(opn) else np.nan, past_sla=int(D.past_sla.sum()),
                median_close=float(closed.days_to_close.median()) if len(closed) else np.nan, p90_close=float(closed.days_to_close.quantile(.9)) if len(closed) else np.nan,
                closed_30=float((closed.days_to_close <= 30).mean()) if len(closed) else np.nan, closed_60=float((closed.days_to_close <= 60).mean()) if len(closed) else np.nan,
                denial_rate=float(D.status.eq("DENIED").sum() / max(len(D), 1)), report_lag=float(D.days_to_report.median()) if len(D) else np.nan,
                avg_open_paid=float(opn.paid.mean()) if len(opn) else np.nan)


def by_adjuster(D):
    g = D.groupby("adjuster_name").agg(claims=("claim_id", "count"), open=("is_open", "sum"), past_sla=("past_sla", "sum"), avg_age_open=("days_open", "mean"),
                                       median_days_to_close=("days_to_close", "median"), paid=("paid", "sum")).reset_index()
    g["closed_per_open"] = safe_div(g.claims - g.open, g.open)
    return g.sort_values("open", ascending=False)


def close_trend(D, freq="Q"):
    """Median days to close by quarter in which the claim was closed."""
    c = D[D.date_closed.notna() & D.days_to_close.notna()]
    if c.empty:
        return pd.DataFrame(columns=["period", "median_days", "p90_days", "closed"])
    g = c.groupby(c.date_closed.dt.to_period(freq)).days_to_close.agg(median_days="median", p90_days=lambda s: s.quantile(.9), closed="count").reset_index()
    g["period"] = g.date_closed.astype(str)
    return g[["period", "median_days", "p90_days", "closed"]]


# ------------------------------------------------------------------ risk weighting, concentration, retention
def risk_weighting(ACT, PL, port_lr):
    """By risk band: premium share vs risk-weighted exposure share. Adequacy > 1 = premium is ahead of the risk it carries, < 1 = behind it.
    Risk-weighted exposure = insured value x risk score / 100 (the POC risk score is a 0-100 index, not a probability)."""
    a = ACT.dropna(subset=["assessed_risk_band", "assessed_risk_score"]).copy()
    a["rw"] = a.coverage * a.assessed_risk_score / 100
    g = a.groupby("assessed_risk_band").agg(policies=("property_id", "count"), coverage=("coverage", "sum"), premium=("active_premium", "sum"), rw_exposure=("rw", "sum")).reset_index()
    g["prem_share"], g["rw_share"] = g.premium / g.premium.sum(), g.rw_exposure / g.rw_exposure.sum()
    g["adequacy"] = safe_div(g.prem_share, g.rw_share)
    g["rate_per_1k"] = safe_div(g.premium, g.coverage) * 1000
    lr = by_dim(PL, "assessed_risk_band", portfolio_lr=port_lr)[["assessed_risk_band", "loss_ratio", "claims", "paid"]]
    g = g.merge(lr, on="assessed_risk_band", how="left")
    order = {"High": 0, "Medium": 1, "Low": 2}
    return g.sort_values("assessed_risk_band", key=lambda s: s.map(order))


def concentration(ACT, by="county"):
    """Share of active insured value by area, top-3 share and the Herfindahl index (0-1; above ~0.25 is highly concentrated)."""
    g = ACT.groupby(by).coverage.sum().sort_values(ascending=False)
    s = g / g.sum() if g.sum() else g
    return dict(top3=float(s.head(3).sum()), hhi=float((s ** 2).sum()), table=s.rename("share").reset_index())


def renewal_rate(PO, as_of, grace=60):
    """Share of policy terms that were followed by another term on the same property within `grace` days. Needs property_id on the policy table.
    Terms that expired in the last `grace` days are left out (they may still renew)."""
    if not has(PO, "property_id"):
        return None
    t = PO.dropna(subset=["property_id"]).sort_values(["property_id", "policy_effective_date"]).copy()
    t["next_eff"] = t.groupby("property_id").policy_effective_date.shift(-1)
    t = t[t.policy_termination_date <= as_of - pd.Timedelta(days=grace)]
    t["renewed"] = (t.next_eff - t.policy_termination_date).dt.days.le(grace) & t.next_eff.notna()
    g = t.groupby(t.policy_termination_date.dt.year).renewed.agg(rate="mean", terms="count").reset_index().rename(columns={"policy_termination_date": "year"})
    return dict(rate=float(t.renewed.mean()) if len(t) else np.nan, by_year=g)
