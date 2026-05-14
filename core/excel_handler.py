"""
우편모아 / 라벨텍 엑셀 생성 모듈
"""
from pathlib import Path
from datetime import date
import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

OUTPUT_DIR = Path(__file__).parent.parent / "output"


def _thin_border():
    s = Side(style="thin")
    return Border(left=s, right=s, top=s, bottom=s)


def generate_woopyeonmoa(cases: list[dict]) -> Path:
    """
    우편모아 포맷 xlsx 생성 (원본 xls 컬럼 순서 그대로)
    수수료*=보통, 환부*=환부, 규격*=규격외, 중량=25 고정
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"우편모아_{date.today().strftime('%Y%m%d')}.xlsx"
    out_path = OUTPUT_DIR / fname

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "우편모아"

    headers = [
        "수수료*", "환부*", "규격*", "중량",
        "수취인*", "우편번호*", "기본주소*", "상세주소",
        "휴대폰", "문서번호", "문서제목", "비고",
    ]

    hdr_fill = PatternFill("solid", fgColor="FFFF00")
    hdr_font = Font(bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _thin_border()

    for r, case in enumerate(cases, 2):
        row_data = [
            "보통",                              # 수수료*
            "환부",                              # 환부*
            "규격외",                            # 규격*
            25,                                  # 중량
            case.get("피신청인_성명", ""),        # 수취인*
            case.get("피신청인_우편번호", ""),    # 우편번호*
            case.get("피신청인_주소", ""),        # 기본주소*
            "",                                  # 상세주소
            case.get("피신청인_연락처", ""),      # 휴대폰
            case.get("접수번호", ""),             # 문서번호
            "집합건물 분쟁조정 통지",             # 문서제목
            "",                                  # 비고
        ]
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=col, value=val)
            cell.border = _thin_border()
            cell.alignment = Alignment(vertical="center")

    widths = [10, 8, 8, 6, 16, 10, 40, 20, 14, 12, 18, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    wb.save(out_path)
    return out_path


def generate_labeltek(cases: list[dict]) -> Path:
    """
    라벨텍 포맷 xlsx 생성
    - 제목 열: "집합건물 분쟁조정 관련" (고정)
    - 이후: 주소, 이름, 우편번호
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    fname = f"라벨텍_{date.today().strftime('%Y%m%d')}.xlsx"
    out_path = OUTPUT_DIR / fname

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "라벨텍"

    headers = ["제목", "주소", "이름", "우편번호"]
    hdr_fill = PatternFill("solid", fgColor="D9E1F2")
    hdr_font = Font(bold=True)
    for col, h in enumerate(headers, 1):
        cell = ws.cell(row=1, column=col, value=h)
        cell.fill = hdr_fill
        cell.font = hdr_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = _thin_border()

    for r, case in enumerate(cases, 2):
        row_data = [
            "집합건물 분쟁조정 관련",            # 제목 (고정)
            case.get("피신청인_주소", ""),
            case.get("피신청인_성명", ""),
            case.get("피신청인_우편번호", ""),
        ]
        for col, val in enumerate(row_data, 1):
            cell = ws.cell(row=r, column=col, value=val)
            cell.border = _thin_border()
            cell.alignment = Alignment(vertical="center")

    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 50
    ws.column_dimensions["C"].width = 14
    ws.column_dimensions["D"].width = 10

    wb.save(out_path)
    return out_path
