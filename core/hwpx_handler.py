"""
hwpx 템플릿 치환 엔진
hwpx = ZIP 구조이므로 Contents/section0.xml 내 {{변수}} 를 치환 후 재압축
"""
import zipfile
from pathlib import Path
from datetime import date

TEMPLATE_DIR = Path(__file__).parent.parent / "템플릿" / "사건 관련"
OUTPUT_DIR   = Path(__file__).parent.parent / "output" / "사건자료"

# 날짜 포맷: YYYY. M. D. (한국 공문서 형식)
def _kor_date(d=None):
    d = d or date.today()
    return f"{d.year}. {d.month}. {d.day}."


def _build_mapping(case: dict) -> dict:
    today = _kor_date()
    return {
        "지역":         case.get("지역", ""),
        "건물명":       case.get("건물명", ""),
        "건물소재지":   case.get("건물소재지", "") or case.get("피신청인_주소", ""),
        "신청인_성명":  case.get("신청인_성명", ""),
        "신청인_주소":  case.get("신청인_주소", ""),
        "피신청인_성명": case.get("피신청인_성명", ""),
        "피신청인_주소": case.get("피신청인_주소", ""),
        "신청내용":     case.get("신청내용", ""),
        "문서작성일":   today,
        "작성일자":     today,
        "전결일자":     today,
    }


def _fill_template(xml: str, mapping: dict) -> str:
    for key, val in mapping.items():
        xml = xml.replace("{{" + key + "}}", str(val) if val else "")
    return xml


def generate_hwpx(template_name: str, case: dict, out_filename: str) -> Path:
    """
    template_name : 템플릿 파일명 (e.g. '1. 피신청인_통지_공문.hwpx')
    case          : DB row dict
    out_filename  : 저장 파일명
    반환          : 저장된 파일 Path
    """
    template_path = TEMPLATE_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(f"템플릿 없음: {template_path}")

    case_dir = OUTPUT_DIR / str(case.get("접수번호", "unknown"))
    case_dir.mkdir(parents=True, exist_ok=True)
    out_path = case_dir / out_filename

    mapping = _build_mapping(case)

    with zipfile.ZipFile(template_path, "r") as zin, \
         zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "Contents/section0.xml":
                xml = data.decode("utf-8")
                xml = _fill_template(xml, mapping)
                data = xml.encode("utf-8")
            zout.writestr(item, data)

    return out_path
