"""
위원관리 — 위원 등록·수정·삭제
"""
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import init_db, get_all_members, create_member, update_member, delete_member, get_member
from core.ui_styles import inject_css, page_header

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("👥", "위원관리", "집합건물 분쟁조정위원회 위원 등록 · 수정 · 관리")

# 신규 등록 완료 후 목록 탭으로 자동 이동
if st.session_state.pop("_go_to_list", False):
    components.html(
        "<script>setTimeout(function(){"
        "var tabs=window.parent.document.querySelectorAll('[data-baseweb=\"tab\"]');"
        "if(tabs.length>0)tabs[0].click();"
        "},300);</script>",
        height=0,
    )

tab_list, tab_add = st.tabs(["📋 위원 목록", "➕ 신규 등록"])

# ══════════════════════════════════════════════
# 탭1: 위원 목록 (클릭 → 수정/삭제)
# ══════════════════════════════════════════════
with tab_list:
    show_all = st.checkbox("비활성 위원 포함", value=False)

    @st.cache_data(ttl=5)
    def load_members(active_only):
        rows = get_all_members(active_only=active_only)
        if not rows:
            return pd.DataFrame(), []
        raw = [dict(r) for r in rows]
        df  = pd.DataFrame(raw)
        if "생년월일" in df.columns:
            df["생년월일"] = pd.to_datetime(df["생년월일"], errors="coerce").dt.date
        return df, raw

    df, raw_list = load_members(active_only=not show_all)

    if df.empty:
        st.info("등록된 위원이 없습니다. '신규 등록' 탭에서 추가하세요.")
    else:
        total  = len(df)
        active = int(df["활성여부"].sum()) if "활성여부" in df.columns else total
        st.markdown(f"""
        <div style="display:flex;gap:12px;margin-bottom:14px;">
            <div class="kpi-card" style="flex:1;border-top-color:#1A56A0">
                <div class="kpi-value">{total}</div><div class="kpi-label">전체 위원</div></div>
            <div class="kpi-card" style="flex:1;border-top-color:#27AE60">
                <div class="kpi-value">{active}</div><div class="kpi-label">재직 중</div></div>
            <div class="kpi-card" style="flex:1;border-top-color:#BDC3C7">
                <div class="kpi-value">{total - active}</div><div class="kpi-label">비활성</div></div>
        </div>""", unsafe_allow_html=True)

        st.caption("📌 위원을 클릭하면 수정 · 삭제할 수 있습니다.")

        # 표시용 컬럼만 추출 (id는 row 매핑용으로 유지)
        show_cols = [c for c in ["id", "성명", "소속", "직위", "핸드폰번호", "생년월일", "활성여부"] if c in df.columns]
        disp = df[show_cols].copy()
        disp.insert(0, "번호", range(1, len(disp) + 1))

        event = st.dataframe(
            disp,
            use_container_width=True,
            hide_index=True,
            height=min(80 + len(disp) * 35, 420),
            on_select="rerun",
            selection_mode="single-row",
            column_config={
                "번호":       st.column_config.NumberColumn("번호",   width="small"),
                "id":         None,  # 숨김
                "성명":       st.column_config.TextColumn("성명",     width="medium"),
                "소속":       st.column_config.TextColumn("소속",     width="large"),
                "직위":       st.column_config.TextColumn("직위",     width="small"),
                "핸드폰번호": st.column_config.TextColumn("핸드폰",   width="medium"),
                "생년월일":   st.column_config.DateColumn("생년월일", width="small", format="YYYY-MM-DD"),
                "활성여부":   st.column_config.CheckboxColumn("재직",  width="small"),
            },
        )

        # 선택된 행 처리
        selected_rows = event.selection.rows if event.selection else []

        if not selected_rows:
            st.info("위원을 클릭하면 수정·삭제 폼이 표시됩니다.", icon="👆")
        else:
            row_idx = selected_rows[0]
            sel_id  = int(disp.iloc[row_idx]["id"])
            sel_row = dict(get_member(sel_id))

            st.markdown("---")
            st.markdown(f"### ✏️ {sel_row['성명']} 위원")

            c1, c2, c3 = st.columns(3)
            with c1:
                e_name  = st.text_input("성명 *",    value=sel_row.get("성명", ""),        key="e_성명")
                e_org   = st.text_input("소속",       value=sel_row.get("소속", "") or "",  key="e_소속")
            with c2:
                e_pos   = st.text_input("직위",       value=sel_row.get("직위", "") or "",  key="e_직위")
                e_phone = st.text_input("핸드폰번호", value=sel_row.get("핸드폰번호", "") or "", key="e_핸드폰번호")
            with c3:
                birth_val = None
                if sel_row.get("생년월일"):
                    try:
                        p = str(sel_row["생년월일"]).split("-")
                        birth_val = date(int(p[0]), int(p[1]), int(p[2]))
                    except Exception:
                        pass
                e_birth  = st.date_input("생년월일", value=birth_val, key="e_생년월일",
                                          min_value=date(1950, 1, 1), max_value=date(2030, 12, 31))
                e_active = st.checkbox("재직 중", value=bool(sel_row.get("활성여부", 1)), key="e_활성여부")

            c4, c5 = st.columns(2)
            with c4:
                e_bank = st.text_input("은행명",   value=sel_row.get("은행명", "") or "",   key="e_은행명")
            with c5:
                e_acct = st.text_input("계좌번호", value=sel_row.get("계좌번호", "") or "", key="e_계좌번호")

            e_career = st.text_area(
                "최종학력 및 경력",
                value=sel_row.get("최종학력 및 경력") or "",
                height=130,
                key="e_career",
                placeholder="예)\n서울대학교 법학과 졸업\n법무법인 ○○ 변호사 (2010~2020)",
            )

            col_save, col_del = st.columns([4, 1])
            with col_save:
                if st.button("💾 수정 저장", type="primary", use_container_width=True):
                    if not e_name.strip():
                        st.error("성명은 필수입니다.")
                    else:
                        update_member(sel_id, {
                            "성명":             e_name.strip(),
                            "소속":             e_org.strip() or None,
                            "직위":             e_pos.strip() or None,
                            "핸드폰번호":       e_phone.strip() or None,
                            "생년월일":         str(e_birth) if e_birth else None,
                            "은행명":           e_bank.strip() or None,
                            "계좌번호":         e_acct.strip() or None,
                            "최종학력 및 경력": e_career.strip() or None,
                            "활성여부":         1 if e_active else 0,
                        })
                        st.cache_data.clear()
                        st.success(f"**{e_name}** 위원 정보가 저장되었습니다.")
                        st.rerun()

            with col_del:
                if st.button("🗑️ 삭제", use_container_width=True):
                    st.session_state["confirm_del"] = sel_id

            if st.session_state.get("confirm_del") == sel_id:
                st.warning(f"**{sel_row['성명']}** 위원을 삭제하시겠습니까? 되돌릴 수 없습니다.")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("✅ 확인 삭제", use_container_width=True, key="del_ok"):
                        delete_member(sel_id)
                        st.session_state.pop("confirm_del", None)
                        st.cache_data.clear()
                        st.success("삭제 완료")
                        st.rerun()
                with cc2:
                    if st.button("❌ 취소", use_container_width=True, key="del_cancel"):
                        st.session_state.pop("confirm_del", None)
                        st.rerun()

# ══════════════════════════════════════════════
# 탭2: 신규 등록
# ══════════════════════════════════════════════
with tab_add:
    # 등록할 때마다 카운터를 올려서 모든 위젯 키를 새로 만들어 초기화
    fk = st.session_state.get("_new_member_fk", 0)

    st.markdown("#### 위원 정보 입력")

    c1, c2, c3 = st.columns(3)
    with c1:
        inp_name  = st.text_input("성명 *",     key=f"new_성명_{fk}",       placeholder="홍길동")
        inp_org   = st.text_input("소속",        key=f"new_소속_{fk}",       placeholder="○○대학교")
    with c2:
        inp_pos   = st.text_input("직위",        key=f"new_직위_{fk}",       placeholder="교수")
        inp_phone = st.text_input("핸드폰번호",  key=f"new_핸드폰번호_{fk}", placeholder="010-0000-0000")
    with c3:
        inp_birth  = st.date_input("생년월일", key=f"new_생년월일_{fk}", value=None,
                                    min_value=date(1950, 1, 1), max_value=date(2030, 12, 31))
        inp_active = st.checkbox("재직 중", key=f"new_활성여부_{fk}", value=True)

    c4, c5 = st.columns(2)
    with c4:
        inp_bank = st.text_input("은행명",   key=f"new_은행명_{fk}",   placeholder="국민은행")
    with c5:
        inp_acct = st.text_input("계좌번호", key=f"new_계좌번호_{fk}", placeholder="000-00-000000")

    inp_career = st.text_area(
        "최종학력 및 경력",
        key=f"new_career_{fk}",
        height=130,
        placeholder="예)\n서울대학교 법학과 졸업\n법무법인 ○○ 변호사 (2010~2020)\n경기도 집합건물분쟁조정위원회 위원 (2021~현재)",
    )

    if st.button("💾 위원 등록", use_container_width=True, type="primary"):
        name = inp_name.strip()
        if not name:
            st.error("성명은 필수 입력 항목입니다.")
        else:
            create_member({
                "성명":             name,
                "소속":             inp_org.strip() or None,
                "직위":             inp_pos.strip() or None,
                "핸드폰번호":       inp_phone.strip() or None,
                "생년월일":         str(inp_birth) if inp_birth else None,
                "은행명":           inp_bank.strip() or None,
                "계좌번호":         inp_acct.strip() or None,
                "최종학력 및 경력": inp_career.strip() or None,
                "활성여부":         1 if inp_active else 0,
            })
            st.cache_data.clear()
            # 카운터 증가 → 다음 렌더링에서 모든 입력 필드가 새 키로 빈 값으로 초기화됨
            st.session_state["_new_member_fk"] = fk + 1
            st.session_state["_go_to_list"] = True
            st.rerun()
