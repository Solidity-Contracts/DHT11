import pandas as pd
import streamlit as st
from supabase import create_client

st.set_page_config(page_title="DHT11 Live Dashboard", page_icon="🌡️", layout="wide")

# --- Connect to Supabase (use Streamlit secrets) ---
@st.cache_resource
def get_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)

supabase = get_client()

# --- Data fetcher with caching + auto-refresh window ---
@st.cache_data(ttl=10)  # refresh query results every 10 seconds
def fetch_readings(limit: int = 1000, device_id: str | None = None) -> pd.DataFrame:
    q = supabase.table("dht_readings").select("*").order("created_at", desc=True).limit(limit)
    if device_id:
        q = q.eq("device_id", device_id)
    res = q.execute()
    df = pd.DataFrame(res.data)
    if not df.empty:
        # ensure proper dtypes and sorting oldest->newest for charts
        df["created_at"] = pd.to_datetime(df["created_at"])
        df = df.sort_values("created_at")
    return df

# --- Sidebar controls ---
st.sidebar.header("Filters")
device_id = st.sidebar.text_input("Device ID (optional)")
limit = st.sidebar.slider("Rows to load", min_value=100, max_value=5000, value=1000, step=100)
st.sidebar.caption("Data auto-refreshes every ~10s")

# Manual refresh button (busts cache immediately)
if st.sidebar.button("Refresh now"):
    fetch_readings.clear()  # clear cache
    st.experimental_rerun()

# --- Fetch data ---
df = fetch_readings(limit=limit, device_id=device_id)

st.title("🌡️ DHT11 Live Dashboard")
st.write("Streaming readings from Supabase.")

# --- Top KPIs ---
if df.empty:
    st.info("No data found yet. Once your Arduino starts sending rows to Supabase, they’ll appear here.")
else:
    latest = df.iloc[-1]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Latest Temperature (°C)", f"{latest['temperature_c']:.1f}")
    col2.metric("Latest Humidity (%)", f"{latest['humidity']:.1f}")
    col3.metric("Last Update", latest['created_at'].strftime("%Y-%m-%d %H:%M:%S"))
    col4.metric("Rows Loaded", len(df))

    # --- Charts ---
    ts_cols = ["temperature_c", "humidity"]
    plottable = df.set_index("created_at")[ts_cols]

    st.subheader("Time Series")
    st.line_chart(plottable)  # simple and fast

    # --- Data table ---
    with st.expander("Raw data"):
        st.dataframe(df[::-1], use_container_width=True)

    # --- Optional stats ---
    st.subheader("Summary (last loaded window)")
    stats = (
        df.assign(hour=df["created_at"].dt.floor("H"))
          .groupby("hour")[["temperature_c", "humidity"]]
          .agg(["min", "mean", "max"])
    )
    st.dataframe(stats, use_container_width=True)

