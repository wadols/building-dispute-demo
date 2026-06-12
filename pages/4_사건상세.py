"""
사건 상세 화면
- 탭1: 사건 정보 (전체 필드 조회, 수정 이동)
- 탭2: 메모/일지 (CRUD — 추가/수정/삭제 확인)
- 탭3: 생성 문서 (사건 폴더 파일 목록)
접근: query_params["case"] 또는 session_state["detail_case"] 또는 사이드바 입력
"""
import streamlit as st
from datetime import datetime, date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import (
    init_db, get_case, update_case, delete_case,
    get_notes, create_note, update_note, delete_note,
)
from core.status_resolver import resolve_status, CLOSED_STATUSES
from core.ui_styles import inject_css, page_header, status_badge, section_header, case_folder_path

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()

OUTPUT_ROOT = Path(__file__).parent.parent / "output" / "사건자료"

# ── 접수번호 결정
접수번호 = (
    st.query_params.get("case")
    or st.session_state.get("detail_case")
)

if not 접수번호:
    page_header("🔎", "사건 상세")
    st.info("접수대장에서 사건을 선택한 뒤 🔎 상세보기를 눌러 진입하세요.")
    st.stop()

case = get_case(접수번호.strip())
if case is None:
    st.error(f"**{접수번호}** 사건을 찾을 수 없습니다.")
    st.stop()

case = dict(case)
status = resolve_status(case)

# ────────────────────────────────────────────────
# 페이지 헤더
# ────────────────────────────────────────────────
badge_html = status_badge(status)
st.markdown(
    f'<div class="page-header">'
    f'<span style="font-size:1.6rem">🔎</span>'
    f'<h1>{case["접수번호"]}</h1>'
    f'{badge_html}'
    f'<span class="sub">{case.get("건물명") or ""} | {case["지역"]}</span>'
    f'</div>',
    unsafe_allow_html=True,
)

# ── 빠른 정보 요약
col_a, col_b, col_c, col_d = st.columns(4)
with col_a:
    st.markdown(f'<div class="kpi-card" style="border-top-color:#1A56A0">'
                f'<div class="kpi-label">신청인</div>'
                f'<div style="font-weight:700;font-size:1rem;margin-top:4px">{case["신청인_성명"]}</div>'
                f'<div style="font-size:0.78rem;color:#64748B">{case.get("신청인_지위") or ""}</div>'
                f'</div>', unsafe_allow_html=True)
with col_b:
    st.markdown(f'<div class="kpi-card" style="border-top-color:#E67E22">'
                f'<div class="kpi-label">피신청인</div>'
                f'<div style="font-weight:700;font-size:1rem;margin-top:4px">{case["피신청인_성명"]}</div>'
                f'<div style="font-size:0.78rem;color:#64748B">{case.get("피신청인_지위") or ""}</div>'
                f'</div>', unsafe_allow_html=True)
with col_c:
    dl = case.get("회신기한") or "—"
    today_str = date.today().isoformat()
    dl_color = "#E74C3C" if dl != "—" and dl < today_str else "#1A3660"
    st.markdown(f'<div class="kpi-card" style="border-top-color:{dl_color}">'
                f'<div class="kpi-label">회신기한</div>'
                f'<div style="font-weight:700;font-size:1rem;margin-top:4px;color:{dl_color}">{dl}</div>'
                f'<div style="font-size:0.78rem;color:#64748B">접수: {case["접수일자"]}</div>'
                f'</div>', unsafe_allow_html=True)
with col_d:
    result = case.get("결과") or "—"
    st.markdown(f'<div class="kpi-card" style="border-top-color:#27AE60">'
                f'<div class="kpi-label">처리결과</div>'
                f'<div style="font-weight:700;font-size:1rem;margin-top:4px">{result}</div>'
                f'<div style="font-size:0.78rem;color:#64748B">분쟁: {case.get("분쟁유형") or "—"}</div>'
                f'</div>', unsafe_allow_html=True)

st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════
# 진행단계 시각화
# ════════════════════════════════════════════════
_steps_data = [
    ("접수",    bool(case.get("접수일자")),              (case.get("접수일자") or "")[:10]),
    ("안내발송", bool(case.get("안내도달일")),            (case.get("안내도달일") or "")[:10]),
    ("회신",    bool(case.get("회신접수일")),             (case.get("회신접수일") or "")[:10]),
    ("위원회",  case.get("개최여부") == "개최",           ""),
    ("종결",    status in CLOSED_STATUSES,                 (case.get("종결일자") or "")[:10]),
]
_flags = [s[1] for s in _steps_data]
_current_idx = next((i for i, f in enumerate(_flags) if not f), len(_steps_data))

def _step_cell(label, sub, done, current):
    if done:
        circle = "background:#0066CC;color:#fff"; inner = "✓"; lc = "#0066CC"; lw = "700"
    elif current:
        circle = "background:#fff;border:2px solid #0066CC;color:#0066CC"; inner = "●"; lc = "#0066CC"; lw = "700"
    else:
        circle = "background:#F1F5F9;color:#CBD5E1"; inner = "·"; lc = "#94A3B8"; lw = "400"
    sub_html = (f'<div style="font-size:10px;color:#94A3B8;text-align:center">{sub}</div>'
                if sub else '<div style="font-size:10px;color:transparent">·</div>')
    return (
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:3px;flex-shrink:0;min-width:64px">'
        f'<div style="width:30px;height:30px;border-radius:50%;{circle};'
        f'display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700">{inner}</div>'
        f'<div style="font-size:11.5px;font-weight:{lw};color:{lc};white-space:nowrap">{label}</div>'
        f'{sub_html}</div>'
    )

_step_html = '<div style="display:flex;align-items:flex-start;padding:14px 24px;background:#fff;border:1px solid #E2E8F0;border-radius:10px;margin-bottom:16px">'
for _i, (_label, _done, _sub) in enumerate(_steps_data):
    _step_html += _step_cell(_label, _sub, _done, _i == _current_idx)
    if _i < len(_steps_data) - 1:
        _line_color = "#0066CC" if _done else "#E2E8F0"
        _step_html += f'<div style="flex:1;height:2px;background:{_line_color};margin-top:15px;min-width:16px"></div>'
_step_html += '</div>'
st.markdown(_step_html, unsafe_allow_html=True)

# ════════════════════════════════════════════════
# 탭
# ════════════════════════════════════════════════
tab1, tab2, tab3 = st.tabs(["📋 사건 정보", "📝 메모 / 일지", "📁 생성 문서"])

# ────────────────────────────────────────────────
# TAB 1: 사건 정보
# ────────────────────────────────────────────────
with tab1:
    def row2(label, val):
        v = val if val else "—"
        return (f'<tr><td style="width:140px;color:#64748B;padding:7px 12px;'
                f'font-size:0.85rem;white-space:nowrap">{label}</td>'
                f'<td style="padding:7px 12px;font-size:0.9rem">{v}</td></tr>')

    def info_table(rows_html):
        return f'<table style="width:100%;border-collapse:collapse">{rows_html}</table>'

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            section_header("①", "사건 기본 정보")
            st.markdown(info_table(
                row2("접수번호",  case["접수번호"]) +
                row2("접수일자",  case["접수일자"]) +
                row2("지역",      case["지역"]) +
                row2("분쟁유형",  case.get("분쟁유형")) +
                row2("건물명",    case.get("건물명")) +
                row2("건물소재지",case.get("건물소재지")) +
                row2("건축물용도",case.get("건축물용도")) +
                row2("신청내용",  case.get("신청내용"))
            ), unsafe_allow_html=True)

        with st.container(border=True):
            section_header("③", "진행 정보")
            st.markdown(info_table(
                row2("안내도달일",   case.get("안내도달일")) +
                row2("회신기한",     case.get("회신기한")) +
                row2("회신접수일",   case.get("회신접수일")) +
                row2("조정동의여부", case.get("조정동의여부")) +
                row2("개최여부",     case.get("개최여부")) +
                row2("결과",         case.get("결과")) +
                row2("종결일자",     case.get("종결일자")) +
                row2("진행상태",     status)
            ), unsafe_allow_html=True)

    with c2:
        with st.container(border=True):
            section_header("②", "신청인")
            st.markdown(info_table(
                row2("성명",    case["신청인_성명"]) +
                row2("지위",    case.get("신청인_지위")) +
                row2("주소",    case["신청인_주소"]) +
                row2("우편번호",case.get("신청인_우편번호")) +
                row2("연락처",  case.get("신청인_연락처"))
            ), unsafe_allow_html=True)

        with st.container(border=True):
            section_header("④", "피신청인")
            st.markdown(info_table(
                row2("성명",    case["피신청인_성명"]) +
                row2("지위",    case.get("피신청인_지위")) +
                row2("주소",    case["피신청인_주소"]) +
                row2("우편번호",case.get("피신청인_우편번호")) +
                row2("연락처",  case.get("피신청인_연락처"))
            ), unsafe_allow_html=True)

        if case.get("피신청인2_성명"):
            with st.container(border=True):
                section_header("④-2", "피신청인2")
                st.markdown(info_table(
                    row2("성명",    case.get("피신청인2_성명")) +
                    row2("지위",    case.get("피신청인2_지위")) +
                    row2("주소",    case.get("피신청인2_주소")) +
                    row2("우편번호",case.get("피신청인2_우편번호")) +
                    row2("연락처",  case.get("피신청인2_연락처"))
                ), unsafe_allow_html=True)

    btn_edit, btn_del = st.columns([3, 1])
    with btn_edit:
        if st.button("✏️ 이 사건 수정하기", type="primary", use_container_width=True):
            st.session_state["edit_case"] = case["접수번호"]
            st.session_state["_edit_origin"] = "pages/4_사건상세.py"
            st.session_state["_edit_origin_case"] = case["접수번호"]
            for k in list(st.session_state.keys()):
                if k.startswith("_form_ready_") or k.startswith("inp_"):
                    del st.session_state[k]
            st.switch_page("pages/2_신규접수.py")
    with btn_del:
        if st.button("🗑️ 사건 삭제", use_container_width=True):
            st.session_state["_confirm_case_delete"] = case["접수번호"]

    if st.session_state.get("_confirm_case_delete") == case["접수번호"]:
        st.error(
            f"**{case['접수번호']}** 사건을 삭제하면 메모·첨부 정보도 모두 사라지며 **복구할 수 없습니다.**"
        )
        cc1, cc2, _ = st.columns([1, 1, 4])
        with cc1:
            if st.button("✅ 확인 삭제", type="primary", use_container_width=True, key="del_case_ok"):
                delete_case(case["접수번호"])
                st.session_state.pop("_confirm_case_delete", None)
                st.session_state.pop("detail_case", None)
                st.cache_data.clear()
                st.success("삭제되었습니다. 접수대장으로 이동합니다.")
                st.switch_page("pages/3_접수대장.py")
        with cc2:
            if st.button("✕ 취소", use_container_width=True, key="del_case_cancel"):
                st.session_state.pop("_confirm_case_delete", None)
                st.rerun()

# ────────────────────────────────────────────────
# TAB 2: 메모 / 일지
# ────────────────────────────────────────────────
with tab2:

    CATS = ["전화응대", "방문상담", "자료요청", "위원자문", "내부검토", "기타"]
    CAT_COLORS = {
        "전화응대": "#DBEAFE", "방문상담": "#D1FAE5", "자료요청": "#FEF9C3",
        "위원자문": "#EDE9FE", "내부검토": "#FFE4E6", "기타": "#F1F5F9",
    }
    CAT_TEXT = {
        "전화응대": "#1E40AF", "방문상담": "#065F46", "자료요청": "#92400E",
        "위원자문": "#5B21B6", "내부검토": "#9F1239", "기타": "#475569",
    }

    # ── 새 메모 작성
    with st.container(border=True):
        st.markdown('**✏️ 새 메모 작성**')
        with st.form("new_note_form", clear_on_submit=True):
            nc1, nc2, nc3 = st.columns([2, 3, 1])
            with nc1:
                new_cat = st.selectbox("카테고리", CATS)
            with nc2:
                new_title = st.text_input("제목")
            with nc3:
                new_important = st.checkbox("⭐ 중요")
            new_content = st.text_area("내용 *", height=90)
            save_note = st.form_submit_button("💾 메모 저장", type="primary", use_container_width=True)

        if save_note:
            if not new_content.strip():
                st.error("내용을 입력하세요.")
            else:
                create_note({
                    "접수번호": 접수번호,
                    "카테고리": new_cat,
                    "제목":     new_title.strip() or None,
                    "내용":     new_content.strip(),
                    "중요표시": int(new_important),
                    "작성일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                })
                st.toast("메모가 저장되었습니다.", icon="✅")
                st.rerun()

    # ── 기존 메모 목록
    notes = get_notes(접수번호)
    if not notes:
        st.info("등록된 메모가 없습니다.")
    else:
        st.markdown(f'<p style="font-size:0.85rem;color:#64748B;margin:8px 0">'
                    f'총 {len(notes)}건 (최신순)</p>', unsafe_allow_html=True)

        for note in notes:
            note = dict(note)
            nid = note["id"]
            cat = note.get("카테고리") or "기타"
            bg  = CAT_COLORS.get(cat, "#F1F5F9")
            fg  = CAT_TEXT.get(cat, "#475569")
            star = "⭐ " if note.get("중요표시") else ""
            title_txt = note.get("제목") or "(제목 없음)"
            dt = note.get("작성일시", "")[:16]

            # 메모 카드
            st.markdown(
                f'<div style="background:#fff;border-radius:10px;padding:14px 18px;'
                f'margin-bottom:10px;box-shadow:0 1px 3px rgba(0,0,0,.07);'
                f'border-left:4px solid {fg}">'
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px">'
                f'<span style="background:{bg};color:{fg};padding:2px 8px;border-radius:12px;'
                f'font-size:0.78rem;font-weight:600">{cat}</span>'
                f'<span style="font-weight:700">{star}{title_txt}</span>'
                f'<span style="margin-left:auto;font-size:0.78rem;color:#94A3B8">{dt}</span>'
                f'</div>'
                f'<div style="font-size:0.9rem;color:#334155;white-space:pre-wrap">'
                f'{note["내용"]}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )

            # 수정 / 삭제 버튼
            btn_col1, btn_col2, _ = st.columns([1, 1, 8])
            with btn_col1:
                if st.button("✏️ 수정", key=f"edit_btn_{nid}"):
                    st.session_state[f"editing_{nid}"] = True
            with btn_col2:
                if st.button("🗑️ 삭제", key=f"del_btn_{nid}"):
                    st.session_state[f"confirm_del_{nid}"] = True

            # 삭제 확인
            if st.session_state.get(f"confirm_del_{nid}"):
                st.warning(f'**"{title_txt}"** 메모를 삭제하시겠습니까? 되돌릴 수 없습니다.')
                dc1, dc2, _ = st.columns([1, 1, 6])
                with dc1:
                    if st.button("예, 삭제", key=f"del_yes_{nid}", type="primary"):
                        delete_note(nid)
                        del st.session_state[f"confirm_del_{nid}"]
                        st.toast("메모가 삭제되었습니다.", icon="🗑️")
                        st.rerun()
                with dc2:
                    if st.button("취소", key=f"del_no_{nid}"):
                        del st.session_state[f"confirm_del_{nid}"]
                        st.rerun()

            # 인라인 수정 폼
            if st.session_state.get(f"editing_{nid}"):
                with st.form(f"edit_note_{nid}"):
                    st.markdown("**메모 수정**")
                    ec1, ec2, ec3 = st.columns([2, 3, 1])
                    with ec1:
                        e_cat = st.selectbox("카테고리", CATS,
                                             index=CATS.index(cat) if cat in CATS else 0)
                    with ec2:
                        e_title = st.text_input("제목", value=note.get("제목") or "")
                    with ec3:
                        e_imp = st.checkbox("⭐ 중요", value=bool(note.get("중요표시")))
                    e_content = st.text_area("내용 *", value=note["내용"], height=90)
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        save_edit = st.form_submit_button("💾 저장", type="primary", use_container_width=True)
                    with sc2:
                        cancel_edit = st.form_submit_button("✕ 취소", use_container_width=True)

                if save_edit:
                    if not e_content.strip():
                        st.error("내용을 입력하세요.")
                    else:
                        update_note(nid, {
                            "카테고리": e_cat,
                            "제목":     e_title.strip() or None,
                            "내용":     e_content.strip(),
                            "중요표시": int(e_imp),
                        })
                        del st.session_state[f"editing_{nid}"]
                        st.toast("메모가 수정되었습니다.", icon="✅")
                        st.rerun()
                if cancel_edit:
                    del st.session_state[f"editing_{nid}"]
                    st.rerun()

# ────────────────────────────────────────────────
# TAB 3: 생성 문서
# ────────────────────────────────────────────────
with tab3:
    case_folder = case_folder_path(
        OUTPUT_ROOT, 접수번호,
        case.get("신청인_성명", ""), case.get("피신청인_성명", ""),
    )
    case_folder.mkdir(parents=True, exist_ok=True)

    # 파일 목록 — 재귀적으로 수집 후 하위 폴더별 그룹화
    def _collect_files(root: Path):
        """(relative_folder_label, file_path) 목록 반환"""
        result = []
        if not root.exists():
            return result
        for f in sorted(root.rglob("*")):
            if f.is_file():
                rel = f.relative_to(root).parts
                folder_label = " / ".join(rel[:-1]) if len(rel) > 1 else ""
                result.append((folder_label, f))
        return result

    all_files = _collect_files(case_folder)

    with st.container(border=True):
        st.markdown('**📁 사건 폴더 파일 목록**')
        if all_files:
            cur_folder = None
            for folder_label, f in all_files:
                if folder_label != cur_folder:
                    cur_folder = folder_label
                    label_text = f"📂 {folder_label}" if folder_label else "📂 사건 폴더 (최상위)"
                    st.markdown(
                        f'<div style="margin-top:10px;margin-bottom:4px;'
                        f'font-size:11px;font-weight:700;color:#64748B;'
                        f'letter-spacing:0.3px">{label_text}</div>',
                        unsafe_allow_html=True,
                    )
                size_kb = f.stat().st_size / 1024
                mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
                ext = f.suffix.lower()
                icon = {".hwpx": "📄", ".xlsx": "📊", ".xls": "📊",
                        ".png": "🖼️", ".pdf": "📕"}.get(ext, "📎")
                st.markdown(
                    f'<div style="display:flex;align-items:center;gap:10px;'
                    f'padding:6px 4px 6px 16px;border-bottom:1px solid #F1F5F9">'
                    f'<span style="font-size:1rem">{icon}</span>'
                    f'<span style="flex:1;font-size:0.88rem">{f.name}</span>'
                    f'<span style="font-size:0.75rem;color:#94A3B8">{size_kb:.1f} KB</span>'
                    f'<span style="font-size:0.75rem;color:#94A3B8;margin-left:12px">{mtime}</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.info("아직 생성된 문서가 없습니다. 공문·통보서 등을 생성하면 여기에 표시됩니다.")

        st.markdown(f'<p style="font-size:0.78rem;color:#94A3B8;margin-top:8px">'
                    f'폴더 경로: <code>{case_folder}</code></p>', unsafe_allow_html=True)

        if st.button("📂 탐색기에서 열기"):
            import subprocess
            subprocess.Popen(f'explorer "{case_folder}"')

# ── 사이드바 빠른 이동
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 다른 사건 조회")
other = st.sidebar.text_input("접수번호 입력", key="sidebar_other_case")
if other and st.sidebar.button("이동", use_container_width=True):
    st.query_params["case"] = other.strip()
    st.rerun()
