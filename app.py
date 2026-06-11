"""
경기도 집합건물 분쟁조정위원회 업무 자동화 시스템
"""
import streamlit as st
from core.db import init_db

st.set_page_config(
    page_title="집합건물 분쟁조정 관리시스템",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

pg = st.navigation(
    [
        st.Page("pages/1_홈.py",             title="홈",         icon="🏠"),
        st.Page("pages/2_신규접수.py",       title="신규접수",   icon="📋"),
        st.Page("pages/3_접수대장.py",       title="접수대장",   icon="📂"),
        st.Page("pages/4_사건상세.py",       title="사건상세",   icon="🔎"),
        st.Page("pages/11_캘린더.py",        title="캘린더",     icon="📅"),
        st.Page("pages/8_보고서.py",         title="보고서",     icon="📊"),
        st.Page("pages/6_위원회개최.py",     title="위원회개최", icon="🏛️"),
        st.Page("pages/5_위원관리.py",       title="위원관리",   icon="👥"),
        st.Page("pages/10_설정.py",          title="설정",       icon="⚙️"),
    ],
    position="sidebar",
)

st.markdown("""
<style>
[data-testid="stSidebarNavItems"] > li:nth-child(4),
[data-testid="stDecoration"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

if "db_initialized" not in st.session_state:
    init_db()
    from core.db import get_all_cases
    if len(get_all_cases()) == 0:
        try:
            from seed_demo_data import reset_and_seed
            reset_and_seed()
        except Exception:
            pass
    st.session_state["db_initialized"] = True

pg.run()
