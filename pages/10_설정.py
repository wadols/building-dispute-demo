"""
설정 — DB 관리, 백업, 시스템 정보
"""
import streamlit as st
from pathlib import Path
import sys, sqlite3, shutil
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))
from core.db import init_db, get_conn
from core.ui_styles import inject_css, page_header

st.set_page_config(page_title="설정", page_icon="⚙️", layout="wide")
if "db_initialized" not in st.session_state:
    init_db()
    st.session_state["db_initialized"] = True

inject_css()
page_header("⚙️", "설정", "시스템 관리 및 데이터 관리")

DB_PATH     = Path(__file__).parent.parent / "data" / "cases.db"
BACKUP_DIR  = Path(__file__).parent.parent / "data" / "backup"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

tab_db, tab_backup, tab_info = st.tabs(["🗄️ 데이터베이스", "💾 백업·복원", "ℹ️ 시스템 정보"])

# ───── 데이터베이스 탭 ─────
with tab_db:
    st.markdown("#### DB 현황")
    with get_conn() as conn:
        n_cases   = conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0]
        n_notes   = conn.execute("SELECT COUNT(*) FROM case_notes").fetchone()[0]
        n_members = conn.execute("SELECT COUNT(*) FROM committee_members WHERE 활성여부 = 1").fetchone()[0]
        n_hearings= conn.execute(
            "SELECT COUNT(*) FROM cases WHERE 개최여부 = '개최' OR 결과 IN ('조정성립','조정불성립')"
        ).fetchone()[0]

    c1,c2,c3,c4 = st.columns(4)
    for col, label, val in [(c1,"사건",n_cases),(c2,"메모",n_notes),
                            (c3,"위원",n_members),(c4,"위원회 개최",n_hearings)]:
        with col:
            st.metric(label, val)

    st.markdown("---")
    st.markdown("#### DB 직접 조회")
    sql_input = st.text_area("SQL (SELECT만 허용)", height=80,
                              value="SELECT 접수번호, 신청인_성명, 결과 FROM cases LIMIT 10")
    if st.button("실행"):
        if sql_input.strip().upper().startswith("SELECT"):
            try:
                import pandas as pd
                with get_conn() as conn:
                    df = pd.read_sql_query(sql_input, conn)
                st.dataframe(df, use_container_width=True, hide_index=True)
                st.caption(f"{len(df)}행 반환")
            except Exception as e:
                st.error(f"쿼리 오류: {e}")
        else:
            st.warning("SELECT 문만 실행 가능합니다.")

    st.markdown("---")
    st.markdown("#### 데이터 내보내기")
    try:
        import pandas as pd, io
        with get_conn() as conn:
            df_cases = pd.read_sql_query("SELECT * FROM cases", conn)
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_cases.to_excel(writer, sheet_name="사건목록", index=False)
        st.download_button(
            "📥 전체 사건 목록 내보내기 (.xlsx)",
            data=buf.getvalue(),
            file_name=f"사건목록_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    except ImportError:
        st.warning("pandas / openpyxl이 필요합니다.")

# ───── 백업·복원 탭 ─────
with tab_backup:
    st.markdown("#### 현재 DB 다운로드")
    if DB_PATH.exists():
        with open(DB_PATH, "rb") as _f:
            st.download_button(
                "⬇️ cases.db 바로 다운로드",
                data=_f.read(),
                file_name=f"cases_{datetime.now().strftime('%Y%m%d')}.db",
                mime="application/octet-stream",
                use_container_width=True,
                type="primary",
            )
    st.markdown("---")
    st.markdown("#### DB 백업 (서버 저장)")
    if st.button("💾 지금 백업"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = BACKUP_DIR / f"cases_{ts}.db"
        shutil.copy2(DB_PATH, dst)
        st.success(f"백업 완료: {dst.name}")

    st.markdown("---")
    st.markdown("#### 기존 백업 목록")
    backups = sorted(BACKUP_DIR.glob("cases_*.db"), reverse=True)
    if backups:
        for bp in backups[:10]:
            col_name, col_size, col_dl, col_del = st.columns([4, 1, 1, 1])
            with col_name:
                st.text(bp.name)
            with col_size:
                st.text(f"{bp.stat().st_size//1024} KB")
            with col_dl:
                with open(bp, "rb") as f:
                    st.download_button("⬇️", data=f.read(),
                                       file_name=bp.name,
                                       mime="application/octet-stream",
                                       key=f"dl_{bp.name}")
            with col_del:
                if st.button("🗑️", key=f"del_{bp.name}"):
                    bp.unlink()
                    st.rerun()
    else:
        st.info("백업 파일이 없습니다.")

    st.markdown("---")
    st.markdown("#### DB 복원")
    st.warning("⚠️ 복원하면 현재 데이터가 덮어씌워집니다. 먼저 백업하세요.")
    restore_file = st.file_uploader("백업 .db 파일 업로드", type=["db"],
                                    label_visibility="collapsed")
    if restore_file and st.button("🔄 복원 실행", type="primary"):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy2(DB_PATH, BACKUP_DIR / f"cases_before_restore_{ts}.db")
        with open(DB_PATH, "wb") as f:
            f.write(restore_file.read())
        st.success("복원 완료! 페이지를 새로고침하세요.")
        st.session_state.pop("db_initialized", None)

# ───── 시스템 정보 탭 ─────
with tab_info:
    st.markdown("#### 시스템 정보")
    import platform, sqlite3 as _sqlite3
    try:
        import streamlit as _st
        st_ver = _st.__version__
    except Exception:
        st_ver = "?"
    try:
        import openpyxl as _xl
        xl_ver = _xl.__version__
    except ImportError:
        xl_ver = "미설치"
    try:
        import pandas as _pd
        pd_ver = _pd.__version__
    except ImportError:
        pd_ver = "미설치"
    try:
        import plotly as _px
        px_ver = _px.__version__
    except ImportError:
        px_ver = "미설치 (보고서 차트 비활성)"

    info = {
        "Python": platform.python_version(),
        "Streamlit": st_ver,
        "SQLite": _sqlite3.sqlite_version,
        "openpyxl": xl_ver,
        "pandas": pd_ver,
        "plotly": px_ver,
        "DB 경로": str(DB_PATH),
        "DB 크기": f"{DB_PATH.stat().st_size // 1024} KB" if DB_PATH.exists() else "없음",
    }
    for k, v in info.items():
        col_k, col_v = st.columns([2, 4])
        with col_k:
            st.markdown(f"**{k}**")
        with col_v:
            st.text(v)

    st.markdown("---")
    st.markdown("#### 캐시 초기화")
    if st.button("🔄 Streamlit 캐시 비우기"):
        st.cache_data.clear()
        st.cache_resource.clear()
        st.success("캐시가 초기화되었습니다.")
