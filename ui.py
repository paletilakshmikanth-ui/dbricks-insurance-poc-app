"""Shared look & feel (soft lavender-blue canvas, navy + violet accents) and small formatting helpers."""
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

import journey as J

PURPLE, DEEP, MID, SOFT, TINT = "#7B5CE6", "#1F2A4A", "#A28BEF", "#DCD5F8", "#E6ECFC"
INK, MUTED, RED, AMBER = "#232B45", "#7D879F", "#D6567F", "#C9A227"
SEQ = [DEEP, PURPLE, MID, "#C3B5F6", "#8FA3D9", SOFT]
ZONE_COL = {"VE": DEEP, "AE": PURPLE, "A": MID, "B": "#C3B5F6", "X": "#DCE3F7"}
BAND_COL = {"High": DEEP, "Medium": PURPLE, "Low": "#C3B5F6"}
AV_COLORS = ["#7B5CE6", "#1F2A4A", "#A28BEF", "#5B7BD5", "#3B4A7A"]


def inject_css():
    import ui_css
    css = ui_css.CSS
    for k, v in {"@BG": "#E9EFFD", "@PURPLE": PURPLE, "@DEEP": DEEP, "@INK": INK, "@MUTED": MUTED, "@RED": RED}.items():
        css = css.replace(k, v)
    st.markdown(css, unsafe_allow_html=True)


def usd(x):
    x = 0.0 if x is None or pd.isna(x) else float(x)
    for div, s in [(1e9, "B"), (1e6, "M"), (1e3, "K")]:
        if abs(x) >= div:
            return f"${x / div:,.1f}{s}"
    return f"${x:,.0f}"


def n(x):
    return f"{0.0 if x is None or pd.isna(x) else float(x):,.0f}"


def pct(x):
    return "—" if x is None or pd.isna(x) else f"{x:.0%}"


def fig_style(fig, h=330):
    fig.update_layout(height=h, margin=dict(l=8, r=8, t=44, b=8), plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                      font=dict(color=INK, family="Plus Jakarta Sans, Segoe UI, sans-serif"), legend_title_text="",
                      title_font=dict(size=15, color=INK), colorway=SEQ)
    fig.update_xaxes(gridcolor="#DCE3F7", zerolinecolor="#DCE3F7", linecolor="#DCE3F7")
    fig.update_yaxes(gridcolor="#DCE3F7", zerolinecolor="#DCE3F7", linecolor="#DCE3F7")
    return fig


def show(fig, h=330):
    st.plotly_chart(fig_style(fig, h), use_container_width=True)


def initials(name):
    p = name.split()
    return (p[0][0] + (p[-1][0] if len(p) > 1 else "")).upper()


def avatars(names, big=False):
    h = "".join(f'<div class="av" style="background:{AV_COLORS[i % len(AV_COLORS)]}">{initials(nm)}</div>' for i, nm in enumerate(names))
    return f'<div class="avs{" big-avs" if big else ""}">{h}</div>'


def flow_html(active):
    out = ['<div class="flow">']
    for name, a, b in J.PHASES:
        out.append(f'<div class="pg"><div class="phase">{name}</div><div class="chips">')
        for num, title, _ in J.STEPS[a - 1:b]:
            cls = "active" if num == active else ("done" if num < active else "")
            out.append(f'<div class="chip {cls}"><b>{num}</b>{title}</div>')
        out.append("</div></div>")
    out.append("</div>")
    return "".join(out)


def gap_note(text):
    st.markdown(f'<div class="callout"><b>Not in the Gold tables.</b> {text}</div>', unsafe_allow_html=True)


def geo_map(df, color=None, cmap=None, h=520, **kw):
    """Scatter map on a free basemap (no token). Centre and zoom are fitted to the points. Works on plotly 5.24+ (scatter_map) and older (scatter_mapbox)."""
    span = max(df.latitude.max() - df.latitude.min(), (df.longitude.max() - df.longitude.min()) * .8, .05)
    args = dict(lat="latitude", lon="longitude", color=color, height=h, zoom=float(np.clip(np.log2(700 / span) - .4, 2.5, 11)),
                center=dict(lat=float(df.latitude.mean()), lon=float(df.longitude.mean())), **kw)
    if cmap:
        args["color_discrete_map"] = cmap
    fn = getattr(px, "scatter_map", None)
    fig = fn(df, map_style="carto-positron", **args) if fn else px.scatter_mapbox(df, mapbox_style="carto-positron", **args)
    fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), paper_bgcolor="rgba(0,0,0,0)", legend=dict(title_text="", orientation="h", y=1.02, x=0), font=dict(color=INK, family="Plus Jakarta Sans, Segoe UI, sans-serif"))
    return fig
