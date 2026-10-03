"""1페이지 전세계 화면 전용 표시 함수 (단위 변환, 전년 대비, 한글 국가명·국기).

다른 화면의 utils/formatting.py, utils/countries.py 와 표기가 조금씩 달라서 따로 둠.
(예: 금액이 "$1.0B" / 다른 화면은 "$1.0 B")
"""
from babel import Locale
import numpy as np
import pandas as pd
import pycountry

from dashboard.config import MILITARY_VALUES_ARE_MILLION_USD


# ============================================================
# 10. 단위/표시 함수
# ============================================================

def military_to_usd(value):
    if pd.isna(value):
        return np.nan

    value = float(value)

    if MILITARY_VALUES_ARE_MILLION_USD:
        return value * 1_000_000

    return value


def money_format(value):
    if pd.isna(value):
        return "-"

    value = float(value)

    if abs(value) >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f}T"

    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"

    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"

    if abs(value) >= 1_000:
        return f"${value / 1_000:.1f}K"

    return f"${value:,.0f}"


def tiv_format(value):
    if pd.isna(value):
        return "-"

    value = float(value)

    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"

    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"

    return f"{value:,.1f}"


def tiv_share_format(value, tiv_share_is_fraction):
    if pd.isna(value):
        return "-"

    value = float(value)

    if tiv_share_is_fraction:
        value *= 100

    return f"{value:.2f}%"


# ============================================================
# 12. GDP 대비 군사비 비율
# ============================================================

def share_gdp_to_percent(series):
    result = series.dropna().copy()

    if result.empty:
        return result

    if result.abs().median() <= 1:
        result *= 100

    return result


# ============================================================
# 13. KPI 전년 대비
#
# 증가 = 빨강
# 감소 = 초록
# 동일 = 회색
# ============================================================

def percent_delta(current, previous):
    if (
        pd.isna(current)
        or pd.isna(previous)
        or previous == 0
    ):
        return "전년 데이터 없음", "neutral"

    if np.isclose(
        current,
        previous,
        rtol=1e-9,
        atol=1e-12,
    ):
        return "● 전년과 동일", "same"

    change = (
        (current - previous)
        / abs(previous)
        * 100
    )

    # 화면에서 0.0%로 보일 정도의 차이도 동일 처리
    if abs(change) < 0.05:
        return "● 전년과 동일", "same"

    if change > 0:
        return f"▲ 전년 대비 +{change:.1f}%", "up"

    return f"▼ 전년 대비 {abs(change):.1f}%", "down"


def percentage_point_delta(current, previous):
    if pd.isna(current) or pd.isna(previous):
        return "전년 데이터 없음", "neutral"

    change = current - previous

    # 화면에서 0.00%p로 보일 정도의 차이도 동일 처리
    if (
        np.isclose(
            current,
            previous,
            rtol=1e-9,
            atol=1e-12,
        )
        or abs(change) < 0.005
    ):
        return "● 전년과 동일", "same"

    if change > 0:
        return f"▲ 전년 대비 +{change:.2f}%p", "up"

    return f"▼ 전년 대비 {abs(change):.2f}%p", "down"


def count_delta(current, previous, previous_exists):
    if not previous_exists:
        return "전년 데이터 없음", "neutral"

    change = int(current) - int(previous)

    if change == 0:
        return "● 전년과 동일", "same"

    if change > 0:
        return f"▲ 전년 대비 +{change}개국", "up"

    return f"▼ 전년 대비 {abs(change)}개국", "down"


# ============================================================
# 14. ISO / 한글 국가명 / 국기
# ============================================================

KO_LOCALE = Locale.parse("ko")

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


def make_value_format(selected_metric, tiv_share_is_fraction):
    """선택 지표에 맞는 값 표시 함수를 만들어 돌려줌 (지도 툴팁·범례·Top10이 같이 씀)"""

    def selected_value_format(value):

        if pd.isna(value):
            return "-"


        if selected_metric == "GDP":

            # GDP도 군사비처럼 백만 USD 단위 → 달러로 바꿔 표시
            return money_format(
                military_to_usd(
                    value
                )
            )


        if selected_metric == "군사비":

            return money_format(
                military_to_usd(
                    value
                )
            )


        if selected_metric == "분쟁위험도":

            return (
                f"{float(value):.2f}점"
            )


        if selected_metric == "무기 수입 점유율":

            return tiv_share_format(
                value,
                tiv_share_is_fraction,
            )


        return str(value)

    return selected_value_format
