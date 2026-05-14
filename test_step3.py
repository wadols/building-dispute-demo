"""3단계 테스트: 접수대장 필터·상태판정·인라인수정"""
import sys
sys.path.insert(0, ".")
from datetime import date
from core.db import init_db, create_case, get_all_cases, update_case, delete_case, get_case
from core.status_resolver import resolve_status

init_db()

# ── 샘플 사건 3건 삽입
samples = [
    {"접수연도":2026,"접수번호":"2026-S01","지역":"수원시","신청인_성명":"김수원","신청인_주소":"수원시 1로",
     "피신청인_성명":"관리단A","피신청인_주소":"수원시 1로","접수일자":"2026-03-01",
     "안내도달일":"2026-03-05","회신기한":"2026-03-19","분쟁유형":"관리비","건물명":"수원빌라"},
    {"접수연도":2026,"접수번호":"2026-S02","지역":"성남시","신청인_성명":"이성남","신청인_주소":"성남시 2로",
     "피신청인_성명":"관리단B","피신청인_주소":"성남시 2로","접수일자":"2026-04-10",
     "안내도달일":None,"회신기한":None,"분쟁유형":"하자","건물명":"성남아파트"},
    {"접수연도":2026,"접수번호":"2026-S03","지역":"용인시","신청인_성명":"박용인","신청인_주소":"용인시 3로",
     "피신청인_성명":"관리단C","피신청인_주소":"용인시 3로","접수일자":"2026-05-01",
     "안내도달일":"2026-05-02","회신기한":"2026-05-16","분쟁유형":"주차","건물명":"용인타운"},
]
for s in samples:
    s["진행상태"] = resolve_status(s)
    try:
        create_case(s)
    except Exception:
        pass  # 이미 있으면 skip

# ── 전체 조회
rows = get_all_cases()
nums = [r["접수번호"] for r in rows]
for n in ["2026-S01","2026-S02","2026-S03"]:
    assert n in nums, f"{n} 없음"
print(f"OK  전체 조회: {len(rows)}건")

# ── 연도 필터
rows_2026 = get_all_cases(year=2026)
assert all(r["접수연도"] == 2026 for r in rows_2026)
print(f"OK  연도 필터(2026): {len(rows_2026)}건")

# ── 진행상태 판정 확인
s01 = dict(get_case("2026-S01"))
s02 = dict(get_case("2026-S02"))
s03 = dict(get_case("2026-S03"))
# S01: 회신기한 2026-03-19 < 오늘(2026-05-13) → 회신지연
assert resolve_status(s01) == "회신지연", f"S01 기대=회신지연, 실제={resolve_status(s01)}"
# S02: 안내도달일 없음 → 접수
assert resolve_status(s02) == "접수", f"S02 기대=접수, 실제={resolve_status(s02)}"
# S03: 안내도달일 있음, 회신기한 2026-05-16(D-3이내) → 회신임박
assert resolve_status(s03) == "회신임박", f"S03 기대=회신임박, 실제={resolve_status(s03)}"
print("OK  진행상태 자동판정: S01=회신지연, S02=접수, S03=회신임박")

# ── 인라인 수정
update_case("2026-S02", {"지역": "성남시 분당구", "건물명": "분당아파트"})
updated = dict(get_case("2026-S02"))
assert updated["지역"] == "성남시 분당구"
assert updated["건물명"] == "분당아파트"
print(f"OK  인라인 수정: 지역={updated['지역']}, 건물명={updated['건물명']}")

# ── 정리
for n in ["2026-S01","2026-S02","2026-S03"]:
    delete_case(n)
print("OK  테스트 데이터 정리")
print()
print("=== 3단계 모든 테스트 통과 ===")
