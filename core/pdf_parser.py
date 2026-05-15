"""
집합건물 분쟁조정 신청서 PDF 파싱
"""
import re
import io


def _extract_text(file_bytes: bytes) -> str:
    """pymupdf → pdfplumber → pypdfium2 → pdfminer → OCR 순서로 시도"""

    # 1. pymupdf (fitz) — 가장 범용적
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        parts = []
        for page in doc:
            parts.append(page.get_text())
        text = "\n".join(parts)
        if text.strip():
            return text
    except Exception:
        pass

    # 2. pdfplumber
    try:
        import pdfplumber
        parts = []
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                t = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
                parts.append(t)
        text = "\n".join(parts)
        if text.strip():
            return text
    except Exception:
        pass

    # 3. pypdfium2
    try:
        import pypdfium2 as pdfium
        doc = pdfium.PdfDocument(bytes(file_bytes))
        parts = []
        for page in doc:
            tp = page.get_textpage()
            parts.append(tp.get_text_range())
        text = "\n".join(parts)
        if text.strip():
            return text
    except Exception:
        pass

    # 4. pdfminer.six
    try:
        from pdfminer.high_level import extract_text as _pm_extract
        text = _pm_extract(io.BytesIO(file_bytes))
        if text.strip():
            return text
    except Exception:
        pass

    # 5. OCR (스캔 이미지 PDF) — pymupdf로 이미지 변환 후 easyocr
    try:
        import fitz
        import easyocr
        import numpy as np

        reader = easyocr.Reader(['ko', 'en'], gpu=False, verbose=False)
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        parts = []
        for page in doc:
            mat = fitz.Matrix(2, 2)  # 2배 해상도
            pix = page.get_pixmap(matrix=mat)
            img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)
            result = reader.readtext(img, detail=0, paragraph=True)
            parts.append("\n".join(result))
        text = "\n".join(parts)
        if text.strip():
            return text
    except ImportError:
        pass  # easyocr 미설치
    except Exception:
        pass

    return ""


def _find_phone(text: str) -> str:
    """전화번호 추출 — 줄바꿈·공백 무시"""
    joined = re.sub(r'\s+', '', text)
    m = re.search(r'(\d{2,3}-\d{3,4}-\d{4})', joined)
    return m.group(1) if m else ""


# 주소가 끝나고 다음 칸으로 넘어가는 경계 키워드
_ADDR_STOP = re.compile(
    r'생년월일|성명\s*[가-힣]{2,}|\(법인번호|연락처|전화번호|휴대폰|팩스'
    r'|\d{6}\s*[\(\s]|선정된|피\s*청?\s*인',
)


def _clean_address(text: str) -> str:
    """주소에서 전화번호·인접 칸 텍스트 제거 후 순수 주소만 반환"""
    # 괄호 안 전화번호 제거
    cleaned = re.sub(r'\s*\(전화번호[:：]?\s*[\d\-\s]+\)', '', text)
    # 다음 칸 경계 키워드에서 잘라내기
    m = _ADDR_STOP.search(cleaned)
    if m:
        cleaned = cleaned[:m.start()]
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    # 끝에 남은 숫자 잔재 제거
    cleaned = re.sub(r'\s*[\d]{4,}\)?\s*$', '', cleaned).strip()
    return cleaned


def _best_address(raw: str) -> str:
    """OCR 노이즈가 많은 주소 문자열에서 가장 깨끗한 주소 부분 추출"""
    cleaned = _clean_address(raw)
    # 주소 시작점: 광역시/도 단위부터
    m = re.search(r'(서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)\s*\S', cleaned)
    if m:
        return cleaned[m.start():].strip()
    return cleaned


def parse_application_pdf(file_bytes: bytes) -> tuple[dict, str]:
    """
    신청서 PDF bytes → (추출 필드 딕셔너리, 원문 텍스트)
    "_error" 키가 있으면 파싱 자체 실패
    """
    try:
        raw_text = _extract_text(file_bytes)
    except ImportError:
        raise
    except Exception as e:
        return {"_error": str(e)}, ""

    text = raw_text
    r = {}

    # ── 신청일자 (문서 내 마지막 날짜)
    dates = re.findall(r'(\d{4})년\s+(\d{1,2})월\s+(\d{1,2})일', text)
    if dates:
        y, mo, d = dates[-1]
        r["접수일자"] = f"{y}-{int(mo):02d}-{int(d):02d}"

    # ── 블록 분리 (신청인 / 피신청인 / 분쟁대상)
    ap_m = re.search(r'신\s*청\s*인\s*(.*?)(?:피\s*청?\s*인|피청인)', text, re.DOTALL)
    ap_block = ap_m.group(1) if ap_m else text[:len(text)//2]

    rp_m = re.search(r'피\s*청?\s*인\s*(.*?)(?:분쟁대상|조정신청)', text, re.DOTALL)
    rp_block = rp_m.group(1) if rp_m else ""

    # ── 신청인 성명: "성명 홍길동" 또는 "성명홍길동"
    for pat in [r'성명\s+(\S+)', r'성명(\S+)']:
        m = re.search(pat, ap_block)
        if m:
            name = m.group(1).strip()
            if len(name) >= 2 and name not in ('생년월일', '(법인번호)'):
                r["신청인_성명"] = name
                break

    # ── 신청인 주소 + 연락처
    m = re.search(r'주소\s+(.+?)(?=선정된|피\s*청?\s*인|\Z)', ap_block, re.DOTALL)
    if m:
        raw = m.group(1).replace("\n", " ").strip()
        phone = _find_phone(raw)
        if phone:
            r["신청인_연락처"] = phone
        addr = _best_address(raw)
        if addr:
            r["신청인_주소"] = addr

    # ── 피신청인 성명 (여러 줄 가능 / OCR 노이즈 대응 패턴 확장)
    if rp_block:
        for pat in [
            r'성명\s+([가-힣]{2,10})(?:\s|$)',
            r'성명\s+(.+?)(?=생년월일|주소|\d{6})',
            r'성명\s*(.+?)(?=\n.*생년월일|\n.*주소)',
            r'성명(.+?)(?=생년월일|주소)',
        ]:
            m = re.search(pat, rp_block, re.DOTALL)
            if m:
                name = " ".join(m.group(1).split()).strip()
                name = re.sub(r'\s*(생년월일|알수없음|\d{6}).*', '', name).strip()
                name = re.sub(r'[^\w\s]', '', name).strip()
                if 2 <= len(name) <= 20:
                    r["피신청인_성명"] = name
                    break

    # ── 피신청인 주소 + 연락처
    if rp_block:
        m = re.search(r'주소\s+(.+?)(?=분쟁대상|\Z)', rp_block, re.DOTALL)
        if not m:
            m = re.search(r'주소\s+(.+)', rp_block, re.DOTALL)
        if m:
            raw = m.group(1).replace("\n", " ").strip()
            phone = _find_phone(raw)
            if phone:
                r["피신청인_연락처"] = phone
            addr = _best_address(raw)
            if addr:
                r["피신청인_주소"] = addr

    # ── 지역 + 건물소재지 (분쟁대상 건물 위치)
    m = re.search(r'위치\s+(.+?)(?=면적|\n)', text)
    if m:
        loc = m.group(1).strip()
        r["건물소재지"] = loc
        city_m = re.search(r'경기도\s+(\S+시|\S+군)', loc)
        if city_m:
            r["지역"] = f"경기도 {city_m.group(1)}"
        elif loc:
            r["지역"] = loc[:30]

    # 지역이 아직 없으면 신청인 주소에서 추출
    if not r.get("지역") and r.get("신청인_주소"):
        city_m = re.search(r'경기도\s+(\S+시|\S+군)', r["신청인_주소"])
        if city_m:
            r["지역"] = f"경기도 {city_m.group(1)}"

    # ── 신청내용
    m = re.search(r'조정신청\s*내용\s+(.+?)(?=조정을\s*신청하는|피해예상금액)', text, re.DOTALL)
    if m:
        content = " ".join(m.group(1).split()).strip()
        r["신청내용"] = content[:800] + ("..." if len(content) > 800 else "")

    return r, raw_text


# 필드별 한글 레이블
FIELD_LABELS = {
    "접수일자":       "접수일자",
    "신청인_성명":    "신청인 성명",
    "신청인_주소":    "신청인 주소",
    "신청인_연락처":  "신청인 연락처",
    "피신청인_성명":  "피신청인 성명",
    "피신청인_주소":  "피신청인 주소",
    "피신청인_연락처":"피신청인 연락처",
    "지역":           "지역",
    "건물소재지":     "건물소재지",
    "신청내용":       "신청내용",
}
