"""
SQLite 데이터베이스 스키마 생성 및 CRUD 모듈
"""
import sqlite3
import os
from datetime import datetime
from pathlib import Path
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "data" / "cases.db"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


@contextmanager
def conn_ctx():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ────────────────────────────────────────────────
# 스키마 초기화
# ────────────────────────────────────────────────

CREATE_CASES = """
CREATE TABLE IF NOT EXISTS cases (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    접수연도        INTEGER NOT NULL,
    접수번호        TEXT    UNIQUE NOT NULL,
    지역            TEXT    NOT NULL,
    신청인_성명     TEXT    NOT NULL,
    신청인_주소     TEXT    NOT NULL,
    신청인_우편번호 TEXT,
    신청인_연락처   TEXT,
    피신청인_성명   TEXT    NOT NULL,
    피신청인_주소   TEXT    NOT NULL,
    피신청인_우편번호 TEXT,
    피신청인_연락처 TEXT,
    피신청인_지위   TEXT,
    건물소재지      TEXT,
    건축물용도      TEXT,
    신청내용        TEXT,
    접수일자        DATE    NOT NULL,
    안내도달일      DATE,
    회신기한        DATE,
    회신접수일      DATE,
    조정동의여부    TEXT    CHECK(조정동의여부 IN ('동의','부동의','무응답') OR 조정동의여부 IS NULL),
    개최여부        TEXT    CHECK(개최여부 IN ('개최','불개시') OR 개최여부 IS NULL),
    결과            TEXT    CHECK(결과 IN ('조정성립','조정불성립','조정중지','종결') OR 결과 IS NULL),
    종결일자        DATE,
    분쟁유형        TEXT,
    진행상태        TEXT,
    생성일시        DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
    수정일시        DATETIME NOT NULL DEFAULT (datetime('now','localtime'))
)
"""

CREATE_CASE_NOTES = """
CREATE TABLE IF NOT EXISTS case_notes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    접수번호    TEXT NOT NULL REFERENCES cases(접수번호) ON UPDATE CASCADE,
    작성일시    DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
    카테고리    TEXT CHECK(카테고리 IN ('전화응대','방문상담','자료요청','위원자문','내부검토','기타') OR 카테고리 IS NULL),
    제목        TEXT,
    내용        TEXT NOT NULL,
    중요표시    BOOLEAN DEFAULT 0,
    생성일시    DATETIME NOT NULL DEFAULT (datetime('now','localtime')),
    수정일시    DATETIME NOT NULL DEFAULT (datetime('now','localtime'))
)
"""

CREATE_COMMITTEE_MEMBERS = """
CREATE TABLE IF NOT EXISTS committee_members (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    성명        TEXT NOT NULL,
    소속        TEXT,
    직위        TEXT,
    핸드폰번호  TEXT,
    생년월일    DATE,
    은행명      TEXT,
    계좌번호    TEXT,
    활성여부    BOOLEAN DEFAULT 1,
    생성일시    DATETIME NOT NULL DEFAULT (datetime('now','localtime'))
)
"""

CREATE_HEARINGS = """
CREATE TABLE IF NOT EXISTS hearings (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    접수번호    TEXT NOT NULL REFERENCES cases(접수번호) ON UPDATE CASCADE,
    회차        INTEGER,
    개최예정일시 DATETIME,
    개최장소    TEXT,
    개최결과    TEXT CHECK(개최결과 IN ('성립','불성립','연기','취소') OR 개최결과 IS NULL),
    조정내용    TEXT,
    상정안건    TEXT,
    비고        TEXT,
    생성일시    DATETIME NOT NULL DEFAULT (datetime('now','localtime'))
)
"""

CREATE_HEARING_MEMBERS = """
CREATE TABLE IF NOT EXISTS hearing_members (
    hearing_id  INTEGER NOT NULL REFERENCES hearings(id) ON DELETE CASCADE,
    member_id   INTEGER NOT NULL REFERENCES committee_members(id) ON DELETE CASCADE,
    역할        TEXT CHECK(역할 IN ('위원장','위원','간사') OR 역할 IS NULL),
    PRIMARY KEY (hearing_id, member_id)
)
"""

# 수정일시 자동 갱신 트리거
CREATE_TRIGGERS = [
    """
    CREATE TRIGGER IF NOT EXISTS cases_updated
    AFTER UPDATE ON cases
    BEGIN
        UPDATE cases SET 수정일시 = datetime('now','localtime') WHERE id = NEW.id;
    END
    """,
    """
    CREATE TRIGGER IF NOT EXISTS case_notes_updated
    AFTER UPDATE ON case_notes
    BEGIN
        UPDATE case_notes SET 수정일시 = datetime('now','localtime') WHERE id = NEW.id;
    END
    """,
]

INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_cases_접수연도 ON cases(접수연도)",
    "CREATE INDEX IF NOT EXISTS idx_cases_접수일자 ON cases(접수일자)",
    "CREATE INDEX IF NOT EXISTS idx_cases_종결일자 ON cases(종결일자)",
    "CREATE INDEX IF NOT EXISTS idx_cases_진행상태 ON cases(진행상태)",
    "CREATE INDEX IF NOT EXISTS idx_case_notes_접수번호 ON case_notes(접수번호)",
    "CREATE INDEX IF NOT EXISTS idx_hearings_접수번호 ON hearings(접수번호)",
]


def init_db():
    """DB 파일이 없으면 생성하고 스키마를 초기화한다."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conn_ctx() as conn:
        for stmt in [CREATE_CASES, CREATE_CASE_NOTES, CREATE_COMMITTEE_MEMBERS,
                     CREATE_HEARINGS, CREATE_HEARING_MEMBERS]:
            conn.execute(stmt)
        for t in CREATE_TRIGGERS:
            conn.execute(t)
        for idx in INDEXES:
            conn.execute(idx)


# ────────────────────────────────────────────────
# cases CRUD
# ────────────────────────────────────────────────

def create_case(data: dict) -> int:
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT INTO cases ({cols}) VALUES ({placeholders})"
    with conn_ctx() as conn:
        cur = conn.execute(sql, list(data.values()))
        return cur.lastrowid


def get_case(접수번호: str) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM cases WHERE 접수번호 = ?", (접수번호,)).fetchone()


def get_all_cases(year: int | None = None, status: str | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM cases WHERE 1=1"
    params: list = []
    if year:
        sql += " AND 접수연도 = ?"
        params.append(year)
    if status:
        sql += " AND 진행상태 = ?"
        params.append(status)
    sql += " ORDER BY 접수번호"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def update_case(접수번호: str, data: dict) -> None:
    if not data:
        return
    sets = ", ".join(f"{k} = ?" for k in data)
    sql = f"UPDATE cases SET {sets} WHERE 접수번호 = ?"
    with conn_ctx() as conn:
        conn.execute(sql, list(data.values()) + [접수번호])


def delete_case(접수번호: str) -> None:
    with conn_ctx() as conn:
        conn.execute("DELETE FROM cases WHERE 접수번호 = ?", (접수번호,))


def case_exists(접수번호: str) -> bool:
    with get_conn() as conn:
        row = conn.execute("SELECT 1 FROM cases WHERE 접수번호 = ?", (접수번호,)).fetchone()
        return row is not None


def get_cases_by_period(
    start_date: str,
    end_date: str,
    date_col: str = "접수일자",
) -> list[sqlite3.Row]:
    """start_date~end_date 범위의 사건 목록 (보고서용)"""
    sql = f"SELECT * FROM cases WHERE {date_col} BETWEEN ? AND ? ORDER BY {date_col}"
    with get_conn() as conn:
        return conn.execute(sql, (start_date, end_date)).fetchall()


# ────────────────────────────────────────────────
# case_notes CRUD
# ────────────────────────────────────────────────

def create_note(data: dict) -> int:
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT INTO case_notes ({cols}) VALUES ({placeholders})"
    with conn_ctx() as conn:
        cur = conn.execute(sql, list(data.values()))
        return cur.lastrowid


def get_notes(접수번호: str) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM case_notes WHERE 접수번호 = ? ORDER BY 작성일시 DESC",
            (접수번호,),
        ).fetchall()


def get_note(note_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM case_notes WHERE id = ?", (note_id,)).fetchone()


def update_note(note_id: int, data: dict) -> None:
    if not data:
        return
    sets = ", ".join(f"{k} = ?" for k in data)
    sql = f"UPDATE case_notes SET {sets} WHERE id = ?"
    with conn_ctx() as conn:
        conn.execute(sql, list(data.values()) + [note_id])


def delete_note(note_id: int) -> None:
    with conn_ctx() as conn:
        conn.execute("DELETE FROM case_notes WHERE id = ?", (note_id,))


def search_notes(keyword: str) -> list[sqlite3.Row]:
    """제목+내용 전문 검색"""
    q = f"%{keyword}%"
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM case_notes WHERE 제목 LIKE ? OR 내용 LIKE ? ORDER BY 작성일시 DESC",
            (q, q),
        ).fetchall()


def get_recent_notes(limit: int = 10) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM case_notes ORDER BY 생성일시 DESC LIMIT ?", (limit,)
        ).fetchall()


# ────────────────────────────────────────────────
# committee_members CRUD
# ────────────────────────────────────────────────

def create_member(data: dict) -> int:
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT INTO committee_members ({cols}) VALUES ({placeholders})"
    with conn_ctx() as conn:
        cur = conn.execute(sql, list(data.values()))
        return cur.lastrowid


def get_member(member_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM committee_members WHERE id = ?", (member_id,)).fetchone()


def get_all_members(active_only: bool = True) -> list[sqlite3.Row]:
    sql = "SELECT * FROM committee_members"
    if active_only:
        sql += " WHERE 활성여부 = 1"
    sql += " ORDER BY 성명"
    with get_conn() as conn:
        return conn.execute(sql).fetchall()


def update_member(member_id: int, data: dict) -> None:
    if not data:
        return
    sets = ", ".join(f"{k} = ?" for k in data)
    sql = f"UPDATE committee_members SET {sets} WHERE id = ?"
    with conn_ctx() as conn:
        conn.execute(sql, list(data.values()) + [member_id])


def delete_member(member_id: int) -> None:
    with conn_ctx() as conn:
        conn.execute("DELETE FROM committee_members WHERE id = ?", (member_id,))


# ────────────────────────────────────────────────
# hearings CRUD
# ────────────────────────────────────────────────

def create_hearing(data: dict) -> int:
    cols = ", ".join(data.keys())
    placeholders = ", ".join("?" * len(data))
    sql = f"INSERT INTO hearings ({cols}) VALUES ({placeholders})"
    with conn_ctx() as conn:
        cur = conn.execute(sql, list(data.values()))
        return cur.lastrowid


def get_hearing(hearing_id: int) -> sqlite3.Row | None:
    with get_conn() as conn:
        return conn.execute("SELECT * FROM hearings WHERE id = ?", (hearing_id,)).fetchone()


def get_hearings_by_case(접수번호: str) -> list[sqlite3.Row]:
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM hearings WHERE 접수번호 = ? ORDER BY 회차",
            (접수번호,),
        ).fetchall()


def get_all_hearings(year: int | None = None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM hearings WHERE 1=1"
    params: list = []
    if year:
        sql += " AND strftime('%Y', 개최예정일시) = ?"
        params.append(str(year))
    sql += " ORDER BY 개최예정일시"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def update_hearing(hearing_id: int, data: dict) -> None:
    if not data:
        return
    sets = ", ".join(f"{k} = ?" for k in data)
    sql = f"UPDATE hearings SET {sets} WHERE id = ?"
    with conn_ctx() as conn:
        conn.execute(sql, list(data.values()) + [hearing_id])


def delete_hearing(hearing_id: int) -> None:
    with conn_ctx() as conn:
        conn.execute("DELETE FROM hearings WHERE id = ?", (hearing_id,))


# ────────────────────────────────────────────────
# hearing_members CRUD
# ────────────────────────────────────────────────

def set_hearing_members(hearing_id: int, members: list[dict]) -> None:
    """members = [{"member_id": 1, "역할": "위원장"}, ...]"""
    with conn_ctx() as conn:
        conn.execute("DELETE FROM hearing_members WHERE hearing_id = ?", (hearing_id,))
        for m in members:
            conn.execute(
                "INSERT INTO hearing_members (hearing_id, member_id, 역할) VALUES (?, ?, ?)",
                (hearing_id, m["member_id"], m.get("역할")),
            )


def get_hearing_members(hearing_id: int) -> list[sqlite3.Row]:
    sql = """
        SELECT hm.*, cm.성명, cm.소속, cm.직위
        FROM hearing_members hm
        JOIN committee_members cm ON hm.member_id = cm.id
        WHERE hm.hearing_id = ?
        ORDER BY CASE hm.역할 WHEN '위원장' THEN 0 WHEN '간사' THEN 2 ELSE 1 END
    """
    with get_conn() as conn:
        return conn.execute(sql, (hearing_id,)).fetchall()


# ────────────────────────────────────────────────
# 보고서용 집계 쿼리
# ────────────────────────────────────────────────

def get_stats_by_period(start_date: str, end_date: str, date_col: str = "접수일자") -> dict:
    """보고서 핵심 통계 집계"""
    with get_conn() as conn:
        base = f"WHERE {date_col} BETWEEN ? AND ?"
        p = (start_date, end_date)

        total = conn.execute(f"SELECT COUNT(*) FROM cases {base}", p).fetchone()[0]
        closed = conn.execute(
            f"SELECT COUNT(*) FROM cases {base} AND 결과 IN ('조정성립','조정불성립','종결')", p
        ).fetchone()[0]
        agreed = conn.execute(
            f"SELECT COUNT(*) FROM cases {base} AND 조정동의여부 = '동의'", p
        ).fetchone()[0]
        established = conn.execute(
            f"SELECT COUNT(*) FROM cases {base} AND 결과 = '조정성립'", p
        ).fetchone()[0]
        hearing_count = conn.execute(
            f"""SELECT COUNT(*) FROM hearings
                WHERE 접수번호 IN (SELECT 접수번호 FROM cases {base})""",
            p,
        ).fetchone()[0]

        dispute_types = conn.execute(
            f"""SELECT 분쟁유형, COUNT(*) as cnt FROM cases {base}
                GROUP BY 분쟁유형 ORDER BY cnt DESC""",
            p,
        ).fetchall()

        regions = conn.execute(
            f"""SELECT 지역, COUNT(*) as cnt FROM cases {base}
                GROUP BY 지역 ORDER BY cnt DESC""",
            p,
        ).fetchall()

        in_progress = total - closed

        return {
            "접수건수": total,
            "처리중": in_progress,
            "종결": closed,
            "동의건수": agreed,
            "동의율": round(agreed / total * 100, 1) if total else 0,
            "성립건수": established,
            "성립률": round(established / total * 100, 1) if total else 0,
            "개최건수": hearing_count,
            "분쟁유형별": [dict(r) for r in dispute_types],
            "지역별": [dict(r) for r in regions],
        }


# ────────────────────────────────────────────────
# 유틸
# ────────────────────────────────────────────────

def next_case_number(year: int) -> str:
    """해당 연도의 다음 접수번호를 반환 (예: 2026-001)"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT MAX(CAST(SUBSTR(접수번호, 6) AS INTEGER)) FROM cases WHERE 접수연도 = ?",
            (year,),
        ).fetchone()
        last = row[0] or 0
        return f"{year}-{last + 1:03d}"


def get_overdue_cases() -> list[sqlite3.Row]:
    """회신기한 경과 + 미회신 사건"""
    today = datetime.now().strftime("%Y-%m-%d")
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM cases WHERE 회신기한 < ? AND 회신접수일 IS NULL ORDER BY 회신기한",
            (today,),
        ).fetchall()


def get_upcoming_deadline_cases(days: int = 3) -> list[sqlite3.Row]:
    """회신기한 D-days 이내 사건"""
    from datetime import timedelta
    today = datetime.now().date()
    target = (today + timedelta(days=days)).strftime("%Y-%m-%d")
    today_str = today.strftime("%Y-%m-%d")
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM cases WHERE 회신기한 BETWEEN ? AND ? AND 회신접수일 IS NULL ORDER BY 회신기한",
            (today_str, target),
        ).fetchall()
