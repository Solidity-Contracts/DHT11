from supabase import create_client
import pandas as pd
import streamlit as st
import plotly.express as px
 
supabase = create_client(API_URL, API_KEY)
 
supabaseList = supabase.table('maintable').select('*').execute().data
supabaseList
 
# Build rows into a list instead of appending to DataFrame each time
rows = []
for row in supabaseList:
    row["created_at"] = row["created_at"].split(".")[0]
    row["time"] = row["created_at"].split("T")[1]
    row["date"] = row["created_at"].split("T")[0]
    row["DateTime"] = row["created_at"]
    rows.append(row)
 
# Convert list of dicts directly into DataFrame
df = pd.DataFrame(rows)
 
st.set_page_config(page_title="Dashboard", layout='centered', initial_sidebar_state='collapsed')
 
st.markdown('### Temperature')
fig = px.line(df, x="DateTime", y="temperature", title='', markers=True)
st.plotly_chart(fig, use_container_width=True)
 
st.markdown('### Humidity')
fig = px.line(df, x="DateTime", y="humidity", title='', markers=True)
st.plotly_chart(fig, use_container_width=True)
 
