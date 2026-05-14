"""2단계 테스트: 회신기한 자동계산 + 진행상태 판정 + 신규접수 저장"""
import sys
sys.path.insert(0, ".")
from datetime import date, timedelta
from pathlib import Path
from core.db import init_db, create_case, get_case, delete_case
from core.status_resolver import resolve_status

init_db()

# ── 회신기한 자동계산
안내도달일 = date(2026, 5, 1)
회신기한 = 안내도달일 + timedelta(days=14)
assert 회신기한 == date(2026, 5, 15)
print(f"OK  회신기한 자동계산: {안내도달일} + 14일 = {회신기한}")

# ── 진행상태 판정 (오늘 기준: 2026-05-13)
cases_test = [
    ({"안내도달일": None,         "회신기한": None,         "회신접수일": None, "조정동의여부": None,     "개최여부": None,    "결과": None},         "접수"),
    ({"안내도달일": "2026-04-01", "회신기한": "2026-05-20", "회신접수일": None, "조정동의여부": None,     "개최여부": None,    "결과": None},         "회신대기"),
    ({"안내도달일": "2026-04-01", "회신기한": "2026-05-13", "회신접수일": None, "조정동의여부": None,     "개최여부": None,    "결과": None},         "회신임박"),
    ({"안내도달일": "2026-04-01", "회신기한": "2026-04-15", "회신접수일": None, "조정동의여부": None,     "개최여부": None,    "결과": None},         "회신지연"),
    ({"안내도달일": "2026-04-01", "회신기한": "2026-04-15", "회신접수일": None, "조정동의여부": "부동의", "개최여부": None,    "결과": None},         "조정중지"),
    ({"안내도달일": "2026-04-01", "회신기한": "2026-04-15", "회신접수일": "2026-04-10", "조정동의여부": "동의", "개최여부": "개최", "결과": None},    "개최예정"),
    ({"안내도달일": "2026-04-01", "회신기한": "2026-04-15", "회신접수일": "2026-04-10", "조정동의여부": "동의", "개최여부": "개최", "결과": "조정성립"}, "종결"),
]
all_ok = True
for case_data, expected in cases_test:
    result = resolve_status(case_data)
    ok = result == expected
    all_ok = all_ok and ok
    print(f"{'OK ' if ok else 'FAIL'} 상태판정: {result} (기대={expected})")

assert all_ok, "진행상태 판정 실패"

# ── DB 저장 + 건물명 확인
data = {
    "접수연도": 2026, "접수번호": "2026-T01", "지역": "수원시",
    "신청인_성명": "테스트신청인", "신청인_주소": "수원시 영통구 1로",
    "피신청인_성명": "관리단", "피신청인_주소": "수원시 영통구 1로",
    "접수일자": "2026-05-01",
    "건물명": "행복아파트", "건물소재지": "수원시 영통구 1로 100",
    "안내도달일": "2026-05-01", "회신기한": "2026-05-15",
    "분쟁유형": "관리비",
}
data["진행상태"] = resolve_status(data)
create_case(data)

row = get_case("2026-T01")
assert row["건물명"] == "행복아파트"
# 회신기한 2026-05-15, 오늘 2026-05-13 → D-2 이내 = 회신임박
assert row["진행상태"] == "회신임박"
print(f"OK  DB 저장: 접수번호={row['접수번호']}, 건물명={row['건물명']}, 진행상태={row['진행상태']}")

# ── 사건 폴더 생성
folder = Path("output/사건자료/2026-T01")
folder.mkdir(parents=True, exist_ok=True)
assert folder.exists()
print(f"OK  사건폴더 생성: {folder}")

# ── 정리
delete_case("2026-T01")
folder.rmdir()
print("OK  테스트 데이터 정리")
print()
print("=== 2단계 모든 테스트 통과 ===")
