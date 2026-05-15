"""
홈 대시보드 — KPI · 월별 추이 · 분쟁유형 · 회신 임박 알림
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import (
    init_db, get_all_cases,
    get_stats_by_period, get_monthly_counts, get_deadline_cases,
)
from core.status_resolver import resolve_status, STATUS_COLORS
from core.ui_styles import inject_css, page_header, status_badge, kpi_card_html

st.set_page_config(page_title="홈", page_icon="🏠", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("🏛️", "경기도 집합건물 분쟁조정위원회 업무시스템")

try:
    import altair as alt
    HAS_ALTAIR = True
except ImportError:
    HAS_ALTAIR = False

cur_year = date.today().year


@st.cache_data(ttl=30)
def load_dashboard(year):
    start = f"{year}-01-01"
    end   = f"{year}-12-31"
    stats   = get_stats_by_period(start, end)
    monthly = get_monthly_counts(year)
    urgent  = [dict(r) for r in get_deadline_cases(days=7)]
    all_rows = [dict(r) for r in get_all_cases(year=year)]
    today = date.today()
    for r in all_rows:
        r["진행상태"] = resolve_status(r)
        if r.get("접수일자"):
            try:
                r["법정처리기한"] = (date.fromisoformat(r["접수일자"]) + timedelta(days=60)).isoformat()
            except Exception:
                r["법정처리기한"] = None
        else:
            r["법정처리기한"] = None
    # 법정처리기한 14일 이내 사건 (미종결)
    legal_urgent = [
        r for r in all_rows
        if r.get("법정처리기한")
        and r["진행상태"] != "종결"
        and (date.fromisoformat(r["법정처리기한"]) - today).days <= 14
    ]
    legal_urgent.sort(key=lambda x: x["법정처리기한"])
    return stats, monthly, urgent, all_rows, legal_urgent


# 연도 선택
yr_col, _ = st.columns([1, 5])
with yr_col:
    year_list = [str(y) for y in range(2050, 2025, -1)]
    sel_year = st.selectbox(
        "연도",
        year_list,
        index=year_list.index(str(cur_year)) if str(cur_year) in year_list else 0,
        label_visibility="collapsed",
    )

stats, monthly, urgent, all_rows, legal_urgent = load_dashboard(int(sel_year))

# ══════════════════════════════════════════════
# KPI 카드
# ══════════════════════════════════════════════
k1, k2, k3, k4, k5 = st.columns(5)
kpi_data = [
    (k1, stats["접수건수"], "전체 접수",      "#0066CC"),
    (k2, stats["처리중"],   "진행 중",         "#F59E0B"),
    (k3, stats["종결"],     "종결",            "#059669"),
    (k4, stats["개최건수"], "위원회 개최 수",  "#7C3AED"),
    (k5, stats["성립건수"], "조정 성립 건",   "#10B981"),
]
for col, val, label, color in kpi_data:
    with col:
        st.markdown(kpi_card_html(label, val, color), unsafe_allow_html=True)

st.markdown('<div style="height:4px"></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 법정처리기한 임박 알림 (D+60, 14일 이내)
# ══════════════════════════════════════════════
if legal_urgent:
    with st.expander(f"⚖️  법정처리기한 임박 사건  {len(legal_urgent)}건  (접수일 기준 60일)", expanded=True):
        st.markdown('<div style="display:flex;flex-direction:column;gap:6px">', unsafe_allow_html=True)
        for c in legal_urgent:
            remain = (date.fromisoformat(c["법정처리기한"]) - date.today()).days
            if remain <= 0:
                d_color, bg = "#DC2626", "#FFF1F2"
                d_label = f"D+{abs(remain)} 초과"
            elif remain <= 7:
                d_color, bg = "#EA580C", "#FFF7ED"
                d_label = f"D-{remain}"
            else:
                d_color, bg = "#0369A1", "#F0F9FF"
                d_label = f"D-{remain}"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;'
                f'background:{bg};border-radius:8px;border-left:3px solid {d_color}">'
                f'<span style="background:{d_color};color:#fff;padding:1px 8px;border-radius:100px;'
                f'font-size:11px;font-weight:700;white-space:nowrap">{d_label}</span>'
                f'<b style="font-size:13px">{c["접수번호"]}</b>'
                f'<span style="font-size:13px;color:#334155">{c.get("건물명") or c["지역"]}</span>'
                f'<span style="font-size:13px"><b>신청인</b> {c["신청인_성명"]} &nbsp;<b>피신청인</b> {c["피신청인_성명"]}</span>'
                f'<span style="margin-left:auto;font-size:12px;color:#94A3B8">법정기한 {c["법정처리기한"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 회신 임박 알림
# ══════════════════════════════════════════════
if urgent:
    with st.expander(f"⚠️  7일 이내 회신기한 사건  {len(urgent)}건", expanded=True):
        st.markdown('<div style="display:flex;flex-direction:column;gap:6px">', unsafe_allow_html=True)
        for c in urgent:
            remain = (date.fromisoformat(c["회신기한"]) - date.today()).days
            if remain <= 0:
                d_color, bg = "#DC2626", "#FFF1F2"
                d_label = f"D+{abs(remain)} 초과"
            elif remain <= 3:
                d_color, bg = "#EA580C", "#FFF7ED"
                d_label = f"D-{remain}"
            else:
                d_color, bg = "#0369A1", "#F0F9FF"
                d_label = f"D-{remain}"
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:10px;padding:8px 12px;'
                f'background:{bg};border-radius:8px;border-left:3px solid {d_color}">'
                f'<span style="background:{d_color};color:#fff;padding:1px 8px;border-radius:100px;'
                f'font-size:11px;font-weight:700;white-space:nowrap">{d_label}</span>'
                f'<b style="font-size:13px">{c["접수번호"]}</b>'
                f'<span style="font-size:13px;color:#334155">{c.get("건물명") or c["지역"]}</span>'
                f'<span style="font-size:13px"><b>신청인</b> {c["신청인_성명"]} &nbsp;<b>피신청인</b> {c["피신청인_성명"]}</span>'
                f'<span style="margin-left:auto;font-size:12px;color:#94A3B8">기한 {c["회신기한"]}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# 차트 2열
# ══════════════════════════════════════════════
ch1, ch2 = st.columns(2)

with ch1:
  with st.container(border=True):
    st.markdown('**월별 접수 · 종결 추이**')
    if monthly and HAS_ALTAIR:
        rows = []
        for r in monthly:
            rows.append({"월": f"{r['월']}월", "구분": "접수", "건수": r["접수"]})
            rows.append({"월": f"{r['월']}월", "구분": "종결", "건수": r["종결"]})
        df_m = pd.DataFrame(rows)

        color_scale = alt.Scale(domain=["접수", "종결"], range=["#0066CC", "#10B981"])
        bars = (
            alt.Chart(df_m)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=16)
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
                tooltip=[alt.Tooltip("월:O"), alt.Tooltip("구분:N"), alt.Tooltip("건수:Q")],
                opacity=alt.condition(alt.datum.건수 > 0, alt.value(1.0), alt.value(0.3)),
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
        st.altair_chart((bars + labels).properties(height=220).configure_view(strokeWidth=0),
                        use_container_width=True)
    elif monthly:
        df_m = pd.DataFrame(monthly)
        df_m["월"] = df_m["월"].astype(str) + "월"
        st.bar_chart(df_m.set_index("월")[["접수", "종결"]], height=220)
    else:
        st.info(f"{sel_year}년 데이터가 없습니다.")

with ch2:
  with st.container(border=True):
    st.markdown('**분쟁유형별 현황**')
    if stats["분쟁유형별"] and HAS_ALTAIR:
        df_d = (pd.DataFrame(stats["분쟁유형별"])
                .rename(columns={"분쟁유형": "유형", "cnt": "건수"}))
        df_d["유형"] = df_d["유형"].fillna("미분류")
        df_d["유형표시"] = df_d["유형"] + "  " + df_d["건수"].astype(str) + "건"
        PALETTE = ["#0066CC", "#10B981", "#F59E0B", "#EF4444",
                   "#8B5CF6", "#06B6D4", "#F97316", "#64748B"]
        domain = df_d["유형표시"].tolist()
        chart2 = (
            alt.Chart(df_d)
            .mark_arc(innerRadius=50, outerRadius=90, stroke="#fff", strokeWidth=2)
            .encode(
                theta=alt.Theta("건수:Q"),
                color=alt.Color("유형표시:N",
                                scale=alt.Scale(domain=domain, range=PALETTE[:len(domain)]),
                                legend=alt.Legend(orient="right", title=None,
                                                  labelFontSize=11, symbolSize=80)),
                tooltip=[alt.Tooltip("유형:N"), alt.Tooltip("건수:Q")],
            )
            .properties(height=220)
            .configure_view(strokeWidth=0)
        )
        st.altair_chart(chart2, use_container_width=True)
    elif stats["분쟁유형별"]:
        df_d = pd.DataFrame(stats["분쟁유형별"]).rename(columns={"분쟁유형": "유형", "cnt": "건수"})
        st.dataframe(df_d, use_container_width=True, hide_index=True, height=220)
    else:
        st.info("데이터가 없습니다.")

# ══════════════════════════════════════════════
# 진행 중 사건 목록
# ══════════════════════════════════════════════
with st.container(border=True):
    st.markdown('**진행 중 사건 현황**')

STATUS_EMOJI = {
    "접수": "🔵", "회신대기": "🟡", "회신임박": "🟠", "회신지연": "🔴",
    "조정중지": "⚫", "불개시": "⚪", "개최예정": "🟢", "종결": "◻",
    "조정성립": "✅", "조정불성립": "❌",
}

active = [r for r in all_rows if r["진행상태"] != "종결"]
if active:
    df_a = pd.DataFrame(active)[
        ["접수번호", "지역", "건물명", "신청인_성명", "피신청인_성명", "분쟁유형", "회신기한", "진행상태"]
    ].copy()
    df_a["진행상태"] = df_a["진행상태"].map(lambda s: f"{STATUS_EMOJI.get(s,'•')} {s}")
    st.dataframe(
        df_a,
        use_container_width=True,
        hide_index=True,
        height=min(80 + len(df_a) * 35, 340),
        column_config={
            "접수번호":      st.column_config.TextColumn("접수번호",  width="medium"),
            "지역":          st.column_config.TextColumn("지역",      width="small"),
            "건물명":        st.column_config.TextColumn("건물명",    width="medium"),
            "신청인_성명":   st.column_config.TextColumn("신청인",    width="small"),
            "피신청인_성명": st.column_config.TextColumn("피신청인",  width="small"),
            "분쟁유형":      st.column_config.TextColumn("유형",      width="small"),
            "회신기한":      st.column_config.DateColumn("회신기한",  width="small", format="YYYY-MM-DD"),
            "진행상태":      st.column_config.TextColumn("상태",      width="small"),
        },
    )
else:
    st.info(f"{sel_year}년 진행 중인 사건이 없습니다.")
