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

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

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

section.main > div.block-container {
    padding-top: 124px !important;
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    max-width: 1400px;
}

[data-testid="stSidebar"] {
    padding-top: 124px !important;
}
[data-testid="stSidebar"] .stRadio label {
    font-size: 14px !important; padding: 4px 0 !important;
}
[data-testid="stSidebar"] .stRadio > div { gap: 10px !important; }

.metric-card {
    background: rgba(128,128,128,0.06);
    border: 1px solid rgba(128,128,128,0.18);
    border-radius: 12px; padding: 18px 14px; text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.metric-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 6px; }
.metric-value { font-size: 24px; font-weight: 700; color: #2E7D32; line-height: 1.1; }
.metric-sub   { font-size: 11px; color: #888; margin-top: 5px; }

.section-header {
    font-size: 13px; font-weight: 700;
    text-transform: uppercase; letter-spacing: 0.7px;
    border-bottom: 2px solid rgba(46,125,50,0.25);
    padding-bottom: 8px; margin: 32px 0 16px 0;
    color: #2E7D32;
}

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
# SESSION STATE
# ---------------------------------------------------------------

for key in ("user", "access_token", "refresh_token"):
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
    "", [
        "Dashboard",
        "Receive", "Produce", "Adjust",
        "Reports",
        "Bin History Lookup", "PCN Lookup"
    ],
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
        if n is None or pd.isna(n): return "—"
        return f"{n:,.{decimals}f}"
    except:
        return "—"

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
    st.markdown("<div class='section-header'>Receive Bins</div>", unsafe_allow_html=True)
    file = st.file_uploader("Upload Receive Excel", type="xlsx")

    if file:
        df = std_columns(pd.read_excel(file))

        # ── Validation preview ────────────────────────────────
        bins   = df["BIN"].unique().tolist()
        states = get_bin_states(bins)

        dupes_in_file   = df[df.duplicated(subset=["BIN"], keep=False)]["BIN"].unique().tolist()
        already_rcv     = [b for b in bins if states.get(b, {}).get("state") == "RECEIVED"]
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

        st.markdown("**Upload Preview**")
        p1, p2, p3, p4, p5 = st.columns(5)
        with p1: metric_card("Total Rows",        fmt_num(len(df)))
        with p2: metric_card("Will Process",      fmt_num(len(will_process)),  "✅ Ready")
        with p3: metric_card("Dupes in File",     fmt_num(len(dupes_in_file)), "⚠️ Skipped")
        with p4: metric_card("Already Received",  fmt_num(len(already_rcv)),   "⚠️ Skipped")
        with p5: metric_card("Amount Mismatch",   fmt_num(len(amount_mismatch)),"❌ Skipped")

        if dupes_in_file or already_rcv or amount_mismatch:
            with st.expander("View issue details"):
                issue_rows = []
                for b in dupes_in_file:   issue_rows.append({"bin_code": b, "issue": "Duplicate in file"})
                for b in already_rcv:     issue_rows.append({"bin_code": b, "issue": "Already in RECEIVED state"})
                for b in amount_mismatch: issue_rows.append({"bin_code": b, "issue": "Amount ≠ Weight × Rate"})
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

        # ── Validation preview ────────────────────────────────
        bins   = df["BIN"].unique().tolist()
        states = get_bin_states(bins)

        dupes_in_file = df[df.duplicated(subset=["BIN"], keep=False)]["BIN"].unique().tolist()
        not_received  = [b for b in bins if not states.get(b) or states[b]["state"] != "RECEIVED"]
        will_process  = [b for b in bins if b not in dupes_in_file and b not in not_received]

        st.markdown("**Upload Preview**")
        p1, p2, p3, p4 = st.columns(4)
        with p1: metric_card("Total Rows",      fmt_num(len(df)))
        with p2: metric_card("Will Process",    fmt_num(len(will_process)), "✅ Ready")
        with p3: metric_card("Dupes in File",   fmt_num(len(dupes_in_file)), "⚠️ Skipped")
        with p4: metric_card("Not in Stock",    fmt_num(len(not_received)), "⚠️ Skipped")

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
    st.markdown("<div class='section-header'>Reports</div>", unsafe_allow_html=True)

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
            with k1: metric_card("Total PCNs",   fmt_num(len(cls_filt)))
            with k2: metric_card("Open PCNs",    fmt_num(len(cls_filt[cls_filt["pcn_status"]=="OPEN"])))
            with k3: metric_card("Closed PCNs",  fmt_num(len(cls_filt[cls_filt["pcn_status"]=="CLOSED"])))
            with k4: metric_card("Avg Completion", fmt_num(cls_filt["completion_pct"].mean(), 1) + "%")

            st.markdown("<br>", unsafe_allow_html=True)

            # Colour code status
            def highlight_status(row):
                color = "rgba(76,175,80,0.12)" if row["pcn_status"] == "CLOSED" else "rgba(255,152,0,0.12)"
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
        else:
            st.info("No PCN data available.")

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