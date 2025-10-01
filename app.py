import pandas as pd
import streamlit as st
from supabase import create_client

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="DHT11 Dashboard",
    page_icon="🌡️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# Supabase client (from secrets)
# -----------------------------
@st.cache_resource
def get_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]  # anon/public key only
    return create_client(url, key)

supabase = get_client()

# -----------------------------
# Data fetcher
# -----------------------------
@st.cache_data(ttl=10)  # refresh results every ~10s
def fetch_data(limit=1000):
    res = (
        supabase.table("maintable")  # <-- change if your table name differs
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df

    # Parse timestamps robustly
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df = df.dropna(subset=["created_at"]).sort_values("created_at")  # oldest -> newest

    # Convenience column for charts/labels
    df["DateTime"] = df["created_at"].dt.tz_convert(None)  # strip timezone for charts
    return df

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.header("Options")
limit = st.sidebar.slider("Rows to load", min_value=100, max_value=5000, value=1000, step=100)
if st.sidebar.button("Refresh now"):
    fetch_data.clear()
    st.experimental_rerun()

# -----------------------------
# Main UI
# -----------------------------
st.title("🌡️ DHT11 Live Dashboard (Supabase → Streamlit)")

df = fetch_data(limit)
if df.empty:
    st.info("No data found in `maintable` yet. Once your Arduino writes rows to Supabase, they’ll show up here.")
else:
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    if "temperature" in df.columns and pd.notna(latest.get("temperature")):
        c1.metric("Latest Temperature (°C)", f"{latest['temperature']:.1f}")
    if "humidity" in df.columns and pd.notna(latest.get("humidity")):
        c2.metric("Latest Humidity (%)", f"{latest['humidity']:.1f}")
    c3.metric("Last Update", latest["DateTime"].strftime("%Y-%m-%d %H:%M:%S"))

    # ---- Charts (built-in) ----
    st.subheader("Temperature")
    if "temperature" in df.columns:
        st.line_chart(
            df.set_index("DateTime")[["temperature"]],
            use_container_width=True,
        )
    else:
        st.warning("Column `temperature` not found.")

    st.subheader("Humidity")
    if "humidity" in df.columns:
        st.line_chart(
            df.set_index("DateTime")[["humidity"]],
            use_container_width=True,
        )
    else:
        st.warning("Column `humidity` not found.")

    # Raw data
    with st.expander("Raw data"):
        st.dataframe(df.iloc[::-1], use_container_width=True)
