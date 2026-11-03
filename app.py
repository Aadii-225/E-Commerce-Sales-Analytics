from pathlib import Path
from io import BytesIO
import re
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="E-commerce Analytics", page_icon="📊", layout="wide")
DATA_FILE = Path("data/sales.csv")

COLUMN_ALIASES = {
    "Date": [
        "date", "orderdate", "transactiondate", "saledate", "invoicedate",
        "time", "timestamp", "datetime"
    ],
    "Product": [
        "product", "productname", "item", "itemname", "sku", "skucode",
        "style", "title", "producttitle", "description", "designno"
    ],
    "Category": [
        "category", "productcategory", "categoryname", "dept", "department",
        "subcategory", "segment", "type"
    ],
    "Region": [
        "region", "shipstate", "state", "province", "country", "shipcity",
        "city", "zone", "location", "territory", "market"
    ],
    "Sales": [
        "sales", "amount", "total", "totalsales", "totalamount", "revenue",
        "orderamount", "price", "unitprice", "grandtotal", "netamount"
    ],
    "Cost": [
        "cost", "costprice", "cogs", "expenses", "expense", "purchaseprice", "unitcost"
    ],
    "Profit": [
        "profit", "netprofit", "margin", "earnings"
    ],
    "Quantity": [
        "quantity", "qty", "count", "units", "volume"
    ],
    "Order_ID": [
        "orderid", "invoice", "invoiceno", "invoiceid", "transactionid", "id", "ordernumber"
    ],
    "Customer": [
        "customer", "customername", "customerid", "custid", "buyer", "user", "userid", "client"
    ],
}


def norm_str(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def auto_detect_columns(columns):
    clean_cols = {col: norm_str(col) for col in columns}
    mapping = {}
    for canonical, aliases in COLUMN_ALIASES.items():
        norm_aliases = [norm_str(a) for a in aliases]
        for orig_col, norm_col in clean_cols.items():
            if norm_col in norm_aliases:
                mapping[canonical] = orig_col
                break
    return mapping


def clean_numeric(series):
    if pd.api.types.is_numeric_dtype(series):
        return pd.to_numeric(series, errors="coerce")
    cleaned = (
        series.astype(str)
        .str.replace(r"[^\d.-]", "", regex=True)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def parse_csv(file_obj_or_path):
    """Directly parses CSV with multiple encodings without stale caching."""
    for enc in ("utf-8", "utf-8-sig", "latin1", "cp1252", "iso-8859-1"):
        try:
            if isinstance(file_obj_or_path, (str, Path)):
                return pd.read_csv(file_obj_or_path, encoding=enc, low_memory=False)
            else:
                file_obj_or_path.seek(0)
                return pd.read_csv(file_obj_or_path, encoding=enc, low_memory=False)
        except (UnicodeDecodeError, Exception):
            continue
    if isinstance(file_obj_or_path, (str, Path)):
        return pd.read_csv(file_obj_or_path, encoding_errors="replace", low_memory=False)
    file_obj_or_path.seek(0)
    return pd.read_csv(file_obj_or_path, encoding_errors="replace", low_memory=False)


@st.cache_data
def load_sample_csv():
    if not DATA_FILE.exists():
        return pd.DataFrame()
    return parse_csv(DATA_FILE)


@st.cache_data
def load_mysql_data():
    from database import fetch_sales
    return fetch_sales()


def clean_and_standardize_data(raw_df, col_mapping, cost_ratio=0.70):
    df = pd.DataFrame()

    # 1. Date
    date_col = col_mapping.get("Date")
    if not date_col or date_col not in raw_df.columns:
        raise ValueError("A valid Date column is required. Please select your Date column.")
    df["Date"] = pd.to_datetime(raw_df[date_col], errors="coerce")

    # 2. Sales / Amount
    sales_col = col_mapping.get("Sales")
    if not sales_col or sales_col not in raw_df.columns:
        raise ValueError("A valid Sales/Amount column is required. Please select your Sales column.")
    df["Sales"] = clean_numeric(raw_df[sales_col])

    # 3. Product
    prod_col = col_mapping.get("Product")
    if prod_col and prod_col in raw_df.columns:
        df["Product"] = raw_df[prod_col].astype("string").str.strip().fillna("Unknown Product")
    else:
        df["Product"] = "General Product"

    # 4. Region
    reg_col = col_mapping.get("Region")
    if reg_col and reg_col in raw_df.columns:
        df["Region"] = raw_df[reg_col].astype("string").str.strip().fillna("Unspecified")
    else:
        df["Region"] = "All Regions"

    # 5. Category
    cat_col = col_mapping.get("Category")
    if cat_col and cat_col in raw_df.columns:
        df["Category"] = raw_df[cat_col].astype("string").str.strip().fillna(df["Product"])
    else:
        df["Category"] = df["Product"]

    # 6. Quantity
    qty_col = col_mapping.get("Quantity")
    if qty_col and qty_col in raw_df.columns:
        df["Quantity"] = clean_numeric(raw_df[qty_col]).fillna(1).clip(lower=1)
    else:
        df["Quantity"] = 1

    # 7. Customer
    cust_col = col_mapping.get("Customer")
    if cust_col and cust_col in raw_df.columns:
        df["Customer"] = raw_df[cust_col].astype("string").str.strip().fillna("Customer")
    else:
        df["Customer"] = "Customer"

    # 8. Order_ID
    ord_col = col_mapping.get("Order_ID")
    if ord_col and ord_col in raw_df.columns:
        order_s = raw_df[ord_col].astype("string").str.strip()
        df["Order_ID"] = order_s.replace("", None).fillna(pd.Series([f"ORD-{i + 1:05d}" for i in range(len(raw_df))]))
    else:
        df["Order_ID"] = [f"ORD-{i + 1:05d}" for i in range(len(raw_df))]

    # 9. Cost & Profit
    cost_col = col_mapping.get("Cost")
    profit_col = col_mapping.get("Profit")
    if cost_col and cost_col in raw_df.columns:
        df["Cost"] = clean_numeric(raw_df[cost_col]).fillna(df["Sales"] * cost_ratio)
        df["Profit"] = df["Sales"] - df["Cost"]
    elif profit_col and profit_col in raw_df.columns:
        df["Profit"] = clean_numeric(raw_df[profit_col]).fillna(df["Sales"] * (1 - cost_ratio))
        df["Cost"] = df["Sales"] - df["Profit"]
    else:
        df["Cost"] = (df["Sales"] * cost_ratio).round(2)
        df["Profit"] = df["Sales"] - df["Cost"]

    # Drop unparseable records (must have valid Date and Sales >= 0)
    df = df.dropna(subset=["Date", "Sales"]).copy()
    df = df[df["Sales"] >= 0].copy()

    return df


# ------------------- UI Layout -------------------
st.title("📊 E-commerce Sales Analytics")
st.caption("Sales performance, profitability and customer insights")

st.sidebar.header("📁 Data Source")
source = st.sidebar.radio(
    "Choose data source",
    ["📂 Upload CSV", "🧪 Sample CSV", "🐬 MySQL"],
    index=0
)

cost_ratio = 0.70
active_dataset_label = "Sample Data"
uploaded_filename = None
raw = pd.DataFrame()
df = pd.DataFrame()

try:
    if source == "📂 Upload CSV":
        uploaded = st.sidebar.file_uploader("Upload your sales CSV file", type=["csv"], key="csv_uploader")
        if uploaded is None:
            st.info("👈 **Please upload a CSV file from the sidebar** to start analyzing your data.")
            st.markdown("""
            ### 💡 Tips for uploading CSV:
            - Any sales CSV from Amazon, Flipkart, Shopify, WooCommerce, or custom ERP is supported.
            - Required fields: **Date** and **Sales / Amount**.
            - Optional fields: Product, Category, Region/State, Quantity, Cost.
            - If Cost is missing, the dashboard can automatically estimate profit based on margin percentage.
            """)
            st.stop()

        uploaded_filename = uploaded.name
        active_dataset_label = f"Uploaded File: {uploaded_filename}"
        
        # Read uploaded file freshly
        raw = parse_csv(uploaded)
        if raw.empty:
            st.error("The uploaded CSV file has no rows.")
            st.stop()

        # Auto-detect column mapping
        detected = auto_detect_columns(raw.columns)
        available_cols = ["(None)"] + list(raw.columns)

        with st.sidebar.expander("⚙️ CSV Column Mapping", expanded=not ("Date" in detected and "Sales" in detected)):
            st.caption(f"Configuring columns for `{uploaded_filename}`:")

            def get_index(canonical, default_col):
                if canonical in detected and detected[canonical] in raw.columns:
                    return available_cols.index(detected[canonical])
                return available_cols.index(default_col) if default_col in available_cols else 0

            date_col = st.selectbox(
                "Date column *",
                raw.columns,
                index=list(raw.columns).index(detected["Date"]) if "Date" in detected else 0
            )
            sales_col = st.selectbox(
                "Sales / Amount column *",
                raw.columns,
                index=list(raw.columns).index(detected["Sales"]) if "Sales" in detected else 0
            )
            prod_col = st.selectbox(
                "Product / Item column",
                available_cols,
                index=get_index("Product", "(None)")
            )
            reg_col = st.selectbox(
                "Region / State column",
                available_cols,
                index=get_index("Region", "(None)")
            )
            cat_col = st.selectbox(
                "Category column",
                available_cols,
                index=get_index("Category", "(None)")
            )
            qty_col = st.selectbox(
                "Quantity column",
                available_cols,
                index=get_index("Quantity", "(None)")
            )
            cost_col = st.selectbox(
                "Cost column (Optional)",
                available_cols,
                index=get_index("Cost", "(None)")
            )

            if cost_col == "(None)":
                margin_pct = st.slider("Estimated Profit Margin %", min_value=5, max_value=80, value=30)
                cost_ratio = (100 - margin_pct) / 100.0

            col_mapping = {
                "Date": date_col,
                "Sales": sales_col,
                "Product": prod_col if prod_col != "(None)" else None,
                "Region": reg_col if reg_col != "(None)" else None,
                "Category": cat_col if cat_col != "(None)" else None,
                "Quantity": qty_col if qty_col != "(None)" else None,
                "Cost": cost_col if cost_col != "(None)" else None,
            }

        df = clean_and_standardize_data(raw, col_mapping, cost_ratio=cost_ratio)

    elif source == "🐬 MySQL":
        active_dataset_label = "MySQL Database (`ecommerce_analytics.sales`)"
        if st.sidebar.button("🔄 Refresh MySQL Data"):
            st.cache_data.clear()
            st.rerun()
        raw = load_mysql_data()
        if raw.empty:
            st.warning("No data found in MySQL. Run: `python import_to_mysql.py`")
            st.stop()
        detected = auto_detect_columns(raw.columns)
        df = clean_and_standardize_data(raw, detected, cost_ratio=0.70)

    else:  # 🧪 Sample CSV
        active_dataset_label = "Sample Synthetic Dataset (`data/sales.csv`)"
        raw = load_sample_csv()
        if raw.empty:
            st.warning("No sample data found. Run: `python data_generator.py`")
            st.stop()
        detected = auto_detect_columns(raw.columns)
        df = clean_and_standardize_data(raw, detected, cost_ratio=0.70)

except Exception as exc:
    st.error(f"❌ Error loading data: {exc}")
    st.stop()

if df.empty:
    st.warning("⚠️ No valid records were found after data cleaning.")
    st.stop()

# ------------------- Filters -------------------
st.sidebar.divider()
st.sidebar.header("🔍 Filters")
regions = sorted(df["Region"].dropna().unique().tolist())
products = sorted(df["Product"].dropna().unique().tolist())

default_regions = regions if len(regions) <= 20 else []
default_products = products if len(products) <= 20 else []

selected_regions = st.sidebar.multiselect(
    "Filter by Region", regions, default=default_regions,
    placeholder="All regions included"
)
selected_products = st.sidebar.multiselect(
    "Filter by Product", products, default=default_products,
    placeholder="All products included"
)

min_date = df["Date"].min().date()
max_date = df["Date"].max().date()

date_input_res = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if isinstance(date_input_res, (tuple, list)):
    if len(date_input_res) == 2:
        start_date, end_date = date_input_res
    elif len(date_input_res) == 1:
        start_date = end_date = date_input_res[0]
    else:
        start_date, end_date = min_date, max_date
else:
    start_date = end_date = date_input_res

filtered = df[df["Date"].dt.date.between(start_date, end_date)].copy()
if selected_regions:
    filtered = filtered[filtered["Region"].isin(selected_regions)]
if selected_products:
    filtered = filtered[filtered["Product"].isin(selected_products)]

if filtered.empty:
    st.warning("No records match the selected filters.")
    st.stop()

# ------------------- Top Active Dataset Banner -------------------
if source == "📂 Upload CSV" and uploaded_filename:
    st.success(f"📂 **Active Dataset**: `{uploaded_filename}` &nbsp;|&nbsp; **Records**: {len(filtered):,} of {len(df):,} &nbsp;|&nbsp; **Date Range**: {start_date} to {end_date}")
    with st.expander(f"👀 Preview Raw Uploaded File (`{uploaded_filename}`) — First 5 Rows", expanded=False):
        st.dataframe(raw.head(5), width="stretch")
elif source == "🐬 MySQL":
    st.info(f"🐬 **Active Dataset**: MySQL Database &nbsp;|&nbsp; **Records**: {len(filtered):,} &nbsp;|&nbsp; **Date Range**: {start_date} to {end_date}")
else:
    st.info(f"🧪 **Active Dataset**: Built-in Sample Data (`data/sales.csv`) &nbsp;|&nbsp; **Records**: {len(filtered):,} &nbsp;|&nbsp; **Date Range**: {start_date} to {end_date}")

# ------------------- Metrics -------------------
revenue = filtered["Sales"].sum()
profit = filtered["Profit"].sum()
orders = filtered["Order_ID"].nunique()
customers = filtered["Customer"].nunique()
margin = profit / revenue * 100 if revenue else 0

a, b, c, d = st.columns(4)
a.metric("Total Revenue", f"₹{revenue:,.0f}")
b.metric("Total Profit", f"₹{profit:,.0f}")
c.metric("Total Orders", f"{orders:,}")
d.metric("Profit Margin", f"{margin:.1f}%")
st.divider()

# ------------------- Visualizations -------------------
left, right = st.columns(2)
with left:
    st.subheader("Monthly Revenue Trend")
    monthly = filtered.set_index("Date").resample("MS")["Sales"].sum().rename("Revenue").reset_index()
    fig = px.line(monthly, x="Date", y="Revenue", markers=True, title="Revenue Over Time")
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Product Performance")
    product_sales = filtered.groupby("Product", as_index=False).agg(
        Sales=("Sales", "sum"), Profit=("Profit", "sum")
    ).sort_values("Sales", ascending=False).head(10)
    chart_title = "Top 10 Products by Revenue" if filtered["Product"].nunique() > 10 else "Revenue by Product"
    fig = px.bar(product_sales, x="Product", y="Sales", color="Product", title=chart_title)
    st.plotly_chart(fig, width="stretch")

left, right = st.columns(2)
with left:
    st.subheader("Regional Revenue")
    region_sales = filtered.groupby("Region", as_index=False)["Sales"].sum().sort_values("Sales", ascending=False)
    if len(region_sales) > 8:
        top_reg = region_sales.head(7)
        other_sum = region_sales.iloc[7:]["Sales"].sum()
        region_sales = pd.concat([top_reg, pd.DataFrame([{"Region": "Other", "Sales": other_sum}])], ignore_index=True)
    fig = px.pie(region_sales, names="Region", values="Sales", hole=0.4, title="Revenue Share by Region")
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Category Profitability")
    category_profit = filtered.groupby("Category", as_index=False)["Profit"].sum().sort_values("Profit", ascending=False).head(10)
    fig = px.bar(category_profit, x="Category", y="Profit", color="Category", title="Profit by Category")
    st.plotly_chart(fig, width="stretch")

# ------------------- Table & Export -------------------
st.divider()
st.subheader("📄 Sales Data Records")
display_columns = [
    col for col in ["Order_ID", "Date", "Product", "Category", "Region",
                    "Customer", "Quantity", "Sales", "Cost", "Profit"]
    if col in filtered.columns
]
st.dataframe(
    filtered[display_columns].sort_values("Date", ascending=False),
    width="stretch", hide_index=True
)
st.download_button(
    "⬇️ Download Filtered CSV",
    data=filtered[display_columns].to_csv(index=False).encode("utf-8"),
    file_name=f"filtered_{uploaded_filename or 'sales_report'}.csv", mime="text/csv",
)
