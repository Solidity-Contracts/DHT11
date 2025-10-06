import pandas as pd, streamlit as st
from supabase import create_client

st.set_page_config(page_title="Sensor Readings Sanity", layout="centered")

@st.cache_resource
def client():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_ANON_KEY"])

@st.cache_data(ttl=10)
def fetch(limit=200):
    res = (client().table("sensor_readings")
           .select("*")
           .order("created_at", desc=True)
           .limit(limit).execute())
    return pd.DataFrame(res.data or [])

df = fetch()
if df.empty:
    st.warning("No rows found in sensor_readings.")
else:
    st.write("Latest rows:", df.head(10))
    st.metric("Core (latest)", f"{df.iloc[0]['core_c']:.2f}")
    st.metric("Peripheral (latest)", f"{df.iloc[0]['peripheral_c']:.2f}")
