"""국가 코드 변환, 한글 국가명, 국기, 조사 처리"""
from babel import Locale
import pandas as pd
import pycountry

from dashboard.common.config import COUNTRY_DISPLAY_FIX, KOREAN_NAME_FIX
from dashboard.context import ctx


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


KO_LOCALE = Locale.parse("ko")


def josa(word, with_batchim, without_batchim):
    """
    받침에 맞는 조사를 붙입니다. 예) josa("대한민국", "과", "와") → "대한민국과"
    한글이 아닌 글자로 끝나면(GDP 등) 받침 없는 쪽을 씁니다.
    """
    word = str(word)
    last = word[-1] if word else ""

    if "가" <= last <= "힣" and (ord(last) - 0xAC00) % 28:
        return word + with_batchim

    return word + without_batchim


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


def country_display(name):
    """
    화면 표시용 국가명 : 한글 (데이터 원본 값은 그대로 두고 표기만 바꿈).
    한글 이름을 찾지 못하면 영문 표기를 사용합니다.
    """
    korean = country_korean(ctx.country_to_iso3.get(name))
    return korean or country_english(name)


# ---- 아래는 1페이지(전세계 지도/Top10)에서 쓰는 버전 ----

SPECIAL_ISO2 = {
    "XKX": "XK",
}

SPECIAL_KOREAN_NAMES = {
    "XKX": "코소보",
}


def iso3_to_alpha2(iso3):
    if pd.isna(iso3):
        return None

    iso3 = str(iso3).upper()

    if iso3 in SPECIAL_ISO2:
        return SPECIAL_ISO2[iso3]

    try:
        country = pycountry.countries.get(alpha_3=iso3)

        if country:
            return country.alpha_2

    except Exception:
        pass

    return None


def country_name_korean(iso3, fallback):
    iso3 = str(iso3).upper()

    if iso3 in SPECIAL_KOREAN_NAMES:
        return SPECIAL_KOREAN_NAMES[iso3]

    alpha2 = iso3_to_alpha2(iso3)

    if alpha2:
        korean_name = KO_LOCALE.territories.get(alpha2)

        if korean_name:
            return korean_name

    return str(fallback)


def country_flag_html(iso3):
    """
        ISO3 -> 실제 국기 이미지 HTML
        Windows에서 국기 이모지가 문자/빈칸으로 보이는 문제를 피하기 위해
        FlagCDN의 PNG 이미지를 사용합니다.
        """
    alpha2 = iso3_to_alpha2(iso3)

    if not alpha2:
        return """
            <span class="flag-placeholder">
                🌐
            </span>
            """

    code = alpha2.lower()

    return f"""
        <img
            class="country-flag"
            src="https://flagcdn.com/w40/{code}.png"
            alt="{code.upper()}"
        >
        """
