"""
보고서 — 월별/분기별/연도별 통계 및 차트
"""
import streamlit as st
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import init_db, get_stats_by_period, get_monthly_counts, get_all_cases
from core.ui_styles import inject_css, page_header

st.set_page_config(page_title="보고서", page_icon="📊", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("📊", "보고서", "월별·분기별·연도별 업무 통계")

# ── 기간 선택
col_type, col_year, col_q, col_m = st.columns([2, 1, 1, 1])
with col_type:
    period_type = st.radio("집계 단위", ["월별", "분기별", "연도별", "기간 직접설정"],
                           horizontal=True, label_visibility="collapsed")
today = date.today()
year_now = today.year

with col_year:
    sel_year = st.selectbox("연도", list(range(year_now, year_now - 5, -1)), index=0,
                             label_visibility="collapsed")
with col_q:
    sel_q = st.selectbox("분기", ["1분기", "2분기", "3분기", "4분기"],
                         index=(today.month - 1) // 3, label_visibility="collapsed")
with col_m:
    sel_m = st.selectbox("월", [f"{i}월" for i in range(1, 13)],
                         index=today.month - 1, label_visibility="collapsed")

# 기간 계산
if period_type == "월별":
    m = int(sel_m.replace("월", ""))
    start_d = date(sel_year, m, 1)
    next_m = m % 12 + 1
    next_y = sel_year + (1 if m == 12 else 0)
    end_d = date(next_y, next_m, 1) - timedelta(days=1)
    period_label = f"{sel_year}년 {m}월"
elif period_type == "분기별":
    q = int(sel_q[0])
    start_m = (q - 1) * 3 + 1
    end_m   = q * 3
    start_d = date(sel_year, start_m, 1)
    end_d   = date(sel_year, end_m, [31,28,31,30,31,30,31,31,30,31,30,31][end_m-1])
    if sel_year % 4 == 0 and end_m == 2:
        end_d = date(sel_year, 2, 29)
    period_label = f"{sel_year}년 {sel_q}"
elif period_type == "연도별":
    start_d = date(sel_year, 1, 1)
    end_d   = date(sel_year, 12, 31)
    period_label = f"{sel_year}년 전체"
else:
    c1, c2 = st.columns(2)
    with c1:
        start_d = st.date_input("시작일", value=date(today.year, 1, 1))
    with c2:
        end_d = st.date_input("종료일", value=today)
    period_label = f"{start_d} ~ {end_d}"

st.markdown(f"#### {period_label} 통계")
st.markdown("---")

# ── 통계 집계
stats = get_stats_by_period(str(start_d), str(end_d))

# ── KPI 카드
k1, k2, k3, k4 = st.columns(4)
kpis = [
    (k1, "접수건수",   stats["접수건수"],                "#1A56A0", ""),
    (k2, "처리중",     stats["처리중"],                  "#E67E22", "accent"),
    (k3, "동의율",     f"{stats['동의율']}%",            "#27AE60", "green"),
    (k4, "조정성립률", f"{stats['성립률']}%",            "#E74C3C", "red"),
]
for col, label, val, _, accent in kpis:
    with col:
        st.markdown(
            f'<div class="kpi-card {accent}">'
            f'<div class="kpi-value">{val}</div>'
            f'<div class="kpi-label">{label}</div>'
            f'</div>', unsafe_allow_html=True)

st.markdown("")

# ── 차트 (plotly 없으면 테이블로 대체)
col_left, col_right = st.columns(2)

# 분쟁유형별
with col_left:
    st.markdown("##### 분쟁유형별 건수")
    dtype_data = stats.get("분쟁유형별", [])
    if dtype_data:
        try:
            import plotly.express as px
            import pandas as pd
            df = pd.DataFrame(dtype_data)
            fig = px.pie(df, names="분쟁유형", values="cnt",
                         color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280)
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            for row in dtype_data:
                st.write(f"- {row['분쟁유형'] or '미분류'}: {row['cnt']}건")
    else:
        st.info("데이터 없음")

# 지역별
with col_right:
    st.markdown("##### 지역별 건수")
    region_data = stats.get("지역별", [])
    if region_data:
        try:
            import plotly.express as px
            import pandas as pd
            df = pd.DataFrame(region_data)
            fig = px.bar(df, x="지역", y="cnt", text="cnt",
                         color_discrete_sequence=["#1A56A0"])
            fig.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=280,
                              xaxis_title="", yaxis_title="건수")
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            for row in region_data:
                st.write(f"- {row['지역'] or '미지정'}: {row['cnt']}건")
    else:
        st.info("데이터 없음")

# ── 월별 추이 (연도별 모드에서만)
if period_type == "연도별":
    st.markdown("---")
    st.markdown("##### 월별 접수·종결 추이")
    monthly = get_monthly_counts(sel_year)
    if monthly:
        try:
            import plotly.graph_objects as go
            import pandas as pd
            df = pd.DataFrame(monthly)
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df["월"], y=df["접수"], name="접수", marker_color="#1A56A0"))
            fig.add_trace(go.Bar(x=df["월"], y=df["종결"], name="종결", marker_color="#27AE60"))
            fig.update_layout(barmode="group", margin=dict(t=10,b=10,l=10,r=10),
                              height=300, xaxis=dict(tickvals=list(range(1,13)),
                              ticktext=[f"{i}월" for i in range(1,13)]))
            st.plotly_chart(fig, use_container_width=True)
        except ImportError:
            import pandas as pd
            st.dataframe(pd.DataFrame(monthly), use_container_width=True)
    else:
        st.info("데이터 없음")

# ── 사건 목록 테이블
st.markdown("---")
st.markdown("##### 해당 기간 사건 목록")
cases = get_all_cases()
period_cases = [
    c for c in cases
    if str(start_d) <= (dict(c).get("접수일자") or "") <= str(end_d)
]
if period_cases:
    import pandas as pd
    rows = []
    for c in period_cases:
        d = dict(c)
        rows.append({
            "접수번호": d.get("접수번호",""),
            "신청인": d.get("신청인_성명",""),
            "피신청인": d.get("피신청인_성명",""),
            "분쟁유형": d.get("분쟁유형",""),
            "결과": d.get("결과",""),
            "접수일자": d.get("접수일자",""),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.info("해당 기간 사건이 없습니다.")
