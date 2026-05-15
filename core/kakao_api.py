"""
카카오 로컬 REST API — 주소 → 우편번호 조회
"""
import re
import urllib.request
import urllib.parse
import json
import streamlit as st


def _get_api_key() -> str:
    try:
        return st.secrets["KAKAO_REST_API_KEY"]
    except Exception:
        return ""


def _trim_address(address: str) -> str:
    """우편번호 조회용 — 도로명+건물번호 또는 지번까지만 추출, 건물명·동호수 제거"""
    # 괄호 안 건물명·법정동 제거 (예: (신장동) (삼성동))
    addr = re.sub(r'\([^)]*\)', '', address).strip()
    addr = re.sub(r'\s+', ' ', addr).strip()

    # 도로명주소: ~번길/~로/~길 + 공백 + 건물번호
    # \s+ 필수 — "선릉로92" 처럼 도로명 번호를 건물번호로 오인 방지
    m = re.search(r'(.+?(?:번길|로|길)\s+\d+(?:-\d+)?)', addr)
    if m:
        return m.group(1).strip()

    # 지번주소: ~동/~리 + 공백 + 지번
    m = re.search(r'(.+?(?:동|리)\s+\d+(?:-\d+)?)', addr)
    if m:
        return m.group(1).strip()

    return addr[:50].strip()


def lookup_postcode(address: str) -> str:
    """
    주소 문자열로 카카오 로컬 API를 호출해 우편번호(5자리)를 반환.
    실패 시 빈 문자열 반환.
    """
    api_key = _get_api_key()
    if not api_key or not address:
        return ""

    query = _trim_address(address)
    url = "https://dapi.kakao.com/v2/local/search/address.json?" + urllib.parse.urlencode({"query": query})
    req = urllib.request.Request(url, headers={"Authorization": f"KakaoAK {api_key}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
        docs = data.get("documents", [])
        if not docs:
            return ""
        doc = docs[0]
        # 도로명주소 우선, 없으면 지번주소
        zone = (doc.get("road_address") or {}).get("zone_no", "")
        if zone:
            return zone
        return (doc.get("address") or {}).get("zip_code", "")
    except Exception:
        return ""
