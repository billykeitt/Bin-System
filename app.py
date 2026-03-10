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

st.set_page_config(layout="wide", page_title="Keitt Bin Ledger System")

# -----------------------------
# STYLING — White theme, working navbar
# top: 50px accounts for Streamlit's own toolbar so navbar is never hidden
# -----------------------------

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* Apply font globally without overriding theme colors */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Navbar ─────────────────────────────────────────────────
   Uses color-scheme-aware variables so it works in both themes */
.keitt-navbar {
    position: fixed;
    top: 50px;
    left: 0; right: 0;
    height: 56px;
    background: var(--background-color, #FFFFFF);
    border-bottom: 2px solid rgba(128,128,128,0.15);
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    z-index: 999;
    display: flex;
    align-items: center;
    padding: 0 24px;
    gap: 12px;
}
.keitt-navbar-logo {
    width: 34px; height: 34px;
    background: #1B5E20;
    border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-size: 17px; flex-shrink: 0;
}
.keitt-navbar-title {
    font-size: 16px; font-weight: 700;
    color: #2E7D32; letter-spacing: -0.2px;
}
.keitt-navbar-subtitle {
    font-size: 11px; color: #888; line-height: 1; margin-top: 1px;
}
.keitt-navbar-sep { width: 1px; height: 26px; background: rgba(128,128,128,0.25); margin: 0 6px; }
.keitt-navbar-tag {
    font-size: 11px; color: #2E7D32;
    background: rgba(46,125,50,0.1);
    border-radius: 20px; padding: 3px 10px; font-weight: 500;
}

/* ── Content offset ─────────────────────────────────────── */
section.main > div.block-container {
    padding-top: 124px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px;
}

/* ── Sidebar ─────────────────────────────────────────────── */
[data-testid="stSidebar"] {
    padding-top: 124px !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 14px !important; padding: 4px 0 !important;
}
[data-testid="stSidebar"] .stRadio > div { gap: 10px !important; }

/* ── Metric cards — theme-adaptive ──────────────────────── */
.metric-card {
    background: rgba(128,128,128,0.06);
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 12px; padding: 18px 14px; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
.metric-value { font-size: 24px; font-weight: 700; color: #2E7D32; line-height: 1.1; }
.metric-sub   { font-size: 11px; color: #888; margin-top: 5px; }

/* ── Section headers ─────────────────────────────────────── */
.section-header {
    font-size: 13px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.7px;
    border-bottom: 2px solid rgba(46,125,50,0.25);
    padding-bottom: 8px; margin: 32px 0 16px 0;
    color: #2E7D32;
}

/* ── Buttons ─────────────────────────────────────────────── */
.stButton > button {
    background-color: #1B5E20 !important; color: white !important;
    border: none !important; border-radius: 8px !important;
    font-weight: 600 !important; padding: 8px 20px !important;
}
.stButton > button:hover { background-color: #2E7D32 !important; }
</style>

<div class="keitt-navbar">
    <div class="keitt-navbar-logo">🌿</div>
    <div>
        <div class="keitt-navbar-title">Keitt Bin Ledger</div>
        <div class="keitt-navbar-subtitle">Warehouse Inventory &amp; Production Flow</div>
    </div>
    <div class="keitt-navbar-sep"></div>
    <div class="keitt-navbar-tag">📦 Inventory</div>
    <div class="keitt-navbar-tag">🔁 Traceability</div>
    <div class="keitt-navbar-tag">🏭 Production</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------
# SESSION STATE — tokens stored so refresh doesn't log user out
# ---------------------------------------------------------------

for key in ("user", "access_token", "refresh_token"):
    if key not in st.session_state:
        st.session_state[key] = None

# Restore session from stored tokens on page load / refresh
if st.session_state["user"] is None and st.session_state["access_token"]:
    try:
        restored = supabase.auth.set_session(
            st.session_state["access_token"],
            st.session_state["refresh_token"]
        )
        if restored.user:
            st.session_state["user"] = restored.user
    except Exception:
        st.session_state["access_token"]  = None
        st.session_state["refresh_token"] = None

# ---------------------------------------------------------------
# AUTH
# ---------------------------------------------------------------

def login_screen():
    _, col, _ = st.columns([1, 1.1, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### 🌿 Keitt Bin Ledger")
        st.markdown("Sign in to continue")
        email    = st.text_input("Email",    placeholder="you@example.com")
        password = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Sign In", use_container_width=True):
            try:
                result = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if result.user:
                    st.session_state["user"]          = result.user
                    st.session_state["access_token"]  = result.session.access_token
                    st.session_state["refresh_token"] = result.session.refresh_token
                    st.rerun()
            except Exception:
                st.error("Invalid email or password")

if st.session_state["user"] is None:
    login_screen()
    st.stop()

# ---------------------------------------------------------------
# SIDEBAR
# ---------------------------------------------------------------

st.sidebar.markdown("**Menu**")
menu = st.sidebar.radio(
    "", ["Dashboard", "Receive", "Produce", "Adjust", "Bin History Lookup", "PCN Lookup"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")
st.sidebar.markdown(
    f"<small style='color:#999'>Signed in as<br><b>{st.session_state['user'].email}</b></small>",
    unsafe_allow_html=True
)
st.sidebar.markdown("")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state["user"]          = None
    st.session_state["access_token"]  = None
    st.session_state["refresh_token"] = None
    st.rerun()

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
    df["BIN"] = df["BIN"].astype(str).str.strip()
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
        if pd.isna(n): return "—"
        return f"{n:,.{decimals}f}"
    except:
        return "—"

PLOTLY_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",   # transparent — inherits page background
    plot_bgcolor="rgba(0,0,0,0)",    # transparent — inherits page background
    margin=dict(t=48, b=16, l=16, r=16)
)
LEGEND_DEFAULT  = dict(bordercolor="rgba(128,128,128,0.2)", borderwidth=1)
LEGEND_HORIZ    = dict(bordercolor="rgba(128,128,128,0.2)", borderwidth=1, orientation="h", y=1.12)

# Alias kept so existing code using PLOTLY_LIGHT still works
PLOTLY_LIGHT = PLOTLY_BASE
GREEN_SEQ = ["#1B5E20","#2E7D32","#388E3C","#43A047","#66BB6A","#A5D6A7","#C8E6C9"]

# ================================================================
# DASHBOARD
# ================================================================

if menu == "Dashboard":

    st.sidebar.markdown("---")
    st.sidebar.markdown("**Filters**")
    supplier_filter = st.sidebar.text_input("Supplier")
    variety_filter  = st.sidebar.text_input("Variety")

    # ── Current stock ──────────────────────────────────────────
    stock_res = supabase.table("v_current_stock").select("*").execute()
    stock_df  = pd.DataFrame(stock_res.data)

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

    eligible = filt[filt["eligible_for_production"]] if not filt.empty else pd.DataFrame()

    # ── KPIs ──────────────────────────────────────────────────
    st.markdown("<div class='section-header'>Current Stock Balance</div>", unsafe_allow_html=True)

    total_weight = filt["weight"].sum() if not filt.empty else 0
    total_value  = filt["amount"].sum() if not filt.empty else 0
    total_bins   = len(filt)
    avg_rate     = (
        (filt["weight"] * filt["rate"]).sum() / total_weight
        if not filt.empty and total_weight > 0 else 0
    )

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    with c1: metric_card("Bins In Stock",       fmt_num(total_bins))
    with c2: metric_card("Total Weight (kg)",   fmt_num(total_weight, 2))
    with c3: metric_card("Total Value (KES)",   fmt_num(total_value, 2))
    with c4: metric_card("Avg Rate / kg",       fmt_num(avg_rate, 2), "Weighted avg")
    with c5: metric_card("Eligible to Produce", fmt_num(len(eligible)), "14+ days in stock")
    with c6: metric_card("Eligible Wt (kg)",    fmt_num(eligible["weight"].sum() if not eligible.empty else 0, 2))

    # ── Breakdown ─────────────────────────────────────────────
    st.markdown("<div class='section-header'>Stock Breakdown</div>", unsafe_allow_html=True)

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

    # ── PCN Utilisation ───────────────────────────────────────
    st.markdown("<div class='section-header'>PCN Utilisation</div>", unsafe_allow_html=True)

    util_res = supabase.table("v_pcn_utilisation").select("*").execute()
    util_df  = pd.DataFrame(util_res.data)

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

        # % utilisation based on bins
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
                **PLOTLY_LIGHT,
                legend=LEGEND_HORIZ,
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

    # ── Aging Report ──────────────────────────────────────────
    st.markdown("<div class='section-header'>Aging Report</div>", unsafe_allow_html=True)

    aging_res = supabase.table("v_aging_report").select("*").execute()
    aging_df  = pd.DataFrame(aging_res.data)

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
        age_map = {"Aging (< 14 days)": "Aging", "Ready (14+ days)": "Ready", "Produced": "Produced"}
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

    # ── Daily Ledger ──────────────────────────────────────────
    st.markdown("<div class='section-header'>Daily Ledger</div>", unsafe_allow_html=True)

    ledger_res = supabase.table("v_daily_ledger").select("*").execute()
    ledger_df  = pd.DataFrame(ledger_res.data)

    if not ledger_df.empty:
        ledger_df["date"] = pd.to_datetime(ledger_df["date"])
        for col in ["bins_received","weight_received","value_received",
                    "bins_produced","weight_produced","bins_adjusted",
                    "running_balance_bins","running_balance_weight"]:
            ledger_df[col] = pd.to_numeric(ledger_df[col], errors="coerce")

        d1, d2 = st.columns(2)
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
            **PLOTLY_LIGHT,
            legend=LEGEND_HORIZ,
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

    # ── Historical Snapshot ───────────────────────────────────
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
            with s1: metric_card("Bins in Stock", fmt_num(len(snap_df)),      str(snap_date))
            with s2: metric_card("Weight (kg)",   fmt_num(snap_df["weight"].sum(), 2))
            with s3: metric_card("Value (KES)",   fmt_num(snap_df["amount"].sum(), 2))
            st.dataframe(snap_df, use_container_width=True, hide_index=True, height=350)


# ================================================================
# RECEIVE
# ================================================================

if menu == "Receive":
    st.markdown("<div class='section-header'>Receive Bins</div>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Receive Excel", type="xlsx")

    if file:
        df = std_columns(pd.read_excel(file))
        st.dataframe(df.head(5), use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} rows detected")

        if st.button("Process Receive"):
            bins   = df["BIN"].unique().tolist()
            states = get_bin_states(bins)
            rows, errors, seen = [], [], set()

            for row in df.itertuples(index=False):
                bin_code = row.BIN
                if bin_code in seen:
                    errors.append((bin_code, "Duplicate in file")); continue
                seen.add(bin_code)
                if states.get(bin_code, {}).get("state") == "RECEIVED":
                    errors.append((bin_code, "Already in RECEIVED state")); continue
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

            failed = bulk_insert(rows, "Receive")
            st.success(f"✅ {len(rows) - len(failed)} bins received successfully")
            show_errors(errors, failed)


# ================================================================
# PRODUCE
# ================================================================

if menu == "Produce":
    st.markdown("<div class='section-header'>Produce Bins</div>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Production Excel", type="xlsx")

    if file:
        df = std_columns(pd.read_excel(file))
        st.dataframe(df.head(5), use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} rows detected")

        if st.button("Process Production"):
            bins   = df["BIN"].unique().tolist()
            states = get_bin_states(bins)
            rows, errors, seen = [], [], set()

            for row in df.itertuples(index=False):
                bin_code = row.BIN
                if bin_code in seen:
                    errors.append((bin_code, "Duplicate in file")); continue
                seen.add(bin_code)
                s = states.get(bin_code)
                if not s:
                    errors.append((bin_code, "Never received")); continue
                if s["state"] != "RECEIVED":
                    errors.append((bin_code, f"Not in RECEIVED state (current: {s['state']})")); continue
                rows.append({
                    "txid":             str(uuid.uuid4()),
                    "transaction_type": "PRODUCE",
                    "bin_code":         bin_code,
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

            failed = bulk_insert(rows, "Produce")
            st.success(f"✅ {len(rows) - len(failed)} bins produced")
            show_errors(errors, failed)


# ================================================================
# ADJUST OUT
# ================================================================

if menu == "Adjust":
    st.markdown("<div class='section-header'>Adjust Stock</div>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Adjustment Excel", type="xlsx")

    if file:
        df = std_columns(pd.read_excel(file))
        st.dataframe(df.head(5), use_container_width=True, hide_index=True)
        st.caption(f"{len(df)} rows detected")

        if st.button("Process Adjustment"):
            bins   = df["BIN"].unique().tolist()
            states = get_bin_states(bins)
            rows, errors, seen = [], [], set()

            for row in df.itertuples(index=False):
                bin_code = row.BIN
                if bin_code in seen:
                    errors.append((bin_code, "Duplicate in file")); continue
                seen.add(bin_code)
                s = states.get(bin_code)
                if not s or s["state"] != "RECEIVED":
                    current = s["state"] if s else "UNKNOWN"
                    errors.append((bin_code, f"Must be RECEIVED to adjust out (current: {current})")); continue
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
    st.markdown("<div class='section-header'>Bin History Lookup</div>", unsafe_allow_html=True)
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
    st.markdown("<div class='section-header'>PCN Lookup</div>", unsafe_allow_html=True)
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

            state_counts        = pcn_df["current_state"].value_counts().reset_index()
            state_counts.columns = ["state","count"]
            fig_pcn = px.pie(
                state_counts, names="state", values="count",
                title=f"PCN {pcn_lookup} — Bin Status", hole=0.45,
                color_discrete_sequence=GREEN_SEQ
            )
            fig_pcn.update_layout(**PLOTLY_LIGHT, legend=LEGEND_DEFAULT, title_font_size=13)
            st.plotly_chart(fig_pcn, use_container_width=True)