"""
위원회 개최 — 개최 등록 / 결과 입력 / 위원 배정
"""
import streamlit as st
import streamlit.components.v1 as components
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
from core.hwpx_handler import generate_hearing_docs, generate_result_docs
from core.excel_handler import generate_docheong_visit, generate_susang_excel, generate_result_susang_excel

if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("🏛️", "위원회 개최", "개최 등록 · 위원 배정 · 결과 입력")

# 등록/결과입력 완료 후 목록 탭으로 자동 이동
if st.session_state.pop("_go_to_hearing_list", False):
    components.html(
        "<script>setTimeout(function(){"
        "var tabs=window.parent.document.querySelectorAll('[data-baseweb=\"tab\"]');"
        "if(tabs.length>0)tabs[0].click();"
        "},300);</script>",
        height=0,
    )

tab_list, tab_add, tab_result, tab_docs = st.tabs(["📋 개최 목록", "➕ 개최 등록", "✏️ 결과 입력", "📄 문서 생성"])

# ══════════════════════════════════════════════
# 탭1: 개최 목록
# ══════════════════════════════════════════════
with tab_list:
    cur_year = date.today().year
    year_opts = ["전체"] + [str(y) for y in range(2050, 2025, -1)]

    fc1, fc2 = st.columns([2, 5])
    with fc1:
        default_idx = year_opts.index(str(cur_year)) if str(cur_year) in year_opts else 0
        year_sel = st.selectbox("연도", year_opts, index=default_idx, label_visibility="collapsed")

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
    inp_agenda = st.text_area("상정안건", key="new_h_agenda", height=100)
    inp_note   = st.text_area("비고", key="new_h_note", height=100)

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
                for k in ["new_h_case_label", "new_h_round", "new_h_place",
                           "new_h_dt", "new_h_agenda", "new_h_note", "new_h_members"]:
                    st.session_state.pop(k, None)
                st.session_state["_go_to_hearing_list"] = True
                st.rerun()

# ══════════════════════════════════════════════
# 탭3: 결과 입력
# ══════════════════════════════════════════════
with tab_result:
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

            # 사건 자동 업데이트 미리보기
            CASE_UPDATE_MAP = {
                "성립":   {"결과": "조정성립",   "종결일자": date.today().isoformat()},
                "불성립": {"결과": "조정불성립", "종결일자": date.today().isoformat()},
                "취소":   {"결과": "조정중지"},
            }
            if res_outcome in CASE_UPDATE_MAP:
                preview = CASE_UPDATE_MAP[res_outcome]
                preview_parts = [f"**{k}** → {v}" for k, v in preview.items()]
                st.info(
                    f"💡 저장 시 **{h['접수번호']}** 사건이 자동 업데이트됩니다: "
                    + " · ".join(preview_parts)
                )

            if st.button("💾 결과 저장", use_container_width=True, type="primary"):
                if not res_outcome:
                    st.error("개최 결과를 선택하세요.")
                else:
                    update_hearing(int(hearing_id_inp), {
                        "개최결과": res_outcome,
                        "조정내용": res_content.strip() or None,
                    })
                    # 사건 자동 종결 처리
                    if res_outcome in CASE_UPDATE_MAP:
                        from core.db import update_case
                        update_case(h["접수번호"], CASE_UPDATE_MAP[res_outcome])
                    st.cache_data.clear()
                    st.session_state.pop("res_hearing_sel", None)
                    st.session_state.pop("res_outcome", None)
                    st.session_state.pop("res_content", None)
                    st.session_state["_go_to_hearing_list"] = True
                    st.toast("결과가 저장되었습니다.", icon="✅")
                    st.rerun()
        else:
            st.error("존재하지 않는 개최 ID입니다.")

# ══════════════════════════════════════════════
# 탭4: 문서 생성
# ══════════════════════════════════════════════
with tab_docs:
    st.markdown("#### 개최 문서 일괄 생성")
    st.caption("개최 일정을 선택하면 관련 hwpx 문서 8종을 자동으로 생성합니다.")

    all_hearings_d = get_all_hearings()
    doc_opts = {
        f"{dict(r)['접수번호']} {dict(r).get('회차', '')}회차  ({(dict(r).get('개최예정일시') or '')[:10]})": dict(r)["id"]
        for r in all_hearings_d
    }

    doc_sel = st.selectbox(
        "개최 일정 선택",
        [""] + list(doc_opts.keys()),
        label_visibility="collapsed",
        placeholder="문서를 생성할 개최 일정을 선택하세요",
        key="doc_hearing_sel",
    )

    # 선택 바뀌면 이전 생성 경로 초기화
    if st.session_state.get("_doc_sel_prev") != doc_sel:
        for k in ["_hearing_docs_folder", "_result_docs_folder"]:
            st.session_state.pop(k, None)
        st.session_state["_doc_sel_prev"] = doc_sel

    if doc_sel:
        hid = doc_opts[doc_sel]
        h   = dict(get_hearing(hid))
        c   = dict(get_case(h["접수번호"]))
        mems = [dict(m) for m in get_hearing_members(hid)]

        st.info(
            f"📌 **{h['접수번호']}** {h.get('회차','')}회차 | "
            f"{(h.get('개최예정일시') or '')[:16]} | "
            f"{h.get('개최장소','')}"
        )

        if mems:
            role_order = {"위원장": 0, "위원": 1, "간사": 2}
            sorted_mems = sorted(mems, key=lambda m: role_order.get(m.get("역할", "위원"), 1))
            mem_text = " · ".join(
                f"{m['성명']}({m.get('역할','위원')})" for m in sorted_mems
            )
            st.markdown(f"**참석 위원:** {mem_text}")
        else:
            st.warning("참석 위원이 배정되지 않았습니다. '개최 등록' 탭에서 위원을 배정하세요.")

        with st.expander("생성될 문서 목록", expanded=True):
            doc_names = [
                "개최알림_참석요청 공문",
                "참석위원명단",
                "개최계획",
                "조정서",
                "간사 시나리오",
                "위원장 시나리오",
                "위원 서명부",
                "제안서 수령증",
            ]
            for name in doc_names:
                st.markdown(f"- `{name}_{h['접수번호']}_{h.get('회차',1)}차.hwpx`")

        st.markdown("---")
        col_hwpx, col_excel = st.columns(2)

        with col_hwpx:
            if st.button("📄 문서 8종 일괄 생성", type="primary", use_container_width=True):
                with st.spinner("문서 생성 중..."):
                    try:
                        generated = generate_hearing_docs(c, h, mems)
                        st.success(f"✅ {len(generated)}개 문서 생성 완료!")
                        if generated:
                            st.session_state["_hearing_docs_folder"] = str(generated[0].parent)
                        for p in generated:
                            st.markdown(f"- `{p.name}`")
                    except Exception as e:
                        st.error(f"생성 실패: {e}")

            saved_folder = st.session_state.get("_hearing_docs_folder")
            if saved_folder:
                st.caption(f"📁 `{saved_folder}`")
                if st.button("📂 폴더 열기", key="open_hearing_docs", use_container_width=True):
                    import subprocess
                    subprocess.Popen(f'explorer "{saved_folder}"')

        with col_excel:
            if st.button("📊 도청방문등록 엑셀 생성", use_container_width=True):
                with st.spinner("엑셀 생성 중..."):
                    try:
                        excel_path = generate_docheong_visit(c, h, mems)
                        st.success("✅ 도청방문등록 엑셀 생성 완료!")
                        with open(excel_path, "rb") as f:
                            st.download_button(
                                "⬇️ 다운로드",
                                data=f.read(),
                                file_name=excel_path.name,
                                mime="application/vnd.ms-excel",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.error(f"생성 실패: {e}")

        st.markdown("---")
        st.markdown("##### 📋 결과보고 문서")
        col_result1, col_result2 = st.columns(2)

        with col_result1:
            if st.button("📄 결과보고 문서 생성\n(조정결과보고 · 회의록)", use_container_width=True):
                with st.spinner("문서 생성 중..."):
                    try:
                        generated = generate_result_docs(c, h, mems)
                        st.success(f"✅ {len(generated)}개 문서 생성 완료!")
                        for p in generated:
                            st.markdown(f"- `{p.name}`")
                        if generated:
                            st.session_state["_result_docs_folder"] = str(generated[0].parent)
                    except Exception as e:
                        st.error(f"생성 실패: {e}")

            saved_result_folder = st.session_state.get("_result_docs_folder")
            if saved_result_folder:
                st.caption(f"📁 `{saved_result_folder}`")
                if st.button("📂 폴더 열기", key="open_result_docs", use_container_width=True):
                    import subprocess
                    subprocess.Popen(f'explorer "{saved_result_folder}"')

        with col_result2:
            if st.button("💰 수당 지급내역 생성", use_container_width=True):
                with st.spinner("엑셀 생성 중..."):
                    try:
                        susang_path = generate_result_susang_excel(c, h, mems)
                        st.success("✅ 수당 지급내역 생성 완료!")
                        with open(susang_path, "rb") as f:
                            st.download_button(
                                "⬇️ 다운로드",
                                data=f.read(),
                                file_name=susang_path.name,
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                use_container_width=True,
                            )
                    except Exception as e:
                        st.error(f"생성 실패: {e}")
