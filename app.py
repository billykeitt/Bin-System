import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
from supabase import create_client
import plotly.express as px
import os
from dotenv import load_dotenv
from postgrest.exceptions import APIError

# -----------------------------
# SUPABASE CONNECTION
# -----------------------------

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# PAGE CONFIG
# -----------------------------

st.set_page_config(layout="wide", page_title="Keitt Bin Ledger System")

# -----------------------------
# FIXED TOP HEADER + DARK THEME STYLING
# -----------------------------

st.markdown("""
<style>

.navbar {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    background-color: #0D0D0D;
    padding: 15px 25px;
    z-index: 9999;
    border-bottom: 1px solid #222222;
    box-shadow: 0px 2px 6px rgba(0,0,0,0.6);
}

.navbar-title {
    font-size: 22px;
    font-weight: 600;
    color: #4CAF50;
    letter-spacing: 0.5px;
}

.navbar-subtitle {
    font-size: 13px;
    color: #CCCCCC;
    margin-top: -3px;
}

.block-container {
    padding-top: 90px !important;
}

html, body, [class*="css"]  {
    font-family: 'Inter', sans-serif;
    color: #E0E0E0;
}

h1, h2, h3 {
    font-weight: 600;
    color: #FFFFFF;
}

.metric-card {
    background-color: #1E1E1E;
    padding: 20px;
    border-radius: 12px;
    border: 1px solid #333333;
    text-align: center;
    box-shadow: 0px 0px 8px rgba(0,0,0,0.4);
}

tbody tr:nth-child(even) {
    background-color: #1A1A1A !important;
}

tbody tr:nth-child(odd) {
    background-color: #161616 !important;
}

tbody tr:hover {
    background-color: #2A2A2A !important;
}

thead th {
    background-color: #222222 !important;
    color: #E0E0E0 !important;
}

hr {
    border: 1px solid #333333;
}

/* SIDEBAR */
[data-testid="stSidebar"] {
    background-color: #0F0F0F;
    padding-top: 100px;
    border-right: 1px solid #222222;
}

[data-testid="stSidebar"] label {
    color: #E0E0E0 !important;
    font-size: 16px;
}

/* Increase spacing between sidebar radio items */
[data-testid="stSidebar"] .stRadio > div {
    gap: 18px !important;   /* space between items */
}

[data-testid="stSidebar"] .stRadio label {
    padding: 6px 0 !important;  /* vertical padding */
    font-size: 17px !important;
}

[data-testid="stSidebar"] {
    padding-left: 25px !important;
    padding-right: 15px !important;
}

            /* Widen sidebar */
[data-testid="stSidebar"] {
    width: 270px !important;
}


</style>

<div class="navbar">
    <div class="navbar-title">Keitt Bin Ledger System</div>
    <div class="navbar-subtitle">Warehouse Inventory • Traceability • Production Flow</div>
</div>
""", unsafe_allow_html=True)


# Initialize session state keys
if "user" not in st.session_state:
    st.session_state["user"] = None


def login_screen():
    st.title("Sign In")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Sign In"):
        try:
            result = supabase.auth.sign_in_with_password(
                {"email": email, "password": password}
            )
            if result.user:
                st.session_state["user"] = result.user
                st.rerun()
        except Exception:
            st.error("Invalid email or password")

if st.session_state["user"] is None:
    login_screen()
    st.stop()

# -----------------------------
# SIDEBAR NAVIGATION
# -----------------------------

menu = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Receive", "Produce", "Adjust", "Bin History Lookup", "PCN Lookup"]
)

st.sidebar.write("---")
if st.sidebar.button("Logout"):
    supabase.auth.sign_out()
    st.session_state["user"] = None
    st.rerun()

# -----------------------------
# UTILS
# -----------------------------


def clean(val):
    if val is None:
        return None
    if isinstance(val, float) and pd.isna(val):
        return None
    if isinstance(val, str) and val.strip() == "":
        return None
    return val

def parse_date(d):
    try:
        return pd.to_datetime(d).isoformat()
    except:
        return None

def insert_with_error_capture(rows, tx_label):
    failed_bins = []
    for i in range(0, len(rows), 200):
        batch = rows[i:i+200]
        try:
            supabase.table("bin_transactions").insert(batch).execute()
        except APIError as e:
            if e.code == "23505":
                failed_bins.extend([r.get("bin_code") for r in batch])
            else:
                st.error(f"❌ {tx_label}: Database error: {e.message}")
                st.stop()
    return failed_bins

# ============================================================
# RECEIVE
# ============================================================

if menu == "Receive":

    st.header("Receive Bins")

    file = st.file_uploader("Upload Receive Excel", type="xlsx")

    if file:

        df = pd.read_excel(file)
        df.columns = [c.strip().replace(" ","_").replace("/","_") for c in df.columns]
        df["BIN"] = df["BIN"].astype(str).str.strip()

        if st.button("Process Receive"):

            bins = df["BIN"].unique().tolist()

            res = supabase.rpc("get_latest_bins", {"bins": bins}).execute()
            latest = {r["bin_code"]: r["transaction_type"] for r in res.data}

            rows, errors, seen = [], [], set()

            for row in df.itertuples(index=False):

                bin_code = row.BIN

                if bin_code in seen:
                    errors.append((bin_code, "Duplicate in file"))
                    continue
                seen.add(bin_code)

                if latest.get(bin_code) == "RECEIVE":
                    errors.append((bin_code, "Already received for current cycle"))
                    continue

                rows.append({
                    "txid": str(uuid.uuid4()),
                    "transaction_type": "RECEIVE",
                    "bin_code": bin_code,
                    "transaction_date": parse_date(row.DATE),
                    "pcn": clean(getattr(row, "PCN", None)),
                    "wslip": clean(getattr(row, "W_SLIP", None)),
                    "grn_no": clean(getattr(row, "GRN_NO", None)),
                    "wht_no": clean(getattr(row, "W_HT_NO", None)),
                    "supplier": clean(getattr(row, "SUPPLIER", None)),
                    "source": clean(getattr(row, "SOURCE", None)),
                    "variety": clean(getattr(row, "VARIETY", None)),
                    "weight": clean(getattr(row, "WEIGHT", None)),
                    "rate": clean(getattr(row, "RATE", None)),
                    "amount": clean(getattr(row, "AMOUNT", None)),
                    "created_at": datetime.now().isoformat()
                })

            failed_bins = insert_with_error_capture(rows, "Receive")
            supabase.rpc("refresh_bin_state").execute()

            st.success(f"{len(rows) - len(failed_bins)} bins received")

            if errors or failed_bins:
                st.warning("Issues encountered")
                err_df = pd.DataFrame(errors, columns=["bin_code", "reason"])
                if failed_bins:
                    fb = pd.DataFrame({"bin_code": failed_bins, "reason": "Database rejected insert"})
                    err_df = pd.concat([err_df, fb], ignore_index=True)
                st.dataframe(err_df)

# ============================================================
# PRODUCE
# ============================================================

if menu == "Produce":

    st.header("Produce Bins")

    file = st.file_uploader("Upload Production Excel", type="xlsx")

    if file:

        df = pd.read_excel(file)
        df.columns = [c.strip().replace(" ","_") for c in df.columns]
        df["BIN"] = df["BIN"].astype(str).str.strip()

        if st.button("Process Production"):

            bins = df["BIN"].unique().tolist()
            res = supabase.rpc("get_latest_bins", {"bins": bins}).execute()
            latest = {r["bin_code"]: r for r in res.data}

            rows, errors, seen = [], [], set()

            for row in df.itertuples(index=False):

                bin_code = row.BIN

                if bin_code in seen:
                    errors.append((bin_code, "Duplicate in file"))
                    continue
                seen.add(bin_code)

                l = latest.get(bin_code)

                if not l:
                    errors.append((bin_code, "Never received"))
                    continue

                if l["transaction_type"] != "RECEIVE":
                    errors.append((bin_code, "Not in stock"))
                    continue

                rows.append({
                    "txid": str(uuid.uuid4()),
                    "transaction_type": "PRODUCE",
                    "bin_code": bin_code,
                    "transaction_date": parse_date(row.DATE),
                    "batch_no": clean(getattr(row, "BATCHNO", None)),
                    "machine_id": clean(getattr(row, "MACHINEID", None)),
                    "linked_txid": l["txid"],

                    "pcn": l.get("pcn"),
                    "supplier": l.get("supplier"),
                    "source": l.get("source"),
                    "variety": l.get("variety"),
                    "weight": l.get("weight"),
                    "rate": l.get("rate"),
                    "amount": l.get("amount"),

                    "created_at": datetime.now().isoformat()
                })

            failed_bins = insert_with_error_capture(rows, "Produce")
            supabase.rpc("refresh_bin_state").execute()

            st.success(f"{len(rows) - len(failed_bins)} bins produced")

            if errors or failed_bins:
                st.warning("Issues encountered")
                err_df = pd.DataFrame(errors, columns=["bin_code", "reason"])
                if failed_bins:
                    fb = pd.DataFrame({"bin_code": failed_bins, "reason": "Database rejected insert"})
                    err_df = pd.concat([err_df, fb], ignore_index=True)
                st.dataframe(err_df)

# ============================================================
# ADJUST
# ============================================================

if menu == "Adjust":

    st.header("Adjust Stock")

    file = st.file_uploader("Upload Adjustment Excel", type="xlsx")

    if file:

        df = pd.read_excel(file)
        df.columns = [c.strip().replace(" ","_") for c in df.columns]
        df["BIN"] = df["BIN"].astype(str).str.strip()

        if st.button("Process Adjustment"):

            bins = df["BIN"].unique().tolist()
            res = supabase.rpc("get_latest_bins", {"bins": bins}).execute()
            latest = {r["bin_code"]: r for r in res.data}

            rows, errors, seen = [], [], set()

            for row in df.itertuples(index=False):

                bin_code = row.BIN

                if bin_code in seen:
                    errors.append((bin_code, "Duplicate in file"))
                    continue
                seen.add(bin_code)

                l = latest.get(bin_code)

                rows.append({
                    "txid": str(uuid.uuid4()),
                    "transaction_type": "ADJUST_OUT",
                    "bin_code": bin_code,
                    "transaction_date": parse_date(row.DATE),
                    "linked_txid": l["txid"] if l else None,

                    "pcn": l.get("pcn") if l else None,
                    "supplier": l.get("supplier") if l else None,
                    "source": l.get("source") if l else None,
                    "variety": l.get("variety") if l else None,
                    "weight": l.get("weight") if l else None,
                    "rate": l.get("rate") if l else None,
                    "amount": l.get("amount") if l else None,

                    "created_at": datetime.now().isoformat()
                })

            failed_bins = insert_with_error_capture(rows, "Adjust")
            supabase.rpc("refresh_bin_state").execute()

            st.success(f"Adjustment completed. {len(rows) - len(failed_bins)} rows applied.")

            if errors or failed_bins:
                st.warning("Issues encountered")
                err_df = pd.DataFrame(errors, columns=["bin_code", "reason"])
                if failed_bins:
                    fb = pd.DataFrame({"bin_code": failed_bins, "reason": "Database rejected insert"})
                    err_df = pd.concat([err_df, fb], ignore_index=True)
                st.dataframe(err_df)

# ============================================================
# DASHBOARD
# ============================================================

if menu == "Dashboard":

    st.header("Inventory Dashboard")

    colf1, colf2, colf3 = st.columns(3)
    supplier_filter = colf1.text_input("Filter by Supplier (optional)")
    variety_filter = colf2.text_input("Filter by Variety (optional)")
    aging_choice = colf3.selectbox(
        "Aging Period",
        ["All", "0–7 days", "7–14 days", "14–21 days", "21–28 days", "28+ days"]
    )

    # -------------------------
    # Live Inventory
    # -------------------------

    res = supabase.table("bin_current_state").select("*").execute()
    df = pd.DataFrame(res.data)

    if len(df) == 0:
        st.warning("No data available")
    else:
        current = df[df.transaction_type == "RECEIVE"]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Bins In Stock", len(current))
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Total Weight (kg)", round(current.weight.sum(), 2))
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown("<div class='metric-card'>", unsafe_allow_html=True)
            st.metric("Total Value (KES)", round(current.amount.sum(), 2))
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("### Stock Overview")
        left, right = st.columns([1, 1])

        with left:
            st.markdown("#### Stock by Variety")
            fig_var = px.pie(current, names="variety", values="weight")
            st.plotly_chart(fig_var, use_container_width=True)

        with right:
            st.markdown("#### Stock by Supplier")
            supplier_table = (
                current.groupby("supplier")[["weight", "amount"]]
                .sum()
                .reset_index()
                .sort_values("weight", ascending=False)
            )
            supplier_table.columns = ["Supplier", "Total Weight", "Total Value"]
            st.dataframe(supplier_table, use_container_width=True)

    # -------------------------
    # Stock per Supplier
    # -------------------------

    st.markdown("### Supplier Performance")

    stock_res = supabase.table("v_stock_per_supplier").select("*").execute()
    stock_df = pd.DataFrame(stock_res.data)

    if supplier_filter:
        stock_df = stock_df[stock_df["supplier"] == supplier_filter]
    if variety_filter:
        stock_df = stock_df[stock_df["variety"] == variety_filter]

    st.dataframe(stock_df, use_container_width=True)

    # -------------------------
    # PCN Utilisation
    # -------------------------

    st.markdown("### PCN Utilisation")

    util_res = supabase.table("v_pcn_utilisation").select("*").execute()
    util_df = pd.DataFrame(util_res.data)

    if supplier_filter:
        util_df = util_df[util_df["supplier"] == supplier_filter]
    if variety_filter:
        util_df = util_df[util_df["variety"] == variety_filter]
    if aging_choice != "All":
        util_df = util_df[util_df["aging_bucket"] == aging_choice]

    st.dataframe(util_df, use_container_width=True)

# ============================================================
# BIN HISTORY LOOKUP
# ============================================================

if menu == "Bin History Lookup":

    st.header("Bin History Lookup")

    bin_lookup = st.text_input("Enter Bin Code")

    if bin_lookup:

        hist = supabase.table("bin_transactions")\
            .select("*")\
            .eq("bin_code", bin_lookup)\
            .order("created_at")\
            .execute()

        hist_df = pd.DataFrame(hist.data)

        if len(hist_df) == 0:
            st.warning("No history found")
        else:
            st.dataframe(hist_df)
            st.plotly_chart(
                px.scatter(hist_df, x="transaction_date", y="transaction_type"),
                use_container_width=True
            )

# ============================================================
# PCN LOOKUP
# ============================================================

if menu == "PCN Lookup":

    st.header("PCN Lookup")

    pcn_lookup = st.text_input("Enter PCN")

    if pcn_lookup:

        pcn_bins_res = supabase.table("v_pcn_bins")\
            .select("*")\
            .eq("pcn", pcn_lookup)\
            .order("transaction_date")\
            .execute()

        pcn_bins_df = pd.DataFrame(pcn_bins_res.data)

        if len(pcn_bins_df) == 0:
            st.warning("No bins found for this PCN.")
        else:
            st.dataframe(pcn_bins_df)

            total_weight = pcn_bins_df["weight"].sum()
            total_amount = pcn_bins_df["amount"].sum()

            c1, c2 = st.columns(2)
            c1.metric("Total Weight (PCN)", round(total_weight, 2))
            c2.metric("Total Amount (PCN)", round(total_amount, 2))
