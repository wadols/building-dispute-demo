"""
메모 통합검색 — 전체 사건의 메모·일지를 키워드로 검색
"""
import streamlit as st
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import init_db, search_notes, get_recent_notes
from core.ui_styles import inject_css, page_header

st.set_page_config(page_title="메모 통합검색", page_icon="🔍", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("🔍", "메모 통합검색", "전체 사건의 메모 · 진행일지 통합 검색")

CAT_COLORS = {
    "전화응대":  "#DBEAFE", "방문상담":  "#D1FAE5", "자료요청": "#FEF9C3",
    "위원자문":  "#EDE9FE", "내부검토":  "#FFE4E6", "기타":     "#F1F5F9",
}
CAT_TEXT = {
    "전화응대": "#1D4ED8", "방문상담": "#059669", "자료요청": "#B45309",
    "위원자문": "#7C3AED", "내부검토": "#BE123C", "기타":     "#475569",
}

# ── 검색 입력
col_kw, col_btn = st.columns([5, 1])
with col_kw:
    keyword = st.text_input("검색어", placeholder="제목, 내용에서 검색 (예: 관리비, 통보서, 위원 요청...)",
                            label_visibility="collapsed")
with col_btn:
    do_search = st.button("🔍 검색", type="primary", use_container_width=True)

# ── 필터
f1, f2, f3 = st.columns(3)
with f1:
    cat_filter = st.multiselect(
        "카테고리",
        ["전화응대", "방문상담", "자료요청", "위원자문", "내부검토", "기타"],
        placeholder="전체",
        label_visibility="collapsed",
    )
with f2:
    only_important = st.checkbox("⭐ 중요 표시만")
with f3:
    date_range = st.date_input(
        "기간",
        value=[],
        label_visibility="collapsed",
    )

st.markdown("---")

# ── 검색 실행
if keyword.strip() or do_search:
    notes = [dict(n) for n in search_notes(keyword.strip())]
elif keyword == "":
    notes = [dict(n) for n in get_recent_notes(limit=50)]
else:
    notes = []

# 필터 적용
if cat_filter:
    notes = [n for n in notes if n.get("카테고리") in cat_filter]
if only_important:
    notes = [n for n in notes if n.get("중요표시")]
if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
    start_d, end_d = date_range
    notes = [
        n for n in notes
        if start_d.isoformat() <= (n.get("작성일시") or "")[:10] <= end_d.isoformat()
    ]

# ── 결과 표시
if keyword.strip():
    st.markdown(f"**검색 결과: {len(notes)}건** (키워드: `{keyword.strip()}`)")
else:
    st.markdown(f"**최근 메모 {len(notes)}건**")

if not notes:
    st.info("검색 결과가 없습니다.")
else:
    for note in notes:
        cat  = note.get("카테고리") or "기타"
        bg   = CAT_COLORS.get(cat, "#F1F5F9")
        fg   = CAT_TEXT.get(cat, "#475569")
        star = "⭐ " if note.get("중요표시") else ""
        title_txt = note.get("제목") or "(제목 없음)"
        dt   = (note.get("작성일시") or "")[:16]
        case_no = note.get("접수번호", "")

        # 키워드 하이라이트
        def _hl(text: str) -> str:
            if not keyword.strip() or not text:
                return text or ""
            import re
            escaped = re.escape(keyword.strip())
            return re.sub(
                f"({escaped})",
                r'<mark style="background:#FEF08A;border-radius:2px">\1</mark>',
                text,
                flags=re.IGNORECASE,
            )

        content_hl = _hl(note.get("내용", ""))
        title_hl   = _hl(title_txt)

        col_card, col_btn = st.columns([9, 1])
        with col_card:
            st.markdown(
                f'<div style="background:#fff;border-radius:10px;padding:14px 18px;'
                f'margin-bottom:8px;box-shadow:0 1px 3px rgba(0,0,0,.07);'
                f'border-left:4px solid {fg}">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">'
                f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:12px;'
                f'font-size:0.78rem;font-weight:600">{cat}</span>'
                f'<span style="font-weight:700">{star}{title_hl}</span>'
                f'<span style="margin-left:auto;font-size:0.78rem;color:#94A3B8">{dt}</span>'
                f'</div>'
                f'<div style="font-size:0.9rem;color:#334155;white-space:pre-wrap;'
                f'max-height:120px;overflow:hidden">{content_hl}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            if case_no and st.button("🔎 사건", key=f"goto_{note['id']}", use_container_width=True):
                st.session_state["detail_case"] = case_no
                st.switch_page("pages/4_사건상세.py")
