import streamlit as st
import os
import subprocess
import sys

# 📂 Path management for imports
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from translations import init_language_state, apply_rtl_styling

st.set_page_config(page_title="Executive Reports Hub", page_icon="📑", layout="wide")

# Initialize language and apply RTL layout if Arabic is active
init_language_state()
apply_rtl_styling()

is_arabic = st.session_state.get("language", "English") == "العربية (Arabic)"

# --- PAGE HEADER ---
if is_arabic:
    st.title("📑 مركز التقارير التنفيذية وتحليلات مجلس الإدارة")
    st.markdown(
        "إنشاء ومراجعة وتحميل التقارير الاستراتيجية المهنية بصيغة PDF المدعومة مباشرة من قاعدة بيانات Supabase."
    )
else:
    st.title("📑 Executive Reports Hub & Board Analytics")
    st.markdown(
        "Generate, review, and download professional PDF strategic reports powered live by your Supabase database."
    )

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    if is_arabic:
        st.subheader("🎯 مولد التقارير الرئيسي")
        st.markdown(
            "انقر على الزر أدناه لتنفيذ البرنامج النصي الرئيسي وتحديث جميع التقارير الإستراتيجية الـ 6 في نفس الوقت بأحدث بيانات Supabase."
        )

        generate_btn_label = "🚀 إنشاء جميع التقارير التنفيذية الـ 6"
        spinner_text = "جاري الاتصال بـ Supabase وتجميع التقارير..."
        success_msg = "✅ تم بنجاح إنشاء وتحديث جميع التقارير التنفيذية الـ 6!"
        error_msg = "❌ خطأ أثناء إنشاء التقارير:"
    else:
        st.subheader("🎯 Master Report Generator")
        st.markdown(
            "Click the button below to execute the master script and refresh all 6 strategic management reports simultaneously with the latest Supabase data."
        )

        generate_btn_label = "🚀 Generate All 6 Executive Reports"
        spinner_text = "Connecting to Supabase and compiling reports..."
        success_msg = "✅ All 6 executive reports successfully generated and updated!"
        error_msg = "❌ Error generating reports:"

    if st.button(generate_btn_label, type="primary"):
        with st.spinner(spinner_text):
            try:
                result = subprocess.run(
                    ["python", "generate_all_reports.py"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                st.success(success_msg)
                st.code(result.stdout)
            except subprocess.CalledProcessError as e:
                st.error(f"{error_msg} {e.stderr}")

with col2:
    if is_arabic:
        st.subheader("📂 أرشيف التقارير")
        st.markdown("تحميل تقارير PDF النشطة:")
        download_label = "تحميل"
        no_reports_text = "لم يتم إنشاء تقارير بعد. انقر على 'إنشاء الكل' على اليسار."
    else:
        st.subheader("📂 Report Archive")
        st.markdown("Download active PDF reports:")
        download_label = "📥"
        no_reports_text = "No reports generated yet. Click 'Generate All' on the left."

    reports_dir = "reports"
    if os.path.exists(reports_dir):
        pdf_files = [f for f in os.listdir(reports_dir) if f.endswith(".pdf")]
        if pdf_files:
            for pdf in sorted(pdf_files):
                file_path = os.path.join(reports_dir, pdf)
                with open(file_path, "rb") as f:
                    st.download_button(
                        label=f"{download_label} {pdf}",
                        data=f,
                        file_name=pdf,
                        mime="application/pdf",
                        key=pdf,
                    )
        else:
            st.info(no_reports_text)
    else:
        st.info(no_reports_text)

st.markdown("---")

if is_arabic:
    st.subheader("📋 ملخص حزمة التقارير التنفيذية")
    st.markdown("""
    1. **سعر الشراء عند تعادل التكلفة وجدول إعادة التسكين:** يحسب الحد الأقصى المسموح به لأسعار شراء الحملان الخارجية بناءً على تكاليف خلط الأعلاف الفعلية ($13.21/كجم).
    2. **تحليل ربحية خطوط الإنتاج:** يفصل بين حظائر التسمين النشطة، دفعات التسمين المكتملة، وقطيع التربية الأساسي.
    3. **نسبة التحويل الغذائي (FCR) والتكلفة لكل كجم مکتسب:** يقيّم الكفاءة الغذائية، استهلاك الأعلاف، والتكلفة لكل كجم تم كسبه عبر قطيع التسمين.
    4. **تقييم الأصول البيولوجية وديناميكيات القطيع:** يدقق في تعداد القطيع، أصول التربية النشطة، المواليد، ومعدلات دوران المخزون.
    5. **لوحة تدقيق المواليد والنافِق:** يتتبع معدلات نجاح الولادات، أداء نعاج التكاثر، وتسربات الأمن الحيوي.
    6. **حاسبة نقطة التعادل وتوقيت البيع الأمثل:** يراقب متوسط الزيادة اليومية في الوزن (ADG) وأيام التغذية لتحديد النافذة المثالية للبيع في السوق.
    """)
else:
    st.subheader("📋 Summary of Executive Reports Suite")
    st.markdown("""
    1. **Breakeven Purchase Price & Restocking Schedule:** Calculates maximum allowable purchase prices for external feeder lambs based on live feed mix costs ($13.21/kg).
    2. **Production Line Profitability Analysis:** Segregates active fattening pens, completed finishing batches, and the general breeding herd.
    3. **Feed Conversion Ratio (FCR) & Cost-Per-Kg:** Evaluates nutritional efficiency, feed consumption, and cost per kg gained across finishing stock.
    4. **Biological Asset Valuation & Flock Dynamics:** Audits flock census, active breeding capital, births, and inventory turnover.
    5. **Reproductive & Mortality Leakage Dashboard:** Tracks lambing success rates, breeding ewe performance, and biosecurity mortality leaks.
    6. **Breakeven & Optimal Off-Take Timing Calculator:** Monitors average daily gain (ADG) and days on feed to determine the optimal market selling window.
    """)
