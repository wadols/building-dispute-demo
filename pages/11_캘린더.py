"""
처리기한 캘린더 — 회신기한(파랑) · 법정처리기한 D+60(빨강) 월간 뷰
"""
import streamlit as st
import pandas as pd
import calendar
from datetime import date, timedelta
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import init_db, get_all_cases
from core.status_resolver import resolve_status, CLOSED_STATUSES
from core.ui_styles import inject_css, page_header

st.set_page_config(page_title="캘린더", page_icon="📅", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("📅", "처리기한 캘린더", "회신기한 · 법정처리기한(접수일 +60일)")

today = date.today()
if "cal_year" not in st.session_state:
    st.session_state["cal_year"] = today.year
if "cal_month" not in st.session_state:
    st.session_state["cal_month"] = today.month


# ── 월 이동
nav_l, nav_c, nav_r, nav_today = st.columns([1, 3, 1, 1])
with nav_l:
    if st.button("← 이전달", use_container_width=True):
        m = st.session_state["cal_month"] - 1
        if m == 0:
            st.session_state["cal_month"] = 12
            st.session_state["cal_year"] -= 1
        else:
            st.session_state["cal_month"] = m
        st.rerun()
with nav_c:
    st.markdown(
        f'<h3 style="text-align:center;color:#0F172A;margin:6px 0;font-weight:700;letter-spacing:-0.5px">'
        f'{st.session_state["cal_year"]}년 {st.session_state["cal_month"]}월</h3>',
        unsafe_allow_html=True,
    )
with nav_r:
    if st.button("다음달 →", use_container_width=True):
        m = st.session_state["cal_month"] + 1
        if m == 13:
            st.session_state["cal_month"] = 1
            st.session_state["cal_year"] += 1
        else:
            st.session_state["cal_month"] = m
        st.rerun()
with nav_today:
    if st.button("오늘", use_container_width=True):
        st.session_state["cal_year"] = today.year
        st.session_state["cal_month"] = today.month
        st.rerun()

year  = st.session_state["cal_year"]
month = st.session_state["cal_month"]


# ── 데이터 로드
@st.cache_data(ttl=30)
def load_cases_calendar():
    rows = get_all_cases()
    data = []
    for r in rows:
        d = dict(r)
        d["진행상태"] = resolve_status(d)
        if d.get("접수일자"):
            try:
                d["법정처리기한"] = (
                    date.fromisoformat(d["접수일자"]) + timedelta(days=60)
                ).isoformat()
            except Exception:
                d["법정처리기한"] = None
        else:
            d["법정처리기한"] = None
        data.append(d)
    return data

cases = load_cases_calendar()

# 이벤트 딕셔너리: {날짜str: [(접수번호, 구분)]}
events: dict[str, list] = {}
for c in cases:
    if c["진행상태"] in CLOSED_STATUSES:
        continue
    for key, label in [("회신기한", "reply"), ("법정처리기한", "legal")]:
        d = c.get(key)
        if d:
            display = f'{c["신청인_성명"]} - {c["피신청인_성명"]}'
            events.setdefault(d, []).append((c["접수번호"], label, display))


# ── 범례
st.markdown(
    '<div style="display:flex;gap:14px;margin:8px 0 12px;align-items:center">'
    '<span style="background:#EBF4FF;color:#0052A3;padding:2px 10px;'
    'border-radius:100px;font-size:12px;font-weight:600">● 회신기한</span>'
    '<span style="background:#FEE2E2;color:#991B1B;padding:2px 10px;'
    'border-radius:100px;font-size:12px;font-weight:600">● 법정처리기한 (+60일)</span>'
    '<span style="color:#94A3B8;font-size:12px">종결 사건 제외</span>'
    '</div>',
    unsafe_allow_html=True,
)


# ── 달력 HTML 생성
WEEKDAYS = ["일", "월", "화", "수", "목", "금", "토"]
month_cal = calendar.monthcalendar(year, month)

html = (
    '<div style="display:grid;grid-template-columns:repeat(7,1fr);gap:5px;'
    'background:#E2E8F0;border-radius:12px;padding:5px">'
)

# 요일 헤더
for i, wd in enumerate(WEEKDAYS):
    color = "#DC2626" if i == 0 else "#2563EB" if i == 6 else "#475569"
    html += (
        f'<div style="text-align:center;font-weight:700;font-size:12px;'
        f'color:{color};padding:8px 0;background:#F8FAFC;border-radius:6px">{wd}</div>'
    )

# 날짜 셀
for week in month_cal:
    for idx, day in enumerate(week):
        if day == 0:
            html += '<div style="background:#F8FAFC;border-radius:8px;min-height:90px"></div>'
            continue

        date_str = f"{year:04d}-{month:02d}-{day:02d}"
        is_today  = (date_str == today.isoformat())
        is_past   = (date_str < today.isoformat())
        is_sun    = (idx == 0)
        is_sat    = (idx == 6)

        num_color  = "#DC2626" if is_sun else "#2563EB" if is_sat else "#0F172A"
        cell_bg    = "#EFF6FF" if is_today else "#FAFAFA" if is_past else "#FFFFFF"
        cell_border = "2px solid #0066CC" if is_today else "1px solid transparent"

        day_events = events.get(date_str, [])
        evt_html = ""
        for num, etype, display in day_events[:3]:
            if etype == "reply":
                bg_e, fg_e = "#DBEAFE", "#1D4ED8"
            else:
                bg_e, fg_e = "#FEE2E2", "#B91C1C"
            evt_html += (
                f'<div style="background:{bg_e};color:{fg_e};padding:1px 5px;'
                f'border-radius:4px;font-size:10.5px;font-weight:600;'
                f'margin-top:2px;white-space:nowrap;overflow:hidden;'
                f'text-overflow:ellipsis" title="{num}">{display}</div>'
            )
        if len(day_events) > 3:
            evt_html += (
                f'<div style="font-size:10px;color:#94A3B8;margin-top:2px">'
                f'+{len(day_events) - 3}건 더</div>'
            )

        today_dot = (
            '<div style="width:5px;height:5px;background:#0066CC;'
            'border-radius:50%;display:inline-block;margin-left:4px;'
            'vertical-align:middle"></div>'
            if is_today else ""
        )

        html += (
            f'<div style="background:{cell_bg};border:{cell_border};'
            f'border-radius:8px;padding:7px 8px;min-height:90px">'
            f'<div style="font-size:13px;font-weight:{"700" if is_today else "500"};'
            f'color:{num_color};opacity:{"1" if not is_past else "0.5"}">'
            f'{day}{today_dot}</div>'
            f'{"" if not is_past else ""}'
            f'{evt_html}</div>'
        )

html += '</div>'
st.markdown(html, unsafe_allow_html=True)


# ── 이번 달 기한 목록
st.markdown('<div style="height:16px"></div>', unsafe_allow_html=True)
last_day   = calendar.monthrange(year, month)[1]
month_start = f"{year:04d}-{month:02d}-01"
month_end   = f"{year:04d}-{month:02d}-{last_day:02d}"

this_month = []
for c in cases:
    if c["진행상태"] in CLOSED_STATUSES:
        continue
    if c.get("회신기한") and month_start <= c["회신기한"] <= month_end:
        remain = (date.fromisoformat(c["회신기한"]) - today).days
        this_month.append({
            "구분": "📬 회신기한",
            "접수번호": c["접수번호"],
            "기한": c["회신기한"],
            "잔여일": f"D-{remain}" if remain >= 0 else f"D+{abs(remain)} 초과",
            "건물명": c.get("건물명") or "—",
            "신청인": c["신청인_성명"],
            "피신청인": c["피신청인_성명"],
            "진행상태": c["진행상태"],
        })
    if c.get("법정처리기한") and month_start <= c["법정처리기한"] <= month_end:
        remain = (date.fromisoformat(c["법정처리기한"]) - today).days
        this_month.append({
            "구분": "⚖️ 법정처리기한",
            "접수번호": c["접수번호"],
            "기한": c["법정처리기한"],
            "잔여일": f"D-{remain}" if remain >= 0 else f"D+{abs(remain)} 초과",
            "건물명": c.get("건물명") or "—",
            "신청인": c["신청인_성명"],
            "피신청인": c["피신청인_성명"],
            "진행상태": c["진행상태"],
        })

this_month.sort(key=lambda x: x["기한"])

if this_month:
    st.markdown(
        f'<div style="font-size:0.9rem;font-weight:700;color:#0F172A;margin-bottom:12px">'
        f'{year}년 {month}월 기한 목록  <span style="font-weight:400;color:#64748B;'
        f'font-size:13px">{len(this_month)}건</span></div>',
        unsafe_allow_html=True,
    )
    df_evt = pd.DataFrame(this_month)
    st.dataframe(
        df_evt,
        use_container_width=True,
        hide_index=True,
        height=min(46 + len(df_evt) * 30, 380),
        row_height=30,
        column_config={
            "구분":      st.column_config.TextColumn("구분",      width="medium"),
            "접수번호":  st.column_config.TextColumn("접수번호",  width="medium"),
            "기한":      st.column_config.DateColumn("기한",      width="small", format="YYYY-MM-DD"),
            "잔여일":    st.column_config.TextColumn("잔여일",    width="small"),
            "건물명":    st.column_config.TextColumn("건물명",    width="medium"),
            "신청인":    st.column_config.TextColumn("신청인",    width="small"),
            "피신청인":  st.column_config.TextColumn("피신청인",  width="small"),
            "진행상태":  st.column_config.TextColumn("상태",      width="small"),
        },
    )
else:
    st.markdown(
        '<div class="empty-state"><div class="empty-icon">🎉</div>'
        f'<div class="empty-title">{year}년 {month}월 기한 사건 없음</div>'
        '<div class="empty-sub">이번 달에 도래하는 회신기한 또는 법정처리기한이 없습니다</div>'
        '</div>',
        unsafe_allow_html=True,
    )
