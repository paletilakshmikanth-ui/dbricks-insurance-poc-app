"""Demo data in the EXACT shape of gold_customer_profile / gold_property_profile / gold_policy_report / gold_claim_report
(from Synthetic_Data_To_Gold). Used only when GENIE_SPACE_ID is not set. Maria Chen matches the notebook's own check."""
import datetime as dt
import numpy as np
import pandas as pd

AS_OF = pd.Timestamp("2026-10-09")
rng = np.random.default_rng(5)
rng_l = np.random.default_rng(31)     # lapses
rng_g = np.random.default_rng(11)     # map jitter
rng_c = np.random.default_rng(21)     # claim lifecycle
# state, county, city, zip, weight, flood-zone mix [AE, VE, A, X, B]
GEO = [("TX", "Harris", "Baytown", "77520", 6, [.45, .05, .1, .35, .05]), ("TX", "Galveston", "Galveston", "77550", 3, [.4, .25, .1, .2, .05]),
       ("TX", "Brazoria", "Freeport", "77541", 2, [.4, .15, .1, .3, .05]), ("LA", "Jefferson", "Metairie", "70001", 4, [.5, .05, .15, .25, .05]),
       ("LA", "Orleans", "New Orleans", "70112", 3, [.45, .05, .15, .3, .05]), ("FL", "Miami-Dade", "Miami", "33101", 7, [.35, .25, .1, .25, .05]),
       ("FL", "Lee", "Fort Myers", "33901", 4, [.4, .2, .1, .25, .05]), ("FL", "Hillsborough", "Tampa", "33602", 3, [.35, .15, .1, .35, .05]),
       ("NC", "New Hanover", "Wilmington", "28401", 3, [.35, .15, .1, .35, .05]), ("NC", "Dare", "Nags Head", "27959", 2, [.3, .3, .1, .25, .05]),
       ("SC", "Charleston", "Charleston", "29401", 3, [.4, .15, .1, .3, .05]), ("SC", "Horry", "Myrtle Beach", "29577", 2, [.35, .2, .1, .3, .05])]
# approximate city-centre coordinates, same order as GEO (demo only)
COORD = [(29.735, -94.977), (29.301, -94.797), (28.954, -95.359), (29.984, -90.153), (29.951, -90.071), (25.762, -80.192),
         (26.640, -81.872), (27.951, -82.457), (34.226, -77.945), (35.957, -75.624), (32.777, -79.931), (33.689, -78.887)]
ADJUSTERS = [("ADJ-01", "Grace Whitfield"), ("ADJ-02", "Marcus Odum"), ("ADJ-03", "Selin Kaya"), ("ADJ-04", "Diego Salazar"), ("ADJ-05", "Fatima Noor")]
ZONES = ["AE", "VE", "A", "X", "B"]
CRS = {"AE": 7, "VE": 6, "A": 7, "X": 8, "B": 8}
ZONE_RATE = {"VE": 2.4, "AE": 1.5, "A": 1.3, "B": .7, "X": .5}
ZONE_CLAIM = {"VE": .2, "AE": .12, "A": .1, "B": .05, "X": .03}
ZONE_RISK = {"VE": 62, "AE": 50, "A": 44, "B": 22, "X": 15}
FIRST = ["Alex", "Sam", "Priya", "Jordan", "Lee", "Chris", "Dana", "Riley", "Noor", "Omar", "Elena", "Kai", "Mia", "Ravi", "Zoe", "Ana", "Ben", "Cora"]
LAST = ["Nguyen", "Patel", "Garcia", "Smith", "Johnson", "Brown", "Lopez", "Kim", "Davis", "Clark", "Reyes", "Singh", "Walker", "Young"]
AGENTS = [("AGT-01", "Hannah Brooks"), ("AGT-02", "Luis Ortega"), ("AGT-03", "Aisha Rahman"), ("AGT-04", "Tom Becker"), ("AGT-05", "Mei Lin")]
_cache = {}


def band(s):
    return "High" if s >= 66 else "Medium" if s >= 33 else "Low"


def build(n_customers=700):
    w = np.array([g[4] for g in GEO], float); w /= w.sum()
    props, pols, clms, custs = [], [], [], []
    pol_seq = clm_seq = 0
    specs = []
    # --- Maria Chen exactly as in the business-process PDF ---
    specs.append(dict(cid="CUST-10492", fn="Maria", ln="Chen", since=dt.date(2019, 3, 1), agent=AGENTS[0], props=[dict(
        pid="PROP-58210", addr="214 Riverbend Lane", gi=0, zone="AE", band="Pre-FIRM", elevated=False, eff=pd.Timestamp("2024-03-01"), bcov=250000., ccov=100000., base=1850.,
        claim=("2024-09-12", 17250.0, "CLOSED"), mit=2, risk=58.0, rl=False)]))
    for i in range(n_customers):
        cid = f"CUST-{20000 + i}"
        since = dt.date(int(rng.integers(2017, 2026)), int(rng.integers(1, 13)), int(rng.integers(1, 28)))
        plist = []
        for k in range(int(rng.choice([1, 2, 3], p=[.8, .17, .03]))):
            gi = int(rng.choice(len(GEO), p=w)); zone = str(rng.choice(ZONES, p=GEO[gi][5]))
            first_eff = pd.Timestamp(since) + pd.Timedelta(days=int(rng.integers(5, 30)))
            plist.append(dict(pid=f"PROP-{60000 + len(props) + len(specs) * 5 + k + i * 4}", addr=f"{int(rng.integers(10, 999))} {rng.choice(['Oak', 'Bay', 'Harbor', 'Pine', 'Cedar', 'Lake'])} St",
                              gi=gi, zone=zone, band=str(rng.choice(["Pre-FIRM", "Post-FIRM"], p=[.45, .55])), elevated=bool(rng.random() < .15), eff=first_eff,
                              bcov=float(rng.choice([100e3, 150e3, 200e3, 250e3, 350e3, 500e3], p=[.15, .2, .2, .25, .1, .1])), ccov=float(rng.choice([25e3, 50e3, 75e3, 100e3], p=[.25, .35, .2, .2])),
                              base=None, claim=None, mit=None, risk=None, rl=None))
        specs.append(dict(cid=cid, fn=str(rng.choice(FIRST)), ln=str(rng.choice(LAST)), since=since, agent=AGENTS[int(rng.integers(0, len(AGENTS)))], props=plist))
    seen = set()
    for sp in specs:
        for p in sp["props"]:
            while p["pid"] in seen:
                p["pid"] += "x"
            seen.add(p["pid"])
    rows_p = []
    for sp in specs:
        for p in sp["props"]:
            st_, cty, city, zp, _, _ = GEO[p["gi"]]
            if p["base"] is None:
                p["base"] = round((p["bcov"] + p["ccov"]) * .0055 * ZONE_RATE[p["zone"]] * (1.15 if p["band"] == "Pre-FIRM" else 1), 0)
            terms, eff = [], p["eff"]
            while eff < AS_OF:
                if terms and p["claim"] is None and rng_l.random() < .03:
                    break                                   # lapsed: did not renew
                pol_seq += 1
                terms.append(dict(pid=f"POL-{eff.year}-{zp}-{pol_seq:04d}", eff=eff, exp=eff + pd.DateOffset(years=1), prem=round(p["base"] * (1 + .01 * len(terms)), 2)))
                eff = eff + pd.DateOffset(years=1)
            cl = []
            if p["claim"] is not None:
                ld, paid, stt = p["claim"]; cl.append((pd.Timestamp(ld), paid, stt))
            else:
                for tm in terms:
                    if rng.random() < ZONE_CLAIM[p["zone"]]:
                        ld = tm["eff"] + pd.Timedelta(days=int(rng.integers(20, 340)))
                        if ld < AS_OF:
                            stt = "OPEN" if (AS_OF - ld).days < 120 and rng.random() < .8 else ("DENIED" if rng.random() < .08 else "CLOSED")
                            amt = 0.0 if stt in ("OPEN", "DENIED") else float(round(min(rng.lognormal(9.7, .9), p["bcov"]), -1))
                            cl.append((ld, amt, stt))
            p["terms"], p["claims"] = terms, cl
            if p["mit"] is None:
                p["mit"] = int(rng.random() < (.3 if cl else .08)) + int(rng.random() < .05)
            if p["risk"] is None:
                p["risk"] = float(np.clip(ZONE_RISK[p["zone"]] + (12 if p["band"] == "Pre-FIRM" else 0) + 8 * len(cl) - 8 * p["mit"] + rng.normal(0, 8), 2, 99).round(1))
            if p["rl"] is None:
                p["rl"] = len([c for c in cl if c[2] == "CLOSED"]) >= 2
            for tm in terms:
                pols.append((tm["pid"], st_, f"{48000 + p['gi']}", city, tm["eff"], tm["exp"], p["bcov"], p["ccov"], tm["prem"], sp["cid"], p["pid"]))
            for ld, amt, stt in cl:
                clm_seq += 1
                pl = [t for t in terms if t["eff"] <= ld < t["exp"]]
                pid_ = pl[0]["pid"] if pl else terms[-1]["pid"]
                clms.append((f"CLM-{ld.year}-{80000 + clm_seq}", pid_, st_, city, ld, ld.year, amt, 0.0, 0.0, p["bcov"], p["ccov"], stt))
            rows_p.append((sp, p))
    # county context
    cty = {}
    for sp, p in rows_p:
        k = p["gi"]; c = cty.setdefault(k, dict(insured=0., terms=0, paid=0.))
        c["terms"] += len(p["terms"]); c["paid"] += sum(a for _, a, _ in p["claims"])
        a = next((t for t in p["terms"] if t["eff"] <= AS_OF < t["exp"]), None)
        if a: c["insured"] += p["bcov"] + p["ccov"]
    tot = sum(c["insured"] for c in cty.values()) or 1
    rank = {k: i + 1 for i, k in enumerate(sorted(cty, key=lambda k: -cty[k]["insured"]))}
    ctx = {k: dict(dis=int(rng.integers(2, 9)), last=int(rng.integers(2019, 2026)), hma=int(rng.integers(3, 40)), hma_amt=float(rng.uniform(2e6, 80e6))) for k in cty}
    prop_rows = []
    for sp, p in rows_p:
        st_, cty_n, city, zp, _, _ = GEO[p["gi"]]; k = p["gi"]; c = cty[k]
        a = next((t for t in p["terms"] if t["eff"] <= AS_OF < t["exp"]), None)
        ncl = len(p["claims"]); opn = sum(1 for _, _, s in p["claims"] if s == "OPEN")
        prop_rows.append(dict(property_id=p["pid"], customer_id=sp["cid"], address_line=p["addr"], city=city, zip_code=zp, state=st_, county=cty_n, flood_zone=p["zone"], construction_date_band=p["band"],
            elevated=p["elevated"], crs_class=CRS[p["zone"]], active_policy_id=a["pid"] if a else None, policy_expiration_date=a["exp"] if a else pd.NaT,
            active_building_coverage=p["bcov"] if a else np.nan, active_contents_coverage=p["ccov"] if a else np.nan, active_premium=(a["prem"] + 50) if a else np.nan,
            latitude=round(COORD[k][0] + rng_g.normal(0, .035), 5), longitude=round(COORD[k][1] + rng_g.normal(0, .035), 5),
            policy_terms=len(p["terms"]), claims_total=ncl, claims_open=opn, claims_paid_total=sum(x for _, x, _ in p["claims"]), last_loss_date=max((d for d, _, _ in p["claims"]), default=pd.NaT),
            nfip_rl=p["rl"], mitigation_count=p["mit"], assessed_risk_score=p["risk"], assessed_risk_band=band(p["risk"]), county_declared_disasters_window=ctx[k]["dis"],
            county_last_declared_year=ctx[k]["last"], county_hma_projects=ctx[k]["hma"], county_hma_obligated=ctx[k]["hma_amt"], county_insured_value=c["insured"],
            county_share_of_portfolio=round(c["insured"] / tot, 4), county_rank=rank[k], county_claims_paid_per_policy=round(c["paid"] / max(c["terms"], 1), 2)))
    P = pd.DataFrame(prop_rows)
    pending_ids = set(P.active_policy_id.dropna().sample(frac=.05, random_state=2))
    cust_rows = []
    for sp in specs:
        pr = P[P.customer_id == sp["cid"]]
        act = pr[pr.active_policy_id.notna()]
        nxt = act.policy_expiration_date.min() if len(act) else pd.NaT
        d2r = int((nxt - AS_OF).days) if pd.notna(nxt) else None
        prim = (act if len(act) else pr).sort_values("active_building_coverage", ascending=False, na_position="last").iloc[0]
        hi = pr.sort_values("assessed_risk_score", ascending=False).iloc[0]
        cust_rows.append(dict(customer_id=sp["cid"], first_name=sp["fn"], last_name=sp["ln"], customer_status="ACTIVE" if len(act) else "LAPSED", customer_since=pd.Timestamp(sp["since"]),
            agent_id=sp["agent"][0], agent_name=sp["agent"][1], properties=len(pr), states=pr.state.nunique(), active_policies=len(act), policy_terms_total=int(pr.policy_terms.sum()),
            building_coverage_active=act.active_building_coverage.sum(), contents_coverage_active=act.active_contents_coverage.sum(), premium_active=act.active_premium.sum(),
            next_renewal_date=nxt, days_to_renewal=d2r, renewal_due_60d=bool(d2r is not None and d2r <= 60), renewal_pending=bool(set(act.active_policy_id) & pending_ids),
            claims_total=int(pr.claims_total.sum()), claims_open=int(pr.claims_open.sum()), claims_paid_total=pr.claims_paid_total.sum(), last_loss_date=pr.last_loss_date.max(),
            mitigation_count=int(pr.mitigation_count.sum()), primary_property_id=prim.property_id, primary_county=prim.county, primary_state=prim.state, highest_risk_score=hi.assessed_risk_score,
            highest_risk_band=band(hi.assessed_risk_score), highest_risk_property_id=hi.property_id, in_special_flood_hazard_area=bool(pr.flood_zone.str[0].isin(list("AV")).any()),
            pre_firm_properties=int((pr.construction_date_band == "Pre-FIRM").sum()), insured_value_active=(act.active_building_coverage + act.active_contents_coverage).sum(),
            primary_county_insured_value=prim.county_insured_value, primary_county_share=prim.county_share_of_portfolio, primary_county_rank=prim.county_rank,
            primary_county_declared_disasters_window=prim.county_declared_disasters_window, primary_county_last_declared_year=prim.county_last_declared_year,
            primary_county_hma_projects=prim.county_hma_projects, primary_county_claims_paid_per_policy=prim.county_claims_paid_per_policy))
    C = pd.DataFrame(cust_rows)
    PO = pd.DataFrame(pols, columns=["policy_id", "state", "county_code", "community_name", "policy_effective_date", "policy_termination_date", "total_building_insurance_coverage",
                                     "total_contents_insurance_coverage", "total_insurance_premium", "customer_id", "property_id"])
    CL = pd.DataFrame(clms, columns=["claim_id", "policy_id", "state", "community_name", "date_of_loss", "year_of_loss", "amount_paid_on_building_claim", "amount_paid_on_contents_claim",
                                     "amount_paid_on_icc_claim", "total_building_insurance_coverage", "total_contents_insurance_coverage", "claim_status"])
    CL = _lifecycle(CL)
    return {"customer_profile": C, "property_profile": P, "policy_report": PO, "claim_report": CL}


def _lifecycle(CL):
    """Demo-only claim lifecycle columns (reported / closed dates, adjuster). Not in the real Gold tables yet: see README."""
    n_ = len(CL)
    rep_ = CL.date_of_loss + pd.to_timedelta(rng_c.integers(0, 11, n_), unit="D")
    dur = np.exp(rng_c.normal(np.log(42), .55, n_)) * np.where(CL.year_of_loss.isin([2022, 2024]), 1.5, 1.0)     # catastrophe years close slower
    closed = (rep_ + pd.to_timedelta(dur.round(), unit="D")).clip(upper=AS_OF - pd.Timedelta(days=1))
    is_open = CL.claim_status.eq("OPEN")
    adj = rng_c.choice(len(ADJUSTERS), n_, p=[.28, .24, .2, .16, .12])
    return CL.assign(date_reported=rep_, date_closed=closed.where(~is_open, pd.NaT), adjuster_id=[ADJUSTERS[i][0] for i in adj], adjuster_name=[ADJUSTERS[i][1] for i in adj])


def get():
    if not _cache:
        _cache.update(build())
    return _cache


def disasters():
    return pd.DataFrame({"incident_type": ["Hurricane", "Flood", "Severe Storm", "Tropical Storm"], "claims": [610, 420, 150, 140], "paid": [21.4e6, 9.8e6, 3.1e6, 2.6e6]})
