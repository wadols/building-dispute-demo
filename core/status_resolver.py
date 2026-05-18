"""
진행상태 자동 판정 모듈
사건 딕셔너리(또는 sqlite3.Row)를 받아 진행상태 문자열을 반환한다.
"""
from datetime import date, timedelta


CLOSED_STATUSES = frozenset({"종결", "조정성립", "조정불성립", "조정중지", "불개시"})

STATUS_COLORS = {
    "접수":       "#4A90D9",   # 파랑
    "회신대기":   "#F5A623",   # 노랑
    "회신임박":   "#E67E22",   # 주황
    "회신지연":   "#E74C3C",   # 빨강
    "개최예정":   "#27AE60",   # 초록
    "조정성립":   "#16A085",   # 청록 (종결 성립)
    "조정불성립": "#8E44AD",   # 보라 (종결 불성립)
    "조정중지":   "#7F8C8D",   # 회색 (종결 중지)
    "불개시":     "#95A5A6",   # 연회색 (종결 불개시)
    "종결":       "#BDC3C7",   # 가장 연한 회색
}


def _to_date(v) -> date | None:
    if v is None:
        return None
    if isinstance(v, date):
        return v
    try:
        return date.fromisoformat(str(v)[:10])
    except (ValueError, TypeError):
        return None


def resolve_status(case) -> str:
    """
    진행상태 자동 판정 규칙 (프롬프트 기준):
    1. 결과 = 조정성립/조정불성립/종결  → 종결
    2. 조정동의여부 = 부동의            → 조정중지
    3. 개최여부 = 불개시                → 불개시
    4. 개최여부 = 개최 + 결과 없음      → 개최예정
    5. 회신기한 경과 + 회신접수일 없음   → 회신지연
    6. 회신기한 D-3 이내 + 미회신       → 회신임박
    7. 안내도달일 있음 + 회신접수일 없음 → 회신대기
    8. 안내도달일 없음                  → 접수
    """
    def get(key):
        try:
            return case[key]
        except (KeyError, IndexError, TypeError):
            return None

    today = date.today()
    결과         = get("결과")
    조정동의여부  = get("조정동의여부")
    개최여부      = get("개최여부")
    안내도달일_d  = _to_date(get("안내도달일"))
    회신기한_d    = _to_date(get("회신기한"))
    회신접수일_d  = _to_date(get("회신접수일"))

    if 결과 in ("조정성립", "조정불성립", "조정중지", "종결"):
        return 결과   # 결과값 그대로 반환 (모두 종결 계열)
    if 개최여부 == "불개시":
        return "불개시"
    if 조정동의여부 == "부동의":
        return "조정중지"
    if 개최여부 == "개최" and not 결과:
        return "개최예정"
    if 회신기한_d and not 회신접수일_d:
        if today > 회신기한_d:
            return "회신지연"
        if today >= (회신기한_d - timedelta(days=3)):
            return "회신임박"
    if 안내도달일_d and not 회신접수일_d:
        return "회신대기"
    return "접수"


def status_badge(status: str) -> str:
    """Streamlit markdown용 색상 배지 HTML"""
    color = STATUS_COLORS.get(status, "#888")
    return f'<span style="background:{color};color:white;padding:2px 8px;border-radius:4px;font-size:0.85em">{status}</span>'
