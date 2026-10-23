import os

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import data
import journey as J
import kpis
import ui
from ui import (AV_COLORS, AMBER, BAND_COL, DEEP, INK, MID, MUTED, PURPLE, RED, SOFT, ZONE_COL, avatars, fig_style, flow_html, gap_note, initials, n, pct, show, usd)

st.set_page_config(page_title="Insurance Dashboard", page_icon="🔮", layout="wide")
ui.inject_css()

# ------------------------------------------------------------------ data
LIVE = data.live() and not st.session_state.get("force_demo", False)
try:
    with st.spinner("Loading your portfolio… the first load can take a minute."):
        SRC = data.load_core(use_genie=LIVE)
except Exception as e:
    st.error(f"Could not load the Gold tables from the Genie space: {e}")
    if any(k in str(e) for k in ("PERMISSION_DENIED", "No access to", "USE CATALOG", "USE SCHEMA")):
        who = data.whoami()
        st.warning("This is a Unity Catalog permission problem, not a code problem. The identity the app runs as can use the Genie space but cannot read the tables behind it. "
                   "Run this in a Databricks SQL editor as the table owner or an admin, then reload:" + (f"\n\nApp identity detected: `{who}`" if who else ""))
        st.code(data.grant_sql(who), language="sql")
        st.caption("Also give the same identity CAN RUN on the Genie space (Share) and CAN USE on its SQL warehouse. Adding the Genie space as an app resource grants the space part automatically.")
    st.markdown("**Most likely causes, in order:**\n"
                "1. The four Gold tables are not added to the Genie space (or are named differently from `" + data.T + ".*`).\n"
                "2. The app's service principal can't query them: it needs CAN RUN on the space, CAN USE on the space's SQL warehouse (which must be running) and USE CATALOG / USE SCHEMA / SELECT on the Gold schema.\n"
                "3. Genie couldn't turn the question into SQL. Open the space in Databricks, paste `" + data.question("customer_profile") + "` and see what it says.")
    c1, c2 = st.columns(2)
    c1.button("Use demo data for now", on_click=lambda: st.session_state.update(force_demo=True))
    if c2.button("Run diagnostics (4 small Genie questions)"):
        with st.spinner("Asking Genie one small question per table…"):
            st.session_state["diag"] = data.diagnose()
    for table, ok_, detail, sql_ in st.session_state.get("diag") or []:
        (st.success if ok_ else st.error)(f"{table}: {detail}")
        if sql_:
            st.code(sql_, language="sql")
    st.stop()
C_ALL, P_ALL, PO_ALL, CL_ALL = (SRC[k]["df"] for k in data.CORE)
for _k in data.CORE:
    if SRC[_k].get("note"):
        st.warning(f"{SRC[_k]['table']}: {SRC[_k]['note']}")
if LIVE:
    AS_OF = pd.Timestamp(os.getenv("AS_OF_DATE") or pd.Timestamp.today().normalize())
else:
    import mock_gold
    AS_OF = mock_gold.AS_OF
TODAY = AS_OF

# ------------------------------------------------------------------ navigation helpers
nz_ = lambda v: 0 if v is None or pd.isna(v) else v


def goto(page_, **state):
    st.session_state.update(state)
    if "cj_search" in state:
        st.session_state["hdr_search"] = state["cj_search"]
        st.session_state["cj_cid"] = None
    st.session_state["page"] = page_


def _search():
    q = st.session_state.get("hdr_search", "").strip()
    if st.session_state.get("page") == "Customer 360":
        st.session_state.update(cj_search=q, cj_cid=None)   # filter right here: only the searched customer shows
    elif q:
        goto("Search", search_q=q)


def seg(label, options, key):
    """Pill switcher: native segmented control (falls back to radio on older Streamlit)."""
    if st.session_state.get(key) not in options:
        st.session_state[key] = options[0]
    if hasattr(st, "segmented_control"):
        return st.segmented_control(label, options, key=key, label_visibility="collapsed") or options[0]
    return st.radio(label, options, key=key, horizontal=True, label_visibility="collapsed")


def cols(spec, **kw):
    try:
        return st.columns(spec, vertical_alignment="center", **kw)
    except TypeError:
        return st.columns(spec, **kw)


def card_link(key, html, target, **state):
    """Whole card is clickable: the HTML card with a transparent button laid over it."""
    with st.container(key="card_" + key):
        st.markdown(html, unsafe_allow_html=True)
        st.button("Open", key="cb_" + key, on_click=goto, args=(target,), kwargs=state)


def _greeting():
    """Good morning / afternoon / evening by US Eastern time."""
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        h = datetime.now(ZoneInfo("America/New_York")).hour
    except Exception:
        h = datetime.utcnow().hour - 4
    h %= 24
    return ("🌤️ Good morning" if h < 12 else "☀️ Good afternoon" if h < 17 else "🌙 Good evening")


def card_action(key, html, fn, *args):
    with st.container(key="card_" + key):
        st.markdown(html, unsafe_allow_html=True)
        st.button("Open", key="cb_" + key, on_click=fn, args=args)


def header(title, sub=""):
    c = cols([3.6, 3.6, 2.0])
    with c[0]:
        st.markdown(f'<div class="h1">{title}</div>' + (f'<div class="hsub">{sub}</div>' if sub else ""), unsafe_allow_html=True)
    with c[1]:
        with st.container(key="searchbox"):
            st.text_input("Search", key="hdr_search", placeholder="Search customer name or ID…" if page == "Customer 360" else "Search customers, policies, claims…", label_visibility="collapsed", on_change=_search)
    with c[2]:
        st.markdown(f'<div class="hdr-right"><div class="chip-d">{_greeting()}</div></div>', unsafe_allow_html=True)


MAIN = ["Overview", "Process Flow", "Customer 360", "Portfolio & Geography", "Loss Ratios", "Ask Genie"]
ROLES = ["Claims Desk", "Management"]
RECORDS = ["Customers", "Properties", "Policies", "Claims", "Renewals"]
st.session_state.setdefault("page", "Overview")
page = st.session_state["page"]

with st.sidebar:
    st.markdown('<div class="brand"><div class="logo"><svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
                '<path d="M12 3l8 3v6c0 4.5-3.2 8-8 9-4.8-1-8-4.5-8-9V6z"/><path d="M9 12l2 2 4-4"/></svg></div>'
                '<div class="bt2"><b>Property Insurance</b></div></div>', unsafe_allow_html=True)

    def nav_item(name):
        slug = name.lower().replace(" & ", "_").replace(" ", "_")
        st.button(name, key=("navon_" if name == page else "nav_") + slug, on_click=goto, args=(name,), kwargs={"cj_search": "", "cj_cid": None} if name == "Customer 360" else {}, use_container_width=True)

    st.markdown('<div class="navlbl">Dashboard</div>', unsafe_allow_html=True)
    for p_ in MAIN:
        nav_item(p_)
    st.markdown('<div class="navlbl">Role views</div>', unsafe_allow_html=True)
    for p_ in ROLES:
        nav_item(p_)
    st.markdown('<div class="navlbl">Records</div>', unsafe_allow_html=True)
    for p_ in RECORDS:
        nav_item(p_)
    st.markdown('<div class="navlbl">Filter</div>', unsafe_allow_html=True)
    sel_states = st.multiselect("State", sorted(P_ALL.state.dropna().unique()), placeholder="All states", label_visibility="collapsed")
    if LIVE:
        st.button("↻  Refresh data", key="refresh_data", on_click=lambda: data.load_core(use_genie=True, force=True), use_container_width=True)

# ------------------------------------------------------------------ state filter
P = P_ALL[P_ALL.state.isin(sel_states)] if sel_states else P_ALL
cust_ids = set(P.customer_id)
C = C_ALL[C_ALL.customer_id.isin(cust_ids)]
PO = PO_ALL[PO_ALL.state.isin(sel_states)] if sel_states else PO_ALL
CL = CL_ALL[CL_ALL.state.isin(sel_states)] if sel_states else CL_ALL
CL = CL.assign(paid=CL.amount_paid_on_building_claim.fillna(0) + CL.amount_paid_on_contents_claim.fillna(0) + CL.amount_paid_on_icc_claim.fillna(0))
PO = PO.assign(coverage=PO.total_building_insurance_coverage.fillna(0) + PO.total_contents_insurance_coverage.fillna(0))
ACT = P[P.active_policy_id.notna()].assign(coverage=lambda d: d.active_building_coverage.fillna(0) + d.active_contents_coverage.fillna(0))
ACT = ACT.assign(days=(ACT.policy_expiration_date - AS_OF).dt.days)
SFHA = lambda s: s.fillna("").astype(str).str[:1].isin(["A", "V"])


def empty(msg="No data for this selection."):
    st.info(msg)

# ------------------------------------------------------------------ KPI helpers shared by Loss Ratios / Claims Desk / Management / Geography
st.session_state.setdefault("sla_days", kpis.SLA_DAYS)
CNAME = dict(zip(C_ALL.customer_id, (C_ALL.first_name.fillna("") + " " + C_ALL.last_name.fillna("")).str.strip()))
fmt_lr = lambda x: "—" if x is None or pd.isna(x) else f"{x:.0%}"
fmt_d1 = lambda x: "—" if x is None or pd.isna(x) else f"{x:,.0f} d"


def tiles(items, per_row=4):
    """KPI tiles: (label, value, note). Wraps onto further rows."""
    for i in range(0, len(items), per_row):
        for col_, (l_, v_, n_) in zip(st.columns(per_row), items[i:i + per_row]):
            col_.markdown(f'<div class="subtile"><div class="sl">{l_}</div><div class="sv">{v_}</div><div class="sn">{n_}</div></div>', unsafe_allow_html=True)


def table(df, key, cfg=None, open_col=None, height=420):
    """Table with CSV export; with open_col, selecting a row offers that customer's Customer 360."""
    if df.empty:
        st.info("Nothing matches this view.")
        return
    st.download_button("⬇ CSV", df.to_csv(index=False), file_name=f"{key}.csv", mime="text/csv", key="dl_" + key)
    kw = dict(use_container_width=True, hide_index=True, height=height, column_config=cfg or {})
    if open_col and open_col in df.columns:
        try:
            ev = st.dataframe(df, key="t_" + key, on_select="rerun", selection_mode="single-row", **kw)
            sel = list(ev.selection.rows)
            if sel and sel[0] < len(df):
                cid_ = df.iloc[sel[0]][open_col]
                st.button(f"Open Customer 360 for {CNAME.get(cid_, cid_)} →", key="o_" + key, on_click=goto, args=("Customer 360",), kwargs={"cj_search": cid_})
            else:
                st.caption("Select a row to open the Customer 360 view.")
            return
        except TypeError:
            pass
    st.dataframe(df, **kw)


def lr_year_chart(Y, h=330):
    """Loss ratio per calendar year (bars) and cumulative (line): single years swing with catastrophe events, the cumulative line settles."""
    xs = [str(y) + (" YTD" if y == AS_OF.year else "") for y in Y.year]
    fig = go.Figure()
    fig.add_bar(x=xs, y=Y.loss_ratio * 100, name="Loss ratio, that year", marker_color=[RED if v > 1 else PURPLE for v in Y.loss_ratio], width=0.5,
                customdata=Y[["paid", "earned_premium", "claims"]].values, hovertemplate="%{x}: %{y:.0f}%<br>paid $%{customdata[0]:,.0f} · earned $%{customdata[1]:,.0f} · %{customdata[2]:.0f} claims<extra></extra>")
    fig.add_scatter(x=xs, y=Y.cum_loss_ratio * 100, name="Cumulative", mode="lines+markers", line=dict(color=DEEP, width=3), hovertemplate="Cumulative to %{x}: %{y:.0f}%<extra></extra>")
    fig.add_hline(y=100, line_dash="dot", line_color=MUTED, annotation_text="100%: paid = premium", annotation_position="top left")
    fig.update_yaxes(ticksuffix="%", zeroline=False)
    fig.update_layout(legend=dict(orientation="h", y=1.12, x=0), title="Loss ratio by year")
    return fig_style(fig, h)


def lr_bar(tbl, label, h=360):
    """Horizontal bars of credibility-adjusted loss ratio; red above 100%. Hover shows the raw ratio and the credibility weight."""
    t = tbl.sort_values("adj_loss_ratio", ascending=False).head(15)
    fig = go.Figure(go.Bar(y=t[label].astype(str), x=t.adj_loss_ratio * 100, orientation="h", marker_color=[RED if v > 1 else PURPLE for v in t.adj_loss_ratio.fillna(0)],
                           customdata=t[["loss_ratio", "credibility", "earned_premium", "claims"]].values,
                           hovertemplate="%{y}<br>adjusted %{x:.0f}% · raw %{customdata[0]:.0%} · credibility %{customdata[1]:.0%}<br>earned $%{customdata[2]:,.0f} · %{customdata[3]:.0f} claims<extra></extra>"))
    fig.add_vline(x=PORT_LR * 100, line_dash="dot", line_color=MUTED, annotation_text="portfolio", annotation_position="top")
    fig.update_yaxes(autorange="reversed")
    fig.update_xaxes(ticksuffix="%")
    fig.update_layout(showlegend=False, bargap=0.4, title="Credibility-adjusted loss ratio (top 15)")
    return fig_style(fig, h)


def lr_pct_cfg():
    return {"loss_ratio": st.column_config.NumberColumn("Loss ratio", format="%.0f%%"), "adj_loss_ratio": st.column_config.NumberColumn("Adjusted LR", format="%.0f%%"),
            "credibility": st.column_config.ProgressColumn("Credibility", min_value=0, max_value=100, format="%d%%"), "earned_premium": st.column_config.NumberColumn("Earned premium", format="$%d"),
            "paid": st.column_config.NumberColumn("Claims paid", format="$%d"), "claims": st.column_config.NumberColumn("Claims", format="%d"), "properties": st.column_config.NumberColumn("Properties", format="%d"),
            "policy_years": st.column_config.NumberColumn("Policy-years", format="%.1f"), "frequency": st.column_config.NumberColumn("Claims / policy-yr", format="%.3f"),
            "severity": st.column_config.NumberColumn("Avg paid / claim", format="$%d"), "customer_id": st.column_config.TextColumn("Customer ID"), "customer": st.column_config.TextColumn("Customer")}


def as_pct(df):
    return df.assign(loss_ratio=df.loss_ratio * 100, adj_loss_ratio=df.adj_loss_ratio * 100, credibility=df.credibility * 100)


# loss-ratio frame: one row per property with earned premium, claims paid, policy-years and dimensions (state-filtered like every other page)
if page in ("Loss Ratios", "Claims Desk", "Management", "Portfolio & Geography"):
    PL, LR_MODE = kpis.property_lr(P, PO, CL, AS_OF)
    PL = PL.assign(area=PL.county.fillna("") + ", " + PL.state.fillna(""), agent_name=PL.customer_id.map(dict(zip(C_ALL.customer_id, C_ALL.agent_name))))
    PORT_LR = kpis.safe_div(PL.paid.sum(), PL.earned_premium.sum())
    LIFE = kpis.has(CL, "claim_status", "date_reported")
    DOPS = kpis.claim_ops(CL, PO, P, C, AS_OF, st.session_state["sla_days"])
    LR_GAP = ("Premium history is not linked to properties or customers in <code>gold_policy_report</code>, so premium by customer, county, flood zone and risk band is <b>estimated</b> "
              "(current premium × policy terms; lapsed properties count as zero). Add <code>customer_id</code> and <code>property_id</code> to the policy report for exact figures. "
              "Portfolio and by-year figures are exact either way.")


# =====================================================================
# OVERVIEW
# =====================================================================
if page == "Overview":
    header("Insurance Dashboard")
    exposure = ACT.coverage.sum()
    hr_share = ACT[SFHA(ACT.flood_zone)].coverage.sum() / max(exposure, 1)
    n_claims, n_open = len(CL), int(P.claims_open.fillna(0).sum())
    paid_total = CL.paid.sum()
    due60 = int(ACT.days.between(0, 60).sum())
    tiles = [("👥", "Customers", n(len(C)), "Customers", {}), ("🏠", "Properties", n(len(P)), "Properties", {}), ("🛡️", "Active policies", n(len(ACT)), "Policies", {"pol_view": "Active"}),
             ("⚠️", "Open claims", n(n_open), "Claims", {"claims_view": "Open claims"}), ("🔁", "Renewals due ≤60d", n(due60), "Renewals", {"ren_win": "≤60 days"})]
    for col_, (i, l, v, tgt, st_) in zip(st.columns(5), tiles):
        with col_:
            card_link("kpi_" + tgt.lower(), f'<div class="kpi"><div class="ico">{i}</div><div class="kt"><div class="kl">{l}</div><div class="kv">{v}</div></div><div class="go">›</div></div>', tgt, **st_)

    c1, c2, c3 = st.columns(3)
    with c1:
      card_link("big_pol", f'''<div class="bigcard dark"><div class="top"><div class="sq">🛡️</div><div class="chev">›</div></div>
        <div class="bt">Policies in force</div><div class="bs">{n(len(ACT))} active policies · {n(ACT.customer_id.nunique())} customers</div>
        <div class="row"><div class="bv">{usd(ACT.active_premium.sum())}</div><div class="bn">{usd(exposure)} insured</div></div>
        <div class="bar"><span style="width:{hr_share * 100:.0f}%"></span></div><div class="cap">{hr_share:.0%} of insured value in high-risk flood zones</div></div>''', "Policies", pol_view="Active")
    closed_share = 1 - (n_open / max(n_claims, 1))
    with c2:
      card_link("big_clm", f'''<div class="bigcard"><div class="top"><div class="sq">⚠️</div><div class="chev">›</div></div>
        <div class="bt">Claims</div><div class="bs">{n(n_claims)} claims · {n(n_open)} open</div>
        <div class="row"><div class="bv">{usd(paid_total)}</div><div class="bn">{usd(paid_total / max(n_claims, 1))} avg / claim</div></div>
        <div class="bar"><span style="width:{closed_share * 100:.0f}%"></span></div><div class="cap">{closed_share:.0%} of claims settled</div></div>''', "Claims", claims_view="All claims")
    n_act_c = int((C.customer_status == "ACTIVE").sum())
    act_share = n_act_c / max(len(C), 1)
    with c3:
        card_link("big_cust", f'''<div class="bigcard"><div class="top"><div class="sq">👥</div><div class="chev">›</div></div>
            <div class="bt">Customers</div><div class="bs">{n(n_act_c)} active · {n((C.properties > 1).sum())} with several properties</div>
            <div class="row"><div class="bv">{n(len(C))}</div><div class="bn">{usd(C.premium_active.sum())} annual premium</div></div>
            <div class="bar"><span style="width:{act_share * 100:.0f}%"></span></div><div class="cap">{act_share:.0%} of customers are active</div></div>''', "Customers")

    left, right = st.columns([3, 2])
    FREQ = {"Monthly": "M", "Quarterly": "Q", "Yearly": "Y"}

    def window(df, col, val=None, freq="M"):
        idx = pd.period_range(end=pd.Timestamp(AS_OF).to_period(freq), periods=8, freq=freq)
        d_ = df[df[col].notna()]
        if d_.empty:
            return pd.Series(0.0, index=idx)
        per = d_[col].dt.to_period(freq)
        s = d_.groupby(per)[val].sum() if val else d_.groupby(per).size()
        return s.reindex(idx, fill_value=0).astype(float)

    def label(p, freq):
        return p.strftime("%b") if freq == "M" else (f"Q{p.quarter} {str(p.year)[2:]}" if freq == "Q" else str(p.year))

    with left:
        with st.container(key="stats_card", border=True):
            a, b = st.columns([2, 3])
            a.markdown('<div class="ct">Statistics</div>', unsafe_allow_html=True)
            with b:
                period = seg("Period", list(FREQ), "period")
            fq = FREQ[period]
            prem_s = window(PO, "policy_effective_date", "total_insurance_premium", fq)
            pol_s = window(PO, "policy_effective_date", None, fq)
            paid_s = window(CL, "date_of_loss", "paid", fq)
            clm_s = window(CL, "date_of_loss", None, fq)
            unit = {"M": "months", "Q": "quarters", "Y": "years"}[fq]

            def delta(ser_, bad_if_up=False):
                prev, cur = ser_.iloc[:4].sum(), ser_.iloc[4:].sum()
                if prev <= 0:
                    return ""
                ch = (cur - prev) / prev
                good = (ch >= 0) != bad_if_up
                return f'<span class="dl {"up" if good else "dn"}">{"▲" if ch >= 0 else "▼"} {abs(ch):.0%}</span>'

            lr = paid_s.sum() / prem_s.sum() if prem_s.sum() else float("nan")
            tl = [("Premium written", usd(prem_s.sum()), delta(prem_s), f"{n(pol_s.sum())} policy terms"),
                  ("Claims paid", usd(paid_s.sum()), delta(paid_s, True), f"{n(clm_s.sum())} claims"),
                  ("Policies written", n(pol_s.sum()), delta(pol_s), f"avg premium {usd(prem_s.sum() / max(pol_s.sum(), 1))}"),
                  ("Paid vs premium", pct(lr), "", "claims paid ÷ premium written")]
            for col_, (l_, v_, d_, n_) in zip(st.columns(4), tl):
                col_.markdown(f'<div class="subtile"><div class="sl">{l_}</div><div class="sv">{v_} {d_}</div><div class="sn">{n_}</div></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="cap2">Last 8 {unit} · arrows compare the latest 4 with the 4 before</div>', unsafe_allow_html=True)
            metric = seg("Metric", ["Premium", "Claims paid", "Policies"], "metric")
            ser, money = {"Premium": (prem_s, True), "Claims paid": (paid_s, True), "Policies": (pol_s, False)}[metric]
            xs = [label(p, fq) for p in ser.index]
            fig = go.Figure(go.Bar(x=xs, y=ser.values, marker_color=PURPLE, width=0.34, name=metric,
                                   hovertemplate=("%{x}: $%{y:,.0f}" if money else "%{x}: %{y:,.0f}") + "<extra></extra>"))
            fig.add_trace(go.Scatter(x=xs, y=ser.rolling(3, min_periods=1).mean().values, mode="lines", name="3-period average", line=dict(color=DEEP, width=2.5, dash="dot"),
                                     hovertemplate="3-period avg: %{y:,.0f}<extra></extra>"))
            fig.update_layout(bargap=0.5, showlegend=True, legend=dict(orientation="h", y=1.12, x=0))
            fig.update_yaxes(zeroline=False, showline=False, tickprefix="$" if money else "", tickformat="~s")
            fig.update_xaxes(showgrid=False)
            fig_style(fig, 300)
            fig.update_layout(margin=dict(l=8, r=8, t=8, b=8))
            st.plotly_chart(fig, use_container_width=True)

    with right:
        with st.container(key="txn_card", border=True):
            a, b = st.columns([2, 3])
            a.markdown('<div class="ct">Transactions</div>', unsafe_allow_html=True)
            with b:
                flt = seg("Type", ["All", "Claims", "Renewals"], "txnf")
            rows = []
            pol_cust = dict(zip(P_ALL.active_policy_id.dropna(), P_ALL.customer_id[P_ALL.active_policy_id.notna()]))
            if flt in ("All", "Claims"):
                for r in CL.sort_values("date_of_loss", ascending=False).head(6).itertuples():
                    done = r.paid > 0
                    cid = pol_cust.get(r.policy_id)
                    tgt = ("Customer 360", {"cj_search": cid}) if cid else ("Claims", {"claims_view": "All claims", "f_k2_q": r.claim_id})
                    rows.append((r.date_of_loss, "📄", usd(r.paid), f"{r.claim_id} · {r.community_name}", "Paid" if done else "Pending", "paid" if done else "pending", tgt))
            if flt in ("All", "Renewals"):
                due = C[C.next_renewal_date.notna()].sort_values("next_renewal_date").head(6)
                for r in due.itertuples():
                    rows.append((r.next_renewal_date, "🔁", usd(r.premium_active), f"Renewal · {r.first_name} {r.last_name}", "Pending" if r.renewal_pending else f"In {int(r.days_to_renewal)}d",
                                 "pending" if r.renewal_pending else "paid", ("Customer 360", {"cj_search": r.customer_id})))
            rows = [x for x in rows if pd.notna(x[0])]
            rows.sort(key=lambda x: x[0], reverse=True)
            if not rows:
                st.markdown('<div class="hsub">No transactions.</div>', unsafe_allow_html=True)
            for i_, (d_, ic, amt, sub, stt, cls, (tp, ts_)) in enumerate(rows[:6]):
                card_link(f"txn_{i_}", f'<div class="txn"><div class="sq">{ic}</div><div class="mid"><div class="ta">{amt}</div><div class="ts">{sub} · {pd.Timestamp(d_).strftime("%b %d, %Y")}</div></div>'
                                       f'<span class="pill {cls}">{stt}</span></div>', tp, **ts_)
            if flt == "Renewals":
                st.button("View all renewals →", key="txn_all", on_click=goto, args=("Renewals",), kwargs={"ren_win": "≤60 days"})
            else:
                st.button("View all claims →", key="txn_all", on_click=goto, args=("Claims",), kwargs={"claims_view": "All claims"})

    # ---- insights row
    i1, i2, i3 = st.columns(3)
    with i1:
        with st.container(key="ins_attn", border=True):
            st.markdown('<div class="ct">Needs attention</div>', unsafe_allow_html=True)
            pend = int(C.renewal_pending.fillna(False).astype(bool).sum())
            items = [("⚠️", "Open claims", n_open, "Claims", {"claims_view": "Open claims"}),
                     ("🔁", "Renewals due within 30 days", int(ACT.days.between(0, 30).sum()), "Renewals", {"ren_win": "≤30 days"}),
                     ("⏳", "Renewals still pending", pend, "Renewals", {"ren_win": "≤60 days"}),
                     ("🌊", "High-risk properties", int((P.assessed_risk_band == "High").sum()), "Properties", {"f_p_r": "High", "f_p_c": "All properties", "f_p_z": "All flood zones"}),
                     ("🏚️", "Properties without an active policy", int(P.active_policy_id.isna().sum()), "Properties", {"f_p_c": "No active policy", "f_p_r": "All risk bands", "f_p_z": "All flood zones"})]
            for k_, (ic, lb, ct, tp, st_) in enumerate(items):
                card_link(f"attn_{k_}", f'<div class="attn"><div class="sq">{ic}</div><div class="al">{lb}</div><div class="ac">{n(ct)}</div><div class="go">›</div></div>', tp, **st_)
    with i2:
        with st.container(key="ins_risk", border=True):
            st.markdown('<div class="ct">Insured value by risk band</div>', unsafe_allow_html=True)
            rk = ACT.dropna(subset=["assessed_risk_band"]).groupby("assessed_risk_band", as_index=False).coverage.sum()
            if rk.empty:
                st.markdown('<div class="hsub">No active policies.</div>', unsafe_allow_html=True)
            else:
                fig = px.pie(rk, names="assessed_risk_band", values="coverage", hole=.62, color="assessed_risk_band", color_discrete_map=BAND_COL)
                fig.update_traces(textinfo="percent", hovertemplate="%{label}: $%{value:,.0f}<extra></extra>")
                fig_style(fig, 290)
                fig.update_layout(margin=dict(l=8, r=8, t=8, b=8), legend=dict(orientation="h", y=-0.05))
                st.plotly_chart(fig, use_container_width=True)
    with i3:
        with st.container(key="ins_cty", border=True):
            st.markdown('<div class="ct">Top counties by insured value</div>', unsafe_allow_html=True)
            ct_ = P.drop_duplicates(["state", "county"]).assign(area=lambda d: d.county + ", " + d.state).sort_values("county_insured_value", ascending=False).head(6)
            if ct_.empty:
                st.markdown('<div class="hsub">No data.</div>', unsafe_allow_html=True)
            else:
                fig = go.Figure(go.Bar(x=ct_.county_insured_value, y=ct_.area, orientation="h", marker_color=PURPLE, hovertemplate="%{y}: $%{x:,.0f}<extra></extra>"))
                fig.update_yaxes(autorange="reversed")
                fig.update_xaxes(tickprefix="$", tickformat="~s", showgrid=True)
                fig_style(fig, 290)
                fig.update_layout(margin=dict(l=8, r=8, t=8, b=8), showlegend=False, bargap=0.45)
                st.plotly_chart(fig, use_container_width=True)

# =====================================================================
# PROCESS FLOW
# =====================================================================
elif page == "Process Flow":
    header("Property Insurance Process")
    st.session_state.setdefault("step", 1)

    def go_to(k):
        st.session_state.step = max(1, min(12, k))

    st.markdown(flow_html(st.session_state.step), unsafe_allow_html=True)
    c = st.columns([1, 1, 6])
    c[0].button("◀ Previous", on_click=go_to, args=(st.session_state.step - 1,), disabled=st.session_state.step == 1, use_container_width=True)
    c[1].button("Next ▶", on_click=go_to, args=(st.session_state.step + 1,), disabled=st.session_state.step == 12, use_container_width=True)
    pick = c[2].selectbox("Jump to stage", [f"{i}. {t}" for i, t, _ in J.STEPS], index=st.session_state.step - 1, label_visibility="collapsed")
    if int(pick.split(".")[0]) != st.session_state.step:
        st.session_state.step = int(pick.split(".")[0])
        st.rerun()
    s = st.session_state.step
    _, title, question = J.STEPS[s - 1]
    src = J.SOURCE[s]
    st.markdown(f'<div class="card tint"><span class="tag">Step {s} of 12</span>' + ('' if src else '<span class="gapnote">no data yet</span>')
                + f'<div class="q">{title}</div><div>{question}</div></div>', unsafe_allow_html=True)

    def bar(df, x, y, title_, color=PURPLE, h=330, orient=None, **kw):
        fig = px.bar(df, x=x, y=y, title=title_, orientation=orient, color_discrete_sequence=[color], **kw)
        if orient == "h":
            fig.update_yaxes(autorange="reversed")
        return fig

    if len(P) == 0:
        empty()
    elif s == 1:
        k = st.columns(4)
        k[0].metric("Customers", n(len(C))); k[1].metric("Active customers", n((C.customer_status == "ACTIVE").sum()))
        k[2].metric("Multi-property customers", n((C.properties > 1).sum())); k[3].metric("Avg properties / customer", f"{C.properties.mean():.2f}")
        a, b = st.columns(2)
        cs = C.assign(year=C.customer_since.dt.year).groupby("year", as_index=False).size()
        a.plotly_chart(fig_style(bar(cs, "year", "size", "Customers by year they joined")), use_container_width=True)
        ag = C.groupby("agent_name", as_index=False).size().sort_values("size", ascending=False).head(10)
        b.plotly_chart(fig_style(bar(ag, "size", "agent_name", "Customers by agent", orient="h")), use_container_width=True)
        st.markdown('<div class="callout">A customer can own several properties. Identify the customer first, then the insured property.</div>', unsafe_allow_html=True)
    elif s == 2:
        k = st.columns(4)
        k[0].metric("Insured properties", n(len(P))); k[1].metric("Pre-FIRM share", pct((P.construction_date_band == "Pre-FIRM").mean()))
        k[2].metric("Elevated buildings", pct(P.elevated.fillna(False).astype(bool).mean())); k[3].metric("Properties / customer", f"{len(P) / max(len(C), 1):.2f}")
        a, b = st.columns(2)
        bb = P.assign(elev=P.elevated.map({True: "Elevated", False: "Not elevated"})).groupby(["construction_date_band", "elev"], as_index=False).size()
        a.plotly_chart(fig_style(px.bar(bb, x="construction_date_band", y="size", color="elev", title="Properties by construction band", color_discrete_map={"Elevated": PURPLE, "Not elevated": SOFT})), use_container_width=True)
        npc = P.groupby("customer_id").size().value_counts().sort_index().reset_index()
        npc.columns = ["properties", "customers"]
        npc["properties"] = npc.properties.astype(str) + " propert" + npc.properties.map(lambda x: "y" if x == 1 else "ies")
        b.plotly_chart(fig_style(px.pie(npc, names="properties", values="customers", hole=.55, title="Customers by number of properties")), use_container_width=True)
    elif s == 3:
        k = st.columns(4)
        k[0].metric("States", P.state.nunique()); k[1].metric("Counties", P.groupby(["state", "county"]).ngroups); k[2].metric("Cities", P.groupby(["state", "city"]).ngroups); k[3].metric("ZIP codes", P.zip_code.nunique())
        tm = P.assign(country="USA").groupby(["country", "state", "county", "city"], as_index=False).size()
        show(px.treemap(tm, path=["country", "state", "county", "city"], values="size", title="Geography: Country → State → County → City", color_discrete_sequence=ui.SEQ), 420)
        st.markdown('<div class="callout"><b>Geography belongs to the property, not the customer.</b> Each insured property carries its own state, county, city and ZIP.</div>', unsafe_allow_html=True)
    elif s == 4:
        k = st.columns(4)
        k[0].metric("High-risk zone (SFHA) share", pct(SFHA(P.flood_zone).mean())); k[1].metric("High-band properties", n((P.assessed_risk_band == "High").sum()))
        k[2].metric("Avg risk score", f"{P.assessed_risk_score.mean():.0f}"); k[3].metric("Counties tracked", P.groupby(["state", "county"]).ngroups)
        a, b = st.columns(2)
        z = P.flood_zone.value_counts().reset_index(); z.columns = ["flood_zone", "properties"]
        a.plotly_chart(fig_style(px.bar(z, x="flood_zone", y="properties", color="flood_zone", color_discrete_map=ZONE_COL, title="Properties by flood zone")), use_container_width=True)
        rb = P.groupby(["flood_zone", "assessed_risk_band"], as_index=False).size()
        b.plotly_chart(fig_style(px.bar(rb, x="flood_zone", y="size", color="assessed_risk_band", color_discrete_map=BAND_COL, title="Assessed risk band by flood zone")), use_container_width=True)
        cty = P.drop_duplicates(["state", "county"]).assign(area=lambda d: d.county + ", " + d.state).sort_values("county_insured_value", ascending=False).head(10)
        show(bar(cty, "county_insured_value", "area", "Top 10 counties by insured value (county exposure)", orient="h"), 360)
    elif s == 5:
        gap_note("There is no quote or application table. The result of the quote is visible in the policy: premium per $1,000 of coverage on active policies, by risk.")
        A = ACT[ACT.coverage > 0].assign(rate=lambda d: d.active_premium / d.coverage * 1000)
        k = st.columns(3)
        k[0].metric("Avg active premium", usd(A.active_premium.mean())); k[1].metric("Avg coverage", usd(A.coverage.mean())); k[2].metric("Avg premium per $1,000", f"${A.rate.mean():.2f}")
        a, b = st.columns(2)
        zr = A.groupby("flood_zone", as_index=False).rate.mean()
        a.plotly_chart(fig_style(px.bar(zr, x="flood_zone", y="rate", color="flood_zone", color_discrete_map=ZONE_COL, title="Premium per $1,000 coverage by flood zone")), use_container_width=True)
        br = A.groupby("construction_date_band", as_index=False).rate.mean()
        b.plotly_chart(fig_style(bar(br, "construction_date_band", "rate", "Pricing: Pre-FIRM vs Post-FIRM")), use_container_width=True)
    elif s == 6:
        gap_note("There is no accept / decline decision. This shows the risk the insurer holds on the book today, which is what underwriting evaluates.")
        k = st.columns(3)
        for col_, bnd in zip(k, ["High", "Medium", "Low"]):
            col_.metric(f"{bnd} risk properties", n((P.assessed_risk_band == bnd).sum()))
        a, b = st.columns(2)
        a.plotly_chart(fig_style(px.histogram(P.dropna(subset=["assessed_risk_score"]), x="assessed_risk_score", nbins=20, title="Assessed risk score distribution", color_discrete_sequence=[PURPLE])), use_container_width=True)
        rp = P.assign(zone_type=lambda d: SFHA(d.flood_zone).map({True: "High-risk zone (A*/V*)", False: "Other"})).groupby(["zone_type", "construction_date_band"], as_index=False).size()
        b.plotly_chart(fig_style(px.bar(rp, x="zone_type", y="size", color="construction_date_band", title="Zone type × construction band", color_discrete_map={"Pre-FIRM": DEEP, "Post-FIRM": SOFT})), use_container_width=True)
    elif s == 7:
        k = st.columns(4)
        k[0].metric("Policy terms issued", n(len(PO))); k[1].metric("Active today", n(len(ACT)))
        k[2].metric("Premium written", usd(PO.total_insurance_premium.sum())); k[3].metric("Insured exposure (all terms)", usd(PO.coverage.sum()))
        a, b = st.columns(2)
        py = PO.assign(year=PO.policy_effective_date.dt.year).groupby("year", as_index=False).agg(premium=("total_insurance_premium", "sum"), terms=("policy_id", "count"))
        a.plotly_chart(fig_style(bar(py, "year", "premium", "Premium written by effective year")), use_container_width=True)
        ps = PO.groupby("state", as_index=False).agg(coverage=("coverage", "sum"))
        b.plotly_chart(fig_style(px.pie(ps, names="state", values="coverage", hole=.55, title="Insured exposure by state")), use_container_width=True)
    elif s == 8:
        gap_note("Endorsements and mid-term changes are not modelled. This shows the policies currently in force.")
        k = st.columns(4)
        k[0].metric("Active policies", n(len(ACT))); k[1].metric("Active premium", usd(ACT.active_premium.sum()))
        k[2].metric("Insured value", usd(ACT.coverage.sum())); k[3].metric("Avg terms per property", f"{ACT.policy_terms.mean():.1f}")
        a, b = st.columns(2)
        ap = ACT.groupby("state", as_index=False).active_premium.sum()
        a.plotly_chart(fig_style(bar(ap, "state", "active_premium", "Active premium by state")), use_container_width=True)
        tier = pd.cut(ACT.coverage, [-1, 100e3, 250e3, 500e3, 1e12], labels=["<100K Low", "100K–250K Medium", "250K–500K High", ">500K Very high"]).value_counts().reindex(["<100K Low", "100K–250K Medium", "250K–500K High", ">500K Very high"]).reset_index()
        tier.columns = ["tier", "policies"]
        b.plotly_chart(fig_style(px.pie(tier, names="tier", values="policies", hole=.55, title="Active policies by coverage tier")), use_container_width=True)
    elif s == 9:
        k = st.columns(4)
        k[0].metric("Claims", n(len(CL))); k[1].metric("Paid", usd(CL.paid.sum())); k[2].metric("Open claims", n(P.claims_open.sum()))
        k[3].metric("Avg paid (paid claims)", usd(CL[CL.paid > 0].paid.mean()))
        a, b = st.columns(2)
        cy = CL.groupby("year_of_loss", as_index=False).agg(paid=("paid", "sum"), claims=("claim_id", "count"))
        fig = go.Figure()
        fig.add_bar(x=cy.year_of_loss, y=cy.paid, name="Paid", marker_color=PURPLE)
        fig.add_scatter(x=cy.year_of_loss, y=cy.claims, name="Claims", yaxis="y2", line=dict(color=AMBER, width=3))
        fig.update_layout(title="Losses by year", yaxis2=dict(overlaying="y", side="right", showgrid=False))
        a.plotly_chart(fig_style(fig), use_container_width=True)
        sp = pd.DataFrame({"component": ["Building", "Contents", "ICC"], "paid": [CL.amount_paid_on_building_claim.sum(), CL.amount_paid_on_contents_claim.sum(), CL.amount_paid_on_icc_claim.sum()]})
        b.plotly_chart(fig_style(px.pie(sp, names="component", values="paid", hole=.55, title="Paid by coverage component")), use_container_width=True)
        st.caption("Only the date of loss is tracked (no FNOL, reserve or close dates), so claim cycle time can't be shown.")
        if st.button("Load claims by disaster type", key="load_dis"):
            try:
                with st.spinner("Loading…"):
                    st.session_state["dis_df"] = data.load_disasters(use_genie=LIVE)
            except Exception as e:
                st.warning(f"Couldn't load the disaster breakdown: {e}")
        if st.session_state.get("dis_df") is not None:
            dd = st.session_state["dis_df"]
            show(bar(dd, "paid", "incident_type", "Claim dollars by disaster incident type", orient="h"), 280)
    elif s == 10:
        cc = P.claims_total.fillna(0).astype(int)
        grp = pd.cut(cc, [-1, 0, 1, 999], labels=["0 claims", "1 claim", "2+ claims"]).value_counts().reindex(["0 claims", "1 claim", "2+ claims"]).reset_index()
        grp.columns = ["history", "properties"]
        k = st.columns(4)
        k[0].metric("Properties with ≥1 claim", n((cc >= 1).sum())); k[1].metric("Repetitive-loss (nfip_rl)", n(P.nfip_rl.fillna(False).astype(bool).sum()))
        k[2].metric("Loss-free properties", pct((cc == 0).mean())); k[3].metric("Avg claims / property", f"{cc.mean():.2f}")
        a, b = st.columns(2)
        a.plotly_chart(fig_style(px.bar(grp, x="history", y="properties", color="history", title="Properties by loss history", color_discrete_map={"0 claims": SOFT, "1 claim": MID, "2+ claims": DEEP})), use_container_width=True)
        zr = P.assign(c=cc).groupby("flood_zone", as_index=False).c.mean()
        b.plotly_chart(fig_style(px.bar(zr, x="flood_zone", y="c", color="flood_zone", color_discrete_map=ZONE_COL, title="Average claims per property by flood zone")), use_container_width=True)
    elif s == 11:
        mit = P.mitigation_count.fillna(0)
        k = st.columns(4)
        k[0].metric("Mitigation actions", n(mit.sum())); k[1].metric("Properties mitigated", n((mit > 0).sum()))
        cl_m, cl_n = P[mit > 0].claims_total.mean(), P[mit == 0].claims_total.mean()
        k[2].metric("Avg claims: mitigated", f"{cl_m:.2f}" if pd.notna(cl_m) else "—"); k[3].metric("Avg claims: not mitigated", f"{cl_n:.2f}" if pd.notna(cl_n) else "—")
        a, b = st.columns(2)
        gm = pd.DataFrame({"group": ["Mitigated", "Not mitigated"], "claims": [cl_m, cl_n]}).dropna()
        a.plotly_chart(fig_style(px.bar(gm, x="group", y="claims", color="group", title="Avg claims per property (indicative)", color_discrete_map={"Mitigated": PURPLE, "Not mitigated": SOFT})), use_container_width=True)
        hc = P.drop_duplicates(["state", "county"]).assign(area=lambda d: d.county + ", " + d.state).sort_values("county_hma_obligated", ascending=False).head(10)
        b.plotly_chart(fig_style(bar(hc, "county_hma_obligated", "area", "County HMA funding obligated (top 10)", orient="h")), use_container_width=True)
    else:
        k = st.columns(4)
        due = ACT[ACT.days.between(0, 60)]
        k[0].metric("Renewals due ≤60 days", n(len(due))); k[1].metric("Decision pending", n(C.renewal_pending.fillna(False).astype(bool).sum()))
        k[2].metric("Premium up for renewal (60d)", usd(due.active_premium.sum())); k[3].metric("Avg days to renewal", f"{ACT.days.mean():.0f}")
        a, b = st.columns(2)
        bk = pd.cut(ACT.days, [-1, 30, 60, 90, 180, 366], labels=["≤30 days", "31–60", "61–90", "91–180", ">180"]).value_counts().reindex(["≤30 days", "31–60", "61–90", "91–180", ">180"]).reset_index()
        bk.columns = ["window", "policies"]
        a.plotly_chart(fig_style(bar(bk, "window", "policies", "Policies by time to renewal")), use_container_width=True)
        rm = ACT.assign(month=ACT.policy_expiration_date.dt.to_period("M").dt.to_timestamp()).groupby("month", as_index=False).agg(premium=("active_premium", "sum"))
        b.plotly_chart(fig_style(bar(rm, "month", "premium", "Premium renewing by month")), use_container_width=True)
        st.write("**Customers due within 60 days**")
        tb = C[C.renewal_due_60d.fillna(False).astype(bool)].sort_values("premium_active", ascending=False).head(25)
        st.dataframe(tb[["customer_id", "first_name", "last_name", "agent_name", "next_renewal_date", "days_to_renewal", "premium_active", "renewal_pending", "claims_total", "highest_risk_band"]], use_container_width=True, hide_index=True)

# =====================================================================
# CUSTOMER JOURNEY
# =====================================================================
elif page == "Customer 360":
    header("Customer 360")
    lab = C_ALL.assign(label=C_ALL.first_name + " " + C_ALL.last_name + " · " + C_ALL.customer_id)
    q = st.session_state.get("cj_search", "").strip()
    cid = st.session_state.get("cj_cid")
    if not cid and q:
        m_ = lab[lab.label.str.contains(q, case=False, regex=False)]
        if len(m_) == 1:
            cid = m_.customer_id.iloc[0]

    # ---------------------------------------------- directory: what you see before choosing a customer
    if not cid:
        DIR = C.assign(customer=C.first_name.fillna("") + " " + C.last_name.fillna(""))
        DIR = DIR.assign(days=(DIR.next_renewal_date - AS_OF).dt.days)
        if q:
            DIR = DIR[DIR[["customer_id", "customer", "agent_name", "primary_county", "primary_state"]].fillna("").astype(str).agg(" ".join, axis=1).str.lower().str.contains(q.lower(), regex=False)]
        stat_c = st.columns(4)
        stat_c[0].metric("Customers", n(len(C))); stat_c[1].metric("Renewing in 60 days", n(C.days_to_renewal.between(0, 60).sum()))
        stat_c[2].metric("With open claims", n((C.claims_open.fillna(0) > 0).sum())); stat_c[3].metric("High-risk customers", n((C.highest_risk_band == "High").sum()))
        f1, f2 = st.columns([4, 1.4])
        with f1:
            view = seg("View", ["All", "Renewing soon", "Open claims", "High risk", "Multi-property"], "cj_view")
        sort = f2.selectbox("Sort", ["Highest premium", "Name A–Z", "Next renewal", "Most claims"], key="cj_sort", label_visibility="collapsed")
        if view == "Renewing soon":
            DIR = DIR[DIR.days_to_renewal.between(0, 60)]
        elif view == "Open claims":
            DIR = DIR[DIR.claims_open.fillna(0) > 0]
        elif view == "High risk":
            DIR = DIR[DIR.highest_risk_band == "High"]
        elif view == "Multi-property":
            DIR = DIR[DIR.properties.fillna(0) > 1]
        DIR = {"Highest premium": DIR.sort_values("premium_active", ascending=False), "Name A–Z": DIR.sort_values("customer"),
               "Next renewal": DIR.sort_values("next_renewal_date"), "Most claims": DIR.sort_values("claims_total", ascending=False)}[sort]
        if q:
            st.markdown(f'<div class="srch-chip">{len(DIR):,} customers match “{q}”</div>', unsafe_allow_html=True)
        if DIR.empty:
            st.info("No customers match this view.")
            st.stop()
        limit = st.session_state.setdefault("cj_limit", 12)
        st.caption(f"Showing {min(limit, len(DIR)):,} of {len(DIR):,} customers. Click a card to open the full Customer 360.")

        def open_cust(c_):
            st.session_state.update(cj_cid=c_, cj_tab="Customer")

        gcols = st.columns(3)
        for i_, r in enumerate(DIR.head(limit).itertuples()):
            tags = []
            if pd.notna(r.days_to_renewal) and 0 <= r.days_to_renewal <= 60:
                tags.append(f'<span class="ctag warn">Renews in {int(r.days_to_renewal)}d</span>')
            if nz_(r.claims_open) > 0:
                tags.append(f'<span class="ctag bad">{int(r.claims_open)} open claim{"s" if r.claims_open > 1 else ""}</span>')
            if r.highest_risk_band == "High":
                tags.append('<span class="ctag bad">High risk</span>')
            if nz_(r.properties) > 1:
                tags.append(f'<span class="ctag">{int(r.properties)} properties</span>')
            with gcols[i_ % 3]:
                card_action(f"cc_{i_}", f'''<div class="ccard"><div class="cc-top"><div class="av cc-av" style="background:{AV_COLORS[i_ % len(AV_COLORS)]}">{initials(r.customer)}</div>
                    <div class="cc-id"><div class="cc-name">{r.customer}</div><div class="cc-sub">{r.customer_id} · {r.primary_county}, {r.primary_state}</div></div>
                    <span class="cc-st {"on" if str(r.customer_status).upper() == "ACTIVE" else ""}">{str(r.customer_status).title()}</span></div>
                    <div class="cc-grid"><div><i>Properties</i><b>{n(r.properties)}</b></div><div><i>Policies</i><b>{n(r.active_policies)}</b></div><div><i>Premium</i><b>{usd(r.premium_active)}</b></div></div>
                    <div class="cc-tags">{"".join(tags) or '<span class="ctag ok">In good standing</span>'}</div></div>''', open_cust, r.customer_id)
        if len(DIR) > limit:
            st.button("Show more customers", key="cj_more", on_click=lambda: st.session_state.update(cj_limit=limit + 12))
        st.stop()

    crow = lab[lab.customer_id == cid].iloc[0]
    st.button("← All customers", key="back", on_click=lambda: st.session_state.update(cj_cid=None, cj_search="", hdr_search="", cj_limit=12))
    cprops = P_ALL[P_ALL.customer_id == crow.customer_id]
    if cprops.empty:
        st.info("This customer has no property rows.")
        st.stop()

    # ------------------------------------------------ Customer 360 data (only relationships present in the Gold tables)
    full = f"{crow.first_name} {crow.last_name}"
    nz = lambda v: 0 if pd.isna(v) else v
    fmt_d = lambda v: pd.Timestamp(v).strftime("%b %d, %Y") if pd.notna(v) else "—"
    pols = cprops[cprops.active_policy_id.notna()]
    po_by_id = PO_ALL.drop_duplicates("policy_id").set_index("policy_id")
    n_props, n_pols = len(cprops), len(pols)
    premium = cprops.active_premium.fillna(0).sum()
    insured = (cprops.active_building_coverage.fillna(0) + cprops.active_contents_coverage.fillna(0)).sum()
    open_cl, tot_cl, paid_cl = int(cprops.claims_open.fillna(0).sum()), int(cprops.claims_total.fillna(0).sum()), cprops.claims_paid_total.fillna(0).sum()
    status = str(crow.customer_status).title()
    nxt = crow.next_renewal_date
    dnext = (pd.Timestamp(nxt) - AS_OF).days if pd.notna(nxt) else None

    # claims: exact policy-id link first; otherwise same ZIP + same loss date as the property profile (labelled)
    parts = []
    for r in cprops.itertuples():
        if int(nz(r.claims_total)) == 0:
            continue
        ex = CL_ALL[CL_ALL.policy_id == r.active_policy_id].assign(link="Policy ID")
        fz = CL_ALL[CL_ALL.policy_id.str.contains(str(r.zip_code), regex=False) & (CL_ALL.date_of_loss == r.last_loss_date)].assign(link="ZIP + loss date")
        parts.append(pd.concat([ex, fz]).assign(property_id=r.property_id))
    CLM = pd.concat(parts).drop_duplicates("claim_id") if parts else CL_ALL.iloc[0:0].assign(link=None, property_id=None)
    CLM = CLM.assign(paid=CLM.amount_paid_on_building_claim.fillna(0) + CLM.amount_paid_on_contents_claim.fillna(0) + CLM.amount_paid_on_icc_claim.fillna(0))

    # ------------------------------------------------ hero
    since = f"{pd.Timestamp(crow.customer_since).year}" if pd.notna(crow.customer_since) else "—"
    kp = [("Properties insured", n(n_props)), ("Active policies", n(n_pols)), ("Annual premium", usd(premium)), ("Open claims", n(open_cl))]
    st.markdown(f'''<div class="hero360"><div class="h-l"><div class="av h-av">{initials(full)}</div>
        <div class="h-id"><div class="h-name">{full}<span class="stat {"on" if status.lower() == "active" else ""}">{status}</span></div>
        <div class="h-sub">Customer ID: {crow.customer_id}</div><div class="h-sub">📍 {crow.primary_county} County, {crow.primary_state}, USA</div>
        <div class="h-tags"><span class="tag">Customer since {since}</span><span class="tag">Agent {crow.agent_name}</span><span class="tag">Highest risk {crow.highest_risk_band}</span></div></div></div>
        <div class="h-r">{"".join(f'<div class="hk"><div class="hv">{v}</div><div class="hl">{l}</div></div>' for l, v in kp)}</div></div>''', unsafe_allow_html=True)

    # ------------------------------------------------ 360 connector cards (click to open a section)
    TABS = ["Customer", "Properties", "Policies", "Claims", "Renewals"]
    tab = st.session_state.get("cj_tab", "Customer")
    if tab not in TABS:
        tab = "Customer"

    def set_tab(t_):
        st.session_state["cj_tab"] = t_

    tiles = [("Customer", "👤", status, f"Since {since}"), ("Properties", "🏠", n(n_props), f"{cprops.state.nunique()} state{'s' if cprops.state.nunique() != 1 else ''} · {usd(insured)} insured"),
             ("Policies", "🛡️", n(n_pols), f"{usd(premium)} / year"), ("Claims", "⚠️", n(tot_cl), f"{n(open_cl)} open · {usd(paid_cl)} paid"),
             ("Renewals", "🔁", fmt_d(nxt) if pd.notna(nxt) else "—", f"in {dnext} days" if dnext is not None and dnext >= 0 else ("none scheduled" if pd.isna(nxt) else "overdue"))]
    for col_, (t_, ic, big, sub) in zip(st.columns(5), tiles):
        with col_:
            card_action(f"c3_{t_.lower()}", f'<div class="c360 {"on" if t_ == tab else ""}"><div class="c-h"><span class="c-ic">{ic}</span><span>{t_}</span></div><div class="c-big">{big}</div><div class="c-sub">{sub}</div></div>', set_tab, t_)

    # ------------------------------------------------ section body
    T_ = st.column_config.TextColumn
    with st.container(key="c360_body", border=True):
        st.markdown(f'<div class="ct">{ {"Customer": "Customer information", "Properties": "Property details", "Policies": "Policy details", "Claims": "Claims history", "Renewals": "Risk and renewal"}[tab] }</div>', unsafe_allow_html=True)

        if tab == "Customer":
            kv = [("Customer ID", crow.customer_id), ("Name", full), ("Status", status), ("Customer since", fmt_d(crow.customer_since)), ("Assigned agent", crow.agent_name),
                  ("Primary location", f"{crow.primary_county} County, {crow.primary_state}"), ("Properties", n(n_props)), ("Policy terms to date", n(cprops.policy_terms.fillna(0).sum())),
                  ("Insured value", usd(insured)), ("Annual premium", usd(premium)), ("Claims paid to date", usd(paid_cl)), ("Mitigation measures", n(cprops.mitigation_count.fillna(0).sum()))]
            st.markdown('<div class="dgrid">' + "".join(f'<div class="di"><div class="dk">{k}</div><div class="dv">{v}</div></div>' for k, v in kv) + '</div>', unsafe_allow_html=True)
            st.markdown('<div class="note360">Contact details (phone, email) are not part of the customer profile in the Gold layer, so they are not shown.</div>', unsafe_allow_html=True)

        elif tab == "Properties":
            d = cprops.assign(elev=cprops.elevated.map({True: "Yes", False: "No"}))
            st.dataframe(d[["property_id", "address_line", "city", "state", "county", "zip_code", "flood_zone", "construction_date_band", "elev", "crs_class", "assessed_risk_score", "assessed_risk_band", "active_policy_id"]],
                         use_container_width=True, hide_index=True,
                         column_config={"property_id": "Property ID", "address_line": "Address", "city": "City", "state": "State", "county": "County", "zip_code": "ZIP", "flood_zone": "Flood zone",
                                        "construction_date_band": "Construction", "elev": "Elevated", "crs_class": st.column_config.NumberColumn("CRS class", format="%d"),
                                        "assessed_risk_score": st.column_config.NumberColumn("Risk score", format="%.0f"), "assessed_risk_band": "Risk band", "active_policy_id": "Active policy"})
            st.markdown('<div class="note360">Property type, construction year and building value are not in the Gold property profile. The construction band and coverage amounts are shown instead.</div>', unsafe_allow_html=True)

        elif tab == "Policies":
            if pols.empty:
                st.info("No active policies for this customer.")
            else:
                def status_of(r):
                    if pd.isna(r.policy_expiration_date):
                        return "—"
                    dd = (pd.Timestamp(r.policy_expiration_date) - AS_OF).days
                    return "Expired" if dd < 0 else ("Expiring soon" if dd <= 60 else "Active")
                rows = []
                for r in pols.itertuples():
                    t_ = po_by_id.loc[r.active_policy_id] if r.active_policy_id in po_by_id.index else None
                    rows.append({"Policy number": r.active_policy_id, "Property": f"{r.address_line}, {r.city}", "Start date": t_.policy_effective_date if t_ is not None else pd.NaT,
                                 "Expiry date": r.policy_expiration_date, "Building cover": nz(r.active_building_coverage), "Contents cover": nz(r.active_contents_coverage),
                                 "Annual premium": nz(r.active_premium), "Terms": nz(r.policy_terms), "Status": status_of(r)})
                st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True,
                             column_config={"Start date": st.column_config.DateColumn(format="MMM D, YYYY"), "Expiry date": st.column_config.DateColumn(format="MMM D, YYYY"),
                                            "Building cover": st.column_config.NumberColumn(format="$%d"), "Contents cover": st.column_config.NumberColumn(format="$%d"),
                                            "Annual premium": st.column_config.NumberColumn(format="$%d")})

        elif tab == "Claims":
            k = st.columns(4)
            k[0].metric("Claims", n(tot_cl)); k[1].metric("Open", n(open_cl)); k[2].metric("Paid to date", usd(paid_cl))
            k[3].metric("Last loss", fmt_d(cprops.last_loss_date.max()))
            _pl, _mode = kpis.property_lr(P_ALL, PO_ALL, CL_ALL.assign(paid=CL_ALL.amount_paid_on_building_claim.fillna(0) + CL_ALL.amount_paid_on_contents_claim.fillna(0) + CL_ALL.amount_paid_on_icc_claim.fillna(0)), AS_OF)
            _me, _port = _pl[_pl.customer_id == cid], kpis.safe_div(_pl.paid.sum(), _pl.earned_premium.sum())
            if len(_me) and _me.earned_premium.sum() > 0:
                _lr, _z = kpis.safe_div(_me.paid.sum(), _me.earned_premium.sum()), float(kpis.credibility(_me.policy_years.sum()))
                lk = st.columns(4)
                lk[0].metric("Loss ratio" + (" (est.)" if _mode == "approx" else ""), fmt_lr(_lr), help="Claims paid ÷ premium earned, all terms to date")
                lk[1].metric("Credibility", fmt_lr(_z), help="How much weight this customer's own history gets, from policy-years of history")
                lk[2].metric("Adjusted loss ratio", fmt_lr(_z * _lr + (1 - _z) * _port), help="Own ratio blended with the portfolio ratio by credibility")
                lk[3].metric("Portfolio loss ratio", fmt_lr(_port))
            if tot_cl == 0:
                st.info("No claims on this customer's properties.")
            elif CLM.empty:
                st.info("Claims exist on the property profile, but no individual claim record could be linked to them.")
            else:
                st.dataframe(CLM[["claim_id", "policy_id", "property_id", "community_name", "date_of_loss", "amount_paid_on_building_claim", "amount_paid_on_contents_claim", "amount_paid_on_icc_claim", "paid", "link"]],
                             use_container_width=True, hide_index=True,
                             column_config={"claim_id": "Claim number", "policy_id": "Policy", "property_id": "Property", "community_name": "Community", "date_of_loss": st.column_config.DateColumn("Date of loss", format="MMM D, YYYY"),
                                            "amount_paid_on_building_claim": st.column_config.NumberColumn("Building paid", format="$%d"), "amount_paid_on_contents_claim": st.column_config.NumberColumn("Contents paid", format="$%d"),
                                            "amount_paid_on_icc_claim": st.column_config.NumberColumn("ICC paid", format="$%d"), "paid": st.column_config.NumberColumn("Total paid", format="$%d"), "link": "Linked by"})
            st.markdown('<div class="note360">Reported amount, claim status and settlement date are not in the Gold claim report. “Linked by” shows how each claim was tied to this customer: by policy ID, or, where the IDs differ, by ZIP code and date of loss from the property profile.</div>', unsafe_allow_html=True)

        else:  # Renewals / risk
            nr = st.columns([1, 1, 1, 1])
            nr[0].metric("Next renewal", fmt_d(nxt)); nr[1].metric("Days to renewal", "—" if dnext is None else n(dnext))
            nr[2].metric("Renewal pending", "Yes" if pd.notna(crow.renewal_pending) and bool(crow.renewal_pending) else "No"); nr[3].metric("Properties in high-risk flood zone", n(SFHA(cprops.flood_zone).sum()))
            if dnext is None:
                act = "No renewal is scheduled."
            elif dnext < 0:
                act = "Policy has passed its expiry date, so confirm whether it lapsed or was renewed."
            elif pd.notna(crow.renewal_pending) and bool(crow.renewal_pending):
                act = f"Renewal is pending and due in {dnext} days, so follow up with agent {crow.agent_name}."
            elif dnext <= 60:
                act = f"Renewal falls due in {dnext} days. Start the renewal conversation."
            else:
                act = f"Next renewal is in {dnext} days. No action needed yet."
            st.markdown(f'<div class="callout"><b>Next action.</b> {act}</div>', unsafe_allow_html=True)
            peers_all = P_ALL.assessed_risk_score.mean()
            cards = []
            for r in cprops.itertuples():
                hr = SFHA(pd.Series([r.flood_zone])).iloc[0]
                cards.append(f'<div class="rk"><div class="rk-h"><b>{r.address_line}</b><span>{r.city}, {r.state}</span></div>'
                             f'<div class="rk-g"><div><i>Flood zone</i><b>{r.flood_zone}{" · high-risk" if hr else ""}</b></div><div><i>Risk score</i><b>{nz(r.assessed_risk_score):.0f} · {r.assessed_risk_band}</b></div>'
                             f'<div><i>Loss history</i><b>{n(r.claims_total)} claim(s) · {usd(r.claims_paid_total)}</b></div><div><i>Mitigation</i><b>{n(r.mitigation_count)} measure(s)</b></div></div></div>')
            st.markdown('<div class="rk-wrap">' + "".join(cards) + '</div>', unsafe_allow_html=True)
            cmp_ = pd.DataFrame({"who": [f"{r.address_line[:24]}" for r in cprops.itertuples()] + ["Portfolio average"], "score": list(cprops.assessed_risk_score) + [peers_all]}).dropna()
            fig = px.bar(cmp_, x="score", y="who", orientation="h", title="Risk score vs portfolio", color="who", color_discrete_sequence=[PURPLE, MID, DEEP, SOFT])
            fig.update_layout(showlegend=False, yaxis_title=None, xaxis_title=None)
            fig.update_yaxes(autorange="reversed")
            show(fig, 120 + 46 * len(cmp_))

    # ------------------------------------------------ journey timeline (recorded dates only)
    ev = []
    if pd.notna(crow.customer_since):
        ev.append((crow.customer_since, "👤", "Became a customer", f"Assigned to agent {crow.agent_name}"))
    for r in pols.itertuples():
        if r.active_policy_id in po_by_id.index and pd.notna(po_by_id.loc[r.active_policy_id].policy_effective_date):
            ev.append((po_by_id.loc[r.active_policy_id].policy_effective_date, "🛡️", f"Policy {r.active_policy_id} took effect", f"{r.address_line}, {r.city}"))
        if pd.notna(r.policy_expiration_date):
            ev.append((r.policy_expiration_date, "🔁", f"Policy {r.active_policy_id} expires", f"{r.address_line} · renewal {'pending' if pd.notna(crow.renewal_pending) and bool(crow.renewal_pending) else 'due'}"))
    if len(CLM):
        for r in CLM.itertuples():
            ev.append((r.date_of_loss, "⚠️", f"Loss recorded · claim {r.claim_id}", f"{usd(r.paid)} paid · {r.community_name}"))
    else:
        for r in cprops[cprops.claims_total.fillna(0) > 0].itertuples():
            ev.append((r.last_loss_date, "⚠️", "Loss recorded", f"{r.address_line} · {n(r.claims_total)} claim(s)"))
    ev = sorted([e for e in ev if pd.notna(e[0])], key=lambda e: pd.Timestamp(e[0]))
    st.markdown('<div class="ct" style="margin:22px 0 10px">Customer insurance journey</div>', unsafe_allow_html=True)
    st.markdown('<div class="tl2">' + "".join(
        f'<div class="ev {"up" if pd.Timestamp(d_) > AS_OF else ""}"><div class="ev-dot">{ic}</div><div class="ev-b"><div class="ev-d">{fmt_d(d_)}{" · upcoming" if pd.Timestamp(d_) > AS_OF else ""}</div><div class="ev-t">{t_}</div><div class="ev-s">{s_}</div></div></div>'
        for d_, ic, t_, s_ in ev) + '</div>', unsafe_allow_html=True)
    st.markdown('<div class="note360">Events use only dates recorded in the Gold tables. Relationships shown are those established in the Gold layer (customer → property → policy). Claims are linked as described under Claims.</div>', unsafe_allow_html=True)

# =====================================================================
# PORTFOLIO & GEOGRAPHY
# =====================================================================
# =====================================================================
# LOSS RATIOS
# =====================================================================
elif page == "Loss Ratios":
    header("Loss Ratios", "Claims paid ÷ premium earned, by customer and for the whole portfolio")
    if len(P) == 0 or PO.empty:
        empty()
    else:
        if LIVE and (len(PO_ALL) >= 5000 or len(CL_ALL) >= 5000):
            st.warning("A Gold table is at Genie's 5,000-row limit, so these totals are incomplete. For production, read loss-ratio inputs through a SQL warehouse or a pre-aggregated Gold table.")
        if LR_MODE == "approx":
            gap_note(LR_GAP)
        Y = kpis.yearly(PO, CL, AS_OF)
        all_lr = kpis.safe_div(Y.paid.sum(), Y.earned_premium.sum())
        w = {d_: kpis.window_lr(PO, CL, AS_OF, d_) for d_ in (365, 365 * 3, 365 * 5)}
        yrs = PL.policy_years.sum()
        tiles([("Loss ratio · all time", fmt_lr(all_lr), f"{usd(Y.paid.sum())} paid ÷ {usd(Y.earned_premium.sum())} earned"),
               ("Last 12 months", fmt_lr(w[365][0]), f"{usd(w[365][1])} paid"), ("Last 3 years", fmt_lr(w[365 * 3][0]), f"{usd(w[365 * 3][1])} paid"),
               ("Last 5 years", fmt_lr(w[365 * 5][0]), f"{usd(w[365 * 5][1])} paid"),
               ("Claim frequency", f"{kpis.safe_div(PL.claims.sum(), yrs) * 100:.1f}", "claims per 100 policy-years"),
               ("Severity", usd(CL.paid[CL.paid > 0].mean()), "average paid per paid claim"),
               ("Pure premium", usd(kpis.safe_div(PL.paid.sum(), yrs)), "claims paid per policy-year"),
               ("Average premium", usd(kpis.safe_div(PL.earned_premium.sum(), yrs)), "earned per policy-year")])
        st.markdown('<div class="cap2">Paid loss ratio = claims paid ÷ earned premium. Reserves are not in the Gold tables, so open claims count as paid so far (this is not an incurred loss ratio). '
                    'Single customers are volatile; the credibility weight below pulls thin histories toward the portfolio figure.</div>', unsafe_allow_html=True)

        a, b = st.columns([3, 2])
        with a:
            with st.container(border=True):
                st.plotly_chart(lr_year_chart(Y), use_container_width=True)
                st.caption("Bars swing with catastrophe years; the dark cumulative line settles as years are added. The current year is year-to-date.")
        with b:
            with st.container(border=True):
                fig = go.Figure()
                fig.add_bar(x=Y.year.astype(str), y=Y.earned_premium, name="Earned premium", marker_color=SOFT)
                fig.add_bar(x=Y.year.astype(str), y=Y.paid, name="Claims paid", marker_color=PURPLE)
                fig.update_layout(barmode="group", title="Premium vs claims paid", legend=dict(orientation="h", y=1.12, x=0))
                fig.update_yaxes(tickprefix="$", tickformat="~s")
                st.plotly_chart(fig_style(fig, 330), use_container_width=True)

        st.markdown('<div class="ct">Credibility</div>', unsafe_allow_html=True)
        full = st.slider("Policy-years of history at which a customer's own loss ratio is fully credible", 3, 25, kpis.FULL_CRED_YEARS, key="full_cred",
                         help="Credibility Z = sqrt(policy-years ÷ this number), capped at 100%. Adjusted loss ratio = Z × own + (1 − Z) × portfolio.")

        st.markdown('<div class="ct">By segment</div>', unsafe_allow_html=True)
        DIMS = {"State": "state", "County": "area", "Flood zone": "flood_zone", "Risk band": "assessed_risk_band", "Construction": "construction_date_band", "Agent": "agent_name"}
        dim_lbl = seg("Break down by", list(DIMS), "lr_dim")
        seg_t = kpis.by_dim(PL, DIMS[dim_lbl], full, PORT_LR)
        seg_t = seg_t[seg_t.earned_premium > 0]
        if seg_t.empty:
            empty()
        else:
            a, b = st.columns([2, 3])
            with a:
                st.plotly_chart(lr_bar(seg_t, DIMS[dim_lbl]), use_container_width=True)
            with b:
                disp = as_pct(seg_t.sort_values("adj_loss_ratio", ascending=False)).rename(columns={DIMS[dim_lbl]: dim_lbl})
                table(disp[[dim_lbl, "properties", "policy_years", "earned_premium", "paid", "claims", "loss_ratio", "credibility", "adj_loss_ratio", "frequency", "severity"]], "lr_segment", lr_pct_cfg(), height=360)

        st.markdown('<div class="ct">By customer</div>', unsafe_allow_html=True)
        cu = kpis.by_dim(PL[PL.earned_premium > 0], "customer_id", full, PORT_LR)
        cu["customer"] = cu.customer_id.map(CNAME)
        f1, f2 = st.columns([4, 2])
        with f1:
            cview = seg("Customers", ["All", "Loss ratio above 100%", "Credible (80%+)", "Thin history"], "lr_cview")
        cu_v = {"All": cu, "Loss ratio above 100%": cu[cu.loss_ratio > 1], "Credible (80%+)": cu[cu.credibility >= .8], "Thin history": cu[cu.credibility < .5]}[cview]
        f2.markdown(f'<div class="srch-chip">{len(cu_v):,} of {len(cu):,} customers</div>', unsafe_allow_html=True)
        table(as_pct(cu_v.sort_values("adj_loss_ratio", ascending=False))[["customer_id", "customer", "properties", "policy_years", "earned_premium", "paid", "claims", "loss_ratio", "credibility", "adj_loss_ratio"]],
              "lr_customer", lr_pct_cfg(), open_col="customer_id", height=380)

        a, b = st.columns([3, 2])
        CAP = 3.0
        with a:
            fig = px.scatter(cu.assign(lr_pct=cu.loss_ratio.clip(upper=CAP) * 100), x="policy_years", y="lr_pct", color="credibility", hover_name="customer",
                             hover_data={"policy_years": ":.1f", "lr_pct": ":.0f", "earned_premium": ":$,.0f", "paid": ":$,.0f", "credibility": ":.0%"},
                             color_continuous_scale=[[0, SOFT], [1, DEEP]], title="Customer loss ratio vs years of history")
            fig.add_hline(y=PORT_LR * 100, line_dash="dot", line_color=MUTED, annotation_text="portfolio", annotation_position="top left")
            fig.update_yaxes(ticksuffix="%", title="Loss ratio (capped at 300%)")
            fig.update_xaxes(title="Policy-years of history")
            fig.update_traces(marker=dict(size=7, opacity=.75))
            st.plotly_chart(fig_style(fig, 360), use_container_width=True)
        with b:
            bk = cu.assign(bucket=pd.cut(cu.policy_years, [0, 2, 4, 7, 10, 10 ** 4], labels=["under 2", "2-4", "4-7", "7-10", "10+"]), lr_c=cu.loss_ratio.clip(upper=CAP))
            sp = bk.groupby("bucket", observed=True).agg(swing=("lr_c", "std"), customers=("customer_id", "count")).reset_index()
            fig = go.Figure(go.Bar(x=sp.bucket.astype(str), y=sp.swing * 100, marker_color=PURPLE, width=0.5, customdata=sp.customers, hovertemplate="%{x} years: %{y:.0f} pts spread · %{customdata} customers<extra></extra>"))
            fig.update_yaxes(ticksuffix=" pts")
            fig.update_xaxes(title="Policy-years of history")
            fig.update_layout(title="Spread of customer loss ratios shrinks with history")
            st.plotly_chart(fig_style(fig, 360), use_container_width=True)
            st.caption("Spread = standard deviation of customer loss ratios (each capped at 300%). This is the stabilising effect the data volume gives you.")


# =====================================================================
# CLAIMS DESK  (role view: claims adjuster)
# =====================================================================
elif page == "Claims Desk":
    header("Claims Desk", "Work queue and claim health for claims adjusters")
    if CL.empty:
        empty()
    else:
        if not LIFE:
            gap_note("Claim status, reported date, closed date and adjuster are not in <code>gold_claim_report</code> yet, so the queue, aging, time to close and workload cannot be shown. "
                     "Below is what the current Gold tables support: claims that deserve a second look. See the README for the columns to add.")
        f = st.columns([2, 1.2, 3])
        who = "All adjusters"
        if LIFE and kpis.has(DOPS, "adjuster_name"):
            who = f[0].selectbox("Adjuster", ["All adjusters"] + sorted(DOPS.adjuster_name.dropna().unique()), key="cd_adj")
        if LIFE:
            f[1].number_input("Past-SLA after (days open)", min_value=15, max_value=365, step=5, key="sla_days")
        DS = DOPS if who == "All adjusters" else DOPS[DOPS.adjuster_name == who]
        flags = DS.assign(f_waiting=DS.loss_within_30d_of_inception.fillna(False), f_limit=DS.coverage_used.fillna(0) > .75, f_lag=DS.days_to_report.fillna(0) > 30,
                          f_repeat=(DS.claims_on_property.fillna(1) > 1) if "claims_on_property" in DS.columns else False)
        flags["review_reasons"] = (flags.f_waiting.map({True: "Loss within 30 days of policy start · ", False: ""}) + flags.f_repeat.map({True: "Repeat loss on property · ", False: ""}) +
                                   flags.f_limit.map({True: "Paid over 75% of cover · ", False: ""}) + flags.f_lag.map({True: "Reported over 30 days after loss · ", False: ""})).str.rstrip(" ·")
        flags = flags[flags.review_reasons != ""]

        if LIFE:
            s = kpis.ops_summary(DS)
            tiles([("Open claims", n(s["open"]), f"{fmt_d1(s['open_avg_age'])} average age"), ("Past SLA", n(s["past_sla"]), f"open more than {st.session_state['sla_days']} days"),
                   ("Median days to close", fmt_d1(s["median_close"]), f"90th percentile {fmt_d1(s['p90_close'])}"), ("Closed within 60 days", pct(s["closed_60"]), f"within 30 days: {pct(s['closed_30'])}"),
                   ("Denied", pct(s["denial_rate"]), "share of all claims"), ("Report lag", fmt_d1(s["report_lag"]), "median, loss to reported"), ("Flagged for review", n(len(flags[flags.is_open])), "open claims with a review reason"),
                   ("Paid to date", usd(DS.paid.sum()), f"{n(len(DS))} claims")], per_row=4)
            view = seg("View", ["Open queue", "Needs review", "Closed claims"], "cd_view")
        else:
            rec = DS[DS.date_of_loss >= AS_OF - pd.Timedelta(days=365)]
            tiles([("Claims, last 12 months", n(len(rec)), f"{usd(rec.paid.sum())} paid"), ("Average paid", usd(rec.paid[rec.paid > 0].mean()), "per paid claim"),
                   ("Loss within 30 days of start", n(rec.loss_within_30d_of_inception.fillna(False).sum()), "possible waiting-period cases"), ("Paid over 75% of cover", n((rec.coverage_used.fillna(0) > .75).sum()), "close to the policy limit")])
            view = "Needs review"

        CFG = {"claim_id": st.column_config.TextColumn("Claim"), "customer": st.column_config.TextColumn("Customer"), "city": st.column_config.TextColumn("City"), "flood_zone": st.column_config.TextColumn("Zone"),
               "assessed_risk_band": st.column_config.TextColumn("Risk"), "date_of_loss": st.column_config.DateColumn("Date of loss", format="MMM D, YYYY"), "date_reported": st.column_config.DateColumn("Reported", format="MMM D, YYYY"),
               "date_closed": st.column_config.DateColumn("Closed", format="MMM D, YYYY"), "days_open": st.column_config.NumberColumn("Days open", format="%d"), "days_to_close": st.column_config.NumberColumn("Days to close", format="%d"),
               "age_bucket": st.column_config.TextColumn("Age"), "paid": st.column_config.NumberColumn("Paid", format="$%d"), "coverage": st.column_config.NumberColumn("Cover", format="$%d"),
               "adjuster_name": st.column_config.TextColumn("Adjuster"), "status": st.column_config.TextColumn("Status"), "review_reasons": st.column_config.TextColumn("Why review", width="large"),
               "past_sla": st.column_config.CheckboxColumn("Past SLA"), "community_name": st.column_config.TextColumn("Community")}
        keep = lambda df, cols_: df[[c for c in cols_ if c in df.columns]]

        if view == "Open queue":
            Q = DS[DS.is_open].sort_values("days_open", ascending=False)
            a, b = st.columns([3, 2])
            with a:
                table(keep(Q, ["claim_id", "customer", "city", "flood_zone", "assessed_risk_band", "adjuster_name", "date_of_loss", "date_reported", "days_open", "age_bucket", "past_sla", "coverage", "customer_id"]), "cd_queue", CFG, open_col="customer_id", height=430)
            with b:
                ag = Q.groupby("age_bucket", observed=False).size().reindex(kpis.AGE_LABELS, fill_value=0).reset_index(name="claims")
                fig = go.Figure(go.Bar(x=ag.age_bucket.astype(str), y=ag.claims, marker_color=[SOFT, MID, PURPLE, RED], width=0.55, hovertemplate="%{x}: %{y} claims<extra></extra>"))
                fig.update_layout(title="Open claims by age")
                st.plotly_chart(fig_style(fig, 330), use_container_width=True)
                st.caption("Age runs from the reported date. Oldest claims are at the top of the queue.")
        elif view == "Closed claims":
            Z = DS[DS.days_to_close.notna()]
            a, b = st.columns(2)
            with a:
                fig = px.histogram(Z, x="days_to_close", nbins=30, color_discrete_sequence=[PURPLE], title="Days from reported to closed")
                if len(Z):
                    fig.add_vline(x=Z.days_to_close.median(), line_dash="dot", line_color=DEEP, annotation_text=f"median {Z.days_to_close.median():.0f} d")
                fig.update_layout(bargap=.05, yaxis_title="claims", xaxis_title="days")
                st.plotly_chart(fig_style(fig, 320), use_container_width=True)
            with b:
                tr = kpis.close_trend(DS)
                fig = go.Figure()
                fig.add_scatter(x=tr.period, y=tr.median_days, mode="lines+markers", name="Median", line=dict(color=PURPLE, width=3))
                fig.add_scatter(x=tr.period, y=tr.p90_days, mode="lines", name="90th percentile", line=dict(color=MID, dash="dot"))
                fig.update_layout(title="Time to close by quarter closed", legend=dict(orientation="h", y=1.12, x=0))
                fig.update_yaxes(title="days")
                st.plotly_chart(fig_style(fig, 320), use_container_width=True)
            table(keep(Z.sort_values("date_closed", ascending=False), ["claim_id", "customer", "city", "status", "adjuster_name", "date_of_loss", "date_reported", "date_closed", "days_to_close", "paid", "customer_id"]), "cd_closed", CFG, open_col="customer_id", height=360)
        else:
            st.markdown('<div class="cap2">Prompts for a second look, not findings. A claim can have several reasons. '
                        'NFIP policies normally carry a 30-day waiting period, so a loss shortly after the policy started is worth checking against the policy dates.</div>', unsafe_allow_html=True)
            scope = flags if (not LIFE or st.toggle("Include closed claims", value=False, key="cd_incl")) else flags[flags.is_open]
            if not LIFE:
                scope = scope[scope.date_of_loss >= AS_OF - pd.Timedelta(days=365)]
            tiles([("Loss within 30 days of start", n(scope.f_waiting.sum()), "waiting-period check"), ("Repeat loss on property", n(scope.f_repeat.sum()), "more than one claim on the property" if "claims_on_property" in DS.columns else "needs property link in Gold"),
                   ("Paid over 75% of cover", n(scope.f_limit.sum()), "near the policy limit"), ("Reported late", n(scope.f_lag.sum()), "over 30 days after the loss")])
            table(keep(scope.sort_values("date_of_loss", ascending=False), ["claim_id", "customer", "city", "status", "review_reasons", "date_of_loss", "days_open", "paid", "coverage", "adjuster_name", "customer_id"]), "cd_review", CFG, open_col="customer_id", height=420)

# =====================================================================
# MANAGEMENT  (role view: insurance manager)
# =====================================================================
elif page == "Management":
    header("Management", "Performance, operations and risk across the portfolio")
    if len(P) == 0 or PO.empty:
        empty()
    else:
        if LR_MODE == "approx":
            gap_note(LR_GAP)
        tab = seg("Section", ["Performance", "Operations", "Risk & portfolio"], "mg_tab")
        Y = kpis.yearly(PO, CL, AS_OF)
        yrs = PL.policy_years.sum()
        if tab == "Performance":
            all_lr = kpis.safe_div(Y.paid.sum(), Y.earned_premium.sum())
            lr12, paid12, prem12 = kpis.window_lr(PO, CL, AS_OF, 365)
            rr = kpis.renewal_rate(PO, AS_OF)
            tiles([("Loss ratio · all time", fmt_lr(all_lr), "claims paid ÷ earned premium"), ("Loss ratio · 12 months", fmt_lr(lr12), f"{usd(paid12)} paid on {usd(prem12)} earned"),
                   ("Claim frequency", f"{kpis.safe_div(PL.claims.sum(), yrs) * 100:.1f}", "claims per 100 policy-years"), ("Severity", usd(CL.paid[CL.paid > 0].mean()), "average paid per paid claim"),
                   ("Pure premium", usd(kpis.safe_div(PL.paid.sum(), yrs)), "paid per policy-year"), ("Premium per $1k cover", f"${kpis.safe_div(ACT.active_premium.sum(), ACT.coverage.sum()) * 1000:,.2f}", "active policies"),
                   ("Renewal rate", pct(rr["rate"]) if rr else "—", "terms followed by another within 60 days" if rr else "needs property link in Gold"), ("Premium in force", usd(ACT.active_premium.sum()), f"{n(len(ACT))} active policies")])
            a, b = st.columns([3, 2])
            with a:
                with st.container(border=True):
                    st.plotly_chart(lr_year_chart(Y), use_container_width=True)
            with b:
                with st.container(border=True):
                    st_t = kpis.by_dim(PL, "state", portfolio_lr=PORT_LR)
                    st_t = st_t[st_t.earned_premium > 0]
                    fig = go.Figure(go.Bar(x=st_t.state, y=st_t.loss_ratio * 100, marker_color=[RED if v > 1 else PURPLE for v in st_t.loss_ratio], width=0.5, hovertemplate="%{x}: %{y:.0f}%<extra></extra>"))
                    fig.add_hline(y=100, line_dash="dot", line_color=MUTED)
                    fig.update_yaxes(ticksuffix="%")
                    fig.update_layout(title="Loss ratio by state")
                    st.plotly_chart(fig_style(fig, 330), use_container_width=True)
            a, b = st.columns(2)
            with a:
                if rr and len(rr["by_year"]):
                    ry = rr["by_year"]
                    fig = go.Figure(go.Bar(x=ry.year.astype(str), y=ry.rate * 100, marker_color=PURPLE, width=0.5, customdata=ry.terms, hovertemplate="%{x}: %{y:.1f}% of %{customdata} terms<extra></extra>"))
                    fig.update_yaxes(ticksuffix="%", range=[max(0, ry.rate.min() * 100 - 10), 100])
                    fig.update_layout(title="Renewal rate by year of expiry")
                    st.plotly_chart(fig_style(fig, 300), use_container_width=True)
                else:
                    st.info("Renewal rate needs property_id on the policy report (see README).")
            with b:
                ag_t = kpis.by_dim(PL[PL.agent_name.notna()], "agent_name", portfolio_lr=PORT_LR)
                ag_t = ag_t[ag_t.earned_premium > 0]
                table(as_pct(ag_t.sort_values("earned_premium", ascending=False))[["agent_name", "properties", "earned_premium", "paid", "loss_ratio", "adj_loss_ratio"]].rename(columns={"agent_name": "Agent"}), "mg_agents",
                      dict(lr_pct_cfg(), Agent=st.column_config.TextColumn("Agent")), height=300)
        elif tab == "Operations":
            if not LIFE:
                gap_note("Time to close, backlog and adjuster workload need claim status, reported date, closed date and adjuster on <code>gold_claim_report</code>. They are not in Gold yet (see README).")
            else:
                s = kpis.ops_summary(DOPS)
                tiles([("Open backlog", n(s["open"]), f"{fmt_d1(s['open_avg_age'])} average age"), ("Past SLA", n(s["past_sla"]), f"open over {st.session_state['sla_days']} days (set on Claims Desk)"),
                       ("Median days to close", fmt_d1(s["median_close"]), f"90th percentile {fmt_d1(s['p90_close'])}"), ("Closed within 60 days", pct(s["closed_60"]), f"within 30 days: {pct(s['closed_30'])}")])
                a, b = st.columns(2)
                with a:
                    tr = kpis.close_trend(DOPS)
                    fig = go.Figure()
                    fig.add_scatter(x=tr.period, y=tr.median_days, mode="lines+markers", name="Median", line=dict(color=PURPLE, width=3))
                    fig.add_scatter(x=tr.period, y=tr.p90_days, mode="lines", name="90th percentile", line=dict(color=MID, dash="dot"))
                    fig.update_layout(title="Days to close, by quarter closed", legend=dict(orientation="h", y=1.12, x=0))
                    st.plotly_chart(fig_style(fig, 320), use_container_width=True)
                with b:
                    ag = DOPS[DOPS.is_open].groupby("age_bucket", observed=False).size().reindex(kpis.AGE_LABELS, fill_value=0).reset_index(name="claims")
                    fig = go.Figure(go.Bar(x=ag.age_bucket.astype(str), y=ag.claims, marker_color=[SOFT, MID, PURPLE, RED], width=0.55))
                    fig.update_layout(title="Open backlog by age")
                    st.plotly_chart(fig_style(fig, 320), use_container_width=True)
                if kpis.has(DOPS, "adjuster_name"):
                    st.markdown('<div class="ct">Adjuster workload</div>', unsafe_allow_html=True)
                    wl = kpis.by_adjuster(DOPS)
                    table(wl.rename(columns={"adjuster_name": "Adjuster", "claims": "Claims", "open": "Open", "past_sla": "Past SLA", "avg_age_open": "Avg age of open (d)", "median_days_to_close": "Median days to close", "paid": "Paid"}).drop(columns="closed_per_open"),
                          "mg_workload", {"Paid": st.column_config.NumberColumn(format="$%d"), "Avg age of open (d)": st.column_config.NumberColumn(format="%.0f"), "Median days to close": st.column_config.NumberColumn(format="%.0f")}, height=240)
        else:
            rw = kpis.risk_weighting(ACT, PL, PORT_LR)
            conc = kpis.concentration(ACT.assign(area=ACT.county.fillna("") + ", " + ACT.state.fillna("")), "area")
            hi = P[P.assessed_risk_band == "High"]
            pre = ACT[ACT.construction_date_band == "Pre-FIRM"].coverage.sum() / max(ACT.coverage.sum(), 1)
            wavg = (ACT.assessed_risk_score * ACT.coverage).sum() / max(ACT.dropna(subset=["assessed_risk_score"]).coverage.sum(), 1)
            tiles([("Risk score, value-weighted", f"{wavg:.0f}", "0-100 POC index across active cover"), ("Top-3 county share", pct(conc["top3"]), "of active insured value"), ("Concentration (HHI)", f"{conc['hhi']:.2f}", "above 0.25 = highly concentrated"),
                   ("Pre-FIRM share", pct(pre), "of active insured value"), ("High-risk, mitigated", pct((hi.mitigation_count.fillna(0) > 0).mean() if len(hi) else float("nan")), "high-risk properties with a mitigation measure"),
                   ("In high-risk flood zones", pct(ACT[SFHA(ACT.flood_zone)].coverage.sum() / max(ACT.coverage.sum(), 1)), "of active insured value"), ("Properties without cover", n(P.active_policy_id.isna().sum()), "no active policy"),
                   ("Repetitive-loss properties", n(P.nfip_rl.fillna(False).astype(bool).sum()), "NFIP repetitive-loss flag")])
            a, b = st.columns(2)
            with a:
                fig = go.Figure()
                fig.add_bar(x=rw.assessed_risk_band, y=rw.prem_share * 100, name="Share of premium", marker_color=SOFT)
                fig.add_bar(x=rw.assessed_risk_band, y=rw.rw_share * 100, name="Share of risk-weighted exposure", marker_color=PURPLE)
                fig.update_layout(barmode="group", title="Premium vs risk it carries, by risk band", legend=dict(orientation="h", y=1.12, x=0))
                fig.update_yaxes(ticksuffix="%")
                st.plotly_chart(fig_style(fig, 330), use_container_width=True)
                st.caption("Risk-weighted exposure = insured value × risk score ÷ 100. Where the premium bar is shorter than the exposure bar, the band is priced below the risk it carries. The risk score is a POC index, not a probability.")
            with b:
                ca = kpis.by_dim(PL, "area", portfolio_lr=PORT_LR).merge(PL.groupby("area").assessed_risk_score.mean().rename("avg_risk").reset_index(), on="area")
                ca = ca[ca.earned_premium > 0]
                fig = px.scatter(ca, x="avg_risk", y=ca.adj_loss_ratio * 100, size="earned_premium", hover_name="area", color_discrete_sequence=[PURPLE], title="Risk vs loss ratio by county (bubble = premium)",
                                 hover_data={"avg_risk": ":.0f", "earned_premium": ":$,.0f"})
                fig.add_hline(y=PORT_LR * 100, line_dash="dot", line_color=MUTED, annotation_text="portfolio", annotation_position="top left")
                fig.update_yaxes(ticksuffix="%", title="Adjusted loss ratio")
                fig.update_xaxes(title="Average risk score")
                st.plotly_chart(fig_style(fig, 330), use_container_width=True)
            disp = rw.assign(prem_share=rw.prem_share * 100, rw_share=rw.rw_share * 100, loss_ratio=rw.loss_ratio * 100)[["assessed_risk_band", "policies", "coverage", "premium", "rate_per_1k", "prem_share", "rw_share", "adequacy", "loss_ratio", "claims"]]
            table(disp.rename(columns={"assessed_risk_band": "Risk band", "policies": "Policies", "coverage": "Insured value", "premium": "Premium", "rate_per_1k": "Premium per $1k", "prem_share": "Premium share",
                                       "rw_share": "Risk-weighted share", "adequacy": "Pricing adequacy", "loss_ratio": "Loss ratio", "claims": "Claims"}), "mg_risk",
                  {"Insured value": st.column_config.NumberColumn(format="$%d"), "Premium": st.column_config.NumberColumn(format="$%d"), "Premium per $1k": st.column_config.NumberColumn(format="$%.2f"),
                   "Premium share": st.column_config.NumberColumn(format="%.0f%%"), "Risk-weighted share": st.column_config.NumberColumn(format="%.0f%%"), "Pricing adequacy": st.column_config.NumberColumn(format="%.2f"),
                   "Loss ratio": st.column_config.NumberColumn(format="%.0f%%")}, height=170)
            st.caption("Pricing adequacy = share of premium ÷ share of risk-weighted exposure. Above 1.0 the band's premium is ahead of its risk; below 1.0 it is behind.")

elif page == "Portfolio & Geography":
    header("Portfolio & Geography")
    if len(P) == 0:
        empty()
    else:
        n_with_claim = int((P.claims_total.fillna(0) > 0).sum())
        fun = pd.DataFrame({"stage": ["Customers", "Properties", "Active policies", "Properties with a claim", "Renewals due ≤60d"],
                            "count": [len(C), len(P), len(ACT), n_with_claim, int(ACT.days.between(0, 60).sum())]})
        cty = P.drop_duplicates(["state", "county"]).assign(area=lambda d: d.county + ", " + d.state)
        k = st.columns(4)
        k[0].metric("Counties", len(cty)); k[1].metric("Top-3 county share", pct(cty.sort_values("county_insured_value", ascending=False).head(3).county_share_of_portfolio.sum()))
        k[2].metric("Properties with a claim", pct(n_with_claim / max(len(P), 1))); k[3].metric("Insured value", usd(ACT.coverage.sum()))

        # ---- map: where the properties are
        st.markdown('<div class="ct">Where the properties are</div>', unsafe_allow_html=True)
        if not kpis.has(P, "latitude", "longitude"):
            gap_note("Property latitude and longitude are not in <code>gold_property_profile</code> yet, so there is nothing to place on a map. Add <code>latitude</code> and <code>longitude</code> to the property profile (see README); "
                     "the map switches on as soon as they arrive.")
        else:
            m1, m2, m3 = st.columns([2, 2, 2])
            with m1:
                layer = seg("Map layer", ["Properties", "Counties"], "map_layer")
            if layer == "Properties":
                color_by = m2.selectbox("Colour by", ["Risk band", "Flood zone", "Claim history", "Policy status"], key="map_color")
                show_ = m3.selectbox("Show", ["All properties", "Active policies", "With claims", "Open claims", "High risk"], key="map_show")
                G = P.dropna(subset=["latitude", "longitude"]).assign(
                    claim_history=lambda d: np.where(d.claims_open.fillna(0) > 0, "Open claim", np.where(d.claims_total.fillna(0) > 0, "Has claims", "No claims")),
                    policy_status=lambda d: np.where(d.active_policy_id.notna(), "Active policy", "No active policy"), risk_band=lambda d: d.assessed_risk_band.fillna("Unscored"),
                    paid=lambda d: d.claims_paid_total.fillna(0), coverage=lambda d: d.active_building_coverage.fillna(0) + d.active_contents_coverage.fillna(0))
                G = {"All properties": G, "Active policies": G[G.active_policy_id.notna()], "With claims": G[G.claims_total.fillna(0) > 0], "Open claims": G[G.claims_open.fillna(0) > 0], "High risk": G[G.assessed_risk_band == "High"]}[show_]
                col_, cmap_ = {"Risk band": ("risk_band", {"High": RED, "Medium": AMBER, "Low": "#8FA3D9", "Unscored": MUTED}), "Flood zone": ("flood_zone", ZONE_COL),
                               "Claim history": ("claim_history", {"Open claim": RED, "Has claims": AMBER, "No claims": "#8FA3D9"}), "Policy status": ("policy_status", {"Active policy": PURPLE, "No active policy": MUTED})}[color_by]
                if G.empty:
                    st.info("No properties match this view.")
                else:
                    fig = ui.geo_map(G, color=col_, cmap=cmap_, hover_data={"property_id": True, "city": True, "state": True, "flood_zone": True, "risk_band": True, "claims_total": True, "paid": ":$,.0f", "coverage": ":$,.0f", "latitude": False, "longitude": False})
                    fig.update_traces(marker=dict(size=8, opacity=.78))
                    st.plotly_chart(fig, use_container_width=True)
                    st.caption(f"{len(G):,} properties shown. Hover shows property, place and risk details only; names and street addresses are left off the map on purpose.")
            else:
                color_c = m2.selectbox("Colour by", ["Loss ratio", "Claims paid per policy", "Risk score"], key="map_color_c")
                ctab = kpis.by_dim(PL.dropna(subset=["latitude", "longitude"]), "area", portfolio_lr=PORT_LR).merge(
                    PL.dropna(subset=["latitude", "longitude"]).groupby("area").agg(latitude=("latitude", "mean"), longitude=("longitude", "mean"), avg_risk=("assessed_risk_score", "mean")).reset_index(), on="area")
                ctab = ctab.merge(P.drop_duplicates(["state", "county"]).assign(area=lambda d: d.county + ", " + d.state)[["area", "county_insured_value", "county_claims_paid_per_policy"]], on="area", how="left")
                ctab = ctab.assign(lr_pct=ctab.adj_loss_ratio * 100, insured=ctab.county_insured_value.fillna(0).clip(lower=1))
                cc = {"Loss ratio": ("lr_pct", "Adjusted loss ratio %"), "Claims paid per policy": ("county_claims_paid_per_policy", "Claims paid per policy"), "Risk score": ("avg_risk", "Average risk score")}[color_c]
                fig = ui.geo_map(ctab, color=cc[0], size="insured", size_max=46, hover_name="area", color_continuous_scale=[[0, "#DCE3F7"], [.5, PURPLE], [1, RED]], labels={cc[0]: cc[1]},
                                 hover_data={"area": False, "latitude": False, "longitude": False, "insured": ":$,.0f", "properties": True, "earned_premium": ":$,.0f", "paid": ":$,.0f", "lr_pct": ":.0f"})
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Bubble size = active insured value in the county. Loss ratio is credibility-adjusted, so a county with little history stays close to the portfolio figure.")
        a, b = st.columns([2, 3])
        fig = go.Figure(go.Funnel(y=fun.stage, x=fun["count"], marker=dict(color=[DEEP, PURPLE, MID, "#C3B5F6", SOFT]), textinfo="value+percent initial"))
        fig.update_layout(title="Process funnel")
        a.plotly_chart(fig_style(fig, 430), use_container_width=True)
        fig = px.scatter(cty, x="county_insured_value", y="county_claims_paid_per_policy", size="county_declared_disasters_window", color="state", hover_name="area",
                         title="Insured value vs claims paid per policy (bubble = declared disasters)", color_discrete_sequence=ui.SEQ + [AMBER, RED])
        fig.update_xaxes(tickprefix="$")
        b.plotly_chart(fig_style(fig, 430), use_container_width=True)
        a, b = st.columns(2)
        a.plotly_chart(fig_style(px.treemap(cty, path=["state", "county"], values="county_insured_value", title="Insured value by county", color_discrete_sequence=ui.SEQ), 380), use_container_width=True)
        zs = ACT.groupby("flood_zone", as_index=False).coverage.sum()
        b.plotly_chart(fig_style(px.pie(zs, names="flood_zone", values="coverage", hole=.55, title="Active exposure by flood zone", color="flood_zone", color_discrete_map=ZONE_COL), 380), use_container_width=True)
        cty = cty.merge(kpis.by_dim(PL, "area", portfolio_lr=PORT_LR)[["area", "loss_ratio", "adj_loss_ratio"]].assign(loss_ratio=lambda d: d.loss_ratio * 100, adj_loss_ratio=lambda d: d.adj_loss_ratio * 100), on="area", how="left")
        st.dataframe(cty[["state", "county", "county_rank", "county_insured_value", "county_share_of_portfolio", "loss_ratio", "adj_loss_ratio", "county_claims_paid_per_policy", "county_declared_disasters_window",
                          "county_last_declared_year", "county_hma_projects", "county_hma_obligated"]].sort_values("county_rank"), use_container_width=True, hide_index=True,
                     column_config={"loss_ratio": st.column_config.NumberColumn("Loss ratio", format="%.0f%%"), "adj_loss_ratio": st.column_config.NumberColumn("Adjusted LR", format="%.0f%%")})

# =====================================================================
# RECORD PAGES (drill-downs) + SEARCH
# =====================================================================
elif page in RECORDS or page == "Search":
    NAME = (C_ALL.first_name.fillna("") + " " + C_ALL.last_name.fillna("")).str.strip()
    NAME = dict(zip(C_ALL.customer_id, NAME))
    MAXROWS = 5000
    D_ = st.column_config.DateColumn
    M_ = lambda label: st.column_config.NumberColumn(label, format="$%d")
    N_ = lambda label: st.column_config.NumberColumn(label, format="%d")
    T_ = st.column_config.TextColumn

    def find(df, cols_, q):
        if not q or df.empty:
            return df
        hay = df[cols_].fillna("").astype(str).agg(" ".join, axis=1).str.lower()
        return df[hay.str.contains(q.strip().lower(), regex=False)]

    def stat_strip(items):
        for c_, (l, v) in zip(st.columns(len(items)), items):
            c_.metric(l, v)

    def grid(df, key, cfg, order, open_col=None, name="records"):
        """Table with CSV export; if open_col is given, selecting a row offers the customer's journey."""
        df = df[[c for c in order if c in df.columns]]
        total = len(df)
        shown = df.head(MAXROWS)
        a_, b_ = st.columns([5, 1])
        a_.caption(f"{total:,} records" + (f" · showing the first {MAXROWS:,}, narrow with the filters above" if total > MAXROWS else ""))
        b_.download_button("⬇ CSV", shown.to_csv(index=False), file_name=f"{name}.csv", mime="text/csv", key="dl_" + key, use_container_width=True)
        if shown.empty:
            st.info("Nothing matches these filters.")
            return
        kw = dict(use_container_width=True, hide_index=True, height=520, column_config=cfg)
        if open_col:
            try:
                ev = st.dataframe(shown, key="tbl_" + key, on_select="rerun", selection_mode="single-row", **kw)
                rows_ = list(ev.selection.rows)
                if rows_ and rows_[0] < len(shown):
                    cid = shown.iloc[rows_[0]][open_col]
                    st.button(f"Open Customer 360 for {NAME.get(cid, cid)} →", key="oj_" + key, on_click=goto, args=("Customer 360",), kwargs={"cj_search": cid})
                else:
                    st.caption("Select a row to open the Customer 360 view.")
                return
            except TypeError:
                pass
        st.dataframe(shown, **kw)

    CUST_CFG = {"customer_id": T_("Customer ID"), "customer": T_("Customer"), "customer_status": T_("Status"), "customer_since": D_("Since", format="MMM D, YYYY"), "agent_name": T_("Agent"),
                "properties": N_("Properties"), "active_policies": N_("Active policies"), "premium_active": M_("Active premium"), "insured_value_active": M_("Insured value"),
                "next_renewal_date": D_("Next renewal", format="MMM D, YYYY"), "claims_total": N_("Claims"), "claims_open": N_("Open claims"), "claims_paid_total": M_("Claims paid"),
                "highest_risk_band": T_("Risk band"), "primary_county": T_("County"), "primary_state": T_("State")}
    CUST_ORDER = ["customer_id", "customer", "customer_status", "agent_name", "properties", "active_policies", "premium_active", "insured_value_active", "next_renewal_date",
                  "claims_total", "claims_open", "claims_paid_total", "highest_risk_band", "primary_county", "primary_state", "customer_since"]
    PROP_CFG = {"property_id": T_("Property ID"), "customer_id": T_("Customer ID"), "customer": T_("Customer"), "address_line": T_("Address"), "city": T_("City"), "state": T_("State"), "county": T_("County"),
                "zip_code": T_("ZIP"), "flood_zone": T_("Flood zone"), "construction_date_band": T_("Construction"), "elevated": st.column_config.CheckboxColumn("Elevated"),
                "active_policy_id": T_("Active policy"), "policy_expiration_date": D_("Expires", format="MMM D, YYYY"), "active_premium": M_("Premium"), "claims_total": N_("Claims"),
                "claims_open": N_("Open claims"), "claims_paid_total": M_("Claims paid"), "last_loss_date": D_("Last loss", format="MMM D, YYYY"),
                "assessed_risk_score": st.column_config.NumberColumn("Risk score", format="%.0f"), "assessed_risk_band": T_("Risk band")}
    PROP_ORDER = ["property_id", "customer", "address_line", "city", "state", "county", "zip_code", "flood_zone", "construction_date_band", "elevated", "active_policy_id",
                  "policy_expiration_date", "active_premium", "claims_total", "claims_open", "claims_paid_total", "assessed_risk_score", "assessed_risk_band", "customer_id"]
    POL_CFG = dict(PROP_CFG, active_policy_id=T_("Policy ID"), coverage=M_("Coverage"), days=N_("Days to renewal"), active_building_coverage=M_("Building cover"),
                   active_contents_coverage=M_("Contents cover"), agent_name=T_("Agent"), renewal_pending=st.column_config.CheckboxColumn("Renewal pending"))
    POL_ORDER = ["active_policy_id", "customer", "property_id", "address_line", "city", "state", "flood_zone", "policy_expiration_date", "days", "active_building_coverage",
                 "active_contents_coverage", "coverage", "active_premium", "claims_total", "customer_id"]
    CLM_CFG = {"claim_id": T_("Claim ID"), "policy_id": T_("Policy ID"), "state": T_("State"), "community_name": T_("Community"), "date_of_loss": D_("Date of loss", format="MMM D, YYYY"),
               "year_of_loss": N_("Year"), "paid": M_("Total paid"), "amount_paid_on_building_claim": M_("Building"), "amount_paid_on_contents_claim": M_("Contents"), "amount_paid_on_icc_claim": M_("ICC")}
    CLM_ORDER = ["claim_id", "policy_id", "community_name", "state", "date_of_loss", "amount_paid_on_building_claim", "amount_paid_on_contents_claim", "amount_paid_on_icc_claim", "paid"]

    def with_names(df):
        return df.assign(customer=df.customer_id.map(NAME))

    if page == "Search":
        q = st.session_state.get("search_q", "")
        header("Search results", f"Results for “{q}”" if q else "Type in the search bar above and press Enter.")
        st.button("← Back to Overview", key="back", on_click=goto, args=("Overview",))
        if q:
            r_c = find(with_names(C_ALL).assign(customer=lambda d: d.customer), ["customer_id", "customer", "agent_name", "primary_county", "primary_state"], q)
            r_p = find(with_names(P_ALL), ["property_id", "customer_id", "customer", "address_line", "city", "zip_code", "county", "state", "active_policy_id"], q)
            r_o = find(with_names(P_ALL[P_ALL.active_policy_id.notna()]), ["active_policy_id", "property_id", "customer", "city", "state"], q)
            r_l = find(CL_ALL.assign(paid=CL_ALL.amount_paid_on_building_claim.fillna(0) + CL_ALL.amount_paid_on_contents_claim.fillna(0) + CL_ALL.amount_paid_on_icc_claim.fillna(0)), ["claim_id", "policy_id", "community_name", "state"], q)
            tabs = st.tabs([f"Customers ({len(r_c):,})", f"Properties ({len(r_p):,})", f"Policies ({len(r_o):,})", f"Claims ({len(r_l):,})"])
            with tabs[0]:
                grid(r_c, "s_c", CUST_CFG, CUST_ORDER, "customer_id", "customers_search")
            with tabs[1]:
                grid(r_p, "s_p", PROP_CFG, PROP_ORDER, "customer_id", "properties_search")
            with tabs[2]:
                grid(r_o, "s_o", POL_CFG, POL_ORDER, "customer_id", "policies_search")
            with tabs[3]:
                grid(r_l, "s_l", CLM_CFG, CLM_ORDER, None, "claims_search")

    elif page == "Customers":
        header("Customers", f"{n(len(C))} customers" + (f" in {', '.join(sel_states)}" if sel_states else ""))
        st.button("← Back to Overview", key="back", on_click=goto, args=("Overview",))
        stat_strip([("Customers", n(len(C))), ("Active", n((C.customer_status == "ACTIVE").sum())), ("Multi-property", n((C.properties > 1).sum())), ("Active premium", usd(C.premium_active.sum()))])
        f = st.columns([3, 1.5, 1.5, 2])
        q = f[0].text_input("Search customers", key="f_c_q", placeholder="Search name, ID, agent or county", label_visibility="collapsed")
        s1 = f[1].selectbox("Status", ["All statuses"] + sorted(C.customer_status.dropna().unique()), key="f_c_s", label_visibility="collapsed")
        s2 = f[2].selectbox("Risk", ["All risk bands", "High", "Medium", "Low"], key="f_c_r", label_visibility="collapsed")
        s3 = f[3].selectbox("Agent", ["All agents"] + sorted(C.agent_name.dropna().unique()), key="f_c_a", label_visibility="collapsed")
        d = with_names(C)
        d = find(d, ["customer_id", "customer", "agent_name", "primary_county"], q)
        d = d[d.customer_status == s1] if not s1.startswith("All") else d
        d = d[d.highest_risk_band == s2] if not s2.startswith("All") else d
        d = d[d.agent_name == s3] if not s3.startswith("All") else d
        grid(d.sort_values("premium_active", ascending=False), "cust", CUST_CFG, CUST_ORDER, "customer_id", "customers")

    elif page == "Properties":
        header("Properties", f"{n(len(P))} insured properties" + (f" in {', '.join(sel_states)}" if sel_states else ""))
        st.button("← Back to Overview", key="back", on_click=goto, args=("Overview",))
        stat_strip([("Properties", n(len(P))), ("With active policy", n(P.active_policy_id.notna().sum())), ("High-risk flood zone", pct(SFHA(P.flood_zone).mean()) if len(P) else "—"),
                    ("Avg risk score", f"{P.assessed_risk_score.mean():.0f}" if len(P) else "—")])
        f = st.columns([3, 1.5, 1.5, 2])
        q = f[0].text_input("Search properties", key="f_p_q", placeholder="Search address, city, ZIP, property or customer", label_visibility="collapsed")
        z = f[1].selectbox("Zone", ["All flood zones"] + sorted(P.flood_zone.dropna().unique()), key="f_p_z", label_visibility="collapsed")
        r = f[2].selectbox("Risk", ["All risk bands", "High", "Medium", "Low"], key="f_p_r", label_visibility="collapsed")
        pcov = f[3].selectbox("Policy", ["All properties", "With active policy", "No active policy", "With claims"], key="f_p_c", label_visibility="collapsed")
        d = find(with_names(P), ["property_id", "customer_id", "customer", "address_line", "city", "zip_code", "county"], q)
        d = d[d.flood_zone == z] if not z.startswith("All") else d
        d = d[d.assessed_risk_band == r] if not r.startswith("All") else d
        d = {"With active policy": d[d.active_policy_id.notna()], "No active policy": d[d.active_policy_id.isna()], "With claims": d[d.claims_total.fillna(0) > 0]}.get(pcov, d)
        grid(d.sort_values("assessed_risk_score", ascending=False), "prop", PROP_CFG, PROP_ORDER, "customer_id", "properties")

    elif page == "Policies":
        header("Policies", "Active policies and every policy term")
        st.button("← Back to Overview", key="back", on_click=goto, args=("Overview",))
        view = seg("View", ["Active", "All terms"], "pol_view")
        if view == "Active":
            stat_strip([("Active policies", n(len(ACT))), ("Annual premium", usd(ACT.active_premium.sum())), ("Insured value", usd(ACT.coverage.sum())), ("Expiring ≤60d", n(ACT.days.between(0, 60).sum()))])
            f = st.columns([3, 1.5, 2])
            q = f[0].text_input("Search policies", key="f_o_q", placeholder="Search policy, property, customer or city", label_visibility="collapsed")
            z = f[1].selectbox("Zone", ["All flood zones"] + sorted(ACT.flood_zone.dropna().unique()), key="f_o_z", label_visibility="collapsed")
            w = f[2].selectbox("Expiry", ["Any expiry", "Within 30 days", "Within 60 days", "Within 90 days"], key="f_o_w", label_visibility="collapsed")
            d = find(with_names(ACT), ["active_policy_id", "property_id", "customer_id", "customer", "city", "address_line"], q)
            d = d[d.flood_zone == z] if not z.startswith("All") else d
            lim = {"Within 30 days": 30, "Within 60 days": 60, "Within 90 days": 90}.get(w)
            d = d[d.days.between(0, lim)] if lim else d
            grid(d.sort_values("policy_expiration_date"), "pol", POL_CFG, POL_ORDER, "customer_id", "active_policies")
        else:
            stat_strip([("Policy terms", n(len(PO))), ("Premium written", usd(PO.total_insurance_premium.sum())), ("Coverage written", usd(PO.coverage.sum())), ("Communities", n(PO.community_name.nunique()))])
            f = st.columns([3, 2])
            q = f[0].text_input("Search terms", key="f_t_q", placeholder="Search policy ID, community or state", label_visibility="collapsed")
            yr = f[1].selectbox("Year", ["All years"] + [str(y) for y in sorted(PO.policy_effective_date.dt.year.dropna().astype(int).unique(), reverse=True)], key="f_t_y", label_visibility="collapsed")
            d = find(PO, ["policy_id", "community_name", "state"], q)
            d = d[d.policy_effective_date.dt.year == int(yr)] if yr != "All years" else d
            cfg = {"policy_id": T_("Policy ID"), "state": T_("State"), "community_name": T_("Community"), "policy_effective_date": D_("Effective", format="MMM D, YYYY"),
                   "policy_termination_date": D_("Terminates", format="MMM D, YYYY"), "total_building_insurance_coverage": M_("Building cover"), "total_contents_insurance_coverage": M_("Contents cover"),
                   "total_insurance_premium": M_("Premium")}
            grid(d.sort_values("policy_effective_date", ascending=False), "terms", cfg, ["policy_id", "community_name", "state", "policy_effective_date", "policy_termination_date",
                 "total_building_insurance_coverage", "total_contents_insurance_coverage", "total_insurance_premium"], None, "policy_terms")

    elif page == "Claims":
        header("Claims", "Open claims by property and the full claims history")
        st.button("← Back to Overview", key="back", on_click=goto, args=("Overview",))
        view = seg("View", ["Open claims", "All claims"], "claims_view")
        if view == "Open claims":
            op = P[P.claims_open.fillna(0) > 0]
            stat_strip([("Open claims", n(op.claims_open.sum())), ("Properties affected", n(len(op))), ("Customers affected", n(op.customer_id.nunique())), ("Paid to date", usd(op.claims_paid_total.sum()))])
            q = st.text_input("Search open claims", key="f_k_q", placeholder="Search property, customer, address or city", label_visibility="collapsed")
            d = find(with_names(op), ["property_id", "customer_id", "customer", "address_line", "city"], q)
            grid(d.sort_values("last_loss_date", ascending=False), "open", PROP_CFG, ["property_id", "customer", "address_line", "city", "state", "claims_open", "claims_total", "claims_paid_total", "last_loss_date",
                 "flood_zone", "active_policy_id", "customer_id"], "customer_id", "open_claims")
        else:
            stat_strip([("Claims", n(len(CL))), ("Total paid", usd(CL.paid.sum())), ("Avg per claim", usd(CL.paid.mean() if len(CL) else 0)), ("Communities", n(CL.community_name.nunique()))])
            f = st.columns([3, 2])
            q = f[0].text_input("Search claims", key="f_k2_q", placeholder="Search claim ID, policy ID or community", label_visibility="collapsed")
            yr = f[1].selectbox("Year", ["All years"] + [str(y) for y in sorted(CL.year_of_loss.dropna().astype(int).unique(), reverse=True)], key="f_k2_y", label_visibility="collapsed")
            d = find(CL, ["claim_id", "policy_id", "community_name"], q)
            d = d[d.year_of_loss == int(yr)] if yr != "All years" else d
            grid(d.sort_values("date_of_loss", ascending=False), "claims", CLM_CFG, CLM_ORDER, None, "claims")

    else:  # Renewals
        header("Renewals", "Active policies approaching their expiration date")
        st.button("← Back to Overview", key="back", on_click=goto, args=("Overview",))
        win = seg("Window", ["≤30 days", "≤60 days", "≤90 days", "All upcoming"], "ren_win")
        lim = {"≤30 days": 30, "≤60 days": 60, "≤90 days": 90}.get(win, 100000)
        R = with_names(ACT[ACT.days.between(0, lim)])
        R = R.merge(C_ALL[["customer_id", "agent_name", "renewal_pending"]], on="customer_id", how="left")
        stat_strip([("Renewals due", n(len(R))), ("Premium up for renewal", usd(R.active_premium.sum())), ("Insured value", usd(R.coverage.sum())), ("Pending", n(R.renewal_pending.fillna(False).astype(bool).sum()))])
        f = st.columns([3, 2])
        q = f[0].text_input("Search renewals", key="f_r_q", placeholder="Search customer, policy, property or agent", label_visibility="collapsed")
        ag = f[1].selectbox("Agent", ["All agents"] + sorted(R.agent_name.dropna().unique()), key="f_r_a", label_visibility="collapsed")
        d = find(R, ["active_policy_id", "property_id", "customer", "agent_name", "city"], q)
        d = d[d.agent_name == ag] if not ag.startswith("All") else d
        grid(d.sort_values("days"), "ren", POL_CFG, ["active_policy_id", "customer", "agent_name", "property_id", "city", "state", "policy_expiration_date", "days", "active_premium", "coverage",
             "renewal_pending", "claims_total", "customer_id"], "customer_id", "renewals")

# =====================================================================
# ASK GENIE
# =====================================================================
else:
    header("Ask Genie")
    chat = st.session_state.setdefault("chat", [])
    SUGG = [("📍", "Top counties", "Which counties have the highest claims paid per policy?"), ("🔁", "Renewals by agent", "How many policies renew in the next 60 days by agent?"),
            ("🌊", "Risk without mitigation", "Which high-risk properties have no mitigation?"), ("♻️", "Repetitive loss", "Show repetitive-loss properties by flood zone.")]

    def ask_q(q_):
        st.session_state["chat_pending"] = q_

    def clear_chat():
        st.session_state.update(chat=[], chat_conv=None)

    if not chat:
        st.markdown('''<div class="gen-hero"><div class="gen-orb">✨</div><div class="gen-t">What would you like to know?</div>
            <div class="gen-s">Ask about customers, policies, claims, renewals or risk in plain English. Genie writes the query and shows you the result.</div></div>''', unsafe_allow_html=True)
        g = st.columns(2)
        for i_, (ic, ttl, qq) in enumerate(SUGG):
            with g[i_ % 2]:
                card_action(f"sg_{i_}", f'<div class="sugg"><div class="sq">{ic}</div><div class="mid"><div class="st1">{ttl}</div><div class="st2">{qq}</div></div><div class="go">›</div></div>', ask_q, qq)
        st.markdown('<div class="gen-foot">Shared across the workspace: about 5 questions a minute · results capped at 5,000 rows</div>', unsafe_allow_html=True)
    else:
        top = st.columns([6, 1])
        top[1].button("New chat", key="chat_new", on_click=clear_chat, use_container_width=True)
        for m in chat:
            if m["role"] == "me":
                st.markdown(f'<div class="msg-row me"><div class="msg me">{m["text"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="msg-row"><div class="msg-av">✨</div><div class="msg gn">{m["text"] or "Here is the result."}</div></div>', unsafe_allow_html=True)
                if m.get("df") is not None:
                    st.dataframe(m["df"], use_container_width=True, hide_index=True)
                if m.get("sql"):
                    with st.expander("Show query"):
                        st.code(m["sql"], language="sql")
                for note in m.get("notes", []):
                    st.caption("⚠️ " + note)
    pending = st.session_state.pop("chat_pending", None)
    ask = st.chat_input("Ask Genie about customers, claims, renewals, risk…") or pending
    if ask:
        chat.append({"role": "me", "text": ask})
        if not LIVE:
            chat.append({"role": "genie", "text": "Genie isn't connected in this environment yet. Once the Genie space is attached, this chat answers live."})
        else:
            try:
                with st.spinner("Genie is working…"):
                    ans = data._genie().ask(ask, st.session_state.get("chat_conv"))
                st.session_state["chat_conv"] = ans.conversation_id
                chat.append({"role": "genie", "text": ans.text or ans.description, "sql": ans.sql, "df": ans.df, "notes": ans.notes})
            except Exception as e:
                chat.append({"role": "genie", "text": f"Couldn't answer that: {e}"})
        st.rerun()
