import pandas as pd
import streamlit as st
try:
    from supabase import create_client
except ImportError:
    st.error("Supabase package not installed. Run: pip install supabase")
    st.stop()

st.set_page_config(page_title="DHT11 Dashboard", page_icon="🌡️", layout="centered")

@st.cache_resource
def get_client():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
        return create_client(url, key)
    except KeyError:
        st.error("Supabase secrets not configured. Check your secrets.toml file")
        return None
    except Exception as e:
        st.error(f"Error connecting to Supabase: {e}")
        return None

supabase = get_client()

st.set_page_config(page_title="DHT11 Dashboard", page_icon="🌡️", layout="centered")

@st.cache_data(ttl=10)
def fetch_data(limit=1000):
    res = (supabase.table("maintable").select("*").order("created_at", desc=True).limit(limit).execute())
    df = pd.DataFrame(res.data or [])
    if df.empty: return df
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df = df.dropna(subset=["created_at"]).sort_values("created_at")
    df["DateTime"] = df["created_at"].dt.tz_convert(None)
    return df

st.title("🌡️ DHT11 Live Dashboard")

df = fetch_data(limit=1000)
if df.empty:
    st.info("No data yet in Supabase table `maintable`.")
else:
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    if "temperature" in df.columns: c1.metric("Latest Temperature (°C)", f"{latest['temperature']:.1f}")
    if "humidity" in df.columns:    c2.metric("Latest Humidity (%)", f"{latest['humidity']:.1f}")
    c3.metric("Last Update", latest["DateTime"].strftime("%Y-%m-%d %H:%M:%S"))

    if "temperature" in df.columns:
        st.subheader("Temperature")
        st.line_chart(df.set_index("DateTime")[["temperature"]], use_container_width=True)
    if "humidity" in df.columns:
        st.subheader("Humidity")
        st.line_chart(df.set_index("DateTime")[["humidity"]], use_container_width=True)

    with st.expander("Raw Data"):
        st.dataframe(df.iloc[::-1], use_container_width=True)
