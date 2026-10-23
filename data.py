"""Gold datasets for the dashboard.

Source of truth is a Genie space (GENIE_SPACE_ID) that you attach manually; if it is not set the app runs on built-in demo data
with the SAME columns, so the UI can be tested first. Each dataset is ONE Genie question, cached for an hour and shared by all sessions.
"""
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

CATALOG = os.getenv("GOLD_CATALOG", "synthetic")
SCHEMA = os.getenv("GOLD_SCHEMA", "gold2")
SPACE_ID = os.getenv("GENIE_SPACE_ID", "").strip()
CACHE_TTL = int(os.getenv("CACHE_TTL_SECONDS", "3600"))

# Column types copied from Synthetic_Data_To_Gold: s string, i int, l bigint, n decimal, f double, b boolean, d date
SPEC = {
    "customer_profile": ("gold_customer_profile", [("customer_id", "s"), ("first_name", "s"), ("last_name", "s"), ("customer_status", "s"), ("customer_since", "d"), ("agent_id", "s"), ("agent_name", "s"),
        ("properties", "i"), ("states", "i"), ("active_policies", "i"), ("policy_terms_total", "i"), ("building_coverage_active", "n"), ("contents_coverage_active", "n"), ("premium_active", "n"),
        ("next_renewal_date", "d"), ("days_to_renewal", "i"), ("renewal_due_60d", "b"), ("renewal_pending", "b"), ("claims_total", "i"), ("claims_open", "i"), ("claims_paid_total", "n"), ("last_loss_date", "d"),
        ("mitigation_count", "i"), ("primary_property_id", "s"), ("primary_county", "s"), ("primary_state", "s"), ("highest_risk_score", "f"), ("highest_risk_band", "s"), ("highest_risk_property_id", "s"),
        ("in_special_flood_hazard_area", "b"), ("pre_firm_properties", "i"), ("insured_value_active", "n"), ("primary_county_insured_value", "n"), ("primary_county_share", "f"), ("primary_county_rank", "i"),
        ("primary_county_declared_disasters_window", "i"), ("primary_county_last_declared_year", "i"), ("primary_county_hma_projects", "i"), ("primary_county_claims_paid_per_policy", "f")]),
    "property_profile": ("gold_property_profile", [("property_id", "s"), ("customer_id", "s"), ("address_line", "s"), ("city", "s"), ("zip_code", "s"), ("state", "s"), ("county", "s"), ("flood_zone", "s"),
        ("construction_date_band", "s"), ("elevated", "b"), ("crs_class", "i"), ("active_policy_id", "s"), ("policy_expiration_date", "d"), ("active_building_coverage", "n"), ("active_contents_coverage", "n"),
        ("active_premium", "n"), ("policy_terms", "i"), ("claims_total", "i"), ("claims_open", "i"), ("claims_paid_total", "n"), ("last_loss_date", "d"), ("nfip_rl", "b"), ("mitigation_count", "i"),
        ("assessed_risk_score", "f"), ("assessed_risk_band", "s"), ("county_declared_disasters_window", "i"), ("county_last_declared_year", "i"), ("county_hma_projects", "i"), ("county_hma_obligated", "n"),
        ("county_insured_value", "n"), ("county_share_of_portfolio", "f"), ("county_rank", "i"), ("county_claims_paid_per_policy", "f"),
        ("latitude", "f"), ("longitude", "f")]),
    "policy_report": ("gold_policy_report", [("policy_id", "s"), ("state", "s"), ("county_code", "s"), ("community_name", "s"), ("policy_effective_date", "d"), ("policy_termination_date", "d"),
        ("total_building_insurance_coverage", "n"), ("total_contents_insurance_coverage", "n"), ("total_insurance_premium", "n"),
        ("customer_id", "s"), ("property_id", "s")]),
    "claim_report": ("gold_claim_report", [("claim_id", "s"), ("policy_id", "s"), ("state", "s"), ("community_name", "s"), ("date_of_loss", "d"), ("year_of_loss", "i"),
        ("amount_paid_on_building_claim", "n"), ("amount_paid_on_contents_claim", "n"), ("amount_paid_on_icc_claim", "n"), ("total_building_insurance_coverage", "n"), ("total_contents_insurance_coverage", "n"),
        ("claim_status", "s"), ("date_reported", "d"), ("date_closed", "d"), ("adjuster_id", "s"), ("adjuster_name", "s")]),
}
# Columns the Gold tables do not have yet. If Genie does not return them the app still loads: they come back empty and the pages that need them
# say what is missing (see README, "Columns to add to Gold"). Everything else in SPEC is required.
OPTIONAL = {"property_profile": {"latitude", "longitude"}, "policy_report": {"customer_id", "property_id"},
            "claim_report": {"claim_status", "date_reported", "date_closed", "adjuster_id", "adjuster_name"}}
CORE = ["customer_profile", "property_profile", "policy_report", "claim_report"]     # 4 Genie questions = within the 5/min limit
T = f"{CATALOG}.{SCHEMA}"


def question(name):
    table, _ = SPEC[name]
    return f"Show all rows and all columns from {T}.{table}. No filter and no limit."


DISASTER_Q = (f"For each incident_type in {T}.dim_disaster_declaration, join {T}.fact_nfip_claim on disaster_key and return incident_type, "
              f"count of claims as claims and the sum of amount_paid_on_building_claim + amount_paid_on_contents_claim + amount_paid_on_icc_claim as paid.")


def coerce(df, cols, optional=()):
    """Genie returns strings (JSON) or typed arrays (Arrow): normalise to the Gold types."""
    df = df.copy()
    df.columns = [str(c).lower() for c in df.columns]
    missing = [c for c, _ in cols if c not in df.columns and c not in optional]
    if missing:
        raise ValueError("missing columns: " + ", ".join(missing))
    out = pd.DataFrame(index=df.index)
    for c, t in cols:
        s = df[c] if c in df.columns else pd.Series([None] * len(df), index=df.index, dtype=object)     # optional column Gold does not have yet
        if t in ("i", "l"):
            out[c] = pd.to_numeric(s, errors="coerce").astype("Int64")
        elif t in ("n", "f"):
            out[c] = pd.to_numeric(s, errors="coerce").astype(float)
        elif t == "b":
            out[c] = s.map(lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else (v if isinstance(v, bool) else str(v).strip().lower() in ("true", "t", "y", "yes", "1"))).astype("boolean")
        elif t == "d":
            out[c] = pd.to_datetime(s, errors="coerce")
        else:
            out[c] = s.astype("string").astype(object).where(s.notna(), None)
    return out


_lock = threading.Lock()
_store = {}          # name -> dict(ts, df, sql, seconds, note)
_source = None


def live():
    return bool(SPACE_ID)


def _genie():
    global _source
    if _source is None:
        from genie_client import GenieSource
        _source = GenieSource(SPACE_ID)
    return _source


def _fresh(name):
    e = _store.get(name)
    return e if e and time.time() - e["ts"] < CACHE_TTL else None


def _load_one(name):
    with _lock:
        e = _fresh(name)
    if e:
        return e
    table, cols = SPEC[name]
    ans = _genie().ask(question(name))
    if ans.df is None:
        raise RuntimeError(f"Genie did not return a table for {table}. It said: {ans.text or 'nothing'}")
    df = coerce(ans.df, cols, OPTIONAL.get(name, ()))
    e = dict(ts=time.time(), df=df, sql=ans.sql, seconds=ans.seconds, note=" ".join(ans.notes), table=table)
    with _lock:
        _store[name] = e
    return e


def load_core(use_genie=None, force=False):
    """All four core Gold tables. Live: parallel Genie questions (rate-limited, cached). Demo: built-in data."""
    use_genie = live() if use_genie is None else (use_genie and live())
    if not use_genie:
        import mock_gold
        return {k: dict(df=v, sql="(demo data)", seconds=0.0, note="", table=SPEC[k][0]) for k, v in mock_gold.get().items()}
    if force:
        with _lock:
            _store.clear()
    with ThreadPoolExecutor(max_workers=len(CORE)) as ex:
        futs = {n: ex.submit(_load_one, n) for n in CORE}
        return {n: f.result() for n, f in futs.items()}


def load_disasters(use_genie=None):
    use_genie = live() if use_genie is None else (use_genie and live())
    if not use_genie:
        import mock_gold
        return mock_gold.disasters()
    e = _fresh("disasters")
    if e:
        return e["df"]
    ans = _genie().ask(DISASTER_Q)
    if ans.df is None:
        raise RuntimeError(ans.text or "Genie did not return a table")
    df = coerce(ans.df, [("incident_type", "s"), ("claims", "i"), ("paid", "n")])
    _store["disasters"] = dict(ts=time.time(), df=df)
    return df


def diagnose():
    """One tiny question per Gold table, run one after another, so a failure points at the exact table / permission."""
    out = []
    for name in CORE:
        table, cols = SPEC[name]
        try:
            ans = _genie().ask(f"How many rows are in {T}.{table}?")
            if ans.df is not None and len(ans.df):
                out.append((table, True, f"answered: {ans.df.iloc[0, 0]} rows", ans.sql))
            else:
                out.append((table, False, ans.text or "Genie answered without a table", ans.sql))
        except Exception as e:
            out.append((table, False, str(e), ""))
    return out


def whoami():
    """The identity the app queries Genie as (for a Databricks App this is its service principal's application id)."""
    try:
        return _genie().w.current_user.me().user_name
    except Exception:
        return None


def grant_sql(principal):
    p = principal or "<app-service-principal-application-id>"
    return (f"GRANT USE CATALOG ON CATALOG {CATALOG} TO `{p}`;\n"
            f"GRANT USE SCHEMA, SELECT ON SCHEMA {CATALOG}.{SCHEMA} TO `{p}`;")
