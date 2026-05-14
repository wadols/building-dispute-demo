"""
hwpx 템플릿 치환 엔진
hwpx = ZIP 구조이므로 Contents/section0.xml 내 {{변수}} 를 치환 후 재압축
"""
import zipfile
import struct
import zlib
from pathlib import Path
from datetime import date, datetime

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


# ────────────────────────────────────────────────
# 위원회 개최 문서 생성
# ────────────────────────────────────────────────

HEARING_TEMPLATE_DIR = Path(__file__).parent.parent / "템플릿" / "위원회 개최"
HEARING_OUTPUT_DIR   = Path(__file__).parent.parent / "output" / "위원회개최"

HEARING_TEMPLATES = [
    "1. 개최알림_참석요청 공문.hwpx",
    "2. 참석위원명단.hwpx",
    "3. 개최계획.hwpx",
    "4. 조정서.hwpx",
    "5. 간사 시나리오.hwpx",
    "6. 위원장 시나리오.hwpx",
    "7. 위원 서명부.hwpx",
    "8. 제안서 수령증.hwpx",
]


def _kor_datetime(dt_str: str | None) -> str:
    """'2026-04-15 14:00' → '2026. 4. 15. 오후 2시 00분'"""
    if not dt_str:
        return ""
    try:
        dt = datetime.fromisoformat(dt_str.replace(" ", "T"))
        ampm = "오후" if dt.hour >= 12 else "오전"
        h12 = dt.hour - 12 if dt.hour > 12 else (12 if dt.hour == 0 else dt.hour)
        return f"{dt.year}. {dt.month}. {dt.day}. {ampm} {h12}시 {dt.minute:02d}분"
    except Exception:
        return dt_str


def _kor_date_str(d: str | None) -> str:
    """'2026-04-15' → '2026. 4. 15.'"""
    if not d:
        return ""
    try:
        parts = str(d)[:10].split("-")
        return f"{parts[0]}. {int(parts[1])}. {int(parts[2])}."
    except Exception:
        return str(d) if d else ""


def _build_hearing_mapping(case: dict, hearing: dict, members: list[dict]) -> dict:
    """위원회 개최 문서용 변수 매핑 생성"""
    개최예정일시 = hearing.get("개최예정일시") or ""

    mapping = {
        "접수연도":         str(case.get("접수연도", "")),
        "신청인_성명":      case.get("신청인_성명", ""),
        "신청인1_성명":     case.get("신청인_성명", ""),  # 간사시나리오 변수명 대응
        "신청인_주소":      case.get("신청인_주소", ""),
        "신청인_연락처":    case.get("신청인_연락처", "") or "",
        "신청인_지위":      case.get("신청인_지위", "") or "",
        "피신청인_성명":    case.get("피신청인_성명", ""),
        "피신청인_주소":    case.get("피신청인_주소", ""),
        "피신청인_연락처":  case.get("피신청인_연락처", "") or "",
        "피신청인_지위":    case.get("피신청인_지위", "") or "",
        "피신청인_직위":    case.get("피신청인_지위", "") or "",  # 개최계획 오타 대응
        "건물명":           case.get("건물명", "") or "",
        "건물소재지":       case.get("건물소재지", "") or "",
        "조정내용":         case.get("신청내용", "") or "",
        "접수일자":         _kor_date_str(case.get("접수일자")),
        "회신접수일":       _kor_date_str(case.get("회신접수일")),
        "회차":             str(hearing.get("회차", "")),
        "개최예정일시":     _kor_date_str(개최예정일시),
        "개최장소":         hearing.get("개최장소", "") or "",
        "일시":             _kor_datetime(개최예정일시),
    }

    # 위원 정보 — 역할 순 정렬(위원장 → 위원 → 간사)
    role_order = {"위원장": 0, "위원": 1, "간사": 2}
    sorted_members = sorted(members, key=lambda m: role_order.get(m.get("역할", "위원"), 1))

    for i, m in enumerate(sorted_members, 1):
        p = f"위원{i}_"
        birth = m.get("생년월일") or ""
        mapping.update({
            p + "성명":             m.get("성명", ""),
            p + "소속":             m.get("소속", "") or "",
            p + "직위":             m.get("직위", "") or "",
            p + "은행명":           m.get("은행명", "") or "",
            p + "계좌번호":         m.get("계좌번호", "") or "",
            p + "최종학력 및 경력": m.get("최종학력 및 경력") or "",
            p + "생년":             birth[:4] if birth else "",
        })

    # 빈 슬롯 처리 (최대 7명 지원)
    for i in range(len(sorted_members) + 1, 8):
        p = f"위원{i}_"
        for field in ["성명", "소속", "직위", "은행명", "계좌번호", "최종학력 및 경력", "생년"]:
            mapping[p + field] = ""

    return mapping


def _hwpx_binary_patch(src_path: Path, out_path: Path, mapping: dict) -> None:
    """
    원본 hwpx 를 바이너리 수준에서 수술적으로 수정.
    변경 대상(section*.xml, PrvText.txt)만 재압축하고, 나머지 항목은
    원본 압축 바이트를 그대로 보존 → Hangul 보안 경고 방지.
    """
    LOCAL_SIG   = b'PK\x03\x04'
    CENTRAL_SIG = b'PK\x01\x02'
    EOCD_SIG    = b'PK\x05\x06'

    raw = bytearray(src_path.read_bytes())

    # ─── 1단계: 로컬 파일 헤더 파싱 ──────────────────────────
    def _parse_locals(raw: bytearray) -> list:
        entries = []
        pos = 0
        while True:
            idx = raw.find(LOCAL_SIG, pos)
            if idx == -1:
                break
            (ver_needed, flag, method,
             mod_time, mod_date,
             crc32, comp_size, uncomp_size) = struct.unpack_from('<HHHHH III', raw, idx + 4)
            fnlen, exlen = struct.unpack_from('<HH', raw, idx + 26)
            fname = raw[idx + 30: idx + 30 + fnlen].decode('utf-8', 'ignore')
            hdr_size  = 30 + fnlen + exlen
            data_start = idx + hdr_size
            data_end   = data_start + comp_size
            entries.append({
                'fname': fname, 'flag': flag, 'method': method,
                'crc32': crc32, 'comp_size': comp_size, 'uncomp_size': uncomp_size,
                'hdr_offset': idx, 'hdr_size': hdr_size,
                'data_start': data_start, 'data_end': data_end,
            })
            pos = idx + 4
        return entries

    entries = _parse_locals(raw)

    # ─── 2단계: 변경 대상 항목 재압축 ───────────────────────
    changed: dict[str, tuple] = {}   # fname → (new_compressed, new_crc32, new_uncomp_size)
    for e in entries:
        fn = e['fname']
        if (fn.startswith('Contents/section') and fn.endswith('.xml')) or \
           fn == 'Preview/PrvText.txt':
            raw_comp = bytes(raw[e['data_start']: e['data_end']])
            if e['method'] == 8:
                orig_bytes = zlib.decompress(raw_comp, -15)
            else:
                orig_bytes = raw_comp
            text     = orig_bytes.decode('utf-8', errors='ignore')
            text     = _fill_template(text, mapping)
            new_data = text.encode('utf-8')
            if e['method'] == 8:
                cobj     = zlib.compressobj(9, zlib.DEFLATED, -15)
                new_comp = cobj.compress(new_data) + cobj.flush()
            else:
                new_comp = new_data
            new_crc = zlib.crc32(new_data) & 0xFFFFFFFF
            changed[fn] = (new_comp, new_crc, len(new_data))

    # ─── 3단계: 새 ZIP 바이너리 구성 ────────────────────────
    result   = bytearray()
    offsets  = {}   # fname → new header offset in result

    for e in entries:
        fn = e['fname']
        offsets[fn] = len(result)
        # 원본 로컬 헤더 복사
        hdr = bytearray(raw[e['hdr_offset']: e['hdr_offset'] + e['hdr_size']])

        if fn in changed:
            new_comp, new_crc, new_uncomp = changed[fn]
            struct.pack_into('<I', hdr, 14, new_crc)
            struct.pack_into('<I', hdr, 18, len(new_comp))
            struct.pack_into('<I', hdr, 22, new_uncomp)
            result += bytes(hdr) + new_comp
        else:
            # 원본 압축 바이트를 그대로 보존
            result += bytes(hdr)
            result += bytes(raw[e['data_start']: e['data_end']])

    # ─── 4단계: 중앙 디렉터리 재구성 ────────────────────────
    cd_start = len(result)
    cd_count = 0
    pos = 0
    while True:
        idx = raw.find(CENTRAL_SIG, pos)
        if idx == -1:
            break
        fnlen  = struct.unpack_from('<H', raw, idx + 28)[0]
        exlen  = struct.unpack_from('<H', raw, idx + 30)[0]
        cmlen  = struct.unpack_from('<H', raw, idx + 32)[0]
        fname  = raw[idx + 46: idx + 46 + fnlen].decode('utf-8', 'ignore')
        cd_len = 46 + fnlen + exlen + cmlen
        cd_ent = bytearray(raw[idx: idx + cd_len])

        # 로컬 헤더 오프셋 갱신 (offset 42)
        struct.pack_into('<I', cd_ent, 42, offsets.get(fname, struct.unpack_from('<I', cd_ent, 42)[0]))

        if fname in changed:
            new_comp, new_crc, new_uncomp = changed[fname]
            struct.pack_into('<I', cd_ent, 16, new_crc)
            struct.pack_into('<I', cd_ent, 20, len(new_comp))
            struct.pack_into('<I', cd_ent, 24, new_uncomp)

        result += bytes(cd_ent)
        cd_count += 1
        pos = idx + 4

    # ─── 5단계: EOCD 갱신 ────────────────────────────────────
    eocd_idx = raw.rfind(EOCD_SIG)
    eocd     = bytearray(raw[eocd_idx: eocd_idx + 22])
    struct.pack_into('<H', eocd,  8, cd_count)
    struct.pack_into('<H', eocd, 10, cd_count)
    struct.pack_into('<I', eocd, 12, len(result) - cd_start)
    struct.pack_into('<I', eocd, 16, cd_start)
    result += bytes(eocd)

    out_path.write_bytes(bytes(result))


def generate_hearing_docs(case: dict, hearing: dict, members: list[dict]) -> list[Path]:
    """위원회 개최 hwpx 문서 7종 일괄 생성. 생성된 파일 Path 목록 반환."""
    접수번호 = case.get("접수번호", "unknown")
    회차 = hearing.get("회차", 1)

    out_dir = HEARING_OUTPUT_DIR / f"{접수번호}_{회차}차"
    out_dir.mkdir(parents=True, exist_ok=True)

    mapping = _build_hearing_mapping(case, hearing, members)
    generated = []

    for tname in HEARING_TEMPLATES:
        tpath = HEARING_TEMPLATE_DIR / tname
        if not tpath.exists():
            continue
        stem = tname.split(". ", 1)[-1].replace(".hwpx", "")
        out_path = out_dir / f"{stem}_{접수번호}_{회차}차.hwpx"

        _hwpx_binary_patch(tpath, out_path, mapping)
        generated.append(out_path)

    return generated


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
    _hwpx_binary_patch(template_path, out_path, mapping)
    return out_path
