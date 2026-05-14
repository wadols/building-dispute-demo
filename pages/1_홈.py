"""
홈 대시보드 — KPI · 월별 추이 · 분쟁유형 · 회신 임박 알림
"""
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import (
    init_db, get_all_cases,
    get_stats_by_period, get_monthly_counts, get_deadline_cases,
)
from core.status_resolver import resolve_status, STATUS_COLORS
from core.ui_styles import inject_css, page_header, status_badge

st.set_page_config(page_title="홈", page_icon="🏠", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("⚖️", "집합건물 분쟁조정위원회 관리시스템", "경기도")

try:
    import altair as alt
    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False

cur_year = date.today().year

# ══════════════════════════════════════════════
# 데이터 로드
# ══════════════════════════════════════════════
@st.cache_data(ttl=30)
def load_dashboard(year):
    start = f"{year}-01-01"
    end   = f"{year}-12-31"
    stats   = get_stats_by_period(start, end)
    monthly = get_monthly_counts(year)
    urgent  = [dict(r) for r in get_deadline_cases(days=7)]
    all_rows = [dict(r) for r in get_all_cases(year=year)]
    for r in all_rows:
        r["진행상태"] = resolve_status(r)
    return stats, monthly, urgent, all_rows

# 연도 선택
year_col, _ = st.columns([1, 5])
with year_col:
    sel_year = st.selectbox("조회 연도", [str(y) for y in range(cur_year, cur_year-6, -1)],
                             label_visibility="collapsed")

stats, monthly, urgent, all_rows = load_dashboard(int(sel_year))

# ══════════════════════════════════════════════
# KPI 카드
# ══════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5)
kpi_data = [
    (k1, stats["접수건수"],  "전체 접수",     "#1A56A0"),
    (k2, stats["처리중"],    "진행 중",       "#F39C12"),
    (k3, stats["종결"],      "종결",          "#27AE60"),
    (k4, stats["개최건수"],  "위원회 개최 수", "#7C3AED"),
    (k5, stats["성립건수"],  "조정 성립 건",  "#059669"),
]
for col, val, label, color in kpi_data:
    with col:
        st.markdown(f"""
        <div class="kpi-card" style="border-top-color:{color}">
            <div class="kpi-value">{val}</div>
            <div class="kpi-label">{label}</div>
        </div>""", unsafe_allow_html=True)

st.markdown('<div style="height:8px"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 회신 임박 알림
# ══════════════════════════════════════════════
if urgent:
    with st.expander(f"⚠️ 7일 이내 회신기한 사건 {len(urgent)}건", expanded=True):
        for c in urgent:
            remain = (date.fromisoformat(c["회신기한"]) - date.today()).days
            color  = "#E74C3C" if remain <= 0 else "#E67E22" if remain <= 3 else "#F39C12"
            badge  = f'<span style="background:{color};color:#fff;padding:2px 8px;border-radius:10px;font-size:0.78rem;">D{"+" if remain<0 else "-"}{abs(remain)}</span>'
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:4px 0;">'
                f'{badge} <b>{c["접수번호"]}</b> {c.get("건물명") or c["지역"]} — '
                f'{c["신청인_성명"]} vs {c["피신청인_성명"]} '
                f'<span style="color:#64748B;font-size:0.82rem;">회신기한: {c["회신기한"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ══════════════════════════════════════════════
# 차트 2열
# ══════════════════════════════════════════════
ch1, ch2 = st.columns(2)

with ch1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 📈 월별 접수·종결 추이")
    if monthly and HAS_ALTAIR:
        rows = []
        for r in monthly:
            rows.append({"월": f"{r['월']}월", "구분": "접수", "건수": r["접수"]})
            rows.append({"월": f"{r['월']}월", "구분": "종결", "건수": r["종결"]})
        df_m = pd.DataFrame(rows)

        color_scale = alt.Scale(domain=["접수", "종결"], range=["#1A56A0", "#10B981"])

        bars = (
            alt.Chart(df_m)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=18)
            .encode(
                x=alt.X("월:O", sort=None,
                         axis=alt.Axis(labelAngle=0, labelFontSize=11, titleOpacity=0)),
                y=alt.Y("건수:Q",
                         axis=alt.Axis(grid=True, gridColor="#F1F5F9", tickCount=5,
                                        labelFontSize=10, titleOpacity=0)),
                color=alt.Color("구분:N", scale=color_scale,
                                 legend=alt.Legend(orient="top", title=None,
                                                    labelFontSize=11, symbolSize=80)),
                xOffset=alt.XOffset("구분:N"),
                tooltip=[alt.Tooltip("월:O", title="월"),
                          alt.Tooltip("구분:N", title="구분"),
                          alt.Tooltip("건수:Q", title="건수")],
                opacity=alt.condition(
                    alt.datum.건수 > 0, alt.value(1.0), alt.value(0.35)
                ),
            )
        )

        labels = (
            alt.Chart(df_m)
            .mark_text(dy=-6, fontSize=10, fontWeight="bold", color="#374151")
            .encode(
                x=alt.X("월:O", sort=None),
                y=alt.Y("건수:Q"),
                xOffset=alt.XOffset("구분:N"),
                text=alt.Text("건수:Q"),
                opacity=alt.condition(alt.datum.건수 > 0, alt.value(1), alt.value(0)),
            )
        )

        chart = (bars + labels).properties(height=230).configure_view(strokeWidth=0)
        st.altair_chart(chart, use_container_width=True)
    elif monthly:
        df_m = pd.DataFrame(monthly)
        df_m["월"] = df_m["월"].astype(str) + "월"
        st.bar_chart(df_m.set_index("월")[["접수", "종결"]], height=220)
    else:
        st.info(f"{sel_year}년 접수 데이터가 없습니다.")
    st.markdown('</div>', unsafe_allow_html=True)

with ch2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown("#### 🥧 분쟁유형별 현황")
    if stats["분쟁유형별"] and HAS_ALTAIR:
        df_d = pd.DataFrame(stats["분쟁유형별"]).rename(columns={"분쟁유형":"유형","cnt":"건수"})
        df_d["유형"] = df_d["유형"].fillna("미분류")
        df_d["유형표시"] = df_d["유형"] + " " + df_d["건수"].astype(str)

        DONUT_COLORS = [
            "#1A56A0", "#10B981", "#F59E0B", "#EF4444",
            "#8B5CF6", "#06B6D4", "#F97316", "#64748B",
        ]
        domain = df_d["유형표시"].tolist()
        rng    = DONUT_COLORS[:len(domain)]

        chart2 = (
            alt.Chart(df_d)
            .mark_arc(innerRadius=52, outerRadius=95, stroke="#fff", strokeWidth=2)
            .encode(
                theta=alt.Theta("건수:Q"),
                color=alt.Color("유형표시:N",
                                 scale=alt.Scale(domain=domain, range=rng),
                                 legend=alt.Legend(orient="right", title=None,
                                                    labelFontSize=11, symbolSize=80)),
                tooltip=[alt.Tooltip("유형:N", title="유형"),
                          alt.Tooltip("건수:Q", title="건수")],
            )
            .properties(height=230)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart2, use_container_width=True)
    elif stats["분쟁유형별"]:
        df_d = pd.DataFrame(stats["분쟁유형별"]).rename(columns={"분쟁유형":"유형","cnt":"건수"})
        df_d["유형"] = df_d["유형"].fillna("미분류")
        df_d["유형표시"] = df_d["유형"] + " " + df_d["건수"].astype(str)
        st.dataframe(df_d[["유형표시","건수"]], use_container_width=True,
                      hide_index=True, height=220)
    else:
        st.info("데이터 없음")
    st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 진행상태별 목록
# ══════════════════════════════════════════════
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown("#### 📋 진행 중 사건 현황")
active = [r for r in all_rows if r["진행상태"] != "종결"]
if active:
    df_a = pd.DataFrame(active)[["접수번호","지역","건물명","신청인_성명","피신청인_성명","분쟁유형","회신기한","진행상태"]]
    st.dataframe(
        df_a,
        use_container_width=True,
        hide_index=True,
        height=min(80 + len(df_a)*35, 350),
        column_config={
            "접수번호":     st.column_config.TextColumn("접수번호",  width="medium"),
            "지역":         st.column_config.TextColumn("지역",      width="small"),
            "건물명":       st.column_config.TextColumn("건물명",    width="medium"),
            "신청인_성명":  st.column_config.TextColumn("신청인",    width="medium"),
            "피신청인_성명":st.column_config.TextColumn("피신청인",  width="medium"),
            "분쟁유형":     st.column_config.TextColumn("유형",      width="small"),
            "회신기한":     st.column_config.DateColumn("회신기한",  width="small", format="YYYY-MM-DD"),
            "진행상태":     st.column_config.TextColumn("상태",      width="small"),
        },
    )
else:
    st.info(f"{sel_year}년 진행 중인 사건이 없습니다.")
st.markdown('</div>', unsafe_allow_html=True)
