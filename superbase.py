import pandas as pd
import streamlit as st

# Debug: Show what's happening
st.title("🌡️ DHT11 Live Dashboard - Debug Mode")

try:
    from supabase import create_client
    st.success("✅ Supabase imported successfully!")
except ImportError as e:
    st.error(f"❌ Supabase import failed: {e}")
    st.info("Trying to install supabase...")
    
    # This won't work on Streamlit Cloud but helps diagnose
    import sys
    import subprocess
    st.write(f"Python executable: {sys.executable}")
    st.write(f"Python path: {sys.path}")
    st.stop()

# Check secrets
if "supabase" not in st.secrets:
    st.error("❌ No supabase secrets found!")
    st.write("Available secret sections:", list(st.secrets.keys()))
else:
    st.success("✅ Supabase secrets found!")

@st.cache_resource
def get_client():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
        client = create_client(url, key)
        st.success("✅ Supabase client created successfully!")
        return client
    except Exception as e:
        st.error(f"❌ Failed to create Supabase client: {e}")
        return None

supabase = get_client()

if supabase:
    try:
        # Test the connection
        result = supabase.table("maintable").select("count", count="exact").execute()
        st.success("✅ Connected to Supabase successfully!")
        
        # Your existing dashboard code here
        @st.cache_data(ttl=10)
        def fetch_data(limit=1000):
            res = supabase.table("maintable").select("*").order("created_at", desc=True).limit(limit).execute()
            df = pd.DataFrame(res.data or [])
            if df.empty: return df
            df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
            df = df.dropna(subset=["created_at"]).sort_values("created_at")
            df["DateTime"] = df["created_at"].dt.tz_convert(None)
            return df

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
                
    except Exception as e:
        st.error(f"❌ Database query failed: {e}")
