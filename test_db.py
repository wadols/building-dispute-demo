"""1단계 DB 스키마 + CRUD 테스트"""
import sys
sys.path.insert(0, ".")
from core.db import (
    init_db, next_case_number,
    create_case, get_case, update_case, delete_case, case_exists,
    create_note, get_notes, delete_note,
    create_member, get_all_members, delete_member,
    create_hearing, set_hearing_members, get_hearing_members, delete_hearing,
    get_stats_by_period,
)

# ── DB 초기화
init_db()
print("OK  DB 초기화")

# ── cases CRUD
cid = create_case({
    "접수연도": 2026, "접수번호": "2026-001", "지역": "서울",
    "신청인_성명": "홍길동", "신청인_주소": "서울 강남구",
    "피신청인_성명": "관리단", "피신청인_주소": "서울 강남구",
    "접수일자": "2026-01-15", "분쟁유형": "관리비",
})
print(f"OK  case 생성 id={cid}")

row = get_case("2026-001")
assert row is not None
assert row["신청인_성명"] == "홍길동"
print(f"OK  case 조회: {row['접수번호']} / {row['신청인_성명']}")

update_case("2026-001", {"지역": "서울특별시"})
row2 = get_case("2026-001")
assert row2["지역"] == "서울특별시"
print(f"OK  case 수정: 지역={row2['지역']}")

assert case_exists("2026-001")
nxt = next_case_number(2026)
assert nxt == "2026-002", f"expected 2026-002 got {nxt}"
print(f"OK  다음 접수번호: {nxt}")

# 중복 접수번호 체크
try:
    create_case({
        "접수연도": 2026, "접수번호": "2026-001", "지역": "서울",
        "신청인_성명": "중복", "신청인_주소": "x",
        "피신청인_성명": "중복", "피신청인_주소": "x",
        "접수일자": "2026-01-15",
    })
    print("FAIL 중복 접수번호 허용됨 (버그)")
except Exception:
    print("OK  중복 접수번호 UNIQUE 제약 동작")

# ── case_notes CRUD
nid = create_note({
    "접수번호": "2026-001", "카테고리": "전화응대",
    "제목": "초기 연락", "내용": "신청인과 첫 통화",
})
notes = get_notes("2026-001")
assert len(notes) == 1
print(f"OK  note 생성/조회: {len(notes)}건")

# ── committee_members CRUD
mid = create_member({
    "성명": "김위원", "소속": "변호사협회", "직위": "위원", "활성여부": 1,
})
members = get_all_members()
assert any(m["id"] == mid for m in members)
print(f"OK  member 생성/조회: {len(members)}명")

# ── hearings + hearing_members
hid = create_hearing({
    "접수번호": "2026-001", "회차": 1,
    "개최예정일시": "2026-02-10 14:00", "개최장소": "3층 회의실",
})
set_hearing_members(hid, [{"member_id": mid, "역할": "위원장"}])
hm = get_hearing_members(hid)
assert hm[0]["성명"] == "김위원"
assert hm[0]["역할"] == "위원장"
print(f"OK  hearing + 참석위원: {hm[0]['성명']} ({hm[0]['역할']})")

# ── 보고서용 집계
stats = get_stats_by_period("2026-01-01", "2026-12-31")
assert stats["접수건수"] == 1
print(f"OK  집계: 접수={stats['접수건수']}, 동의율={stats['동의율']}%")

# ── 테스트 데이터 정리
delete_note(nid)
delete_hearing(hid)
delete_member(mid)
delete_case("2026-001")
assert not case_exists("2026-001")
print("OK  테스트 데이터 정리")

print()
print("=== 1단계 모든 테스트 통과 ===")
