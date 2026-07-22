import streamlit as st

TRANSLATIONS = {
    "English": {
        "lang_label": "Select Language",
        # Dashboard UI
        "farm_control_center": "Jalila's Farm Control Center",
        "control_room": "myHerdApp Control Room",
        "management_apps_header": "Herd Management Applications",
        "performance_reports_header": "Herd Performance Reports",
        # Categories
        "Category": "Category",
        "Female": "Female",
        "Ewes": "Ewes",
        "Pregnant": "Pregnant",
        "(Small) (Male)": "(Small) (Male)",
        "(Small) (Female)": "(Small) (Female)",
        "Permanent Sire": "Permanent Sire",
        "Fattening": "Fattening",
        # Statuses
        "Status": "Status",
        "Active/Healthy": "Active/Healthy",
        "Sick": "Sick",
        "Vet": "Vet",
        "Slaughtered": "Slaughtered",
        "Died": "Died",
        # Feed Ingredients
        "Ingredents": "Ingredents",
        "Soya Bean": "Soya Bean",
        "Wheat": "Wheat",
        "Corn": "Corn",
        "Radda": "Radda",
        "Hay Bean": "Hay Bean",
        "Barseem Hegazy": "Barseem Hegazy",
        "Additions": "Additions",
        # Navigation Sidebar English Labels
        "nav_1": "1. Strategic Metrics",
        "nav_2": "2. Active Herd Registry",
        "nav_3": "3. Birth Records",
        "nav_4": "4. Growth Logs",
        "nav_5": "5. Feed Inventory",
        "nav_6": "6. Data Corrections",
        "nav_7": "7. Performance Reports",
        "nav_8": "8. Achievements",
        "nav_9": "9. Data Audit",
        "nav_10": "10. Breeding Prediction",
        "nav_11": "11. Breeding Readiness",
        "nav_12": "12. Off-Take History",
        "sidebar_user": "User",
        "sidebar_signout": "🔒 Secure Sign-Out",
        # Strategic Metrics Page Labels
        "current_inventory_status": "Current Inventory Status (Living Herd)",
        "total_living": "Total Living",
        "newborns_label": "Newborns (0-2m)",
        "structural_breakdowns": "📊 Structural Population Breakdowns",
        "herd_structure_title": "Herd Structure (Excluding Newborns & Off-Take)",
        "allocation_ratio_title": "Allocation Ratio (Excluding Newborns & Off-Take)",
        "no_active_herd": "📂 No active herd logs found.",
    },
    "العربية (Arabic)": {
        "lang_label": "اختر اللغة",
        # Dashboard UI
        "farm_control_center": "مركز قيادة مزرعة جليلة",
        "control_room": "غرفة تحكم تطبيق المزرعة",
        "management_apps_header": "تطبيقات إدارة القطيع",
        "performance_reports_header": "تقارير أداء القطيع",
        # Categories
        "Category": "فئة الحيوان",
        "Female": "نعجة",
        "Ewes": "مرضعة",
        "Pregnant": "نعجة حامل",
        "(Small) (Male)": "حمل - ذكر",
        "(Small) (Female)": "حمل - أنثى",
        "Permanent Sire": "كبش",
        "Fattening": "خروف تسمين",
        # Statuses
        "Status": "الحالة الصحية",
        "Active/Healthy": "سليم",
        "Sick": "مريض",
        "Vet": "تحت العلاج",
        "Slaughtered": "تم الذبح",
        "Died": "مات",
        # Feed Ingredients
        "Ingredents": "نوع العلف",
        "Soya Bean": "فول صويا",
        "Wheat": "غلة",
        "Corn": "ذرة",
        "Radda": "ردة",
        "Hay Bean": "تبن فول سودانى",
        "Barseem Hegazy": "برسيم حجازى",
        "Additions": "إضافات",
        # Navigation Sidebar Arabic Labels
        "nav_1": "1. مؤشرات الأداء الاستراتيجية",
        "nav_2": "2. سجل القطيع النشط",
        "nav_3": "3. سجلات الولادة",
        "nav_4": "4. سجلات أداءالنمو",
        "nav_5": "5. مخزون العلف",
        "nav_6": "6. تصحيح إدخال البيانات",
        "nav_7": "7. تقارير الأداء",
        "nav_8": "8. الإنجازات",
        "nav_9": "9. تدقيق البيانات",
        "nav_10": "10. تقرير التنبؤ بالتكاثر",
        "nav_11": "11. تقرير جاهزية التكاثر",
        "nav_12": "12. تقرير تاريخ الاستهلاك",
        # Strategic Metrics Page Labels (Arabic)
        "current_inventory_status": "حالة المخزون الحالية (القطيع الحي)",
        "total_living": "إجمالي الأحياء",
        "newborns_label": "الولادات (0-2 شهور)",
        "structural_breakdowns": "📊 توزيع التركيبة السكانية للقطيع",
        "herd_structure_title": "تركيبة القطيع (باستثناء المواليد الجدد والمستبعدات)",
        "allocation_ratio_title": "نسب التوزيع (باستثناء المواليد الجدد والمستبعدات)",
        "no_active_herd": "📂 لم يتم العثور على سجلات للقطيع النشط.",
    },
}


def init_language_state():
    """Initializes the language state in Streamlit session storage."""
    if "language" not in st.session_state:
        st.session_state.language = "English"


def t(text_key):
    """Returns the translated string based on the current active language state."""
    lang = st.session_state.get("language", "English")
    return TRANSLATIONS.get(lang, {}).get(text_key, text_key)


def apply_rtl_styling():
    """Injects custom CSS to handle Right-to-Left layout if Arabic is selected."""
    lang = st.session_state.get("language", "English")
    if lang == "العربية (Arabic)":
        st.markdown(
            """
            <style>
                .stApp {
                    direction: rtl;
                    text-align: right;
                }
                [data-testid="stSidebar"] {
                    direction: rtl;
                    text-align: right;
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
