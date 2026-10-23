# Generated from the approved design: do not hand-edit colours here, change them in ui.py
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stApp {font-family:'Plus Jakarta Sans','Inter','Segoe UI',sans-serif;}
.stApp {background:@BG;}
header[data-testid="stHeader"] {background:transparent;}
#MainMenu, footer {visibility:hidden;}
.block-container {padding:1.6rem 2.4rem 3rem; max-width:100% !important;}

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {background:#F4F6FD; border-right:1px solid #DCE3F7;}
section[data-testid="stSidebar"][aria-expanded="true"] {width:268px; min-width:268px;}
section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"], section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] > * {margin-bottom:0 !important;}
section[data-testid="stSidebar"] [data-testid="stSidebarHeader"] {height:2.2rem; padding:0 .8rem;}
section[data-testid="stSidebar"] [data-testid="stSidebarUserContent"] {padding:0 1rem 1.2rem;}
section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] {gap:0 !important;}
section[data-testid="stSidebar"] [data-testid="stElementContainer"] {margin:0;}
.brand {display:flex; gap:12px; align-items:center; margin:0 0 20px 2px; padding-bottom:18px; border-bottom:1px solid #E1E7F8;}
.brand .logo {width:42px; height:42px; border-radius:13px; background:linear-gradient(135deg,@PURPLE,#4F34C4); display:flex; align-items:center; justify-content:center; flex:none; box-shadow:0 6px 14px rgba(123,92,230,.35);}
.brand b {display:block; font-size:1.02rem; color:@INK; line-height:1.15; letter-spacing:-.01em;}
.brand .bt2 b {font-size:1.08rem;}
.navlbl {font-size:.68rem; line-height:1.3; letter-spacing:.12em; text-transform:uppercase; color:#98A2BC; font-weight:700; margin:0; padding:0 0 6px 12px; height:38px; display:flex; align-items:flex-end; box-sizing:border-box;}
section[data-testid="stSidebar"] [class*="st-key-nav_"] button, section[data-testid="stSidebar"] [class*="st-key-navon_"] button {
  justify-content:flex-start; text-align:left; border:none; background:transparent; box-shadow:none; border-radius:10px; padding:0 .8rem; height:40px; min-height:40px; color:#4A5573; width:100%; margin:1px 0;}
section[data-testid="stSidebar"] [class*="st-key-nav_"] button > div, section[data-testid="stSidebar"] [class*="st-key-navon_"] button > div, section[data-testid="stSidebar"] [class*="st-key-nav_"] [data-testid="stMarkdownContainer"], section[data-testid="stSidebar"] [class*="st-key-navon_"] [data-testid="stMarkdownContainer"] {justify-content:flex-start !important; text-align:left !important; width:100%;}
section[data-testid="stSidebar"] [class*="st-key-nav_"] button p, section[data-testid="stSidebar"] [class*="st-key-navon_"] button p {font-size:.93rem; font-weight:500; text-align:left; margin:0;}
section[data-testid="stSidebar"] [class*="st-key-nav_"] button:hover {background:#E8EDFC; color:@INK; border:none;}
section[data-testid="stSidebar"] [class*="st-key-navon_"] button {background:#fff; color:@PURPLE; box-shadow:0 1px 3px rgba(31,42,74,.08), inset 3px 0 0 @PURPLE; cursor:default;}
section[data-testid="stSidebar"] [class*="st-key-navon_"] button p {font-weight:700; color:@PURPLE;}
section[data-testid="stSidebar"] [class*="st-key-navon_"] button:hover {border:none; color:@PURPLE;}
section[data-testid="stSidebar"] .st-key-refresh_data button {margin-top:14px; font-size:.82rem; background:transparent; border:1px dashed #C9D2EE;}

/* ---------- header ---------- */
.h1 {font-size:2.05rem; white-space:nowrap; font-weight:800; color:@INK; line-height:1.08; letter-spacing:-.02em;}
.hsub {color:@MUTED; font-size:.95rem; margin-top:2px;}
.chip-d {display:flex; width:fit-content; margin:0; align-items:center; gap:8px; height:46px; padding:0 18px; border-radius:999px; background:#F3F6FE; border:1px solid #DCE3F7; color:@INK; font-weight:600; font-size:.9rem; white-space:nowrap;}
.hdr-right {display:flex; width:100%; align-items:center; gap:12px; justify-content:flex-end; flex-wrap:nowrap;}
.stagepill {display:flex; align-items:center; gap:10px; height:46px; padding:0 16px; border-radius:999px; background:#F3F6FE; border:1px solid #DCE3F7; font-size:.85rem; font-weight:600; color:@INK;}
.seg {display:flex; gap:4px;} .seg i {display:block; width:26px; height:6px; border-radius:6px; background:#D5DCF2;} .seg i.on {background:@DEEP;}
.avs {display:flex;} .av {width:40px; height:40px; border-radius:50%; display:flex; align-items:center; justify-content:center; color:#fff; font-weight:700; font-size:.8rem; border:3px solid #EAF0FE; margin-left:-8px;}
.avs .av:first-child {margin-left:0;}
.st-key-searchbox div[data-baseweb="input"], .st-key-searchbox div[data-baseweb="base-input"], .st-key-searchbox [data-testid="stTextInputRootElement"] {height:48px; border-radius:999px !important; background:#fff !important; border:1px solid #D5DDF3 !important; box-shadow:0 2px 8px rgba(31,42,74,.06); overflow:hidden; transition:.15s;}
.st-key-searchbox div[data-baseweb="input"]:focus-within, .st-key-searchbox [data-testid="stTextInputRootElement"]:focus-within {border-color:@PURPLE !important; box-shadow:0 0 0 4px rgba(123,92,230,.16);}
.st-key-searchbox input {height:100%; padding:0 18px 0 48px !important; color:@INK; font-size:.92rem; background:transparent !important;
  background-image:url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='20' height='20' viewBox='0 0 24 24' fill='none' stroke='%237B5CE6' stroke-width='2.2' stroke-linecap='round' stroke-linejoin='round'><circle cx='11' cy='11' r='7'/><path d='M21 21l-4.3-4.3'/></svg>") !important;
  background-repeat:no-repeat !important; background-position:16px center !important;}
.st-key-searchbox input::placeholder {color:#98A2BC;}
.st-key-searchbox [data-testid="InputInstructions"] {display:none;}
.st-key-searchbox div[data-baseweb="base-input"] {border:none !important; box-shadow:none !important; background:transparent !important; height:100%;}
.st-key-searchbox [data-testid="stTextInput"] {margin:0;}
div[data-testid="stTextInput"] input {color:@INK;}

/* ---------- KPI tiles ---------- */
.kpi {display:flex; gap:14px; align-items:center; padding:16px 18px; border-radius:24px; border:1px solid #DCE3F7; background:rgba(255,255,255,.35); transition:.18s;}
.kpi .ico {width:54px; height:54px; border-radius:17px; background:#E3E8FC; display:flex; align-items:center; justify-content:center; font-size:1.35rem; flex:none;}
.kpi .kt {flex:1; min-width:0;} .kpi .kl {font-size:.74rem; color:@MUTED; white-space:nowrap;} .kpi .kv {font-size:1.1rem; font-weight:800; color:@INK;}
.kpi .go {width:26px; height:26px; border-radius:50%; background:#E6EAFB; color:@PURPLE; display:flex; align-items:center; justify-content:center; font-size:1rem; font-weight:700; flex:none;}
/* clickable cards: a transparent button covers the whole card */
[class*="st-key-card_"] {position:relative; margin-bottom:18px;}
[class*="st-key-card_"] [data-testid="stElementContainer"]:has(.stButton), [class*="st-key-card_"] .element-container:has(.stButton), [class*="st-key-card_"] .stButton {position:absolute; inset:0; width:100%; height:100%; margin:0;}
[class*="st-key-card_"] .stButton button {position:absolute; inset:0; width:100%; height:100%; opacity:0; cursor:pointer; border-radius:28px;}
[class*="st-key-card_"]:hover .kpi {border-color:@PURPLE; background:rgba(255,255,255,.7); box-shadow:0 8px 20px rgba(123,92,230,.14); transform:translateY(-2px);}
[class*="st-key-card_"]:hover .kpi .go {background:@PURPLE; color:#fff;}
[class*="st-key-card_"]:hover .bigcard {border-color:@PURPLE; box-shadow:0 10px 24px rgba(123,92,230,.18); transform:translateY(-2px);}
.bigcard {transition:.18s;}
[class*="st-key-card_txn_"] {margin-bottom:10px;}
[class*="st-key-card_txn_"] .stButton button {border-radius:18px;}
[class*="st-key-card_txn_"] .txn {margin-bottom:0; transition:.15s; border:1px solid transparent;}
[class*="st-key-card_txn_"]:hover .txn {border-color:@PURPLE; background:#fff; box-shadow:0 6px 16px rgba(123,92,230,.14);}

/* ---------- hero cards ---------- */
.bigcard {border-radius:28px; padding:22px 24px; height:300px; box-sizing:border-box; border:1px solid #DCE3F7; background:rgba(255,255,255,.35); color:@INK; position:relative;}
.bigcard.dark {background:@DEEP; color:#fff; border-color:@DEEP;}
.bigcard .top {display:flex; justify-content:space-between; align-items:center; margin-bottom:22px;}
.bigcard .sq {width:44px; height:44px; border-radius:14px; background:#E6EAFB; display:flex; align-items:center; justify-content:center; font-size:1.15rem;}
.bigcard.dark .sq {background:rgba(255,255,255,.12);}
.bigcard.dark .chev {background:rgba(255,255,255,.16); color:#fff;}
.bigcard .chev {width:28px; height:28px; border-radius:50%; background:rgba(123,92,230,.14); color:@PURPLE; display:flex; align-items:center; justify-content:center; font-size:.95rem;}
.bigcard .bt {font-size:1.12rem; font-weight:700;}
.bigcard .bs {font-size:.78rem; opacity:.65; margin-top:2px;}
.bigcard .row {display:flex; justify-content:space-between; align-items:flex-end; margin-top:16px;}
.bigcard .bv {font-size:2.15rem; font-weight:800; letter-spacing:-.02em;}
.bigcard .bn {font-size:.82rem; opacity:.85; padding-bottom:6px;}
.bigcard .bar {height:7px; border-radius:7px; background:rgba(120,130,160,.25); margin-top:12px; overflow:hidden;}
.bigcard .bar span {display:block; height:100%; border-radius:7px; background:@PURPLE;}
.bigcard .cap {font-size:.72rem; opacity:.65; margin-top:6px;}
.bigcard .big-avs {margin-top:20px;} .bigcard .big-avs .av {width:44px; height:44px; border-color:#EEF2FE;}

/* ---------- panels ---------- */
div[data-testid="stVerticalBlockBorderWrapper"] {border-radius:28px; border:1px solid #DCE3F7; background:rgba(255,255,255,.35);}
.ct {font-size:1.45rem; font-weight:700; color:@INK;}
.subtile {border-radius:20px; background:rgba(255,255,255,.55); padding:16px 20px;}
.subtile .sl {font-size:.78rem; color:@MUTED;} .subtile .sv {font-size:1.9rem; font-weight:800; color:@INK; letter-spacing:-.02em;} .subtile .sn {font-size:.8rem; color:@PURPLE; font-weight:600;}
.txn {display:flex; align-items:center; gap:14px; padding:12px 14px; border-radius:18px; background:rgba(255,255,255,.5); margin-bottom:10px;}
.txn .sq {width:42px; height:42px; border-radius:13px; background:#fff; display:flex; align-items:center; justify-content:center; flex:none; font-size:1.05rem;}
.txn .ta {font-weight:700; font-size:.98rem; color:@INK;} .txn .ts {font-size:.74rem; color:@MUTED;}
.txn .mid {flex:1; min-width:0;} .txn .ts {white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.pill {font-size:.72rem; padding:5px 12px; border-radius:999px; font-weight:600; white-space:nowrap;}
.pill.paid {background:#D9F2E6; color:#4F9A78;} .pill.pending {background:#F4F0C8; color:#A8962F;} .pill.lost {background:#FADDE6; color:#C0476F;}

/* pill-style radios (period / metric / filter) */
.st-key-period label[data-baseweb="radio"], .st-key-metric label[data-baseweb="radio"], .st-key-txnf label[data-baseweb="radio"] {padding:5px 16px; border-radius:999px; background:#F3F6FE; border:1px solid #DCE3F7; margin-right:2px;}
.st-key-period label[data-baseweb="radio"] > div:first-of-type, .st-key-metric label[data-baseweb="radio"] > div:first-of-type, .st-key-txnf label[data-baseweb="radio"] > div:first-of-type {display:none;}
.st-key-period label p, .st-key-metric label p, .st-key-txnf label p {font-size:.8rem; margin:0; color:#5B6685;}
.st-key-period label:has(input:checked), .st-key-metric label:has(input:checked), .st-key-txnf label:has(input:checked) {background:#2C3556; border-color:#2C3556;}
.st-key-period label:has(input:checked) p, .st-key-metric label:has(input:checked) p, .st-key-txnf label:has(input:checked) p {color:#fff;}
.st-key-period div[role="radiogroup"], .st-key-metric div[role="radiogroup"], .st-key-txnf div[role="radiogroup"] {justify-content:flex-end; gap:6px;}
.st-key-metric div[role="radiogroup"] {justify-content:flex-start;}

/* ---------- process pages ---------- */
div[data-testid="stPlotlyChart"] {background:rgba(255,255,255,.4); border:1px solid #DCE3F7; border-radius:24px; padding:8px 10px; overflow:hidden;}
.st-key-stats_card div[data-testid="stPlotlyChart"] {background:transparent; border:none; padding:0;}
div[data-testid="stMetric"] {background:rgba(255,255,255,.45); border:1px solid #DCE3F7; border-radius:22px; padding:14px 18px;}
div[data-testid="stMetricValue"] {color:@INK; font-weight:800;} div[data-testid="stMetricLabel"] p {color:@MUTED;}
.phase {font-size:.72rem; letter-spacing:.08em; text-transform:uppercase; color:@MUTED; margin:0 0 4px 2px; font-weight:700;}
.flow {display:flex; gap:14px; flex-wrap:wrap; margin:6px 0 10px;} .pg {flex:1 1 0; min-width:210px;}
.chips {display:flex; gap:6px; flex-wrap:wrap;}
.chip {display:flex; align-items:center; gap:7px; padding:7px 12px; border-radius:999px; font-size:.8rem; border:1px solid #DCE3F7; background:rgba(255,255,255,.55); color:@INK;}
.chip b {display:inline-flex; width:20px; height:20px; border-radius:50%; align-items:center; justify-content:center; font-size:.72rem; background:#E6EAFB; color:@PURPLE;}
.chip.done {background:#DDDCFB; border-color:#D0CEF6;}
.chip.active {background:@DEEP; color:#fff; border-color:@DEEP; font-weight:600;} .chip.active b {background:#fff; color:@DEEP;}
.card {border:1px solid #DCE3F7; border-radius:24px; padding:16px 20px; background:rgba(255,255,255,.4); margin-bottom:12px;}
.card.tint {background:rgba(255,255,255,.55);}
.q {color:@PURPLE; font-weight:700; font-size:1.15rem;}
.tag {display:inline-block; font-size:.72rem; padding:3px 11px; border-radius:999px; background:#E3E0FB; color:@PURPLE; margin-right:6px; font-weight:600;}
.tl {position:relative; margin-left:14px; padding-left:26px; border-left:3px solid #D4DBF3;} .ti {position:relative; margin-bottom:14px;}
.dot {position:absolute; left:-43px; top:6px; width:30px; height:30px; border-radius:50%; background:@PURPLE; color:#fff; font-weight:700; font-size:.82rem; display:flex; align-items:center; justify-content:center; border:3px solid #E9EFFD; box-shadow:0 0 0 2px #D4DBF3;}
.dot.none {background:#F3F6FE; color:@MUTED;} .dot.stop {background:@RED;}
.ti .box {border:1px solid #DCE3F7; border-radius:20px; padding:12px 16px; background:rgba(255,255,255,.55);}
.ti .box.none {background:rgba(255,255,255,.25); color:@MUTED;} .ti .box.stop {border-color:#F3C3D3; background:#FDF1F5;}
.ti h4 {margin:0 0 3px 0; font-size:.98rem; color:@INK;} .ti .ln {font-size:.86rem; color:@INK;} .ti .dt {float:right; font-size:.75rem; color:@MUTED;}
.callout {border-left:4px solid @PURPLE; background:rgba(255,255,255,.5); padding:10px 14px; border-radius:10px; font-size:.9rem; margin:8px 0;}
.crumbbtn {} div.stButton > button {border-radius:999px; border:1px solid #D5DDF3; background:#F3F6FE; color:@INK; font-weight:600;}
div.stButton > button:hover {border-color:@PURPLE; color:@PURPLE;}
div[data-baseweb="select"] > div {border-radius:999px; background:#F3F6FE; border-color:#DCE3F7;}
.dot.gap {background:#F3F6FE; color:@MUTED; border:3px solid #E9EFFD; box-shadow:0 0 0 2px #D4DBF3;}
.ti .box.gap {border-style:dashed; background:rgba(255,255,255,.25); color:@MUTED;}
.gapnote {display:inline-block; font-size:.7rem; padding:2px 9px; border-radius:999px; background:#F4F0C8; color:#8A7A1E; font-weight:600; margin-left:6px;}
.st-key-back button {border:none; background:transparent; color:@PURPLE; padding:0 4px; min-height:0; margin:2px 0 8px; font-weight:600;}
.st-key-back button:hover {background:transparent; text-decoration:underline;}
div[data-testid="stSegmentedControl"] button {border-radius:999px;}
/* stats deltas, insights, customer card */
.subtile .dl {font-size:.72rem; font-weight:700; padding:2px 8px; border-radius:999px; margin-left:4px; vertical-align:middle; white-space:nowrap;}
.subtile .dl.up {background:#D9F2E6; color:#3F8A68;} .subtile .dl.dn {background:#FADDE6; color:#C0476F;}
.subtile .sv {font-size:1.55rem;}
.cap2 {font-size:.74rem; color:@MUTED; margin:8px 0 4px 2px;}
.attn {display:flex; align-items:center; gap:12px; padding:11px 14px; border-radius:16px; background:rgba(255,255,255,.55); border:1px solid transparent; transition:.15s;}
.attn .sq {width:38px; height:38px; border-radius:12px; background:#fff; display:flex; align-items:center; justify-content:center; flex:none;}
.attn .al {flex:1; font-size:.9rem; font-weight:600; color:@INK;} .attn .ac {font-weight:800; font-size:1.05rem; color:@INK;}
.attn .go {width:24px; height:24px; border-radius:50%; background:#E6EAFB; color:@PURPLE; display:flex; align-items:center; justify-content:center; font-weight:700;}
[class*="st-key-card_attn_"] {margin-bottom:8px;} [class*="st-key-card_attn_"] .stButton button {border-radius:16px;}
[class*="st-key-card_attn_"]:hover .attn {border-color:@PURPLE; background:#fff;}
[class*="ins_"] div[data-testid="stPlotlyChart"] {background:transparent; border:none; padding:0;}
.pcard {border:1px solid #DCE3F7; border-radius:24px; background:rgba(255,255,255,.5); padding:18px 20px; height:210px; box-sizing:border-box; transition:.18s;}
.pcard.click {cursor:pointer;} [class*="st-key-card_cj_"] {margin-bottom:0;} [class*="st-key-card_cj_"] .stButton button {border-radius:24px;}
[class*="st-key-card_cj_"]:hover .pcard {border-color:@PURPLE; background:#fff; box-shadow:0 8px 20px rgba(123,92,230,.14);}
.pc-top {display:flex; gap:14px; align-items:center; margin-bottom:12px;} .pc-av {width:54px; height:54px; font-size:1.05rem; margin:0; border:none;}
.pc-name {font-size:1.25rem; font-weight:800; color:@INK; line-height:1.15;} .pc-sub {font-size:.78rem; color:@MUTED; margin-top:3px;}
.pc-loc {font-size:.9rem; color:@INK;} .pc-row {font-size:.84rem; color:@MUTED; margin-top:4px;} .pc-row b {color:@INK; margin-left:4px;}
.pc-tags {margin-top:10px; display:flex; gap:6px; flex-wrap:wrap;}
.pc-h {display:flex; justify-content:space-between; align-items:center; font-weight:700; color:@INK; font-size:.95rem; margin-bottom:8px;}
.pc-h i {font-style:normal; width:24px; height:24px; border-radius:50%; background:#E6EAFB; color:@PURPLE; display:flex; align-items:center; justify-content:center;}
.pc-big {font-size:1.05rem; font-weight:800; color:@INK; margin-bottom:6px; word-break:break-all;}
.pc-link {margin-top:10px; font-size:.78rem; font-weight:700; color:@PURPLE;}
.dgrid {display:grid; grid-template-columns:repeat(4, minmax(0,1fr)); gap:14px 20px; margin-top:6px;}
.dgrid .dk {font-size:.74rem; color:@MUTED; margin-bottom:2px;} .dgrid .dv {font-size:.95rem; font-weight:700; color:@INK;}
.srch-chip {font-size:.88rem; color:@INK; background:rgba(255,255,255,.6); border:1px solid #DCE3F7; border-radius:999px; padding:9px 16px; width:fit-content;}
.dgrid.two {grid-template-columns:repeat(2, minmax(0,1fr)); margin-top:10px;}
.gen-hero {text-align:center; padding:34px 20px 22px;}
.gen-orb {width:64px; height:64px; margin:0 auto 14px; border-radius:20px; background:linear-gradient(135deg,@PURPLE,#4F34C4); display:flex; align-items:center; justify-content:center; font-size:1.6rem; box-shadow:0 10px 24px rgba(123,92,230,.35);}
.gen-t {font-size:1.7rem; font-weight:800; color:@INK; letter-spacing:-.02em;} .gen-s {color:@MUTED; max-width:560px; margin:6px auto 0; font-size:.95rem;}
.gen-foot {text-align:center; color:#98A2BC; font-size:.76rem; margin-top:10px;}
.sugg {display:flex; align-items:center; gap:14px; padding:16px 18px; border-radius:20px; border:1px solid #DCE3F7; background:rgba(255,255,255,.55); transition:.15s;}
.sugg .sq {width:44px; height:44px; border-radius:14px; background:#fff; display:flex; align-items:center; justify-content:center; font-size:1.15rem; flex:none;}
.sugg .mid {flex:1; min-width:0;} .sugg .st1 {font-weight:700; color:@INK; font-size:.95rem;} .sugg .st2 {font-size:.8rem; color:@MUTED; margin-top:2px;}
.sugg .go {width:26px; height:26px; border-radius:50%; background:#E6EAFB; color:@PURPLE; display:flex; align-items:center; justify-content:center; font-weight:700; flex:none;}
[class*="st-key-card_sg_"] {margin-bottom:6px;} [class*="st-key-card_sg_"] .stButton button {border-radius:20px;}
[class*="st-key-card_sg_"]:hover .sugg {border-color:@PURPLE; background:#fff; box-shadow:0 8px 20px rgba(123,92,230,.14);}
.msg-row {display:flex; gap:10px; margin:14px 0 6px; align-items:flex-start;} .msg-row.me {justify-content:flex-end;}
.msg-av {width:34px; height:34px; border-radius:11px; background:linear-gradient(135deg,@PURPLE,#4F34C4); display:flex; align-items:center; justify-content:center; flex:none; font-size:.95rem;}
.msg {max-width:78%; padding:12px 16px; border-radius:18px; font-size:.93rem; line-height:1.45;}
.msg.me {background:@DEEP; color:#fff; border-bottom-right-radius:6px;} .msg.gn {background:#fff; color:@INK; border:1px solid #DCE3F7; border-top-left-radius:6px;}
div[data-testid="stChatInput"] {border-radius:999px; background:#fff; border:1px solid #D5DDF3; box-shadow:0 4px 14px rgba(31,42,74,.08);}
div[data-testid="stChatInput"] textarea {color:@INK;}
/* customer 360 */
.hero360 {display:flex; justify-content:space-between; gap:24px; align-items:center; flex-wrap:wrap; padding:24px 28px; border-radius:28px; background:@DEEP; color:#fff; margin:6px 0 16px; box-shadow:0 14px 30px rgba(31,42,74,.22);}
.hero360 .h-l {display:flex; gap:18px; align-items:center;} .hero360 .h-av {width:72px; height:72px; font-size:1.5rem; margin:0; border:3px solid rgba(255,255,255,.25); background:@PURPLE;}
.hero360 .h-name {font-size:1.7rem; font-weight:800; letter-spacing:-.02em; display:flex; align-items:center; gap:12px;}
.hero360 .stat {font-size:.72rem; font-weight:700; padding:4px 12px; border-radius:999px; background:rgba(255,255,255,.18);} .hero360 .stat.on {background:#2FBF8A; color:#fff;}
.hero360 .h-sub {font-size:.9rem; opacity:.82; margin-top:3px;} .hero360 .h-tags {margin-top:10px; display:flex; gap:6px; flex-wrap:wrap;} .hero360 .tag {background:rgba(255,255,255,.14); color:#fff;}
.hero360 .h-r {display:grid; grid-template-columns:repeat(4, minmax(104px,1fr)); gap:12px;}
.hero360 .hk {background:rgba(255,255,255,.1); border:1px solid rgba(255,255,255,.14); border-radius:18px; padding:14px 18px; text-align:left;}
.hero360 .hv {font-size:1.6rem; font-weight:800; letter-spacing:-.02em;} .hero360 .hl {font-size:.74rem; opacity:.75; margin-top:2px;}
.c360 {border:1px solid #DCE3F7; border-radius:20px; background:rgba(255,255,255,.5); padding:14px 16px; height:116px; box-sizing:border-box; transition:.15s;}
.c360.on {background:#fff; border-color:@PURPLE; box-shadow:0 8px 20px rgba(123,92,230,.18);}
.c360 .c-h {display:flex; align-items:center; gap:8px; font-size:.78rem; font-weight:700; color:@MUTED; text-transform:uppercase; letter-spacing:.06em;} .c360.on .c-h {color:@PURPLE;}
.c360 .c-ic {width:26px; height:26px; border-radius:8px; background:#E6EAFB; display:inline-flex; align-items:center; justify-content:center; font-size:.9rem; letter-spacing:0;}
.c360 .c-big {font-size:1.25rem; font-weight:800; color:@INK; margin-top:8px; white-space:nowrap;} .c360 .c-sub {font-size:.76rem; color:@MUTED; margin-top:1px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
[class*="st-key-card_c3_"] {margin-bottom:14px;} [class*="st-key-card_c3_"] .stButton button {border-radius:20px;}
[class*="st-key-card_c3_"]:hover .c360 {border-color:@PURPLE; background:#fff;}
.note360 {font-size:.78rem; color:@MUTED; margin-top:12px; padding:10px 14px; border-left:3px solid #D4DBF3; background:rgba(255,255,255,.4); border-radius:8px;}
.rk-wrap {display:grid; grid-template-columns:repeat(auto-fit,minmax(360px,1fr)); gap:12px; margin:10px 0;}
.rk {border:1px solid #DCE3F7; border-radius:18px; padding:14px 16px; background:rgba(255,255,255,.55);} .rk-h {display:flex; justify-content:space-between; gap:8px; color:@INK; margin-bottom:10px;} .rk-h span {color:@MUTED; font-size:.82rem;}
.rk-g {display:grid; grid-template-columns:1fr 1fr; gap:10px 16px;} .rk-g i {display:block; font-style:normal; font-size:.72rem; color:@MUTED;} .rk-g b {font-size:.9rem; color:@INK;}
.tl2 {position:relative; margin:4px 0 8px 18px; padding-left:30px; border-left:3px solid #D4DBF3;}
.ev {position:relative; margin-bottom:12px;} .ev-dot {position:absolute; left:-49px; top:6px; width:34px; height:34px; border-radius:50%; background:#fff; border:2px solid @PURPLE; display:flex; align-items:center; justify-content:center; font-size:.95rem;}
.ev.up .ev-dot {border-style:dashed; background:#F3F6FE;}
.ev-b {border:1px solid #DCE3F7; border-radius:16px; background:rgba(255,255,255,.55); padding:10px 16px;} .ev.up .ev-b {border-style:dashed; background:rgba(255,255,255,.3);}
.ev-d {font-size:.74rem; color:@PURPLE; font-weight:700;} .ev-t {font-weight:700; color:@INK; font-size:.95rem; margin-top:1px;} .ev-s {font-size:.82rem; color:@MUTED;}
/* customer directory cards */
.ccard {border:1px solid #DCE3F7; border-radius:22px; background:rgba(255,255,255,.55); padding:16px 18px; height:196px; box-sizing:border-box; transition:.16s;}
[class*="st-key-card_cc_"] {margin-bottom:6px;} [class*="st-key-card_cc_"] .stButton button {border-radius:22px;}
[class*="st-key-card_cc_"]:hover .ccard {border-color:@PURPLE; background:#fff; box-shadow:0 10px 24px rgba(123,92,230,.16); transform:translateY(-2px);}
.cc-top {display:flex; align-items:center; gap:12px;} .cc-av {width:46px; height:46px; font-size:.9rem; margin:0; border:none; flex:none;}
.cc-id {flex:1; min-width:0;} .cc-name {font-weight:800; color:@INK; font-size:1.02rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;} .cc-sub {font-size:.74rem; color:@MUTED; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.cc-st {font-size:.68rem; font-weight:700; padding:3px 10px; border-radius:999px; background:#EEF0F8; color:@MUTED;} .cc-st.on {background:#D9F2E6; color:#3F8A68;}
.cc-grid {display:grid; grid-template-columns:repeat(3,1fr); gap:8px; margin:14px 0 12px; padding:10px 12px; border-radius:14px; background:rgba(231,236,252,.6);}
.cc-grid i {display:block; font-style:normal; font-size:.68rem; color:@MUTED;} .cc-grid b {font-size:.98rem; color:@INK;}
.cc-tags {display:flex; gap:6px; flex-wrap:wrap;} .ctag {font-size:.7rem; font-weight:600; padding:3px 10px; border-radius:999px; background:#E3E0FB; color:@PURPLE;}
.ctag.warn {background:#F4F0C8; color:#8A7A1E;} .ctag.bad {background:#FADDE6; color:#C0476F;} .ctag.ok {background:#D9F2E6; color:#3F8A68;}
.chat {border:1px solid #DCE3F7; border-radius:20px; background:rgba(255,255,255,.55); padding:12px 16px; margin-bottom:10px;}
.chat.me {background:#2C3556; color:#fff; border-color:#2C3556;}
</style>
"""
