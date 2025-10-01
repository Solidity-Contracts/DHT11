import pandas as pd
import streamlit as st
import plotly.express as px
from supabase import create_client

# ----------------------------------------------------
# Streamlit page setup
# ----------------------------------------------------
st.set_page_config(
    page_title="DHT11 Dashboard",
    page_icon="🌡️",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ----------------------------------------------------
# Supabase connection (using secrets)
# ----------------------------------------------------
@st.cache_resource
def get_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)

supabase = get_client()

# ----------------------------------------------------
# Fetch data from Supabase
# ----------------------------------------------------
@st.cache_data(ttl=10)   # cache refresh every 10s
def fetch_data(limit=1000):
    res = (
        supabase.table("maintable")        # <-- change table name if needed
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df

    # Parse timestamps
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df = df.sort_values("created_at")

    # Add helper columns
    df["DateTime"] = df["created_at"].dt.tz_convert(None)   # strip timezone
    df["date"] = df["DateTime"].dt.date.astype(str)
    df["time"] = df["DateTime"].dt.time.astype(str)
    return df

# ----------------------------------------------------
# Sidebar controls
# ----------------------------------------------------
st.sidebar.header("Options")
limit = st.sidebar.slider("Rows to load", 100, 5000, 1000, 100)
if st.sidebar.button("Refresh now"):
    fetch_data.clear()
    st.experimental_rerun()

# ----------------------------------------------------
# Main UI
# ----------------------------------------------------
st.title("🌡️ DHT11 Live Dashboard")

df = fetch_data(limit)
if df.empty:
    st.info("No data found in Supabase yet. Once your Arduino uploads rows, they’ll appear here.")
else:
    latest = df.iloc[-1]

    # Latest readings
    c1, c2, c3 = st.columns(3)
    if "temperature" in df:
        c1.metric("Latest Temperature (°C)", f"{latest['temperature']:.1f}")
    if "humidity" in df:
        c2.metric("Latest Humidity (%)", f"{latest['humidity']:.1f}")
    c3.metric("Last Update", latest["DateTime"].strftime("%Y-%m-%d %H:%M:%S"))

    # Temperature chart
    if "temperature" in df:
        st.markdown("### Temperature")
        fig_t = px.line(df, x="DateTime", y="temperature", markers=True)
        st.plotly_chart(fig_t, use_container_width=True)

    # Humidity chart
    if "humidity" in df:
        st.markdown("### Humidity")
        fig_h = px.line(df, x="DateTime", y="humidity", markers=True)
        st.plotly_chart(fig_h, use_container_width=True)

    # Raw data
    with st.expander("Raw data"):
        st.dataframe(df[::-1], use_container_width=True)
