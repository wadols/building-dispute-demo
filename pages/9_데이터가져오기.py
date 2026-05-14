"""
데이터 가져오기 — 엑셀 일괄 가져오기
"""
import streamlit as st
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import init_db, create_case, case_exists, next_case_number
from core.ui_styles import inject_css, page_header

st.set_page_config(page_title="데이터 가져오기", page_icon="📥", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("📥", "데이터 가져오기", "엑셀 파일로 사건 정보 일괄 등록")

# ── 양식 다운로드
st.markdown("#### 1단계 — 양식 다운로드")
col_tmpl, _ = st.columns([2, 3])
with col_tmpl:
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill
        import io

        def _make_template() -> bytes:
            wb = openpyxl.Workbook()
            ws = wb.active
            ws.title = "사건목록"
            headers = [
                "접수번호", "접수연도", "지역", "건물명", "건물소재지",
                "신청인_성명", "신청인_주소", "신청인_연락처",
                "피신청인_성명", "피신청인_주소", "피신청인_연락처", "피신청인_우편번호",
                "신청내용", "분쟁유형", "접수일자", "조정동의여부",
            ]
            fill = PatternFill("solid", fgColor="1A56A0")
            font = Font(bold=True, color="FFFFFF")
            for col, h in enumerate(headers, 1):
                c = ws.cell(1, col, h)
                c.fill = fill
                c.font = font
                c.alignment = Alignment(horizontal="center")
                ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = max(len(h)+4, 14)
            # 예시 행
            ws.append(["2026-999", 2026, "수원시", "예시아파트", "경기도 수원시...",
                        "홍길동", "경기도 수원시...", "010-0000-0000",
                        "김철수", "경기도 성남시...", "010-1111-1111", "12345",
                        "관리비 미납", "관리비", "2026-01-01", "동의"])
            buf = io.BytesIO()
            wb.save(buf)
            return buf.getvalue()

        st.download_button(
            "📥 양식 다운로드 (.xlsx)",
            data=_make_template(),
            file_name="사건등록_양식.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except ImportError:
        st.warning("openpyxl이 설치되지 않아 양식 다운로드를 사용할 수 없습니다.")

st.markdown("---")
st.markdown("#### 2단계 — 파일 업로드 및 미리보기")

uploaded = st.file_uploader("엑셀 파일 선택 (.xlsx)", type=["xlsx"],
                             label_visibility="collapsed")

if uploaded:
    try:
        import pandas as pd
        df = pd.read_excel(uploaded, dtype=str)
        df = df.fillna("")
        st.markdown(f"**{len(df)}행 감지됨**")
        st.dataframe(df.head(10), use_container_width=True, hide_index=True)

        col_dup, col_go = st.columns([2, 1])
        with col_dup:
            skip_dup = st.checkbox("이미 등록된 접수번호 건너뛰기", value=True)

        with col_go:
            if st.button("✅ 가져오기 실행", type="primary", use_container_width=True):
                ok = err = dup = 0
                log_lines = []
                for _, row in df.iterrows():
                    case_no = str(row.get("접수번호", "")).strip()
                    if not case_no:
                        err += 1
                        log_lines.append(f"❌ 접수번호 없음 (행 건너뜀)")
                        continue
                    if case_exists(case_no):
                        if skip_dup:
                            dup += 1
                            log_lines.append(f"⏭ {case_no} — 이미 존재 (건너뜀)")
                            continue
                    try:
                        data = {k: (row.get(k, "") or "") for k in [
                            "접수번호", "접수연도", "지역", "건물명", "건물소재지",
                            "신청인_성명", "신청인_주소", "신청인_연락처",
                            "피신청인_성명", "피신청인_주소", "피신청인_연락처", "피신청인_우편번호",
                            "신청내용", "분쟁유형", "접수일자", "조정동의여부",
                        ]}
                        if not data.get("접수연도"):
                            import re
                            m = re.match(r"(\d{4})", case_no)
                            data["접수연도"] = int(m.group(1)) if m else 2026
                        else:
                            try:
                                data["접수연도"] = int(data["접수연도"])
                            except Exception:
                                data["접수연도"] = 2026
                        create_case(data)
                        ok += 1
                        log_lines.append(f"✅ {case_no} — 등록 완료")
                    except Exception as e:
                        err += 1
                        log_lines.append(f"❌ {case_no} — 오류: {e}")

                st.success(f"완료: 등록 {ok}건 | 중복 {dup}건 | 오류 {err}건")
                with st.expander("상세 로그"):
                    st.text("\n".join(log_lines))

    except Exception as e:
        st.error(f"파일 읽기 오류: {e}")

st.markdown("---")
st.markdown("""
**컬럼 안내**

| 컬럼명 | 필수 | 설명 |
|--------|------|------|
| 접수번호 | ✓ | 예: 2026-001 |
| 접수연도 | | 비어 있으면 접수번호에서 자동 추출 |
| 지역 / 건물명 / 건물소재지 | | 건물 기본 정보 |
| 신청인_성명·주소·연락처 | ✓ | |
| 피신청인_성명·주소·연락처·우편번호 | ✓ | |
| 신청내용 / 분쟁유형 | | |
| 접수일자 | | YYYY-MM-DD 형식 |
| 조정동의여부 | | 동의 / 미동의 |
""")
