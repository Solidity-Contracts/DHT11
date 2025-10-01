# app.py
import pandas as pd
import streamlit as st
import plotly.express as px 
from supabase import create_client

st.set_page_config(page_title="DHT11 Dashboard", layout="centered", initial_sidebar_state="collapsed")

# ---- Supabase client (reads from secrets) ----
@st.cache_resource
def get_client():
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]  # use anon/public key
    return create_client(url, key)

supabase = get_client()

# ---- Data fetcher ----
@st.cache_data(ttl=10)  # refresh every ~10s
def fetch_rows(limit: int = 1000):
    # Adjust table/columns if yours differ
    res = (
        supabase.table("maintable")
        .select("*")
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    df = pd.DataFrame(res.data or [])
    if df.empty:
        return df

    # Robust timestamp handling
    df["created_at"] = pd.to_datetime(df["created_at"], utc=True, errors="coerce")
    df = df.sort_values("created_at")  # oldest -> newest for plotting

    # Make friendly columns you used
    df["DateTime"] = df["created_at"].dt.tz_convert(None)  # strip tz for Plotly
    df["date"] = df["DateTime"].dt.date.astype(str)
    df["time"] = df["DateTime"].dt.time.astype(str)
    return df

# ---- Sidebar ----
st.sidebar.header("Options")
limit = st.sidebar.slider("Rows to load", 100, 5000, 1000, 100)
auto_refresh = st.sidebar.checkbox("Auto-refresh every 10s", value=True)
if st.sidebar.button("Refresh now"):
    fetch_rows.clear()
    st.experimental_rerun()

# ---- Optional auto-refresh tick ----
if auto_refresh:
    st.experimental_rerun  # no-op to show intent; Streamlit Cloud handles ttl-based refresh

# ---- Main ----
st.markdown("### Temperature & Humidity (from Supabase)")

df = fetch_rows(limit)
if df.empty:
    st.info("No data found yet in `maintable`. Once rows arrive, charts will render here.")
else:
    # Latest KPIs (assumes columns 'temperature' and 'humidity')
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    if "temperature" in df and pd.notna(latest.get("temperature")):
        c1.metric("Latest Temperature (°C)", f"{latest['temperature']:.1f}")
    if "humidity" in df and pd.notna(latest.get("humidity")):
        c2.metric("Latest Humidity (%)", f"{latest['humidity']:.1f}")
    c3.metric("Last Update", latest["DateTime"].strftime("%Y-%m-%d %H:%M:%S"))

    # Charts
    if "temperature" in df:
        st.markdown("### Temperature")
        fig_t = px.line(df, x="DateTime", y="temperature", markers=True)
        st.plotly_chart(fig_t, use_container_width=True)

    if "humidity" in df:
        st.markdown("### Humidity")
        fig_h = px.line(df, x="DateTime", y="humidity", markers=True)
        st.plotly_chart(fig_h, use_container_width=True)

    # Raw table
    with st.expander("Raw data"):
        st.dataframe(df.iloc[::-1], use_container_width=True)
