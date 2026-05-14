"""
공통 UI 스타일 모듈 — st.markdown(GLOBAL_CSS, unsafe_allow_html=True) 로 호출
"""
import streamlit as st

GLOBAL_CSS = """
<style>
/* ── 전체 배경 / 폰트 ── */
html, body, [class*="css"] {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', sans-serif !important;
}

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #1A3660 !important;
}
[data-testid="stSidebar"] * {
    color: #E8EEF6 !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    border-radius: 8px;
    margin: 2px 8px;
    padding: 8px 14px;
    transition: background 0.15s;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover,
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: #2563EB33 !important;
}

/* ── 카드 컨테이너 ── */
.card {
    background: #ffffff;
    border-radius: 12px;
    padding: 24px 28px;
    margin-bottom: 18px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08), 0 0 0 1px rgba(0,0,0,0.04);
}
.card-title {
    font-size: 1.0rem;
    font-weight: 700;
    color: #1A3660;
    padding-bottom: 10px;
    margin-bottom: 14px;
    border-bottom: 2px solid #1A56A0;
    letter-spacing: -0.3px;
}

/* ── KPI 카드 ── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 16px;
    margin-bottom: 20px;
}
.kpi-card {
    background: #fff;
    border-radius: 12px;
    padding: 20px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.08);
    border-top: 4px solid #1A56A0;
    text-align: center;
}
.kpi-card .kpi-value {
    font-size: 2.2rem;
    font-weight: 800;
    color: #1A3660;
    line-height: 1.1;
}
.kpi-card .kpi-label {
    font-size: 0.82rem;
    color: #64748B;
    margin-top: 4px;
}
.kpi-card.accent { border-top-color: #E67E22; }
.kpi-card.green  { border-top-color: #27AE60; }
.kpi-card.red    { border-top-color: #E74C3C; }

/* ── 상태 배지 ── */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.2px;
}
.badge-접수     { background:#DBEAFE; color:#1E40AF; }
.badge-회신대기 { background:#FEF9C3; color:#92400E; }
.badge-회신임박 { background:#FFEDD5; color:#C2410C; }
.badge-회신지연 { background:#FEE2E2; color:#B91C1C; }
.badge-조정중지 { background:#1E293B; color:#F1F5F9; }
.badge-불개시   { background:#E2E8F0; color:#475569; }
.badge-개최예정 { background:#D1FAE5; color:#065F46; }
.badge-종결     { background:#F1F5F9; color:#94A3B8; }

/* ── 폼 input 스타일 강화 ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div {
    border-radius: 8px !important;
    border: 1px solid #CBD5E1 !important;
    transition: border-color 0.15s, box-shadow 0.15s;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #1A56A0 !important;
    box-shadow: 0 0 0 3px rgba(26,86,160,0.12) !important;
}

/* ── 기본 버튼 ── */
[data-testid="stFormSubmitButton"] button,
[data-testid="stButton"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: -0.2px !important;
    transition: opacity 0.15s !important;
}
[data-testid="stFormSubmitButton"] button[kind="primary"] {
    background: #1A56A0 !important;
    border-color: #1A56A0 !important;
}
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
    opacity: 0.88 !important;
}

/* ── 섹션 구분선 ── */
hr { border-color: #E2E8F0 !important; margin: 6px 0 !important; }

/* ── 알림 박스 ── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    border-left-width: 4px !important;
}

/* ── 페이지 헤더 ── */
.page-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 6px 0 20px 0;
    border-bottom: 3px solid #1A56A0;
    margin-bottom: 24px;
}
.page-header h1 {
    font-size: 1.5rem !important;
    font-weight: 800;
    color: #1A3660;
    margin: 0 !important;
}
.page-header .sub {
    font-size: 0.85rem;
    color: #64748B;
    margin-left: auto;
}
</style>
"""


def inject_css():
    """모든 페이지 상단에서 호출해 전역 CSS 주입"""
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def card(title: str = "", key: str = ""):
    """with card('제목'): ... 패턴으로 카드 레이아웃"""
    return _CardCtx(title)


class _CardCtx:
    def __init__(self, title):
        self.title = title

    def __enter__(self):
        self._container = st.container()
        with self._container:
            if self.title:
                st.markdown(
                    f'<div class="card-title">{self.title}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown('<div class="card">', unsafe_allow_html=True)
        return self._container

    def __exit__(self, *_):
        st.markdown("</div>", unsafe_allow_html=True)


def page_header(icon: str, title: str, sub: str = ""):
    """페이지 상단 타이틀 바"""
    sub_html = f'<span class="sub">{sub}</span>' if sub else ""
    st.markdown(
        f'<div class="page-header">'
        f'<span style="font-size:1.6rem">{icon}</span>'
        f'<h1>{title}</h1>{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    cls_map = {
        "접수": "badge-접수", "회신대기": "badge-회신대기",
        "회신임박": "badge-회신임박", "회신지연": "badge-회신지연",
        "조정중지": "badge-조정중지", "불개시": "badge-불개시",
        "개최예정": "badge-개최예정", "종결": "badge-종결",
    }
    cls = cls_map.get(status, "badge-접수")
    return f'<span class="badge {cls}">{status}</span>'


def kpi_cards(items: list[dict]):
    """
    items = [
        {"label": "올해 접수", "value": 42, "accent": None},
        ...
    ]
    """
    cols = st.columns(len(items))
    accents = [None, "accent", "green", "red"]
    for i, (col, item) in enumerate(zip(cols, items)):
        accent_cls = item.get("accent", accents[i % 4]) or ""
        with col:
            st.markdown(
                f'<div class="kpi-card {accent_cls}">'
                f'<div class="kpi-value">{item["value"]}</div>'
                f'<div class="kpi-label">{item["label"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
