import streamlit as st
st.write("# 테스트")

st.set_page_config(
    page_title="집합건물 분쟁조정 관리시스템",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 전체 페이지 등록 (switch_page 작동에 필요)
# 사건상세는 등록하되 CSS로 사이드바에서 숨김
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

# 사이드바에서 "사건상세"(4번째 항목) 숨김 — 접수대장에서 진입하는 내부 페이지
st.markdown("""
<style>
[data-testid="stSidebarNavItems"] > li:nth-child(4),
[data-testid="stDecoration"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

if "db_initialized" not in st.session_state:
    init_db()
    # 데모 브랜치: DB가 비어있으면 가상 샘플 데이터 자동 주입
    from core.db import get_all_cases
    if len(get_all_cases()) == 0:
        try:
            from seed_demo_data import reset_and_seed
            reset_and_seed()
        except Exception:
            pass
    st.session_state["db_initialized"] = True

pg.run()
