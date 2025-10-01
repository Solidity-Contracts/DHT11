import pandas as pd
import streamlit as st
from st_supabase_connection import SupabaseConnection

st.set_page_config(page_title="DHT11 Dashboard", page_icon="🌡️", layout="centered")

# Initialize connection using Streamlit's native connection
conn = st.connection("supabase", type=SupabaseConnection)

@st.cache_data(ttl=10)
def fetch_data(limit=1000):
    try:
        # Perform query using the new connection
        result = conn.query("*", table="maintable", ttl="10m").execute()
        
        if hasattr(result, 'data'):
            df = pd.DataFrame(result.data or [])
        else:
            df = pd.DataFrame(result or [])
        
        if df.empty:
            return df
            
        # Convert datetime
        df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
        df = df.dropna(subset=["created_at"]).sort_values("created_at")
        df["DateTime"] = df["created_at"].dt.tz_convert(None)
        
        return df
        
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

st.title("🌡️ DHT11 Live Dashboard")

df = fetch_data(limit=1000)

if df.empty:
    st.info("No data yet in Supabase table `maintable`.")
else:
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    if "temperature" in df.columns: 
        c1.metric("Latest Temperature (°C)", f"{latest['temperature']:.1f}")
    if "humidity" in df.columns:    
        c2.metric("Latest Humidity (%)", f"{latest['humidity']:.1f}")
    c3.metric("Last Update", latest["DateTime"].strftime("%Y-%m-%d %H:%M:%S"))

    if "temperature" in df.columns:
        st.subheader("Temperature")
        st.line_chart(df.set_index("DateTime")[["temperature"]], use_container_width=True)
    if "humidity" in df.columns:
        st.subheader("Humidity")
        st.line_chart(df.set_index("DateTime")[["humidity"]], use_container_width=True)

    with st.expander("Raw Data"):
        st.dataframe(df.iloc[::-1], use_container_width=True)
