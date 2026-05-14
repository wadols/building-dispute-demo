"""
위원회 개최 — 개최 등록 / 결과 입력 / 위원 배정
"""
import streamlit as st
import pandas as pd
from datetime import date, datetime
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import (
    init_db, get_all_cases, get_case,
    create_hearing, get_hearing, get_all_hearings, update_hearing, delete_hearing,
    get_hearings_by_case,
    get_all_members, set_hearing_members, get_hearing_members,
)
from core.ui_styles import inject_css, page_header, status_badge

st.set_page_config(page_title="위원회 개최", page_icon="🏛️", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("🏛️", "위원회 개최", "개최 등록 · 위원 배정 · 결과 입력")

tab_list, tab_add, tab_result = st.tabs(["📋 개최 목록", "➕ 개최 등록", "✏️ 결과 입력"])

# ══════════════════════════════════════════════
# 탭1: 개최 목록
# ══════════════════════════════════════════════
with tab_list:
    cur_year = date.today().year
    year_opts = ["전체"] + [str(y) for y in range(cur_year, cur_year - 6, -1)]

    fc1, fc2 = st.columns([2, 5])
    with fc1:
        year_sel = st.selectbox("연도", year_opts, label_visibility="collapsed")

    @st.cache_data(ttl=5)
    def load_hearings(yr):
        rows = get_all_hearings(year=None if yr == "전체" else int(yr))
        if not rows:
            return pd.DataFrame()
        data = []
        for r in rows:
            d = dict(r)
            members = get_hearing_members(d["id"])
            d["참석위원"] = ", ".join(m["성명"] for m in members) if members else ""
            data.append(d)
        return pd.DataFrame(data)

    df = load_hearings(year_sel)

    if df.empty:
        st.info("등록된 개최 일정이 없습니다.")
    else:
        total   = len(df)
        done    = len(df[df["개최결과"].notna()]) if "개최결과" in df.columns else 0
        pending = total - done
        st.markdown(f"""
        <div style="display:flex;gap:12px;margin-bottom:14px;">
            <div class="kpi-card" style="flex:1;border-top-color:#1A56A0">
                <div class="kpi-value">{total}</div><div class="kpi-label">전체 개최</div></div>
            <div class="kpi-card" style="flex:1;border-top-color:#F39C12">
                <div class="kpi-value">{pending}</div><div class="kpi-label">결과 미입력</div></div>
            <div class="kpi-card" style="flex:1;border-top-color:#27AE60">
                <div class="kpi-value">{done}</div><div class="kpi-label">결과 입력 완료</div></div>
        </div>""", unsafe_allow_html=True)

        # 순번 컬럼 추가, id 숨김
        base_cols = [c for c in ["id", "접수번호", "회차", "개최예정일시", "개최장소", "개최결과", "참석위원"] if c in df.columns]
        disp = df[base_cols].copy()
        disp.insert(0, "번호", range(1, len(disp) + 1))

        st.dataframe(
            disp,
            use_container_width=True,
            hide_index=True,
            height=min(80 + len(disp) * 35, 500),
            column_config={
                "번호":      st.column_config.NumberColumn("번호",   width="small"),
                "id":        None,   # 숨김
                "접수번호":  st.column_config.TextColumn("접수번호", width="medium"),
                "회차":      st.column_config.NumberColumn("회차",   width="small"),
                "개최예정일시": st.column_config.TextColumn("개최일시", width="medium"),
                "개최장소":  st.column_config.TextColumn("개최장소", width="medium"),
                "개최결과":  st.column_config.TextColumn("결과",     width="small"),
                "참석위원":  st.column_config.TextColumn("참석위원", width="large"),
            },
        )

        # 삭제 — 드롭박스 선택
        st.markdown("---")
        hearing_opts = {
            f"{dict(r)['접수번호']} {dict(r).get('회차','')}회차 ({dict(r).get('개최예정일시','')[:10]})": dict(r)["id"]
            for r in get_all_hearings()
        }
        del_label = st.selectbox("삭제할 개최 선택", [""] + list(hearing_opts.keys()),
                                  label_visibility="collapsed",
                                  placeholder="삭제할 개최 일정을 선택하세요")
        if st.button("🗑️ 개최 삭제", use_container_width=False, disabled=not del_label):
            st.session_state["confirm_del_hearing"] = hearing_opts[del_label]
            st.session_state["confirm_del_hearing_label"] = del_label

        if st.session_state.get("confirm_del_hearing"):
            hid   = st.session_state["confirm_del_hearing"]
            hlabel = st.session_state.get("confirm_del_hearing_label", "")
            st.warning(f"**{hlabel}** 개최를 삭제하시겠습니까?")
            cc1, cc2 = st.columns(2)
            with cc1:
                if st.button("✅ 확인 삭제", key="del_hearing_ok", use_container_width=True):
                    delete_hearing(hid)
                    st.session_state.pop("confirm_del_hearing", None)
                    st.session_state.pop("confirm_del_hearing_label", None)
                    st.cache_data.clear()
                    st.success("삭제 완료")
                    st.rerun()
            with cc2:
                if st.button("❌ 취소", key="del_hearing_cancel", use_container_width=True):
                    st.session_state.pop("confirm_del_hearing", None)
                    st.session_state.pop("confirm_del_hearing_label", None)
                    st.rerun()

# ══════════════════════════════════════════════
# 탭2: 개최 등록
# ══════════════════════════════════════════════
with tab_add:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 개최 정보")

    # 사건 선택
    cases_rows = get_all_cases()
    case_opts  = {f"{dict(r)['접수번호']} — {dict(r).get('건물명','') or dict(r)['지역']}": dict(r)['접수번호']
                  for r in cases_rows}

    c1, c2, c3 = st.columns(3)
    with c1:
        sel_label = st.selectbox("사건 선택 *", [""] + list(case_opts.keys()),
                                  key="new_h_case_label")
        sel_case  = case_opts.get(sel_label, "")
    with c2:
        inp_round = st.number_input("회차 *", min_value=1, step=1, value=1, key="new_h_round")
    with c3:
        inp_place = st.text_input("개최장소", key="new_h_place",
                                   placeholder="경기도청 회의실")

    inp_dt = st.text_input("개최 예정 일시 *", key="new_h_dt",
                            placeholder="예: 2026-06-20 14:00",
                            help="YYYY-MM-DD HH:MM 형식")
    inp_agenda = st.text_area("상정안건", key="new_h_agenda", height=80)
    inp_note   = st.text_area("비고", key="new_h_note", height=60)

    # 참석 위원 선택
    st.markdown("#### 참석 위원 배정")
    members_rows = get_all_members(active_only=True)
    member_opts  = {f"{dict(m)['성명']} ({dict(m).get('소속','') or ''})": dict(m)['id']
                    for m in members_rows}

    if not member_opts:
        st.info("등록된 위원이 없습니다. 위원관리 페이지에서 먼저 위원을 등록하세요.")
        sel_members = []
    else:
        sel_labels = st.multiselect("참석 위원 선택", list(member_opts.keys()),
                                     key="new_h_members")
        # 역할 배정
        role_map = {}
        if sel_labels:
            st.markdown("**역할 배정**")
            role_cols = st.columns(min(len(sel_labels), 4))
            for i, label in enumerate(sel_labels):
                with role_cols[i % 4]:
                    role_map[label] = st.selectbox(
                        label.split(" (")[0],
                        ["위원", "위원장", "간사"],
                        key=f"role_{i}",
                    )
        sel_members = [
            {"member_id": member_opts[lb], "역할": role_map.get(lb, "위원")}
            for lb in sel_labels
        ]

    st.markdown('</div>', unsafe_allow_html=True)

    if st.button("💾 개최 등록", use_container_width=True, type="primary"):
        if not sel_case:
            st.error("사건을 선택하세요.")
        elif not inp_dt:
            st.error("개최 예정 일시를 입력하세요.")
        else:
            try:
                datetime.strptime(inp_dt.strip(), "%Y-%m-%d %H:%M")
            except ValueError:
                st.error("일시 형식이 맞지 않습니다. YYYY-MM-DD HH:MM 형식으로 입력하세요.")
            else:
                data = {
                    "접수번호":     sel_case,
                    "회차":         int(inp_round),
                    "개최예정일시": inp_dt.strip(),
                    "개최장소":     inp_place.strip() or None,
                    "상정안건":     inp_agenda.strip() or None,
                    "비고":         inp_note.strip() or None,
                }
                hid = create_hearing(data)
                if sel_members:
                    set_hearing_members(hid, sel_members)
                st.cache_data.clear()
                st.success(f"개최 등록 완료 (ID: {hid}, 사건: {sel_case} {inp_round}회차)")
                for k in ["new_h_case_label", "new_h_round", "new_h_place",
                           "new_h_dt", "new_h_agenda", "new_h_note", "new_h_members"]:
                    if k in st.session_state:
                        del st.session_state[k]
                st.rerun()

# ══════════════════════════════════════════════
# 탭3: 결과 입력
# ══════════════════════════════════════════════
with tab_result:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 개최 결과 입력")

    all_hearings = get_all_hearings()
    res_opts = {
        f"{dict(r)['접수번호']} {dict(r).get('회차','')}회차 ({dict(r).get('개최예정일시','')[:10]})": dict(r)["id"]
        for r in all_hearings
    }
    res_label = st.selectbox("결과 입력할 개최 선택 *", [""] + list(res_opts.keys()),
                              label_visibility="collapsed",
                              placeholder="개최 일정을 선택하세요",
                              key="res_hearing_sel")
    hearing_id_inp = res_opts.get(res_label) if res_label else None

    if hearing_id_inp:
        h = get_hearing(int(hearing_id_inp))
        if h:
            h = dict(h)
            st.info(f"📌 **{h['접수번호']}** — {h.get('회차','')}회차 | {h.get('개최예정일시','')} | {h.get('개최장소','')}")

            # 현재 위원 목록 표시
            cur_members = get_hearing_members(int(hearing_id_inp))
            if cur_members:
                st.markdown("**참석 위원:** " + ", ".join(
                    f"{m['성명']}({m['역할']})" for m in cur_members
                ))

            rc1, rc2 = st.columns(2)
            with rc1:
                res_outcome = st.selectbox(
                    "개최 결과 *",
                    ["", "성립", "불성립", "연기", "취소"],
                    index=["", "성립", "불성립", "연기", "취소"].index(h.get("개최결과") or ""),
                    key="res_outcome",
                )
            with rc2:
                res_content = st.text_area("조정 내용", value=h.get("조정내용") or "",
                                            key="res_content", height=120)

            if st.button("💾 결과 저장", use_container_width=True, type="primary"):
                if not res_outcome:
                    st.error("개최 결과를 선택하세요.")
                else:
                    update_hearing(int(hearing_id_inp), {
                        "개최결과": res_outcome,
                        "조정내용": res_content.strip() or None,
                    })
                    # 사건 결과 자동 반영
                    case_row = get_case(h["접수번호"])
                    if case_row:
                        from core.db import update_case
                        result_map = {
                            "성립":  "조정성립",
                            "불성립": "조정불성립",
                            "취소":  "조정중지",
                        }
                        if res_outcome in result_map:
                            update_case(h["접수번호"], {"결과": result_map[res_outcome]})
                    st.cache_data.clear()
                    st.success("결과 저장 완료")
                    st.rerun()
        else:
            st.error("존재하지 않는 개최 ID입니다.")

    st.markdown('</div>', unsafe_allow_html=True)
