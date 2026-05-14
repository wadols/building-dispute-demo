"""
다음(카카오) 주소 검색 Streamlit 컴포넌트 래퍼
반환값: {"postcode": "12345", "address": "경기도 수원시 ..."} 또는 None
"""
import streamlit.components.v1 as components
from pathlib import Path

_COMPONENT_DIR = (Path(__file__).parent.parent / "components" / "daum_postcode").resolve()
_daum_postcode = components.declare_component(
    "daum_postcode",
    path=str(_COMPONENT_DIR),
)


def address_search_widget(key: str = "addr_search"):
    """
    다음 주소 검색 위젯.
    주소 선택 시 {"postcode": "...", "address": "..."} 반환, 미선택이면 None.
    """
    return _daum_postcode(key=key, default=None)
