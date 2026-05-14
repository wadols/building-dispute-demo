"""
접수대장 — 사건 조회·수정·문서 출력
체크박스 1개로 선택 → 하단 버튼으로 원하는 문서 생성
"""
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import init_db, get_all_cases, update_case, get_case
from core.status_resolver import resolve_status, STATUS_COLORS
from core.ui_styles import inject_css, page_header, status_badge
from core.hwpx_handler import generate_hwpx
from core.excel_handler import generate_woopyeonmoa, generate_labeltek

st.set_page_config(page_title="접수대장", page_icon="📂", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("📂", "접수대장", "사건 조회 · 수정 · 문서 출력")

# ══════════════════════════════════════════════
# 데이터 로드
# ══════════════════════════════════════════════
@st.cache_data(ttl=5)
def load_cases(year_sel, status_sel, type_sel, keyword):
    rows = get_all_cases(year=None if year_sel == "전체" else int(year_sel))
    data = []
    for r in rows:
        d = dict(r)
        d["진행상태"] = resolve_status(d)
        data.append(d)
    df = pd.DataFrame(data) if data else pd.DataFrame()
    if df.empty:
        return df
    if status_sel != "전체":
        df = df[df["진행상태"] == status_sel]
    if type_sel != "전체":
        df = df[df["분쟁유형"] == type_sel]
    if keyword:
        kw = keyword.strip().lower()
        mask = (
            df["접수번호"].str.lower().str.contains(kw, na=False)
            | df["신청인_성명"].str.lower().str.contains(kw, na=False)
            | df["피신청인_성명"].str.lower().str.contains(kw, na=False)
            | df["건물명"].fillna("").str.lower().str.contains(kw, na=False)
            | df["지역"].str.lower().str.contains(kw, na=False)
        )
        df = df[mask]
    return df

# ══════════════════════════════════════════════
# 필터 바
# ══════════════════════════════════════════════
st.markdown('<div class="card">', unsafe_allow_html=True)
f1, f2, f3, f4, f5 = st.columns([2, 2, 2, 3, 1])
cur_year = date.today().year
year_opts = ["전체"] + [str(y) for y in range(cur_year, cur_year - 6, -1)]
with f1:
    year_sel = st.selectbox("연도", year_opts, label_visibility="collapsed")
with f2:
    status_sel = st.selectbox("진행상태", ["전체"] + list(STATUS_COLORS.keys()),
                               label_visibility="collapsed")
with f3:
    type_opts = ["전체", "관리비", "하자", "소음·진동", "주차", "공용부분",
                 "층간소음", "관리단 운영", "선거·의결", "기타"]
    type_sel = st.selectbox("분쟁유형", type_opts, label_visibility="collapsed")
with f4:
    keyword = st.text_input("검색", placeholder="접수번호·이름·건물명·지역",
                             label_visibility="collapsed")
with f5:
    if st.button("🔄", use_container_width=True, help="새로고침"):
        st.cache_data.clear()
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

df = load_cases(year_sel, status_sel, type_sel, keyword)

# ══════════════════════════════════════════════
# 요약 KPI
# ══════════════════════════════════════════════
if not df.empty:
    total   = len(df)
    closed  = len(df[df["진행상태"] == "종결"])
    overdue = len(df[df["진행상태"] == "회신지연"])
    urgent  = len(df[df["진행상태"] == "회신임박"])
    st.markdown(f"""
    <div style="display:flex;gap:12px;margin-bottom:14px;flex-wrap:wrap;">
        <div class="kpi-card" style="flex:1;min-width:110px;border-top-color:#1A56A0">
            <div class="kpi-value">{total}</div><div class="kpi-label">조회 건수</div></div>
        <div class="kpi-card" style="flex:1;min-width:110px;border-top-color:#27AE60">
            <div class="kpi-value">{total - closed}</div><div class="kpi-label">진행 중</div></div>
        <div class="kpi-card" style="flex:1;min-width:110px;border-top-color:#BDC3C7">
            <div class="kpi-value">{closed}</div><div class="kpi-label">종결</div></div>
        <div class="kpi-card" style="flex:1;min-width:110px;border-top-color:#E67E22">
            <div class="kpi-value">{urgent}</div><div class="kpi-label">회신임박</div></div>
        <div class="kpi-card" style="flex:1;min-width:110px;border-top-color:#E74C3C">
            <div class="kpi-value">{overdue}</div><div class="kpi-label">회신지연</div></div>
    </div>""", unsafe_allow_html=True)

if df.empty:
    st.info("조건에 맞는 사건이 없습니다.")
    st.stop()

# ══════════════════════════════════════════════
# 메인 테이블  (체크박스 1개)
# ══════════════════════════════════════════════
st.markdown(
    '<p style="font-size:0.82rem;color:#64748B;margin-bottom:6px;">'
    '☑ 체크박스로 사건을 선택한 뒤 아래 버튼으로 원하는 문서를 출력하세요. '
    '지역·건물명·신청인·피신청인·분쟁유형 셀은 직접 편집할 수 있습니다.'
    '</p>',
    unsafe_allow_html=True,
)

SHOW_COLS = ["접수번호", "지역", "건물명", "신청인_성명", "피신청인_성명",
             "분쟁유형", "접수일자", "회신기한", "진행상태"]
EDIT_COLS = ["지역", "건물명", "신청인_성명", "피신청인_성명", "분쟁유형"]

disp = df[SHOW_COLS].copy()
sel_set = st.session_state.get("sel_cases", set())
disp.insert(0, "선택", disp["접수번호"].isin(sel_set))

edited = st.data_editor(
    disp,
    use_container_width=True,
    hide_index=True,
    height=min(80 + len(disp) * 35, 600),
    column_config={
        "선택":         st.column_config.CheckboxColumn("선택", width="small"),
        "접수번호":     st.column_config.TextColumn("접수번호",  width="medium"),
        "지역":         st.column_config.TextColumn("지역",      width="medium"),
        "건물명":       st.column_config.TextColumn("건물명",    width="medium"),
        "신청인_성명":  st.column_config.TextColumn("신청인",    width="medium"),
        "피신청인_성명":st.column_config.TextColumn("피신청인",  width="medium"),
        "분쟁유형":     st.column_config.TextColumn("분쟁유형",  width="small"),
        "접수일자":     st.column_config.DateColumn("접수일자",  width="small", format="YYYY-MM-DD"),
        "회신기한":     st.column_config.DateColumn("회신기한",  width="small", format="YYYY-MM-DD"),
        "진행상태":     st.column_config.TextColumn("진행상태",  width="small"),
    },
    disabled=["접수번호", "접수일자", "회신기한", "진행상태"],
    key="case_table",
)

# 선택 상태 갱신
st.session_state["sel_cases"] = set(
    edited.loc[edited["선택"] == True, "접수번호"].tolist()
)

# 인라인 수정 감지 → DB 저장
changed = []
for _, row in edited.iterrows():
    orig = df[df["접수번호"] == row["접수번호"]]
    if orig.empty:
        continue
    diff = {c: row[c] for c in EDIT_COLS if str(row.get(c,"")) != str(orig.iloc[0].get(c,""))}
    if diff:
        changed.append((row["접수번호"], diff))

if changed:
    for 번호, diff in changed:
        diff["진행상태"] = resolve_status({**dict(df[df["접수번호"]==번호].iloc[0]), **diff})
        update_case(번호, diff)
    st.cache_data.clear()
    st.toast(f"{len(changed)}건 수정 저장됨", icon="💾")

# ══════════════════════════════════════════════
# 하단 문서 출력 버튼
# ══════════════════════════════════════════════
sel_list = sorted(st.session_state.get("sel_cases", set()))
n = len(sel_list)
disabled = (n == 0)

st.markdown('<div style="height:10px"></div>', unsafe_allow_html=True)
st.markdown('<div class="card">', unsafe_allow_html=True)

# 선택 현황
if sel_list:
    badges = "".join(
        f'<span style="background:#EFF6FF;color:#1D4ED8;border:1px solid #BFDBFE;'
        f'padding:2px 8px;border-radius:12px;font-size:0.8rem;margin:2px;">{n}</span>'
        for n in sel_list[:10]
    )
    st.markdown(
        f'<div style="margin-bottom:10px;font-size:0.85rem;">'
        f'<b>선택된 사건 {n}건</b>: {badges}'
        f'{"…" if len(sel_list) > 10 else ""}</div>',
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        '<p style="color:#94A3B8;font-size:0.85rem;margin-bottom:10px;">'
        '위 표에서 사건을 선택하면 버튼이 활성화됩니다.</p>',
        unsafe_allow_html=True,
    )

# 1건 선택 시 수정/상세 바로가기
if n == 1:
    qa, qb = st.columns(2)
    with qa:
        if st.button("✏️ 수정하기", use_container_width=True, type="primary"):
            st.session_state["edit_case"] = sel_list[0]
            # 이전 폼 캐시 제거 후 이동
            for k in list(st.session_state.keys()):
                if k.startswith("_form_ready_") or k.startswith("inp_"):
                    del st.session_state[k]
            st.switch_page("pages/2_신규접수.py")
    with qb:
        if st.button("🔎 상세보기", use_container_width=True):
            st.session_state["detail_case"] = sel_list[0]
            st.switch_page("pages/4_사건상세.py")

def _hwpx_buttons(label, template, prefix, key_prefix):
    """hwpx 생성 + 다운로드 버튼 공통 로직"""
    if st.button(label, use_container_width=True, disabled=disabled):
        cases_data = [dict(get_case(num)) for num in sel_list if get_case(num)]
        ok, fail = [], []
        for case in cases_data:
            num = case["접수번호"]
            try:
                out = generate_hwpx(template, case, f"{prefix}_{num}.hwpx")
                ok.append((num, out))
            except Exception as e:
                fail.append(f"{num}({e})")
        if ok:
            st.success(f"{len(ok)}건 생성 완료")
            for num, path in ok:
                with open(path, "rb") as f:
                    st.download_button(
                        f"⬇ {num} 다운로드",
                        f,
                        file_name=path.name,
                        mime="application/octet-stream",
                        key=f"{key_prefix}_{num}",
                    )
        if fail:
            st.error(f"실패: {', '.join(fail)}")


# 버튼 2줄
r1c1, r1c2, r1c3, r1c4 = st.columns(4)
with r1c1:
    if st.button("📮 우편모아 엑셀", use_container_width=True, disabled=disabled):
        cases_data = [dict(get_case(num)) for num in sel_list if get_case(num)]
        try:
            out = generate_woopyeonmoa(cases_data)
            st.success(f"{len(cases_data)}건 생성 완료")
            with open(out, "rb") as f:
                st.download_button("⬇ 우편모아 다운로드", f,
                                   file_name=out.name,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="dl_woopyon")
        except Exception as e:
            st.error(str(e))
with r1c2:
    if st.button("🏷️ 라벨텍 엑셀", use_container_width=True, disabled=disabled):
        cases_data = [dict(get_case(num)) for num in sel_list if get_case(num)]
        try:
            out = generate_labeltek(cases_data)
            st.success(f"{len(cases_data)}건 생성 완료")
            with open(out, "rb") as f:
                st.download_button("⬇ 라벨텍 다운로드", f,
                                   file_name=out.name,
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="dl_labeltek")
        except Exception as e:
            st.error(str(e))
with r1c3:
    _hwpx_buttons("📄 피신청인 통지 공문",
                  "1. 피신청인_통지_공문.hwpx",
                  "피신청인_통지공문", "dl_notice")
with r1c4:
    if st.button("🗂️ 사건자료 폴더 열기", use_container_width=True, disabled=(n != 1)):
        if sel_list:
            import subprocess
            folder = Path(__file__).parent.parent / "output" / "사건자료" / sel_list[0]
            folder.mkdir(parents=True, exist_ok=True)
            subprocess.Popen(f'explorer "{folder}"')

r2c1, r2c2, r2c3, r2c4 = st.columns(4)
with r2c1:
    _hwpx_buttons("🚫 조정중지 공문",
                  "2. 조정중지 공문.hwpx",
                  "조정중지_공문", "dl_stop")
with r2c2:
    _hwpx_buttons("📋 조정중지 통보서",
                  "3. 조정중지 통보서.hwpx",
                  "조정중지_통보서", "dl_stopnotice")
with r2c3:
    _hwpx_buttons("🚫 불개시 공문",
                  "5. 조정불개시_ 공문.hwpx",
                  "조정불개시_공문", "dl_reject")
with r2c4:
    _hwpx_buttons("📋 불개시 통보서",
                  "4. 조정불개시_통보서.hwpx",
                  "조정불개시_통보서", "dl_rejectnotice")

if sel_list:
    if st.button("☐ 선택 초기화", use_container_width=True):
        st.session_state["sel_cases"] = set()
        st.rerun()

st.markdown('</div>', unsafe_allow_html=True)

# 사이드바는 비워둠 (접수대장에서 직접 선택 → 수정)
