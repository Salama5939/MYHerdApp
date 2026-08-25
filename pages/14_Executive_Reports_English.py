import streamlit as st
import os
import subprocess

st.set_page_config(page_title="Executive Reports Hub", page_icon="📊", layout="wide")

st.title("📊 Executive Reports Hub & Board Analytics")
st.markdown(
    "Generate, review, and download professional PDF strategic reports powered live by your Supabase database."
)

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("🎯 Master Report Generator")
    st.markdown(
        "Click the button below to execute the master script and refresh all 6 strategic management reports simultaneously with the latest Supabase data."
    )

    if st.button("🚀 Generate All 6 Executive Reports", type="primary"):
        with st.spinner("Connecting to Supabase and compiling reports..."):
            try:
                result = subprocess.run(
                    ["python", "generate_all_reports.py"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                st.success(
                    "✅ All 6 executive reports successfully generated and updated!"
                )
                st.code(result.stdout)
            except subprocess.CalledProcessError as e:
                st.error(f"❌ Error generating reports: {e.stderr}")

with col2:
    st.subheader("📂 Report Archive")
    st.markdown("Download active PDF reports:")

    reports_dir = "reports"
    if os.path.exists(reports_dir):
        pdf_files = [f for f in os.listdir(reports_dir) if f.endswith(".pdf")]
        for pdf in sorted(pdf_files):
            file_path = os.path.join(reports_dir, pdf)
            with open(file_path, "rb") as f:
                st.download_button(
                    label=f"📥 {pdf}",
                    data=f,
                    file_name=pdf,
                    mime="application/pdf",
                    key=pdf,
                )
    else:
        st.info("No reports generated yet. Click 'Generate All' on the left.")

st.markdown("---")
st.subheader("📋 Summary of Executive Reports Suite")
st.markdown("""
1. **Breakeven Purchase Price & Restocking Schedule:** Calculates maximum allowable purchase prices for external feeder lambs based on live feed mix costs ($13.21/kg).
2. **Production Line Profitability Analysis:** Segregates active fattening pens, completed finishing batches, and the general breeding herd.
3. **Feed Conversion Ratio (FCR) & Cost-Per-Kg:** Evaluates nutritional efficiency, feed consumption, and cost per kg gained across finishing stock.
4. **Biological Asset Valuation & Flock Dynamics:** Audits flock census, active breeding capital, births, and inventory turnover.
5. **Reproductive & Mortality Leakage Dashboard:** Tracks lambing success rates, breeding ewe performance, and biosecurity mortality leaks.
6. **Breakeven & Optimal Off-Take Timing Calculator:** Monitors average daily gain (ADG) and days on feed to determine the optimal market selling window.
""")
