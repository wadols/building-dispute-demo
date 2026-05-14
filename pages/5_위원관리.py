"""
위원관리 — 위원 등록·수정·비활성화
"""
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import init_db, get_all_members, create_member, update_member, delete_member, get_member
from core.ui_styles import inject_css, page_header

st.set_page_config(page_title="위원관리", page_icon="👥", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("👥", "위원관리", "집합건물 분쟁조정위원회 위원 등록 · 수정 · 관리")

# ══════════════════════════════════════════════
# 상단 탭: 위원 목록 / 신규 등록
# ══════════════════════════════════════════════
tab_list, tab_add = st.tabs(["📋 위원 목록", "➕ 신규 등록"])

# ──────────────────────────────────────────────
# 탭1: 위원 목록
# ──────────────────────────────────────────────
with tab_list:
    show_all = st.checkbox("비활성 위원 포함", value=False)

    @st.cache_data(ttl=5)
    def load_members(active_only):
        rows = get_all_members(active_only=active_only)
        if not rows:
            return pd.DataFrame()
        data = [dict(r) for r in rows]
        df = pd.DataFrame(data)
        # 생년월일: 문자열 → date 타입으로 변환 (DateColumn 호환)
        if "생년월일" in df.columns:
            df["생년월일"] = pd.to_datetime(df["생년월일"], errors="coerce").dt.date
        return df

    df = load_members(active_only=not show_all)

    if df.empty:
        st.info("등록된 위원이 없습니다. '신규 등록' 탭에서 추가하세요.")
    else:
        # KPI
        total   = len(df)
        active  = int(df["활성여부"].sum()) if "활성여부" in df.columns else total
        st.markdown(f"""
        <div style="display:flex;gap:12px;margin-bottom:14px;">
            <div class="kpi-card" style="flex:1;border-top-color:#1A56A0">
                <div class="kpi-value">{total}</div><div class="kpi-label">전체 위원</div></div>
            <div class="kpi-card" style="flex:1;border-top-color:#27AE60">
                <div class="kpi-value">{active}</div><div class="kpi-label">재직 중</div></div>
            <div class="kpi-card" style="flex:1;border-top-color:#BDC3C7">
                <div class="kpi-value">{total - active}</div><div class="kpi-label">비활성</div></div>
        </div>""", unsafe_allow_html=True)

        # 순번 컬럼 추가 (1, 2, 3…), id는 수정 추적용으로만 유지
        SHOW_COLS = ["번호", "id", "성명", "소속", "직위", "핸드폰번호", "생년월일", "은행명", "계좌번호", "활성여부"]
        disp = df[[c for c in ["id", "성명", "소속", "직위", "핸드폰번호",
                                "생년월일", "은행명", "계좌번호", "활성여부"] if c in df.columns]].copy()
        disp.insert(0, "번호", range(1, len(disp) + 1))

        edited = st.data_editor(
            disp,
            use_container_width=True,
            hide_index=True,
            height=min(80 + len(disp) * 35, 500),
            column_config={
                "번호":     st.column_config.NumberColumn("번호",   width="small"),
                "id":       None,   # 숨김
                "성명":     st.column_config.TextColumn("성명",     width="medium"),
                "소속":     st.column_config.TextColumn("소속",     width="medium"),
                "직위":     st.column_config.TextColumn("직위",     width="small"),
                "핸드폰번호": st.column_config.TextColumn("핸드폰", width="medium"),
                "생년월일": st.column_config.DateColumn("생년월일", width="small", format="YYYY-MM-DD",
                                                         min_value=date(1950, 1, 1),
                                                         max_value=date(2026, 12, 31)),
                "은행명":   st.column_config.TextColumn("은행명",   width="small"),
                "계좌번호": st.column_config.TextColumn("계좌번호", width="medium"),
                "활성여부": st.column_config.CheckboxColumn("재직", width="small"),
            },
            disabled=["번호", "id"],
            key="member_table",
        )

        # 인라인 수정 감지 → DB 저장
        EDIT_COLS = ["성명", "소속", "직위", "핸드폰번호", "생년월일", "은행명", "계좌번호", "활성여부"]
        changed = []
        for _, row in edited.iterrows():
            orig = df[df["id"] == row["id"]]
            if orig.empty:
                continue
            diff = {c: row[c] for c in EDIT_COLS
                    if c in row and c in orig.columns
                    and str(row.get(c, "")) != str(orig.iloc[0].get(c, ""))}
            if diff:
                changed.append((int(row["id"]), diff))

        if changed:
            for mid, diff in changed:
                update_member(mid, diff)
            st.cache_data.clear()
            st.toast(f"{len(changed)}건 수정 저장됨", icon="💾")

        # 삭제 — 이름 선택 방식
        st.markdown("---")
        name_to_id = {f"{dict(r)['성명']} ({dict(r).get('소속','') or ''})": dict(r)["id"]
                      for r in get_all_members(active_only=False)}
        del_label = st.selectbox("삭제할 위원 선택", [""] + list(name_to_id.keys()),
                                  label_visibility="collapsed",
                                  placeholder="삭제할 위원을 선택하세요")
        if st.button("🗑️ 위원 삭제", use_container_width=False, disabled=not del_label):
            st.session_state["confirm_del_member"] = name_to_id[del_label]
            st.session_state["confirm_del_name"]   = del_label

        if st.session_state.get("confirm_del_member"):
            mid  = st.session_state["confirm_del_member"]
            name = st.session_state.get("confirm_del_name", "")
            st.warning(f"**{name}** 위원을 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.")
            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ 확인 삭제", use_container_width=True):
                    delete_member(mid)
                    st.session_state.pop("confirm_del_member", None)
                    st.session_state.pop("confirm_del_name", None)
                    st.cache_data.clear()
                    st.success("삭제 완료")
                    st.rerun()
            with c2:
                if st.button("❌ 취소", use_container_width=True):
                    st.session_state.pop("confirm_del_member", None)
                    st.session_state.pop("confirm_del_name", None)
                    st.rerun()

# ──────────────────────────────────────────────
# 탭2: 신규 등록
# ──────────────────────────────────────────────
with tab_add:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 위원 정보 입력")

    c1, c2, c3 = st.columns(3)
    with c1:
        inp_name   = st.text_input("성명 *", key="new_성명", placeholder="홍길동")
        inp_org    = st.text_input("소속", key="new_소속", placeholder="○○대학교")
    with c2:
        inp_pos    = st.text_input("직위", key="new_직위", placeholder="교수")
        inp_phone  = st.text_input("핸드폰번호", key="new_핸드폰번호", placeholder="010-0000-0000")
    with c3:
        inp_birth  = st.date_input("생년월일", key="new_생년월일", value=None,
                                    min_value=date(1950, 1, 1),
                                    max_value=date(2026, 12, 31))
        inp_active = st.checkbox("재직 중", key="new_활성여부", value=True)

    c4, c5 = st.columns(2)
    with c4:
        inp_bank   = st.text_input("은행명", key="new_은행명", placeholder="국민은행")
    with c5:
        inp_acct   = st.text_input("계좌번호", key="new_계좌번호", placeholder="000-00-000000")

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 위원 등록", use_container_width=True, type="primary"):
        name = st.session_state.get("new_성명", "").strip()
        if not name:
            st.error("성명은 필수 입력 항목입니다.")
        else:
            data = {
                "성명":       name,
                "소속":       st.session_state.get("new_소속", "") or None,
                "직위":       st.session_state.get("new_직위", "") or None,
                "핸드폰번호": st.session_state.get("new_핸드폰번호", "") or None,
                "생년월일":   str(inp_birth) if inp_birth else None,
                "은행명":     st.session_state.get("new_은행명", "") or None,
                "계좌번호":   st.session_state.get("new_계좌번호", "") or None,
                "활성여부":   1 if st.session_state.get("new_활성여부", True) else 0,
            }
            create_member(data)
            st.cache_data.clear()
            st.success(f"**{name}** 위원이 등록되었습니다.")
            # 입력 필드 초기화
            for k in ["new_성명", "new_소속", "new_직위", "new_핸드폰번호",
                      "new_은행명", "new_계좌번호"]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
