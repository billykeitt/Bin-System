import streamlit as st
import pandas as pd
import uuid
from datetime import datetime, date, timedelta
from supabase.client import create_client
import plotly.express as px
import plotly.graph_objects as go
import os
from dotenv import load_dotenv
from postgrest import APIError

# -----------------------------
# SUPABASE CONNECTION
# -----------------------------

load_dotenv()
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(
    layout="wide",
    page_title="Keitt Bin Ledger",
    page_icon="🌿",
    initial_sidebar_state="expanded"
)

# ================================================================
# GLOBAL CSS
# ================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Hide default Streamlit chrome ── */
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }

/* ── Main content padding ── */
section.main > div.block-container {
    padding-top: 2rem !important;
    padding-left: 2.5rem !important;
    padding-right: 2.5rem !important;
    max-width: 1440px;
}

/* ══════════════════════════════════════
   SIDEBAR
══════════════════════════════════════ */
[data-testid="stSidebar"],
[data-testid="stSidebar"] > div,
[data-testid="stSidebar"] > div > div {
    background: #0F2417 !important;
}
[data-testid="stSidebar"] {
    min-width: 230px !important;
    max-width: 230px !important;
}
[data-testid="stSidebar"] > div:first-child {
    padding: 0 !important;
}

/* ── Sidebar brand header ── */
.sb-brand {
    display: flex; align-items: center; gap: 11px;
    padding: 22px 20px 18px 20px;
    border-bottom: 1px solid rgba(255,255,255,0.08);
    margin-bottom: 8px;
}
.sb-brand-icon {
    width: 36px; height: 36px; border-radius: 9px;
    background: #2E7D32;
    display: flex; align-items: center; justify-content: center;
    font-size: 18px; flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(0,0,0,0.35);
}
.sb-brand-text { line-height: 1.2; }
.sb-brand-title {
    font-size: 14px; font-weight: 700;
    color: #FFFFFF; letter-spacing: -0.1px;
}
.sb-brand-sub {
    font-size: 10px; color: rgba(255,255,255,0.4);
    text-transform: uppercase; letter-spacing: 0.5px;
}

/* ── Nav section label ── */
.sb-section-label {
    font-size: 9.5px; font-weight: 600;
    text-transform: uppercase; letter-spacing: 1px;
    color: rgba(255,255,255,0.3);
    padding: 14px 20px 6px 20px;
}

/* ── Nav items (radio overrides) ── */
[data-testid="stSidebar"] .stRadio > label { display: none !important; }
[data-testid="stSidebar"] .stRadio > div {
    gap: 1px !important;
    padding: 0 10px !important;
}
[data-testid="stSidebar"] .stRadio div[role="radiogroup"] { gap: 1px !important; }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] {
    background: transparent !important;
    border-radius: 8px !important;
    padding: 8px 12px !important;
    cursor: pointer !important;
    transition: background 0.15s !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:hover {
    background: rgba(255,255,255,0.07) !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] > div:first-child {
    display: none !important;
}
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] span {
    font-size: 13.5px !important;
    font-weight: 500 !important;
    color: rgba(255,255,255,0.65) !important;
}
[data-testid="stSidebar"] .stRadio label[aria-checked="true"][data-baseweb="radio"] {
    background: rgba(46,125,50,0.35) !important;
}
[data-testid="stSidebar"] .stRadio label[aria-checked="true"][data-baseweb="radio"] span {
    color: #81C784 !important;
    font-weight: 600 !important;
}

/* ── Sidebar divider ── */
.sb-divider {
    border: none; border-top: 1px solid rgba(255,255,255,0.08);
    margin: 10px 20px;
}

/* ── User card at bottom ── */
.sb-user-card {
    margin: 8px 10px;
    padding: 12px 14px;
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
}
.sb-user-name {
    font-size: 12px; font-weight: 600; color: #fff;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    max-width: 170px;
}
.sb-user-email {
    font-size: 10.5px; color: rgba(255,255,255,0.4);
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    max-width: 170px; margin-top: 1px;
}
.sb-role-badge {
    display: inline-block; margin-top: 7px;
    font-size: 9.5px; font-weight: 700; text-transform: uppercase;
    letter-spacing: 0.6px; padding: 2px 8px; border-radius: 20px;
}
.sb-role-admin    { background: rgba(239,108,0,0.25);  color: #FFB74D; }
.sb-role-operator { background: rgba(46,125,50,0.35);  color: #81C784; }
.sb-role-viewer   { background: rgba(33,150,243,0.25); color: #64B5F6; }

/* ── Sidebar logout button ── */
[data-testid="stSidebar"] .stButton > button {
    background: rgba(255,255,255,0.06) !important;
    color: rgba(255,255,255,0.5) !important;
    border: 1px solid rgba(255,255,255,0.1) !important;
    border-radius: 8px !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    padding: 5px 14px !important;
    width: 100%;
}
[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(255,80,80,0.18) !important;
    color: #FF8A80 !important;
    border-color: rgba(255,80,80,0.3) !important;
}

/* ══════════════════════════════════════
   PAGE HEADER (per-page, not fixed)
══════════════════════════════════════ */
.page-header {
    display: flex; align-items: center; gap: 14px;
    padding: 0 0 20px 0;
    border-bottom: 1px solid rgba(128,128,128,0.15);
    margin-bottom: 28px;
}
.page-header-icon {
    width: 40px; height: 40px; border-radius: 10px;
    background: rgba(46,125,50,0.12);
    display: flex; align-items: center; justify-content: center;
    font-size: 20px; flex-shrink: 0;
}
.page-header-title {
    font-size: 20px; font-weight: 700;
    color: inherit; letter-spacing: -0.3px; line-height: 1.1;
}
.page-header-sub {
    font-size: 12px; color: #888; margin-top: 2px;
}

/* ══════════════════════════════════════
   METRIC CARDS
══════════════════════════════════════ */
.metric-card {
    background: rgba(128,128,128,0.06);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 12px; padding: 18px 16px; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-label {
    font-size: 10.5px; color: #888;
    text-transform: uppercase; letter-spacing: 0.7px; margin-bottom: 6px;
}
.metric-value {
    font-size: 24px; font-weight: 700; color: #2E7D32; line-height: 1.1;
}
.metric-sub { font-size: 11px; color: #888; margin-top: 5px; }

/* ══════════════════════════════════════
   SECTION HEADER
══════════════════════════════════════ */
.section-header {
    font-size: 12px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.8px;
    border-bottom: 2px solid rgba(46,125,50,0.2);
    padding-bottom: 8px; margin: 32px 0 16px 0;
    color: #2E7D32;
}

/* ══════════════════════════════════════
   BUTTONS (main content area)
══════════════════════════════════════ */
section.main .stButton > button {
    background-color: #1B5E20 !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; padding: 8px 22px !important;
    font-size: 13px !important;
}
section.main .stButton > button:hover {
    background-color: #2E7D32 !important;
}

/* ══════════════════════════════════════
   LOGIN PAGE
══════════════════════════════════════ */
.login-card {
    background: rgba(128,128,128,0.05);
    border: 1px solid rgba(128,128,128,0.15);
    border-radius: 16px;
    padding: 40px 36px 32px 36px;
    margin-top: 20px;
}
.login-logo {
    width: 52px; height: 52px; border-radius: 14px;
    background: #1B5E20;
    display: flex; align-items: center; justify-content: center;
    font-size: 26px; margin: 0 auto 16px auto;
}
.login-title {
    font-size: 22px; font-weight: 700;
    text-align: center; letter-spacing: -0.3px; margin-bottom: 4px;
}
.login-sub {
    font-size: 13px; color: #888;
    text-align: center; margin-bottom: 28px;
}
.access-denied {
    background: rgba(211,47,47,0.08);
    border: 1px solid rgba(211,47,47,0.25);
    border-radius: 10px; padding: 16px 20px;
    color: #EF9A9A; font-size: 13px; text-align: center;
    margin-top: 16px;
}
</style>
""", unsafe_allow_html=True)

# ================================================================
# SESSION STATE
# ================================================================

for key in ("user", "access_token", "refresh_token", "role"):
    if key not in st.session_state:
        st.session_state[key] = None

if st.session_state["user"] is None and st.session_state["access_token"]:
    try:
        restored = supabase.auth.set_session(
            st.session_state["access_token"],
            st.session_state["refresh_token"]
        )
        if restored.user:
            st.session_state["user"] = restored.user
            meta = restored.user.user_metadata or {}
            st.session_state["role"] = meta.get("role", "viewer")
    except Exception:
        st.session_state["access_token"]  = None
        st.session_state["refresh_token"] = None

# ================================================================
# ROLE HELPERS
# ================================================================

ROLE_LABELS = {"admin": "Admin", "operator": "Operator", "viewer": "Viewer"}

def get_role() -> str:
    return st.session_state.get("role") or "viewer"

def can_write() -> bool:
    """Operators and admins can insert/modify data."""
    return get_role() in ("admin", "operator")

def require_write():
    """Call at top of any write page. Stops rendering if viewer."""
    if not can_write():
        st.markdown("""
        <div class='access-denied'>
            🔒 <b>Access Denied</b><br>
            Your account has read-only (Viewer) access.<br>
            Contact your admin to request Operator access.
        </div>""", unsafe_allow_html=True)
        st.stop()

# ================================================================
# LOGIN SCREEN
# ================================================================

def login_screen():
    st.markdown("<br>", unsafe_allow_html=True)
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("""
        <div class='login-card'>
            <div class='login-logo'>🌿</div>
            <div class='login-title'>Keitt Bin Ledger</div>
            <div class='login-sub'>Sign in to your account</div>
        </div>""", unsafe_allow_html=True)

        # Render inputs outside the HTML card (Streamlit can't render widgets inside HTML)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        email    = st.text_input("Email",    placeholder="you@example.com",  label_visibility="collapsed")
        password = st.text_input("Password", placeholder="Password", type="password", label_visibility="collapsed")
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

        if st.button("Sign In", use_container_width=True):
            try:
                result = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if result.user:
                    meta = result.user.user_metadata or {}
                    st.session_state["user"]          = result.user
                    st.session_state["access_token"]  = result.session.access_token
                    st.session_state["refresh_token"] = result.session.refresh_token
                    st.session_state["role"]          = meta.get("role", "viewer")
                    st.rerun()
            except Exception:
                st.error("Invalid email or password. Please try again.")

        st.markdown(
            "<div style='text-align:center;margin-top:16px;font-size:11px;color:#888'>"
            "Contact your admin if you need access</div>",
            unsafe_allow_html=True
        )

if st.session_state["user"] is None:
    login_screen()
    st.stop()

# ================================================================
# SIDEBAR
# ================================================================

role      = get_role()
user_email = st.session_state["user"].email
# Derive a display name from the email (part before @)
display_name = user_email.split("@")[0].replace(".", " ").replace("_", " ").title()

# Brand header
st.sidebar.markdown(f"""
<div class='sb-brand'>
    <div class='sb-brand-icon'>🌿</div>
    <div class='sb-brand-text'>
        <div class='sb-brand-title'>Keitt Bin Ledger</div>
        <div class='sb-brand-sub'>Warehouse System</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Nav — operators/admins see write pages; viewers only see read pages
st.sidebar.markdown("<div class='sb-section-label'>Navigation</div>", unsafe_allow_html=True)

if can_write():
    all_pages = [
        "📊  Dashboard",
        "📥  Receive",
        "🏭  Produce",
        "⚖️  Adjust",
        "📈  Reports",
        "🔍  Bin Lookup",
        "📋  PCN Lookup",
<<<<<<< HEAD
        "🔧  Reconcile",
=======
>>>>>>> 1ba0970d8e791d50b58939957115b7935f08a72b
    ]
else:
    all_pages = [
        "📊  Dashboard",
        "📈  Reports",
        "🔍  Bin Lookup",
        "📋  PCN Lookup",
    ]

page_selected = st.sidebar.radio("nav", all_pages, label_visibility="collapsed")
# Strip icon prefix to get clean menu key
menu = page_selected.split("  ", 1)[-1].strip()
# Remap display names back to original keys used in page routing
_menu_map = {
<<<<<<< HEAD
    "Dashboard":  "Dashboard",
    "Receive":    "Receive",
    "Produce":    "Produce",
    "Adjust":     "Adjust",
    "Reports":    "Reports",
    "Bin Lookup": "Bin History Lookup",
    "PCN Lookup": "PCN Lookup",
    "Reconcile":  "Reconcile",
=======
    "Dashboard": "Dashboard",
    "Receive":   "Receive",
    "Produce":   "Produce",
    "Adjust":    "Adjust",
    "Reports":   "Reports",
    "Bin Lookup": "Bin History Lookup",
    "PCN Lookup": "PCN Lookup",
>>>>>>> 1ba0970d8e791d50b58939957115b7935f08a72b
}
menu = _menu_map.get(menu, menu)

# User card + logout
st.sidebar.markdown("<hr class='sb-divider'>", unsafe_allow_html=True)
role_css = f"sb-role-{role}"
st.sidebar.markdown(f"""
<div class='sb-user-card'>
    <div class='sb-user-name'>{display_name}</div>
    <div class='sb-user-email'>{user_email}</div>
    <span class='sb-role-badge {role_css}'>{ROLE_LABELS.get(role, role)}</span>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
if st.sidebar.button("Sign Out"):
    supabase.auth.sign_out()
    for k in ("user", "access_token", "refresh_token", "role"):
        st.session_state[k] = None
    st.rerun()

# ================================================================
# PAGE HEADER HELPER
# ================================================================

def page_header(icon: str, title: str, subtitle: str = ""):
    sub_html = f"<div class='page-header-sub'>{subtitle}</div>" if subtitle else ""
    st.markdown(f"""
    <div class='page-header'>
        <div class='page-header-icon'>{icon}</div>
        <div>
            <div class='page-header-title'>{title}</div>
            {sub_html}
        </div>
    </div>""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# UTILS
# ---------------------------------------------------------------

def clean(val):
    if val is None: return None
    if isinstance(val, float) and pd.isna(val): return None
    if isinstance(val, str) and val.strip() == "": return None
    return val

def parse_date(d):
    try: return pd.to_datetime(d).date().isoformat()
    except: return None

def get_bin_states(bins: list) -> dict:
    res = supabase.rpc("get_bin_states", {"bins": bins}).execute()
    return {r["bin_code"]: r for r in res.data}

def fetch_all(table: str) -> pd.DataFrame:
    """Fetch all rows from a view/table, bypassing the 1000-row API limit."""
    res = supabase.table(table).select("*").range(0, 50000).execute()
    return pd.DataFrame(res.data)

def bulk_insert(rows: list, label: str) -> list:
    failed = []
    for i in range(0, len(rows), 200):
        batch = rows[i:i + 200]
        try:
            supabase.table("bin_transactions").insert(batch).execute()
        except APIError as e:
            if e.code == "23505":
                failed.extend(r.get("bin_code") for r in batch)
            else:
                for row in batch:
                    try:
                        supabase.table("bin_transactions").insert([row]).execute()
                    except APIError:
                        failed.append(row.get("bin_code"))
    return failed

def show_errors(errors: list, failed_bins: list):
    if errors or failed_bins:
        st.warning("⚠️ Issues encountered")
        err_df = pd.DataFrame(errors, columns=["bin_code", "reason"])
        if failed_bins:
            err_df = pd.concat([
                err_df,
                pd.DataFrame({"bin_code": failed_bins, "reason": "DB rejected (duplicate or state violation)"})
            ], ignore_index=True)
        st.dataframe(err_df, use_container_width=True)

def std_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [c.strip().replace(" ", "_").replace("/", "_") for c in df.columns]
    # Convert BIN to string cleanly — if Excel stores bins as numbers (e.g. 1234),
    # astype(str) produces "1234.0". We strip the .0 to match DB values.
    def clean_bin(val):
        if pd.isna(val): return ""
        s = str(val).strip()
        if s.endswith(".0"):
            s = s[:-2]
        return s
    df["BIN"] = df["BIN"].apply(clean_bin)
    return df

def metric_card(label, value, sub=None):
    sub_html = f"<div class='metric-sub'>{sub}</div>" if sub else ""
    st.markdown(f"""
    <div class='metric-card'>
        <div class='metric-label'>{label}</div>
        <div class='metric-value'>{value}</div>
        {sub_html}
    </div>""", unsafe_allow_html=True)

def fmt_num(n, decimals=0):
    try:
        if n is None or pd.isna(n): return "—"
        return f"{n:,.{decimals}f}"
    except:
        return "—"

# ================================================================
# FUZZY MATCH UTILITIES
# ================================================================

def edit_distance(a: str, b: str) -> int:
    """Levenshtein edit distance between two strings."""
    a, b = str(a), str(b)
    if a == b: return 0
    if not a: return len(b)
    if not b: return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(
                prev[j + 1] + 1,   # delete
                curr[j]    + 1,    # insert
                prev[j] + (0 if ca == cb else 1)  # replace
            ))
        prev = curr
    return prev[len(b)]

def similarity_pct(a: str, b: str) -> float:
    """Similarity as a percentage (100 = identical)."""
    dist = edit_distance(str(a), str(b))
    max_len = max(len(str(a)), len(str(b)), 1)
    return round((1 - dist / max_len) * 100, 1)

def fuzzy_candidates(
    bin_code: str,
    stock_bins: list,       # list of dicts with bin_code + metadata
    top_n: int = 3,
    min_similarity: float = 60.0
) -> list:
    """
    For a given bin_code that failed validation, find the closest
    matches among bins currently in RECEIVED state.
    Returns up to top_n candidates sorted by similarity descending.
    """
    scored = []
    for s in stock_bins:
        sim = similarity_pct(bin_code, s["bin_code"])
        if sim >= min_similarity:
            scored.append({**s, "similarity": sim})
    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_n]

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=48, b=16, l=16, r=16)
)
PLOTLY_LIGHT = PLOTLY_BASE
LEGEND_DEFAULT = dict(bordercolor="rgba(128,128,128,0.2)", borderwidth=1)
LEGEND_HORIZ   = dict(bordercolor="rgba(128,128,128,0.2)", borderwidth=1, orientation="h", y=1.12)
GREEN_SEQ = ["#1B5E20","#2E7D32","#388E3C","#43A047","#66BB6A","#A5D6A7","#C8E6C9"]

# ================================================================
# DASHBOARD
# ================================================================

if menu == "Dashboard":
    page_header("📊", "Dashboard", "Live stock summary and operational overview")

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filters**")
    supplier_filter = st.sidebar.text_input("Supplier")
    variety_filter  = st.sidebar.text_input("Variety")

    # ── 1. KPIs via RPC — not subject to row limit ─────────────
    st.markdown("<div class='section-header'>Current Stock Balance</div>", unsafe_allow_html=True)

    try:
        summary      = supabase.rpc("get_stock_summary").execute().data[0]
        total_bins   = summary["total_bins"]   or 0
        total_weight = summary["total_weight"] or 0
        total_value  = summary["total_value"]  or 0
        avg_rate     = summary["avg_rate"]     or 0
        eligible_bins   = summary["eligible_bins"]   or 0
        eligible_weight = summary["eligible_weight"] or 0
    except Exception as e:
        st.error(f"Could not load stock summary: {e}")
        total_bins = total_weight = total_value = avg_rate = eligible_bins = eligible_weight = 0

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: metric_card("Bins In Stock",       fmt_num(total_bins))
    with c2: metric_card("Total Weight (kg)",   fmt_num(total_weight, 2))
    with c3: metric_card("Total Value (KES)",   fmt_num(total_value, 2))
    with c4: metric_card("Avg Rate / kg",       fmt_num(avg_rate, 2), "Weighted avg")
    with c5: metric_card("Eligible to Produce", fmt_num(eligible_bins), "14+ days in stock")
    with c6: metric_card("Eligible Wt (kg)",    fmt_num(eligible_weight, 2))

    # ── 2. Row-level data for charts — full fetch ──────────────
    st.markdown("<div class='section-header'>Stock Breakdown</div>", unsafe_allow_html=True)

    stock_df = fetch_all("v_current_stock")

    if not stock_df.empty:
        stock_df["received_date"]           = pd.to_datetime(stock_df["received_date"])
        stock_df["weight"]                  = pd.to_numeric(stock_df["weight"],  errors="coerce")
        stock_df["amount"]                  = pd.to_numeric(stock_df["amount"],  errors="coerce")
        stock_df["rate"]                    = pd.to_numeric(stock_df["rate"],    errors="coerce")
        stock_df["eligible_for_production"] = stock_df["eligible_for_production"].astype(bool)

    filt = stock_df.copy() if not stock_df.empty else pd.DataFrame()
    if supplier_filter and not filt.empty:
        filt = filt[filt["supplier"].str.contains(supplier_filter, case=False, na=False)]
    if variety_filter and not filt.empty:
        filt = filt[filt["variety"].str.contains(variety_filter, case=False, na=False)]

    if not filt.empty:
        left, right = st.columns(2)

        with left:
            by_variety = filt.groupby("variety")["weight"].sum().reset_index()
            fig_var = px.pie(
                by_variety, names="variety", values="weight",
                title="Weight by Variety", hole=0.45,
                color_discrete_sequence=GREEN_SEQ
            )
            fig_var.update_traces(textposition="inside", textinfo="percent+label")
            fig_var.update_layout(**PLOTLY_LIGHT, legend=LEGEND_DEFAULT, title_font_size=13)
            st.plotly_chart(fig_var, use_container_width=True)

        with right:
            st.markdown("**Top 10 Suppliers by Weight**")
            by_supplier = (
                filt.groupby("supplier")
                .agg(bins=("bin_code","count"), total_weight=("weight","sum"),
                     total_value=("amount","sum"), avg_rate=("rate","mean"))
                .reset_index()
                .sort_values("total_weight", ascending=False)
                .head(10)
            )
            by_supplier["total_weight"] = by_supplier["total_weight"].round(2)
            by_supplier["total_value"]  = by_supplier["total_value"].round(2)
            by_supplier["avg_rate"]     = by_supplier["avg_rate"].round(2)
            by_supplier.columns = ["Supplier","Bins","Weight (kg)","Value (KES)","Avg Rate"]
            st.dataframe(by_supplier, use_container_width=True, hide_index=True, height=340)
    else:
        st.info("No current stock data.")

    # ── 3. PCN Utilisation ────────────────────────────────────
    st.markdown("<div class='section-header'>PCN Utilisation</div>", unsafe_allow_html=True)

    util_df = fetch_all("v_pcn_utilisation")

    if not util_df.empty:
        for col in ["total_bins_received","total_bins_produced","total_weight_received",
                    "total_value_received","total_weight_produced",
                    "balance_bins","balance_weight","balance_value"]:
            if col in util_df.columns:
                util_df[col] = pd.to_numeric(util_df[col], errors="coerce")

        if supplier_filter:
            util_df = util_df[util_df["supplier"].str.contains(supplier_filter, case=False, na=False)]
        if variety_filter:
            util_df = util_df[util_df["variety"].str.contains(variety_filter, case=False, na=False)]

        util_df["utilisation_pct"] = (
            util_df["total_bins_produced"]
            / util_df["total_bins_received"].replace(0, pd.NA) * 100
        ).round(1)

        overall_pct = round(
            util_df["total_bins_produced"].sum()
            / max(util_df["total_bins_received"].sum(), 1) * 100, 1
        )

        u1, u2, u3, u4 = st.columns(4)
        with u1: metric_card("Active PCNs",          fmt_num(len(util_df)))
        with u2: metric_card("Total Bins Received",  fmt_num(util_df["total_bins_received"].sum()))
        with u3: metric_card("Total Bins Produced",  fmt_num(util_df["total_bins_produced"].sum()))
        with u4: metric_card("Overall Utilisation",  f"{overall_pct}%", "Produced / received")

        st.markdown("<br>", unsafe_allow_html=True)
        chart_col, table_col = st.columns([1.5, 1])

        with chart_col:
            chart_df = util_df.sort_values("total_bins_received", ascending=False).head(20)
            fig_util = go.Figure()
            fig_util.add_trace(go.Bar(
                x=chart_df["pcn"], y=chart_df["total_bins_received"],
                name="Received", marker_color="#C8E6C9"
            ))
            fig_util.add_trace(go.Bar(
                x=chart_df["pcn"], y=chart_df["total_bins_produced"],
                name="Produced", marker_color="#1B5E20"
            ))
            fig_util.update_layout(
                **PLOTLY_LIGHT, legend=LEGEND_HORIZ,
                title="Bins Received vs Produced per PCN",
                barmode="overlay", xaxis_title="PCN", yaxis_title="Bins",
                title_font_size=13,
            )
            st.plotly_chart(fig_util, use_container_width=True)

        with table_col:
            disp_cols = {
                "pcn":                 "PCN",
                "supplier":            "Supplier",
                "variety":             "Variety",
                "total_bins_received": "Rcvd",
                "total_bins_produced": "Prod",
                "balance_bins":        "Balance",
                "utilisation_pct":     "Util %",
                "earliest_receive":    "First Rcv",
                "latest_receive":      "Latest Rcv",
            }
            disp = util_df[[c for c in disp_cols if c in util_df.columns]].rename(columns=disp_cols)
            st.dataframe(disp, use_container_width=True, hide_index=True, height=380)
    else:
        st.info("No PCN data available.")

    # ── 4. Aging Report ───────────────────────────────────────
    st.markdown("<div class='section-header'>Aging Report</div>", unsafe_allow_html=True)

    aging_df = fetch_all("v_aging_report")

    if not aging_df.empty:
        aging_df["days_held"] = pd.to_numeric(aging_df["days_held"], errors="coerce")
        aging_df["weight"]    = pd.to_numeric(aging_df["weight"],    errors="coerce")

        if supplier_filter:
            aging_df = aging_df[aging_df["supplier"].str.contains(supplier_filter, case=False, na=False)]
        if variety_filter:
            aging_df = aging_df[aging_df["variety"].str.contains(variety_filter, case=False, na=False)]

        age_filter = st.selectbox(
            "Show bins",
            ["All in stock","Aging (< 14 days)","Ready (14+ days)","Produced"],
            key="age_filter"
        )
        age_map  = {"Aging (< 14 days)": "Aging", "Ready (14+ days)": "Ready", "Produced": "Produced"}
        age_disp = aging_df[aging_df["status"] != "Produced"].copy() if age_filter == "All in stock" \
                   else aging_df[aging_df["status"] == age_map[age_filter]].copy()

        a_left, a_right = st.columns(2)
        with a_left:
            in_stock = aging_df[aging_df["status"] != "Produced"]
            fig_age  = px.histogram(
                in_stock, x="days_held", nbins=30, color="status",
                title="Days in Stock Distribution",
                color_discrete_map={"Aging": "#FFA726", "Ready": "#1B5E20"},
                labels={"days_held": "Days Held"}
            )
            fig_age.add_vline(x=14, line_dash="dash", line_color="#E53935",
                              annotation_text="14-day mark", annotation_font_color="#E53935",
                              annotation_position="top right")
            fig_age.update_layout(**PLOTLY_LIGHT, legend=LEGEND_DEFAULT, title_font_size=13)
            st.plotly_chart(fig_age, use_container_width=True)

        with a_right:
            bins_aging = len(aging_df[aging_df["status"] == "Aging"])
            bins_ready = len(aging_df[aging_df["status"] == "Ready"])
            bins_prod  = len(aging_df[aging_df["status"] == "Produced"])
            avg_days   = aging_df[aging_df["status"] != "Produced"]["days_held"].mean()
            aa1, aa2   = st.columns(2)
            with aa1:
                metric_card("Aging (< 14d)", fmt_num(bins_aging), "Not ready")
                st.markdown("<br>", unsafe_allow_html=True)
                metric_card("Produced",      fmt_num(bins_prod),  "Completed")
            with aa2:
                metric_card("Ready (14d+)",  fmt_num(bins_ready), "Can produce")
                st.markdown("<br>", unsafe_allow_html=True)
                metric_card("Avg Days Held", fmt_num(avg_days, 1), "In-stock bins")

        age_show = age_disp[[c for c in [
            "bin_code","pcn","supplier","variety","weight",
            "received_date","produced_date","days_held","status","batch_no"
        ] if c in age_disp.columns]]
        st.dataframe(age_show, use_container_width=True, hide_index=True, height=300)
    else:
        st.info("No aging data available.")

    # ── 5. Daily Ledger ───────────────────────────────────────
    st.markdown("<div class='section-header'>Daily Ledger</div>", unsafe_allow_html=True)

    ledger_df = fetch_all("v_daily_ledger")

    if not ledger_df.empty:
        ledger_df["date"] = pd.to_datetime(ledger_df["date"])
        for col in ["bins_received","weight_received","value_received",
                    "bins_produced","weight_produced","bins_adjusted",
                    "running_balance_bins","running_balance_weight"]:
            ledger_df[col] = pd.to_numeric(ledger_df[col], errors="coerce")

        d1, d2    = st.columns(2)
        min_date  = ledger_df["date"].min().date()
        max_date  = ledger_df["date"].max().date()
        date_from = d1.date_input("From", value=min_date, min_value=min_date, max_value=max_date)
        date_to   = d2.date_input("To",   value=max_date, min_value=min_date, max_value=max_date)

        mask = (ledger_df["date"].dt.date >= date_from) & (ledger_df["date"].dt.date <= date_to)
        ld   = ledger_df[mask].sort_values("date")

        fig_ledger = go.Figure()
        fig_ledger.add_trace(go.Bar(
            x=ld["date"], y=ld["bins_received"],
            name="Received", marker_color="#A5D6A7", opacity=0.9
        ))
        fig_ledger.add_trace(go.Bar(
            x=ld["date"], y=-ld["bins_produced"],
            name="Produced", marker_color="#EF9A9A", opacity=0.9
        ))
        fig_ledger.add_trace(go.Scatter(
            x=ld["date"], y=ld["running_balance_bins"],
            name="Running Balance", mode="lines+markers",
            line=dict(color="#1B5E20", width=2), marker=dict(size=4)
        ))
        fig_ledger.update_layout(
            **PLOTLY_LIGHT, legend=LEGEND_HORIZ,
            title="Daily Ledger: Received vs Produced + Running Balance",
            barmode="relative", xaxis_title="Date", yaxis_title="Bins",
            title_font_size=13,
        )
        st.plotly_chart(fig_ledger, use_container_width=True)

        fig_wt = go.Figure()
        fig_wt.add_trace(go.Scatter(
            x=ld["date"], y=ld["running_balance_weight"],
            fill="tozeroy", name="Balance Weight",
            line=dict(color="#1B5E20", width=2),
            fillcolor="rgba(27,94,32,0.08)"
        ))
        fig_wt.update_layout(
            **PLOTLY_LIGHT, legend=LEGEND_DEFAULT,
            title="Running Weight Balance (kg)",
            xaxis_title="Date", yaxis_title="kg", title_font_size=13
        )
        st.plotly_chart(fig_wt, use_container_width=True)

        ld_disp = ld[["date","bins_received","weight_received","value_received",
                       "bins_produced","weight_produced","bins_adjusted",
                       "running_balance_bins","running_balance_weight"]].copy()
        ld_disp.columns = ["Date","Rcvd Bins","Rcvd Wt","Rcvd Val",
                           "Prod Bins","Prod Wt","Adj Out","Balance Bins","Balance Wt"]
        ld_disp["Date"] = ld_disp["Date"].dt.date
        st.dataframe(ld_disp.sort_values("Date", ascending=False),
                     use_container_width=True, hide_index=True, height=300)
    else:
        st.info("No ledger data available.")

    # ── 6. Historical Snapshot ────────────────────────────────
    st.markdown("<div class='section-header'>Historical Stock Snapshot</div>", unsafe_allow_html=True)

    snap_date = st.date_input("View stock as of date", value=date.today())
    if st.button("Load Snapshot"):
        snap_res = supabase.rpc("get_stock_as_of", {"p_date": snap_date.isoformat()}).execute()
        snap_df  = pd.DataFrame(snap_res.data)
        if snap_df.empty:
            st.info(f"No stock on record as of {snap_date}.")
        else:
            snap_df["weight"] = pd.to_numeric(snap_df["weight"], errors="coerce")
            snap_df["amount"] = pd.to_numeric(snap_df["amount"], errors="coerce")
            s1, s2, s3 = st.columns(3)
            with s1: metric_card("Bins in Stock", fmt_num(len(snap_df)),             str(snap_date))
            with s2: metric_card("Weight (kg)",   fmt_num(snap_df["weight"].sum(), 2))
            with s3: metric_card("Value (KES)",   fmt_num(snap_df["amount"].sum(), 2))
            st.dataframe(snap_df, use_container_width=True, hide_index=True, height=350)


# ================================================================
# RECEIVE
# ================================================================

if menu == "Receive":
    page_header("📥", "Receive Bins", "Upload and register incoming bin deliveries")
    require_write()
<<<<<<< HEAD

    # ── Import mode toggle ────────────────────────────────────
    import_mode = st.radio(
        "Import mode",
        ["Normal — daily receives", "Opening Stock — historical bulk import"],
        horizontal=True,
        help=(
            "Opening Stock mode handles bins that appear more than once "
            "in the file (same bin, different delivery dates). "
            "It keeps the latest row per bin and closes prior cycles automatically."
        )
    )
    is_opening_stock = import_mode.startswith("Opening Stock")

=======
>>>>>>> 1ba0970d8e791d50b58939957115b7935f08a72b
    file = st.file_uploader("Upload Receive Excel", type="xlsx")

    if file:
        try:
            df = std_columns(pd.read_excel(file))
        except Exception as e:
            st.error(f"Could not read Excel file: {e}")
            st.stop()

        with st.expander("📋 Detected columns in your file"):
            st.write(list(df.columns))

        if "BIN" not in df.columns:
            st.error(
                f"No BIN column found. Your file has: {list(df.columns)}\n\n"
                "The column must be named exactly **BIN**."
            )
            st.stop()

        # Ensure DATE column is parseable
        if "DATE" in df.columns:
            df["_date_parsed"] = pd.to_datetime(df["DATE"], errors="coerce")
        else:
            df["_date_parsed"] = pd.NaT

        st.caption(f"{len(df)} rows detected")

        # ── Dedup logic ───────────────────────────────────────
        # Identify bins appearing more than once in the file
        dup_mask      = df.duplicated(subset=["BIN"], keep=False)
        dupes_in_file = df[dup_mask]["BIN"].unique().tolist()

        if is_opening_stock and dupes_in_file:
            # For opening stock: keep only the LATEST row per duplicate bin
            # Sort by date desc, then keep first occurrence per BIN
            df_sorted   = df.sort_values("_date_parsed", ascending=False, na_position="last")
            df_deduped  = df_sorted.drop_duplicates(subset=["BIN"], keep="first")
            dropped_rows = df[dup_mask & ~df.index.isin(df_deduped.index)]

            st.markdown(
                f"<div style='background:rgba(46,125,50,0.08);border:1px solid rgba(46,125,50,0.25);"
                f"border-radius:8px;padding:12px 16px;margin:8px 0;font-size:13px'>"
                f"📦 <b>Opening Stock mode</b> — {len(dupes_in_file)} bin(s) appear more than once. "
                f"Keeping the <b>latest date</b> row for each. "
                f"{len(dropped_rows)} earlier row(s) will be skipped.</div>",
                unsafe_allow_html=True
            )

            if not dropped_rows.empty:
                with st.expander(f"View {len(dropped_rows)} skipped earlier rows"):
                    skip_cols = [c for c in ["BIN","DATE","PCN","SUPPLIER","VARIETY","WEIGHT"] if c in dropped_rows.columns]
                    st.dataframe(dropped_rows[skip_cols], use_container_width=True, hide_index=True)

            # Work with deduped dataframe from here
            df = df_deduped.reset_index(drop=True)
            dupes_in_file = []   # cleared — already resolved

        elif dupes_in_file and not is_opening_stock:
            # Normal mode — duplicates are flagged and blocked as before
            pass  # handled in preview below

        # ── DB state check ────────────────────────────────────
        bins = df["BIN"].unique().tolist()
        try:
            states = get_bin_states(bins)
        except Exception as e:
            st.error(f"Could not fetch bin states from database: {e}")
            st.stop()

        already_rcv = [b for b in bins if states.get(b, {}).get("state") == "RECEIVED"]

        # In opening stock mode: bins already in RECEIVED state need a prior
        # cycle closed first (ADJUST_OUT) before the new receive can go in.
        # We handle this automatically.
        needs_close   = []
        if is_opening_stock and already_rcv:
            needs_close = already_rcv[:]
            already_rcv = []   # will be handled, not blocked

        # Amount mismatch check
        amount_mismatch = []
        if all(c in df.columns for c in ["WEIGHT","RATE","AMOUNT"]):
            df["_expected"] = pd.to_numeric(df["WEIGHT"], errors="coerce") * pd.to_numeric(df["RATE"], errors="coerce")
            df["_actual"]   = pd.to_numeric(df["AMOUNT"], errors="coerce")
            bad = df[((df["_actual"] - df["_expected"]).abs() > 0.01) & df["_expected"].notna() & df["_actual"].notna()]
            amount_mismatch = bad["BIN"].tolist()

        will_process = [b for b in bins
                        if b not in dupes_in_file
                        and b not in already_rcv
                        and b not in amount_mismatch]

        # ── Preview metrics ───────────────────────────────────
        st.markdown("**Upload Preview**")
        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: metric_card("Total Rows",       fmt_num(len(df)))
        with p2: metric_card("Will Process",     fmt_num(len(will_process)),   "✅ Ready")
        with p3: metric_card("Dupes in File",    fmt_num(len(dupes_in_file)),  "⚠️ Skipped" if not is_opening_stock else "✅ Resolved")
        with p4: metric_card("Already Received", fmt_num(len(already_rcv)),    "⚠️ Skipped")
        with p5: metric_card("Amount Mismatch",  fmt_num(len(amount_mismatch)),"❌ Skipped")

        if needs_close:
            st.info(
                f"ℹ️ {len(needs_close)} bin(s) are currently in RECEIVED state and will have their "
                f"prior cycle closed automatically (ADJUST_OUT) before the new receive is inserted."
            )

        if dupes_in_file or already_rcv or amount_mismatch:
            with st.expander("View issue details"):
                issue_rows = []
                for b in dupes_in_file:   issue_rows.append({"bin_code": b, "issue": "Duplicate in file — use Opening Stock mode to resolve"})
                for b in already_rcv:     issue_rows.append({"bin_code": b, "issue": "Already in RECEIVED state"})
                for b in amount_mismatch: issue_rows.append({"bin_code": b, "issue": "Amount ≠ Weight × Rate"})
                st.dataframe(pd.DataFrame(issue_rows), use_container_width=True, hide_index=True)

        if len(will_process) == 0:
            st.error("Nothing to process — all bins have issues.")
        else:
            st.dataframe(df[df["BIN"].isin(will_process)].head(5),
                         use_container_width=True, hide_index=True)
            st.caption(f"Showing first 5 of {len(will_process)} bins that will be inserted"
                       + (f" ({len(needs_close)} will have prior cycle auto-closed)" if needs_close else ""))

            if st.button(f"✅ Confirm & Process {len(will_process)} Bins"):
                rows, close_rows, errors, seen = [], [], [], set()

                for row in df.itertuples(index=False):
                    bin_code = row.BIN
                    if bin_code not in will_process: continue
                    if bin_code in seen: continue
                    seen.add(bin_code)

                    # If this bin needs its prior cycle closed first, insert ADJUST_OUT
                    if bin_code in needs_close:
                        s = states.get(bin_code, {})
                        close_rows.append({
                            "txid":             str(uuid.uuid4()),
                            "transaction_type": "ADJUST_OUT",
                            "bin_code":         bin_code,
                            "transaction_date": parse_date(row.DATE),
                            "linked_txid":      s.get("last_txid"),
                            "pcn":     s.get("pcn"),
                            "supplier":s.get("supplier"),
                            "source":  s.get("source"),
                            "variety": s.get("variety"),
                            "weight":  s.get("weight"),
                            "rate":    s.get("rate"),
                            "amount":  s.get("amount"),
                            "created_at": datetime.now().isoformat(),
                        })

                    rows.append({
                        "txid":             str(uuid.uuid4()),
                        "transaction_type": "RECEIVE",
                        "bin_code":         bin_code,
                        "transaction_date": parse_date(row.DATE),
                        "pcn":     clean(getattr(row, "PCN",      None)),
                        "wslip":   clean(getattr(row, "W_SLIP",   None)),
                        "grn_no":  clean(getattr(row, "GRN_NO",   None)),
                        "wht_no":  clean(getattr(row, "W_HT_NO",  None)),
                        "supplier":clean(getattr(row, "SUPPLIER",  None)),
                        "source":  clean(getattr(row, "SOURCE",   None)),
                        "variety": clean(getattr(row, "VARIETY",  None)),
                        "weight":  clean(getattr(row, "WEIGHT",   None)),
                        "rate":    clean(getattr(row, "RATE",     None)),
                        "amount":  clean(getattr(row, "AMOUNT",   None)),
                        "created_at": datetime.now().isoformat(),
                    })

                try:
                    # Insert ADJUST_OUTs first to close prior cycles
                    if close_rows:
                        bulk_insert(close_rows, "AdjustClose")
                    failed = bulk_insert(rows, "Receive")
                    st.success(
                        f"✅ {len(rows) - len(failed)} bins received successfully"
                        + (f" — {len(close_rows)} prior cycle(s) auto-closed" if close_rows else "")
                    )
                    show_errors(errors, failed)
                except Exception as e:
                    st.error(f"Insert failed: {e}")


# ================================================================
# PRODUCE
# ================================================================

if menu == "Produce":
    page_header("🏭", "Produce Bins", "Record bins sent through production")
    require_write()
    file = st.file_uploader("Upload Production Excel", type="xlsx")

    if file:
        df = std_columns(pd.read_excel(file))

        if "BIN" not in df.columns:
            st.error(f"No BIN column found. Detected: {list(df.columns)}")
            st.stop()

        bins   = df["BIN"].unique().tolist()
        states = get_bin_states(bins)

        dupes_in_file = df[df.duplicated(subset=["BIN"], keep=False)]["BIN"].unique().tolist()
        not_received  = [b for b in bins if not states.get(b) or states[b]["state"] != "RECEIVED"]
        will_process  = [b for b in bins if b not in dupes_in_file and b not in not_received]

        # ── Metrics ───────────────────────────────────────────
        st.markdown("**Upload Preview**")
        p1, p2, p3, p4 = st.columns(4)
        with p1: metric_card("Total Rows",    fmt_num(len(df)))
        with p2: metric_card("Will Process",  fmt_num(len(will_process)),  "✅ Ready")
        with p3: metric_card("Dupes in File", fmt_num(len(dupes_in_file)), "⚠️ Skipped")
        with p4: metric_card("Not in Stock",  fmt_num(len(not_received)),  "⚠️ Review")

        # ── Fuzzy match for failed bins ───────────────────────
        if not_received:
            st.markdown("---")
            st.markdown("#### ⚠️ Bins Not Found — Possible Typo Matches")
            st.caption(
                "These bins were not found in RECEIVED state. "
                "The system searched for similar bin codes currently in stock. "
                "If you recognise a match, tick it — the system will produce "
                "using the correct bin code."
            )

            # Fetch all current stock for fuzzy search (bin_code + metadata)
            stock_df = fetch_all("v_current_stock")
            stock_list = stock_df[["bin_code","pcn","supplier","variety","days_in_stock"]]\
                         .to_dict("records") if not stock_df.empty else []

            # Session state to hold operator approvals
            if "fuzzy_approvals" not in st.session_state:
                st.session_state["fuzzy_approvals"] = {}

            any_candidates = False
            for failed_bin in not_received:
                if states.get(failed_bin, {}).get("state") not in (None, "PRODUCED", "CONSUMED", "EMPTY"):
                    # Already in a non-receivable state — not a typo scenario
                    continue

                candidates = fuzzy_candidates(failed_bin, stock_list)
                if not candidates:
                    st.markdown(
                        f"**{failed_bin}** — no similar bins found in stock "
                        f"*(may be a genuine intake error — check Reconcile page)*"
                    )
                    continue

                any_candidates = True
                st.markdown(f"**{failed_bin}** — not found. Closest matches in stock:")

                for i, c in enumerate(candidates):
                    col1, col2, col3, col4, col5, col6 = st.columns([1.5, 1.2, 1.5, 1.5, 1, 1.2])
                    col1.markdown(f"**{c['bin_code']}**")
                    col2.markdown(f"PCN: `{c.get('pcn','—')}`")
                    col3.markdown(f"Supplier: {c.get('supplier','—')}")
                    col4.markdown(f"Variety: {c.get('variety','—')}")
                    col5.markdown(f"{c['similarity']}% match")

                    key = f"approve_{failed_bin}_{c['bin_code']}"
                    approved = col6.checkbox("Use this", key=key)
                    if approved:
                        # Only allow one approval per failed bin
                        st.session_state["fuzzy_approvals"][failed_bin] = c["bin_code"]
                    elif st.session_state["fuzzy_approvals"].get(failed_bin) == c["bin_code"]:
                        del st.session_state["fuzzy_approvals"][failed_bin]

            # Show summary of approved overrides
            approvals = st.session_state.get("fuzzy_approvals", {})
            if approvals:
                st.markdown("**Approved substitutions:**")
                for wrong, correct in approvals.items():
                    st.markdown(
                        f"- `{wrong}` → `{correct}` "
                        f"*(will produce {correct} and mark {wrong} as the typed value)*"
                    )

        # ── Confirm button ────────────────────────────────────
        approvals  = st.session_state.get("fuzzy_approvals", {})
        total_producible = len(will_process) + len(approvals)

        if total_producible == 0:
            st.error("Nothing to process.")
        else:
            st.markdown("---")
            if will_process:
                st.dataframe(df[df["BIN"].isin(will_process)].head(5),
                             use_container_width=True, hide_index=True)
                st.caption(f"First 5 of {len(will_process)} exact matches + "
                           f"{len(approvals)} approved substitution(s)")

            if st.button(f"✅ Confirm & Process {total_producible} Bins"):
                rows, errors, seen = [], [], set()

                # Build a combined mapping: file_bin → db_bin
                # For exact matches, file_bin == db_bin
                # For fuzzy approvals, file_bin → corrected db_bin
                bin_mapping = {b: b for b in will_process}
                bin_mapping.update(approvals)  # overrides for typo-matched bins

                for row in df.itertuples(index=False):
                    file_bin = row.BIN
                    if file_bin not in bin_mapping: continue
                    db_bin = bin_mapping[file_bin]
                    if db_bin in seen: continue
                    seen.add(db_bin)

                    s = states.get(db_bin) or get_bin_states([db_bin]).get(db_bin)
                    if not s:
                        errors.append((file_bin, f"Could not fetch state for {db_bin}"))
                        continue

                    rows.append({
                        "txid":             str(uuid.uuid4()),
                        "transaction_type": "PRODUCE",
                        "bin_code":         db_bin,   # always use the correct DB bin code
                        "transaction_date": parse_date(row.DATE),
                        "batch_no":         clean(getattr(row, "BATCHNO",   None)),
                        "machine_id":       clean(getattr(row, "MACHINEID", None)),
                        "linked_txid":      s["last_txid"],
                        "pcn":     s.get("pcn"),
                        "supplier":s.get("supplier"),
                        "source":  s.get("source"),
                        "variety": s.get("variety"),
                        "weight":  s.get("weight"),
                        "rate":    s.get("rate"),
                        "amount":  s.get("amount"),
                        "created_at": datetime.now().isoformat(),
                    })

                try:
                    failed = bulk_insert(rows, "Produce")
                    st.success(f"✅ {len(rows) - len(failed)} bins produced successfully")
                    if approvals:
                        st.info(
                            f"ℹ️ {len(approvals)} bin(s) produced via fuzzy match substitution. "
                            f"Consider updating the original receive records via the Reconcile page."
                        )
                    show_errors(errors, failed)
                    # Clear approvals after successful process
                    st.session_state["fuzzy_approvals"] = {}
                except Exception as e:
                    st.error(f"Insert failed: {e}")


# ================================================================
# ADJUST OUT
# ================================================================

if menu == "Adjust":
    page_header("⚖️", "Adjust Stock", "Remove bins from stock via adjustment")
    require_write()
    file = st.file_uploader("Upload Adjustment Excel", type="xlsx")

    if file:
        df = std_columns(pd.read_excel(file))

        bins   = df["BIN"].unique().tolist()
        states = get_bin_states(bins)

        dupes_in_file = df[df.duplicated(subset=["BIN"], keep=False)]["BIN"].unique().tolist()
        not_received  = [b for b in bins if not states.get(b) or states[b]["state"] != "RECEIVED"]
        will_process  = [b for b in bins if b not in dupes_in_file and b not in not_received]

        st.markdown("**Upload Preview**")
        p1, p2, p3, p4 = st.columns(4)
        with p1: metric_card("Total Rows",    fmt_num(len(df)))
        with p2: metric_card("Will Process",  fmt_num(len(will_process)), "✅ Ready")
        with p3: metric_card("Dupes in File", fmt_num(len(dupes_in_file)), "⚠️ Skipped")
        with p4: metric_card("Not in Stock",  fmt_num(len(not_received)), "⚠️ Skipped")

        if dupes_in_file or not_received:
            with st.expander("View issue details"):
                issue_rows = []
                for b in dupes_in_file: issue_rows.append({"bin_code": b, "issue": "Duplicate in file"})
                for b in not_received:
                    state = states.get(b, {}).get("state", "Never received")
                    issue_rows.append({"bin_code": b, "issue": f"Not in RECEIVED state ({state})"})
                st.dataframe(pd.DataFrame(issue_rows), use_container_width=True, hide_index=True)

        if len(will_process) == 0:
            st.error("Nothing to process — all bins have issues.")
        else:
            st.dataframe(df[df["BIN"].isin(will_process)].head(5),
                         use_container_width=True, hide_index=True)
            st.caption(f"Showing first 5 of {len(will_process)} bins that will be inserted")

            if st.button(f"✅ Confirm & Process {len(will_process)} Bins"):
                rows, errors, seen = [], [], set()
                for row in df.itertuples(index=False):
                    bin_code = row.BIN
                    if bin_code not in will_process: continue
                    if bin_code in seen: continue
                    seen.add(bin_code)
                    s = states[bin_code]
                    rows.append({
                        "txid":             str(uuid.uuid4()),
                        "transaction_type": "ADJUST_OUT",
                        "bin_code":         bin_code,
                        "transaction_date": parse_date(row.DATE),
                        "linked_txid":      s["last_txid"],
                        "pcn":     s.get("pcn"),
                        "supplier":s.get("supplier"),
                        "source":  s.get("source"),
                        "variety": s.get("variety"),
                        "weight":  s.get("weight"),
                        "rate":    s.get("rate"),
                        "amount":  s.get("amount"),
                        "created_at": datetime.now().isoformat(),
                    })
                failed = bulk_insert(rows, "Adjust")
                st.success(f"✅ {len(rows) - len(failed)} bins adjusted out")
                show_errors(errors, failed)


# ================================================================
# BIN HISTORY LOOKUP
# ================================================================

if menu == "Bin History Lookup":
    page_header("🔍", "Bin History Lookup", "Full transaction history for a single bin")
    bin_lookup = st.text_input("Enter Bin Code")

    if bin_lookup:
        hist_df = pd.DataFrame(
            supabase.table("bin_transactions")
            .select("*").eq("bin_code", bin_lookup).order("created_at")
            .execute().data
        )
        if hist_df.empty:
            st.warning("No history found for this bin code.")
        else:
            receive_rows = hist_df[hist_df.transaction_type == "RECEIVE"]
            receive_row  = receive_rows.iloc[0] if not receive_rows.empty else None

            h1, h2, h3 = st.columns(3)
            with h1: metric_card("Current State", hist_df.iloc[-1]["transaction_type"])
            with h2: metric_card("Weight", fmt_num(receive_row["weight"] if receive_row is not None else 0, 2) + " kg")
            with h3: metric_card("Transactions", fmt_num(len(hist_df)))

            st.dataframe(hist_df[[c for c in [
                "transaction_type","transaction_date","pcn","supplier",
                "variety","weight","batch_no","machine_id","linked_txid"
            ] if c in hist_df.columns]], use_container_width=True, hide_index=True)

            fig = px.scatter(
                hist_df, x="transaction_date", y="transaction_type",
                color="transaction_type", title=f"Bin {bin_lookup} — Transaction Timeline",
                color_discrete_map={"RECEIVE":"#1B5E20","PRODUCE":"#E53935","ADJUST_OUT":"#FB8C00"}
            )
            fig.update_layout(**PLOTLY_LIGHT, legend=LEGEND_DEFAULT, title_font_size=13)
            fig.update_traces(marker=dict(size=16))
            st.plotly_chart(fig, use_container_width=True)


# ================================================================
# PCN LOOKUP
# ================================================================

if menu == "PCN Lookup":
    page_header("📋", "PCN Lookup", "All bins and utilisation for a specific PCN")
    pcn_lookup = st.text_input("Enter PCN")

    if pcn_lookup:
        pcn_df = pd.DataFrame(
            supabase.table("v_pcn_bins")
            .select("*").eq("pcn", pcn_lookup).order("received_date")
            .execute().data
        )
        if pcn_df.empty:
            st.warning("No bins found for this PCN.")
        else:
            pcn_df["weight"] = pd.to_numeric(pcn_df["weight"], errors="coerce")
            pcn_df["amount"] = pd.to_numeric(pcn_df["amount"], errors="coerce")

            total  = len(pcn_df)
            prod   = len(pcn_df[pcn_df["current_state"] == "PRODUCED"])
            in_stk = len(pcn_df[pcn_df["current_state"] == "RECEIVED"])
            util   = round(prod / max(total, 1) * 100, 1)

            p1, p2, p3, p4, p5 = st.columns(5)
            with p1: metric_card("Total Bins",   fmt_num(total))
            with p2: metric_card("In Stock",     fmt_num(in_stk))
            with p3: metric_card("Produced",     fmt_num(prod))
            with p4: metric_card("Utilisation",  f"{util}%")
            with p5: metric_card("Total Weight", fmt_num(pcn_df["weight"].sum(), 2) + " kg")

            st.dataframe(pcn_df, use_container_width=True, hide_index=True)

            state_counts         = pcn_df["current_state"].value_counts().reset_index()
            state_counts.columns = ["state","count"]
            fig_pcn = px.pie(
                state_counts, names="state", values="count",
                title=f"PCN {pcn_lookup} — Bin Status", hole=0.45,
                color_discrete_sequence=GREEN_SEQ
            )
            fig_pcn.update_layout(**PLOTLY_LIGHT, legend=LEGEND_DEFAULT, title_font_size=13)
            st.plotly_chart(fig_pcn, use_container_width=True)


# ================================================================
# REPORTS  (PCN Closure + Weekly/Monthly Summary + Bulk Bin Lookup)
# ================================================================

if menu == "Reports":
    page_header("📈", "Reports", "PCN closure, weekly & monthly summaries, bulk bin lookup")

    report_tab = st.radio(
        "", ["PCN Closure", "Weekly Summary", "Monthly Summary", "Bulk Bin Lookup"],
        horizontal=True, label_visibility="collapsed"
    )

    # ── helper: excel download button ────────────────────────
    def excel_download(df: pd.DataFrame, filename: str, label: str = "⬇️ Export to Excel"):
        import io
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as w:
            df.to_excel(w, index=False)
        st.download_button(label=label, data=buf.getvalue(),
                           file_name=filename, mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # ──────────────────────────────────────────────────────────
    # PCN CLOSURE REPORT
    # ──────────────────────────────────────────────────────────
    if report_tab == "PCN Closure":
        st.markdown("#### PCN Closure Report")
        st.caption("A PCN is CLOSED when all its bins have been produced or adjusted out.")

        pcn_cls = fetch_all("v_pcn_closure")

        if not pcn_cls.empty:
            # Guard — if view is missing expected columns, show raw data and warn
            expected_cols = {"pcn_status", "completion_pct", "total_bins"}
            missing = expected_cols - set(pcn_cls.columns)
            if missing:
                st.warning(f"View is missing columns: {missing}. Run new_views.sql in Supabase first.")
                st.dataframe(pcn_cls, use_container_width=True, hide_index=True)
            else:
                for col in ["total_bins","bins_in_stock","bins_produced","bins_consumed",
                            "total_weight","weight_in_stock","weight_produced","total_value",
                            "days_open","completion_pct"]:
                    if col in pcn_cls.columns:
                        pcn_cls[col] = pd.to_numeric(pcn_cls[col], errors="coerce")

                # Filter
                cf1, cf2, cf3 = st.columns(3)
                status_filter   = cf1.selectbox("Status", ["All","OPEN","CLOSED"])
                supplier_f      = cf2.text_input("Supplier", key="pcn_cls_sup")
                variety_f       = cf3.text_input("Variety",  key="pcn_cls_var")

                cls_filt = pcn_cls.copy()
                if status_filter != "All":
                    cls_filt = cls_filt[cls_filt["pcn_status"] == status_filter]
                if supplier_f:
                    cls_filt = cls_filt[cls_filt["supplier"].str.contains(supplier_f, case=False, na=False)]
                if variety_f:
                    cls_filt = cls_filt[cls_filt["variety"].str.contains(variety_f, case=False, na=False)]

                # Summary KPIs
                k1, k2, k3, k4 = st.columns(4)
                with k1: metric_card("Total PCNs",     fmt_num(len(cls_filt)))
                with k2: metric_card("Open PCNs",      fmt_num(len(cls_filt[cls_filt["pcn_status"]=="OPEN"])))
                with k3: metric_card("Closed PCNs",    fmt_num(len(cls_filt[cls_filt["pcn_status"]=="CLOSED"])))
                with k4: metric_card("Avg Completion", fmt_num(cls_filt["completion_pct"].mean(), 1) + "%")

                st.markdown("<br>", unsafe_allow_html=True)

                def highlight_status(row):
                    color = "rgba(76,175,80,0.12)" if row.get("Status") == "CLOSED" else "rgba(255,152,0,0.12)"
                    return [f"background-color: {color}"] * len(row)

                display_cols = {
                    "pcn": "PCN", "supplier": "Supplier", "variety": "Variety",
                    "pcn_status": "Status", "completion_pct": "Complete %",
                    "total_bins": "Total Bins", "bins_in_stock": "In Stock",
                    "bins_produced": "Produced", "bins_consumed": "Consumed",
                    "total_weight": "Total Wt", "weight_produced": "Prod Wt",
                    "total_value": "Value", "opened_date": "Opened",
                    "closed_date": "Closed", "days_open": "Days Open"
                }
                disp = cls_filt[[c for c in display_cols if c in cls_filt.columns]].rename(columns=display_cols)
                st.dataframe(
                    disp.style.apply(highlight_status, axis=1),
                    use_container_width=True, hide_index=True, height=420
                )
                excel_download(disp, f"pcn_closure_{date.today()}.xlsx")

    # ──────────────────────────────────────────────────────────
    # WEEKLY SUMMARY
    # ──────────────────────────────────────────────────────────
    elif report_tab == "Weekly Summary":
        st.markdown("#### Weekly Summary")

        weekly = fetch_all("v_weekly_summary")

        if not weekly.empty:
            for col in ["bins_received","bins_produced","bins_adjusted",
                        "weight_received","weight_produced","value_received",
                        "running_balance_bins","running_balance_weight"]:
                if col in weekly.columns:
                    weekly[col] = pd.to_numeric(weekly[col], errors="coerce")

            weekly["week_start"] = pd.to_datetime(weekly["week_start"])

            # Date range filter
            wf1, wf2 = st.columns(2)
            w_min = weekly["week_start"].min().date()
            w_max = weekly["week_start"].max().date()
            w_from = wf1.date_input("From week", value=w_min, min_value=w_min, max_value=w_max, key="wf")
            w_to   = wf2.date_input("To week",   value=w_max, min_value=w_min, max_value=w_max, key="wt")
            wmask  = (weekly["week_start"].dt.date >= w_from) & (weekly["week_start"].dt.date <= w_to)
            wf     = weekly[wmask].sort_values("week_start")

            # KPIs for selected range
            wk1, wk2, wk3, wk4 = st.columns(4)
            with wk1: metric_card("Weeks",          fmt_num(len(wf)))
            with wk2: metric_card("Total Received", fmt_num(wf["bins_received"].sum()))
            with wk3: metric_card("Total Produced", fmt_num(wf["bins_produced"].sum()))
            with wk4: metric_card("Avg / Week",     fmt_num(wf["bins_received"].mean(), 1))

            # Chart
            fig_w = go.Figure()
            fig_w.add_trace(go.Bar(x=wf["week_label"], y=wf["bins_received"],
                                   name="Received", marker_color="#A5D6A7"))
            fig_w.add_trace(go.Bar(x=wf["week_label"], y=wf["bins_produced"],
                                   name="Produced", marker_color="#1B5E20"))
            fig_w.add_trace(go.Scatter(x=wf["week_label"], y=wf["running_balance_bins"],
                                       name="Balance", mode="lines+markers",
                                       line=dict(color="#FF7043", width=2)))
            fig_w.update_layout(**PLOTLY_LIGHT, legend=LEGEND_HORIZ,
                                title="Weekly Bins: Received vs Produced",
                                barmode="group", xaxis_title="Week", yaxis_title="Bins",
                                title_font_size=13)
            st.plotly_chart(fig_w, use_container_width=True)

            # Table
            wf_disp = wf[["week_label","bins_received","weight_received","value_received",
                           "bins_produced","weight_produced","bins_adjusted",
                           "running_balance_bins","running_balance_weight"]].copy()
            wf_disp.columns = ["Week","Rcvd Bins","Rcvd Wt","Rcvd Val",
                                "Prod Bins","Prod Wt","Adj Out","Bal Bins","Bal Wt"]
            st.dataframe(wf_disp.sort_values("Week", ascending=False),
                         use_container_width=True, hide_index=True, height=320)
            excel_download(wf_disp, f"weekly_summary_{date.today()}.xlsx")
        else:
            st.info("No weekly data available.")

    # ──────────────────────────────────────────────────────────
    # MONTHLY SUMMARY
    # ──────────────────────────────────────────────────────────
    elif report_tab == "Monthly Summary":
        st.markdown("#### Monthly Summary")

        monthly = fetch_all("v_monthly_summary")

        if not monthly.empty:
            for col in ["bins_received","bins_produced","bins_adjusted",
                        "weight_received","weight_produced","value_received",
                        "running_balance_bins","running_balance_weight"]:
                if col in monthly.columns:
                    monthly[col] = pd.to_numeric(monthly[col], errors="coerce")

            monthly["month_start"] = pd.to_datetime(monthly["month_start"])

            # KPIs
            mk1, mk2, mk3, mk4 = st.columns(4)
            with mk1: metric_card("Months Active",  fmt_num(len(monthly)))
            with mk2: metric_card("Total Received", fmt_num(monthly["bins_received"].sum()))
            with mk3: metric_card("Total Produced", fmt_num(monthly["bins_produced"].sum()))
            with mk4: metric_card("Total Value",    fmt_num(monthly["value_received"].sum(), 2))

            # Chart
            mf = monthly.sort_values("month_start")
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=mf["month_label"], y=mf["bins_received"],
                                   name="Received", marker_color="#A5D6A7"))
            fig_m.add_trace(go.Bar(x=mf["month_label"], y=mf["bins_produced"],
                                   name="Produced", marker_color="#1B5E20"))
            fig_m.add_trace(go.Scatter(x=mf["month_label"], y=mf["running_balance_bins"],
                                       name="Balance", mode="lines+markers",
                                       line=dict(color="#FF7043", width=2)))
            fig_m.update_layout(**PLOTLY_LIGHT, legend=LEGEND_HORIZ,
                                title="Monthly Bins: Received vs Produced",
                                barmode="group", xaxis_title="Month", yaxis_title="Bins",
                                title_font_size=13)
            st.plotly_chart(fig_m, use_container_width=True)

            # Value trend
            fig_mv = go.Figure()
            fig_mv.add_trace(go.Scatter(
                x=mf["month_label"], y=mf["value_received"],
                fill="tozeroy", name="Value Received",
                line=dict(color="#1B5E20", width=2),
                fillcolor="rgba(27,94,32,0.08)"
            ))
            fig_mv.update_layout(**PLOTLY_LIGHT, legend=LEGEND_DEFAULT,
                                 title="Monthly Value Received (KES)",
                                 xaxis_title="Month", yaxis_title="KES", title_font_size=13)
            st.plotly_chart(fig_mv, use_container_width=True)

            # Table
            mf_disp = mf[["month_label","bins_received","weight_received","value_received",
                           "bins_produced","weight_produced","bins_adjusted",
                           "running_balance_bins","running_balance_weight"]].copy()
            mf_disp.columns = ["Month","Rcvd Bins","Rcvd Wt","Rcvd Val",
                                "Prod Bins","Prod Wt","Adj Out","Bal Bins","Bal Wt"]
            st.dataframe(mf_disp.sort_values("Month", ascending=False),
                         use_container_width=True, hide_index=True, height=320)
            excel_download(mf_disp, f"monthly_summary_{date.today()}.xlsx")
        else:
            st.info("No monthly data available.")

    # ──────────────────────────────────────────────────────────
    # BULK BIN LOOKUP
    # ──────────────────────────────────────────────────────────
    elif report_tab == "Bulk Bin Lookup":
        st.markdown("#### Bulk Bin Lookup")
        st.caption("Paste bin codes below — one per line, or comma-separated.")

        raw = st.text_area("Bin codes", height=140, placeholder="BIN001\nBIN002\nBIN003")

        if raw.strip():
            # Parse — support newline or comma separated
            bin_list = [b.strip() for b in raw.replace(",", "\n").splitlines() if b.strip()]
            bin_list = list(dict.fromkeys(bin_list))   # dedupe, preserve order
            st.caption(f"{len(bin_list)} unique bins entered")

            if st.button("🔍 Look Up Bins"):
                # Fetch latest state
                states = get_bin_states(bin_list)

                # Fetch full transaction history for all bins in one query
                hist_res = (
                    supabase.table("bin_transactions")
                    .select("*")
                    .in_("bin_code", bin_list)
                    .order("created_at")
                    .range(0, 50000)
                    .execute()
                )
                hist_df = pd.DataFrame(hist_res.data)

                if hist_df.empty:
                    st.warning("No transactions found for any of these bins.")
                else:
                    # Summary table — one row per bin
                    summary_rows = []
                    for b in bin_list:
                        s       = states.get(b)
                        b_hist  = hist_df[hist_df["bin_code"] == b]
                        rcv_row = b_hist[b_hist["transaction_type"] == "RECEIVE"]
                        prd_row = b_hist[b_hist["transaction_type"] == "PRODUCE"]
                        summary_rows.append({
                            "Bin Code":      b,
                            "Current State": s["state"] if s else "NOT FOUND",
                            "PCN":           rcv_row.iloc[0]["pcn"]           if not rcv_row.empty else "—",
                            "Supplier":      rcv_row.iloc[0]["supplier"]      if not rcv_row.empty else "—",
                            "Variety":       rcv_row.iloc[0]["variety"]       if not rcv_row.empty else "—",
                            "Weight":        rcv_row.iloc[0]["weight"]        if not rcv_row.empty else "—",
                            "Received Date": rcv_row.iloc[0]["transaction_date"] if not rcv_row.empty else "—",
                            "Produced Date": prd_row.iloc[0]["transaction_date"] if not prd_row.empty else "—",
                            "Batch No":      prd_row.iloc[0]["batch_no"]      if not prd_row.empty else "—",
                        })

                    summary_df = pd.DataFrame(summary_rows)

                    # State breakdown KPIs
                    states_series = summary_df["Current State"].value_counts()
                    bk1, bk2, bk3, bk4 = st.columns(4)
                    with bk1: metric_card("Bins Found",    fmt_num(len(summary_df[summary_df["Current State"] != "NOT FOUND"])))
                    with bk2: metric_card("In Stock",      fmt_num(states_series.get("RECEIVED", 0)))
                    with bk3: metric_card("Produced",      fmt_num(states_series.get("PRODUCED", 0)))
                    with bk4: metric_card("Not Found",     fmt_num(states_series.get("NOT FOUND", 0)))

                    st.markdown("<br>", unsafe_allow_html=True)
                    st.dataframe(summary_df, use_container_width=True, hide_index=True)
                    excel_download(summary_df, f"bulk_bin_lookup_{date.today()}.xlsx")

                    # Full transaction detail in expander
                    with st.expander("Full transaction history for all bins"):
                        st.dataframe(
                            hist_df[[c for c in [
                                "bin_code","transaction_type","transaction_date",
                                "pcn","supplier","variety","weight","batch_no","machine_id"
                            ] if c in hist_df.columns]],
                            use_container_width=True, hide_index=True, height=400
                        )
                        excel_download(hist_df, f"bulk_bin_history_{date.today()}.xlsx",
                                       "⬇️ Export Full History")


# ================================================================
# RECONCILE
# ================================================================

if menu == "Reconcile":
    page_header("🔧", "Reconcile", "Investigate unmatched bins and correct bin code typos")

    if get_role() not in ("admin", "operator"):
        st.error("Access denied.")
        st.stop()

    recon_tab = st.radio(
        "", ["Unmatched Bin Report", "Bin Code Correction", "Correction History"],
        horizontal=True, label_visibility="collapsed"
    )

    # ──────────────────────────────────────────────────────────
    # TAB 1: UNMATCHED BIN REPORT
    # ──────────────────────────────────────────────────────────
    if recon_tab == "Unmatched Bin Report":
        st.markdown("#### Bins in stock beyond 14 days with no production")
        st.caption(
            "These bins should have gone to production by now but haven't. "
            "Likely causes: intake typo (wrong bin code recorded at receive) or "
            "production typo (bin was produced under a different code)."
        )

        unmatched = fetch_all("v_unmatched_bins")

        if unmatched.empty:
            st.success("✅ No unmatched bins — all bins older than 14 days have been produced.")
        else:
            unmatched["days_in_stock"] = pd.to_numeric(unmatched["days_in_stock"], errors="coerce")
            unmatched["weight"]        = pd.to_numeric(unmatched["weight"],        errors="coerce")

            # Filters
            f1, f2, f3 = st.columns(3)
            min_days    = f1.number_input("Min days in stock", value=14, min_value=1, step=1)
            sup_filter  = f2.text_input("Supplier", key="um_sup")
            pcn_filter  = f3.text_input("PCN",      key="um_pcn")

            filt = unmatched[unmatched["days_in_stock"] >= min_days]
            if sup_filter:
                filt = filt[filt["supplier"].str.contains(sup_filter, case=False, na=False)]
            if pcn_filter:
                filt = filt[filt["pcn"].str.contains(pcn_filter, case=False, na=False)]

            u1, u2, u3 = st.columns(3)
            with u1: metric_card("Unmatched Bins",   fmt_num(len(filt)))
            with u2: metric_card("Total Weight",     fmt_num(filt["weight"].sum(), 1) + " kg")
            with u3: metric_card("Oldest Bin",       fmt_num(filt["days_in_stock"].max()) + " days")

            st.markdown("<br>", unsafe_allow_html=True)

            # Fuzzy suggestion column — find similar bin codes in stock for each unmatched bin
            stock_df   = fetch_all("v_current_stock")
            stock_list = stock_df[["bin_code","pcn","supplier","variety"]]\
                         .to_dict("records") if not stock_df.empty else []

            def get_suggestion(bin_code):
                others = [s for s in stock_list if s["bin_code"] != bin_code]
                candidates = fuzzy_candidates(bin_code, others, top_n=1, min_similarity=70)
                if candidates:
                    c = candidates[0]
                    return f"{c['bin_code']} ({c['similarity']}%)"
                return "—"

            filt = filt.copy()
            filt["possible_match"] = filt["bin_code"].apply(get_suggestion)

            display_cols = {
                "bin_code":      "Bin Code",
                "days_in_stock": "Days in Stock",
                "received_date": "Received",
                "pcn":           "PCN",
                "supplier":      "Supplier",
                "variety":       "Variety",
                "weight":        "Weight",
                "wslip":         "W/Slip",
                "grn_no":        "GRN",
                "possible_match":"Possible Match"
            }
            disp = filt[[c for c in display_cols if c in filt.columns]].rename(columns=display_cols)
            st.dataframe(disp, use_container_width=True, hide_index=True, height=420)

            # Export
            import io
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as w:
                disp.to_excel(w, index=False)
            st.download_button(
                "⬇️ Export to Excel", data=buf.getvalue(),
                file_name=f"unmatched_bins_{date.today()}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ──────────────────────────────────────────────────────────
    # TAB 2: BIN CODE CORRECTION
    # ──────────────────────────────────────────────────────────
    elif recon_tab == "Bin Code Correction":
        st.markdown("#### Correct a bin code typo")
        st.caption(
            "Use this when a bin code was recorded incorrectly at intake. "
            "This updates **all** transaction records for that bin and logs the change. "
            "Admin only — this action cannot be undone."
        )

        if get_role() != "admin":
            st.warning("⚠️ Only admins can perform bin code corrections.")
            st.stop()

        c1, c2 = st.columns(2)
        old_code = c1.text_input("Wrong bin code (as recorded)", placeholder="e.g. 10334")
        new_code = c2.text_input("Correct bin code (actual)",    placeholder="e.g. 10234")
        reason   = st.text_input("Reason / notes", placeholder="e.g. Confirmed with receiving supervisor — digit transposed")

        if old_code and new_code:
            if old_code == new_code:
                st.warning("Old and new codes are the same.")
            else:
                # Preview what will change
                preview_res = (
                    supabase.table("bin_transactions")
                    .select("txid, transaction_type, transaction_date, pcn, supplier")
                    .eq("bin_code", old_code)
                    .execute()
                )
                preview_df = pd.DataFrame(preview_res.data)

                if preview_df.empty:
                    st.error(f"No transactions found for bin code **{old_code}**. Check the code.")
                else:
                    st.markdown(f"**Preview — {len(preview_df)} transaction(s) will be renamed:**")
                    st.dataframe(preview_df, use_container_width=True, hide_index=True)

                    st.markdown(
                        f"<div style='background:rgba(255,152,0,0.1);border:1px solid rgba(255,152,0,0.3);"
                        f"border-radius:8px;padding:12px 16px;margin:12px 0;font-size:13px'>"
                        f"⚠️ This will rename <b>{old_code}</b> → <b>{new_code}</b> across "
                        f"<b>{len(preview_df)}</b> transaction row(s) and update bin_status. "
                        f"This is permanent and logged.</div>",
                        unsafe_allow_html=True
                    )

                    confirm_key = f"confirm_correction_{old_code}_{new_code}"
                    confirmed = st.checkbox("I have verified this correction with physical records", key=confirm_key)

                    if confirmed:
                        if st.button("🔧 Apply Correction", type="primary"):
                            try:
                                result = supabase.rpc("correct_bin_code", {
                                    "p_old_code":      old_code,
                                    "p_new_code":      new_code,
                                    "p_corrected_by":  user_email,
                                    "p_reason":        reason or None
                                }).execute()
                                rows_updated = result.data
                                st.success(
                                    f"✅ Correction applied — {rows_updated} transaction row(s) updated. "
                                    f"Bin **{old_code}** is now **{new_code}** across the entire ledger."
                                )
                            except Exception as e:
                                st.error(f"Correction failed: {e}")

    # ──────────────────────────────────────────────────────────
    # TAB 3: CORRECTION HISTORY
    # ──────────────────────────────────────────────────────────
    elif recon_tab == "Correction History":
        st.markdown("#### All bin code corrections ever applied")
        st.caption("Full audit log — every correction is permanent and traceable.")

        try:
            hist_res = (
                supabase.table("bin_corrections")
                .select("*")
                .order("corrected_at", desc=True)
                .range(0, 1000)
                .execute()
            )
            hist_df = pd.DataFrame(hist_res.data)

            if hist_df.empty:
                st.info("No corrections have been applied yet.")
            else:
                st.dataframe(hist_df, use_container_width=True, hide_index=True)
        except Exception:
            st.info("Correction history table not found — run reconcile.sql in Supabase first.")