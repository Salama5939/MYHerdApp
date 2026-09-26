import streamlit as st
import pandas as pd
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from supabase import create_client

st.set_page_config(page_title="Standalone Executive Report Test", layout="wide")

st.title("🧪 Standalone Executive Report Test Module")
st.markdown("---")

# 1. Direct standalone environment check & client creation
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")

# Fallback to st.secrets if running locally via streamlit run
try:
    if not url:
        url = st.secrets.get("SUPABASE_URL")
    if not key:
        key = st.secrets.get("SUPABASE_KEY")
except Exception:
    pass

if not url or not key:
    st.error("🚨 SUPABASE_URL or SUPABASE_KEY missing in environment or secrets!")
    st.stop()


@st.cache_resource
def get_standalone_client(u, k):
    return create_client(u, k)


supabase_client = get_standalone_client(url, key)

# 2. Test fetching the biological asset valuation view directly
st.subheader("1. Testing Biological Asset Valuation View")
try:
    response = (
        supabase_client.table("view_biological_asset_valuation").select("*").execute()
    )
    if response.data:
        df_bio = pd.DataFrame(response.data)
        st.success(
            f"✅ Successfully fetched {len(df_bio)} rows from biological asset valuation!"
        )
        st.dataframe(df_bio, use_container_width=True)

        total_val = df_bio["total_asset_value"].sum()
        total_head = df_bio["total_headcount"].sum()
        c1, c2 = st.columns(2)
        c1.metric("Total Headcount", f"{total_head:,}")
        c2.metric("Total Capital Value", f"{total_val:,.2f} EGP")
    else:
        st.warning("⚠️ Query executed successfully, but returned 0 rows.")
        st.write("Raw response:", response)
except Exception as e:
    st.error(f"❌ API Error encountered: {e}")

st.markdown("---")

# 3. Test fetching Tag-Level Unit Economics
st.subheader("2. Testing Tag-Level Unit Economics View")
try:
    response_tag = (
        supabase_client.table("view_tag_unit_economics").select("*").limit(10).execute()
    )
    if response_tag.data:
        df_tag = pd.DataFrame(response_tag.data)
        st.success(
            f"✅ Successfully fetched sample unit economics data ({len(df_tag)} rows shown)."
        )
        st.dataframe(df_tag, use_container_width=True)
    else:
        st.warning("⚠️ Unit economics view returned 0 rows.")
except Exception as e:
    st.error(f"❌ Unit Economics Error: {e}")

st.markdown("---")

# 4. Test fetching Feed Inventory Audit
st.subheader("3. Testing Feed Inventory Audit View")
try:
    response_feed = (
        supabase_client.table("view_feed_inventory_audit").select("*").execute()
    )
    if response_feed.data:
        df_feed = pd.DataFrame(response_feed.data)
        st.success(
            f"✅ Successfully fetched feed inventory audit data ({len(df_feed)} rows)."
        )
        st.dataframe(df_feed, use_container_width=True)
    else:
        st.warning("⚠️ Feed audit view returned 0 rows.")
except Exception as e:
    st.error(f"❌ Feed Audit Error: {e}")
