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
    init_db, get_all_cases, get_deadline_cases,
)
from core.status_resolver import resolve_status, STATUS_COLORS, CLOSED_STATUSES
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
    all_rows = [dict(r) for r in get_all_cases(year=year)]
    today = date.today()

    for r in all_rows:
        r["진행상태"] = resolve_status(r)
        if r.get("접수일자"):
            try:
                r["법정처리기한"] = (
                    date.fromisoformat(str(r["접수일자"])[:10]) + timedelta(days=60)
                ).isoformat()
            except Exception:
                r["법정처리기한"] = None
        else:
            r["법정처리기한"] = None

    # ── KPI 집계 (resolve_status 기준 → 접수대장과 동일)
    total       = len(all_rows)
    closed      = sum(1 for r in all_rows if r["진행상태"] in CLOSED_STATUSES)
    active      = total - closed
    established = sum(1 for r in all_rows if r["진행상태"] == "조정성립")
    agreed      = sum(1 for r in all_rows if r.get("조정동의여부") == "동의")

    # 위원회 개최 수: 개최여부='개최' 또는 결과가 조정성립/조정불성립인 사건 수
    hearing_count = sum(
        1 for r in all_rows
        if r.get("개최여부") == "개최"
        or r.get("결과") in ("조정성립", "조정불성립")
    )

    # 분쟁유형별
    type_dict: dict = {}
    for r in all_rows:
        t = r.get("분쟁유형") or None
        type_dict[t] = type_dict.get(t, 0) + 1
    dispute_types = [
        {"분쟁유형": k, "cnt": v}
        for k, v in sorted(type_dict.items(), key=lambda x: -x[1])
    ]

    stats = {
        "접수건수":  total,
        "처리중":    active,
        "종결":      closed,
        "동의건수":  agreed,
        "동의율":    round(agreed / total * 100, 1) if total else 0,
        "성립건수":  established,
        "성립률":    round(established / total * 100, 1) if total else 0,
        "개최건수":  hearing_count,
        "분쟁유형별": dispute_types,
        "지역별":    [],
    }

    # ── 월별 추이 (접수일자 연도가 선택 연도와 일치하는 건만)
    monthly_dict: dict = {}
    for r in all_rows:
        접수일자 = r.get("접수일자")
        if not 접수일자:
            continue
        try:
            접수년 = int(str(접수일자)[:4])
            if 접수년 != year:
                continue
            m = int(str(접수일자)[5:7])
        except Exception:
            continue
        bucket = monthly_dict.setdefault(m, {"월": m, "접수": 0, "종결": 0})
        bucket["접수"] += 1
        if r["진행상태"] in CLOSED_STATUSES:
            bucket["종결"] += 1
    monthly = sorted(monthly_dict.values(), key=lambda x: x["월"])

    # ── 회신 임박 알림 (7일 이내)
    urgent = [dict(r) for r in get_deadline_cases(days=7)]

    # ── 법정처리기한 임박 (14일 이내, 미종결)
    legal_urgent = [
        r for r in all_rows
        if r.get("법정처리기한")
        and r["진행상태"] not in CLOSED_STATUSES
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
                d_color, bg = "#B91C1C", "#FEE2E2"
                d_label = f"D+{abs(remain)} 초과"
            elif remain <= 7:
                d_color, bg = "#DC2626", "#FEE2E2"
                d_label = f"D-{remain}"
            else:
                d_color, bg = "#EF4444", "#FEF2F2"
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
    st.markdown('**월별 접수 건수**')
    if monthly and HAS_ALTAIR:
        df_m = pd.DataFrame([{"월": f"{r['월']}월", "건수": r["접수"]} for r in monthly])

        bars = (
            alt.Chart(df_m)
            .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, color="#0066CC")
            .encode(
                x=alt.X("월:O", sort=None,
                        axis=alt.Axis(labelAngle=0, labelFontSize=11, labelFontWeight="bold", titleOpacity=0)),
                y=alt.Y("건수:Q",
                        axis=alt.Axis(grid=True, gridColor="#F1F5F9", tickCount=5,
                                      labelFontSize=10, titleOpacity=0)),
                tooltip=[alt.Tooltip("월:O"), alt.Tooltip("건수:Q", title="접수")],
                opacity=alt.condition(alt.datum.건수 > 0, alt.value(1.0), alt.value(0.3)),
            )
        )
        labels = (
            alt.Chart(df_m)
            .mark_text(dy=-6, fontSize=11, fontWeight="bold", color="#374151")
            .encode(
                x=alt.X("월:O", sort=None),
                y=alt.Y("건수:Q"),
                text=alt.Text("건수:Q"),
                opacity=alt.condition(alt.datum.건수 > 0, alt.value(1), alt.value(0)),
            )
        )
        st.altair_chart(
            (bars + labels)
            .properties(height=220)
            .configure_view(strokeWidth=0)
            .configure_bar(discreteBandSize=48),
            use_container_width=True,
        )
    elif monthly:
        df_m = pd.DataFrame(monthly)
        df_m["월"] = df_m["월"].astype(str) + "월"
        st.bar_chart(df_m.set_index("월")["접수"], height=220)
    else:
        st.info(f"{sel_year}년 데이터가 없습니다.")

with ch2:
  with st.container(border=True):
    st.markdown('**분쟁유형별 현황**')
    if stats["분쟁유형별"]:
        import plotly.graph_objects as go
        df_d = (pd.DataFrame(stats["분쟁유형별"])
                .rename(columns={"분쟁유형": "유형", "cnt": "건수"}))
        df_d["유형"] = df_d["유형"].fillna("미분류")
        PALETTE = ["#0066CC", "#10B981", "#F59E0B", "#EF4444",
                   "#8B5CF6", "#06B6D4", "#F97316", "#64748B"]
        fig = go.Figure(go.Pie(
            labels=df_d["유형"],
            values=df_d["건수"],
            hole=0.52,
            textinfo="value",
            textposition="inside",
            insidetextorientation="horizontal",
            textfont=dict(size=13, color="white", family="Malgun Gothic"),
            marker=dict(
                colors=PALETTE[:len(df_d)],
                line=dict(color="white", width=2),
            ),
            hovertemplate="%{label}<br>%{value}건<extra></extra>",
        ))
        fig.update_layout(
            height=240,
            margin=dict(l=0, r=0, t=0, b=0),
            legend=dict(
                orientation="v", x=1.01, y=0.5,
                font=dict(size=11, family="Malgun Gothic"),
                itemsizing="constant",
            ),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig, use_container_width=True)
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

active = [r for r in all_rows if r["진행상태"] not in CLOSED_STATUSES]
if active:
    df_a = pd.DataFrame(active)[
        ["접수번호", "지역", "건물명", "신청인_성명", "피신청인_성명", "분쟁유형", "회신기한", "진행상태"]
    ].copy()
    df_a["진행상태"] = df_a["진행상태"].map(lambda s: f"{STATUS_EMOJI.get(s,'•')} {s}")
    st.dataframe(
        df_a,
        use_container_width=True,
        hide_index=True,
        height=min(46 + len(df_a) * 30, 320),
        row_height=30,
        column_config={
            "접수번호":      st.column_config.TextColumn("접수번호",  width=88),
            "지역":          st.column_config.TextColumn("지역",      width=62),
            "건물명":        st.column_config.TextColumn("건물명",    width=100),
            "신청인_성명":   st.column_config.TextColumn("신청인",    width=80),
            "피신청인_성명": st.column_config.TextColumn("피신청인",  width=110),
            "분쟁유형":      st.column_config.TextColumn("유형",      width=120),
            "회신기한":      st.column_config.DateColumn("회신기한",  width=84, format="YY-MM-DD"),
            "진행상태":      st.column_config.TextColumn("상태",      width=76),
        },
    )
else:
    st.info(f"{sel_year}년 진행 중인 사건이 없습니다.")

st.markdown(
    '<div style="margin-top:48px;padding:14px 0 4px;'
    'border-top:1px solid #E2E8F0;text-align:center;'
    'color:#94A3B8;font-size:14px;display:flex;align-items:center;'
    'justify-content:center;gap:8px">'
    '<img src="https://www.anthropic.com/favicon.ico" '
    'width="18" height="18" style="vertical-align:middle;border-radius:2px;opacity:0.7">'
    'Created by Myunghun Kang &nbsp;·&nbsp; Built with Claude Code &nbsp;·&nbsp; 2026'
    '</div>',
    unsafe_allow_html=True,
)
