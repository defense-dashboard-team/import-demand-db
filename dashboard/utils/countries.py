"""ISO 코드 변환, 국기 이미지, 한글·영문 국가명."""
from babel import Locale
import pycountry


def iso3_to_iso2(iso3):
    code = str(iso3).upper().strip()

    # Kosovo는 ISO 3166 공식 alpha-3 코드가 없어
    # 대시보드에서는 널리 쓰이는 사용자 지정 코드 XKX를 사용합니다.
    # FlagCDN에서는 Kosovo를 xk로 제공하므로 별도 처리합니다.
    if code == "XKX":
        return "xk"

    try:
        item = pycountry.countries.get(alpha_3=code)
        return item.alpha_2.lower() if item else None
    except Exception:
        return None


def get_flag_url(iso3):
    iso2 = iso3_to_iso2(iso3)
    return f"https://flagcdn.com/w40/{iso2}.png" if iso2 else ""


def flag_html(iso3, css_class):
    url = get_flag_url(iso3)
    if not url:
        return ""
    return f'<img src="{url}" class="{css_class}" alt="{iso3}">'


COUNTRY_DISPLAY_FIX = {
    "Korea, South": "South Korea",
    "Korea, North": "North Korea",
    "Congo, DR": "DR Congo",
    "Congo, Republic": "Republic of the Congo",
    "Gambia, The": "The Gambia",
}


KO_LOCALE = Locale.parse("ko")


# babel 한글 국가명이 없거나 어색한 경우 직접 지정 (ISO3 기준)
KOREAN_NAME_FIX = {
    "XKX": "코소보",
}


def country_korean(iso3):
    """ISO3 → 한글 국가명 (1페이지 TOP10과 같은 방식). 없으면 None."""
    if not iso3:
        return None

    code = str(iso3).upper().strip()

    if code in KOREAN_NAME_FIX:
        return KOREAN_NAME_FIX[code]

    alpha2 = iso3_to_iso2(code)

    if alpha2:
        return KO_LOCALE.territories.get(alpha2.upper())

    return None


def country_english(name):
    """영문 표기 (데이터 원본 값을 읽기 좋게 정리)."""
    name = str(name)
    return COUNTRY_DISPLAY_FIX.get(name, name)
