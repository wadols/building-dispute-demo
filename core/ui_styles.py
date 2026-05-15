"""
공통 UI 스타일 — Clean admin + Toss-style design system
Primary: #0066CC  Background: #F8FAFC  Surface: #FFFFFF
"""
import streamlit as st

GLOBAL_CSS = """
<style>
/* ── 기본 폰트 / 배경 ── */
html, body, [class*="css"] {
    font-family: 'Malgun Gothic', 'Apple SD Gothic Neo', 'Noto Sans KR', sans-serif !important;
    font-size: 14px !important;
    line-height: 1.6 !important;
    color: #1E293B !important;
}
[data-testid="stAppViewContainer"] { background: #F8FAFC !important; }
[data-testid="stMain"] { padding-top: 1.7rem !important; }
[data-testid="stMainBlockContainer"] { padding-top: 1.7rem !important; }

/* ── 사이드바 상단 여백 ── */
[data-testid="stSidebarContent"] { padding-top: 1rem !important; }
[data-testid="stSidebarNav"] { padding-top: 0 !important; }
section[data-testid="stSidebar"] > div { padding-top: 1rem !important; }

/* ── 사이드바 ── */
[data-testid="stSidebar"] {
    background: #FFFFFF !important;
    border-right: 1px solid #E2E8F0 !important;
}
[data-testid="stSidebar"] * { color: #334155 !important; }
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"] {
    border-radius: 7px;
    margin: 2px 8px;
    padding: 8px 14px;
    transition: all 0.12s;
    color: #475569 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"]:hover {
    background: #EBF4FF !important;
    color: #0066CC !important;
}
[data-testid="stSidebar"] [data-testid="stSidebarNavLink"][aria-current="page"] {
    background: #EBF4FF !important;
    color: #0066CC !important;
    font-weight: 700 !important;
}

/* ── 카드 ── */
.card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 20px 24px;
    margin-bottom: 14px;
    border: 1px solid #E2E8F0;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}

/* ── KPI 카드 ── */
.kpi-card {
    background: #FFFFFF;
    border-radius: 10px;
    padding: 16px 18px 14px;
    border: 1px solid #E2E8F0;
    border-top: 4px solid #0066CC;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
    text-align: center;
    margin-bottom: 14px;
}
.kpi-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1.2;
    letter-spacing: -1.5px;
}
.kpi-label {
    font-size: 0.78rem;
    color: #64748B;
    margin-top: 4px;
    font-weight: 500;
    letter-spacing: 0.1px;
}

/* ── 상태 배지 (Linear-style pill) ── */
.badge {
    display: inline-flex;
    align-items: center;
    padding: 2px 10px;
    border-radius: 100px;
    font-size: 12px;
    font-weight: 600;
    line-height: 1.8;
    white-space: nowrap;
}
.badge-접수       { background:#EBF4FF; color:#0052A3; }
.badge-회신대기   { background:#FEF9C3; color:#854D0E; }
.badge-회신임박   { background:#FFF4E5; color:#C25700; }
.badge-회신지연   { background:#FEE2E2; color:#991B1B; }
.badge-조정중지   { background:#F1F5F9; color:#475569; }
.badge-불개시     { background:#F1F5F9; color:#475569; }
.badge-개최예정   { background:#DCFCE7; color:#15803D; }
.badge-진행중     { background:#EBF4FF; color:#0066CC; }
.badge-종결       { background:#F1F5F9; color:#94A3B8; }
.badge-조정성립   { background:#DCFCE7; color:#15803D; }
.badge-조정불성립 { background:#FEE2E2; color:#991B1B; }

/* ── 페이지 헤더 ── */
.page-header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding-bottom: 14px;
    margin-bottom: 18px;
    border-bottom: 1px solid #E2E8F0;
}
.page-header h1 {
    font-size: 1.3rem !important;
    font-weight: 700 !important;
    color: #0F172A !important;
    margin: 0 !important;
    letter-spacing: -0.5px !important;
}
.page-header .sub {
    font-size: 0.8rem;
    color: #94A3B8;
    margin-left: auto;
}

/* ── 폼 레이블 ── */
[data-testid="stWidgetLabel"] p,
[data-testid="stWidgetLabel"] label {
    font-weight: 600 !important;
    color: #1E293B !important;
    font-size: 13.5px !important;
}

/* ── 폼 입력 ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea,
[data-testid="stSelectbox"] > div {
    border-radius: 8px !important;
    border: 1px solid #CBD5E1 !important;
    font-size: 14px !important;
    transition: border-color 0.15s, box-shadow 0.15s;
    background: #FFFFFF !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: #0066CC !important;
    box-shadow: 0 0 0 3px rgba(0,102,204,0.1) !important;
    outline: none !important;
}

/* ── 버튼 ── */
[data-testid="stButton"] button,
[data-testid="stFormSubmitButton"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13.5px !important;
    transition: all 0.15s !important;
}
[data-testid="stButton"] button[kind="primary"],
[data-testid="stFormSubmitButton"] button[kind="primary"] {
    background: #0066CC !important;
    border-color: #0066CC !important;
    color: #fff !important;
}
[data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] button[kind="primary"]:hover {
    background: #0052A3 !important;
    border-color: #0052A3 !important;
}
[data-testid="stButton"] button[kind="secondary"] {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    color: #334155 !important;
}
[data-testid="stButton"] button[kind="secondary"]:hover {
    background: #F8FAFC !important;
    border-color: #CBD5E1 !important;
}

/* ── 구분선 / 알림 ── */
hr { border-color: #E2E8F0 !important; margin: 8px 0 !important; }
[data-testid="stAlert"] { border-radius: 8px !important; border-left-width: 4px !important; font-size: 14px !important; }

/* ── 탭 ── */
[data-testid="stTabs"] [role="tab"] {
    font-size: 14px !important;
    font-weight: 500 !important;
    color: #64748B !important;
    padding: 8px 16px !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: #0066CC !important;
    font-weight: 700 !important;
}

/* ── 사이드 패널 ── */
.side-panel {
    background: #FFFFFF;
    border: 1px solid #E2E8F0;
    border-radius: 10px;
    padding: 18px 20px;
    min-height: 300px;
    box-shadow: 0 1px 3px rgba(15,23,42,0.04);
}
.panel-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    margin-bottom: 14px;
    padding-bottom: 12px;
    border-bottom: 1px solid #F1F5F9;
}
.panel-case-num {
    font-size: 1.05rem;
    font-weight: 700;
    color: #0F172A;
    letter-spacing: -0.3px;
}
.panel-building {
    font-size: 0.82rem;
    color: #64748B;
    margin-top: 2px;
}
.info-row {
    display: flex;
    align-items: baseline;
    padding: 6px 0;
    border-bottom: 1px solid #F8FAFC;
    font-size: 13.5px;
    line-height: 1.5;
}
.info-label {
    width: 72px;
    flex-shrink: 0;
    color: #94A3B8;
    font-size: 12px;
    font-weight: 500;
}
.info-value { color: #1E293B; flex: 1; font-size: 13.5px; }
.info-value.highlight { color: #DC2626; font-weight: 600; }
.panel-section-title {
    font-size: 11px;
    font-weight: 700;
    color: #94A3B8;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    margin: 14px 0 6px;
}

/* ── 빈 상태 ── */
.empty-state {
    text-align: center;
    padding: 40px 20px;
    color: #94A3B8;
}
.empty-icon { font-size: 2.2rem; margin-bottom: 10px; }
.empty-title { font-size: 0.95rem; font-weight: 600; color: #64748B; margin-bottom: 5px; }
.empty-sub { font-size: 0.82rem; color: #94A3B8; line-height: 1.6; }

/* ── 데이터프레임 ── */
[data-testid="stDataFrame"] iframe { border-radius: 8px; }
</style>
"""


def inject_css():
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


def page_header(icon: str, title: str, sub: str = ""):
    sub_html = f'<span class="sub">{sub}</span>' if sub else ""
    st.markdown(
        f'<div class="page-header">'
        f'<span style="font-size:1.35rem;line-height:1">{icon}</span>'
        f'<h1>{title}</h1>{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


def status_badge(status: str) -> str:
    cls_map = {
        "접수": "badge-접수",
        "회신대기": "badge-회신대기",
        "회신임박": "badge-회신임박",
        "회신지연": "badge-회신지연",
        "조정중지": "badge-조정중지",
        "불개시": "badge-불개시",
        "개최예정": "badge-개최예정",
        "진행중": "badge-진행중",
        "종결": "badge-종결",
        "조정성립": "badge-조정성립",
        "조정불성립": "badge-조정불성립",
    }
    cls = cls_map.get(status, "badge-접수")
    return f'<span class="badge {cls}">{status}</span>'


def kpi_card_html(label: str, value, color: str = "#0066CC") -> str:
    return (
        f'<div class="kpi-card" style="border-top-color:{color}">'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f'</div>'
    )


def kpi_cards(items: list[dict]):
    COLORS = ["#0066CC", "#F59E0B", "#059669", "#DC2626", "#7C3AED"]
    cols = st.columns(len(items))
    for i, (col, item) in enumerate(zip(cols, items)):
        color = item.get("color", COLORS[i % len(COLORS)])
        with col:
            st.markdown(
                kpi_card_html(item["label"], item["value"], color),
                unsafe_allow_html=True,
            )


def section_header(num: str, title: str):
    """① 사건 기본 정보 형태의 섹션 헤더"""
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;'
        f'padding-bottom:10px;margin-bottom:14px;border-bottom:1.5px solid #E2E8F0">'
        f'<span style="width:3px;height:18px;background:#0066CC;border-radius:2px;flex-shrink:0"></span>'
        f'<span style="font-size:11px;font-weight:700;color:#94A3B8;letter-spacing:0.5px">{num}</span>'
        f'<span style="font-size:14px;font-weight:700;color:#0F172A">{title}</span>'
        f'</div>',
        unsafe_allow_html=True,
    )


def empty_state(icon: str = "📭", title: str = "데이터가 없습니다", sub: str = ""):
    sub_html = f'<div class="empty-sub">{sub}</div>' if sub else ""
    st.markdown(
        f'<div class="empty-state">'
        f'<div class="empty-icon">{icon}</div>'
        f'<div class="empty-title">{title}</div>'
        f'{sub_html}</div>',
        unsafe_allow_html=True,
    )


def card(title: str = "", key: str = ""):
    return _CardCtx(title)


class _CardCtx:
    def __init__(self, title):
        self.title = title

    def __enter__(self):
        self._container = st.container()
        with self._container:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            if self.title:
                st.markdown(
                    f'<div style="font-size:0.92rem;font-weight:700;color:#0F172A;'
                    f'margin-bottom:12px;letter-spacing:-0.3px">{self.title}</div>',
                    unsafe_allow_html=True,
                )
        return self._container

    def __exit__(self, *_):
        st.markdown("</div>", unsafe_allow_html=True)
