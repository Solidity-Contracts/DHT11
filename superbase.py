import pandas as pd
import streamlit as st

# ---------- Page ----------
st.set_page_config(page_title="DHT11 Dashboard", page_icon="🌡️", layout="centered")

# ---------- Show env for sanity ----------
st.caption("Bootstrapping…")
st.write({
    "streamlit": st.__version__,
})

# ---------- Try to import SDK ----------
try:
    from supabase import create_client
except Exception as e:
    st.error("Failed to import `supabase` package. Did requirements.txt install?")
    st.exception(e)
    st.stop()

# ---------- Connect to Supabase ----------
@st.cache_resource
def get_client():
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["anon_key"]
    except Exception as e:
        st.error("Missing secrets. Add them in App → Settings → Secrets.")
        st.code("""[supabase]\nurl = "https://YOUR-PROJECT-REF.supabase.co"\nanon_key = "YOUR-ANON-KEY" """)
        st.exception(e)
        st.stop()
    try:
        return create_client(url, key)
    except Exception as e:
        st.error("create_client(url, key) failed. Check URL (no /rest/v1) and anon key.")
        st.write({"url": url})
        st.exception(e)
        st.stop()

supabase = get_client()

# ---------- Test a tiny query first ----------
st.subheader("Connection test")
try:
    test = supabase.table("maintable").select("created_at").order("created_at", desc=True).limit(1).execute()
    st.success("Supabase client OK ✅")
    st.write({"rows_returned": len(test.data)})
except Exception as e:
    st.error("Query failed. Most common causes:")
    st.markdown("- RLS denies `SELECT` to `anon`.\n- Table name is wrong.\n- Columns differ.\n- Project URL/key incorrect.")
    st.code("""
-- Enable & allow public SELECT (demo)
alter table public.maintable enable row level security;
create policy "public read" on public.maintable for select to anon using (true);
""")
    st.exception(e)
    st.stop()

# ---------- If we got here, build the dashboard ----------
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
    st.info("No data yet in table `maintable`.")
else:
    latest = df.iloc[-1]
    c1, c2, c3 = st.columns(3)
    if "temperature" in df.columns and pd.notna(latest.get("temperature")):
        c1.metric("Latest Temperature (°C)", f"{latest['temperature']:.1f}")
    if "humidity" in df.columns and pd.notna(latest.get("humidity")):
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
