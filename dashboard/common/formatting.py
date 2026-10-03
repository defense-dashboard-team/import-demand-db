"""숫자/금액/증감 표시 형식"""
import pandas as pd

from dashboard.common.metrics import P4_INDICATORS


def number_format(value, digits=1):
    return "-" if pd.isna(value) else f"{float(value):.{digits}f}"


def money_format(value):
    if pd.isna(value):
        return "-"

    value = float(value)

    if abs(value) >= 1_000_000_000_000:
        return f"${value / 1_000_000_000_000:.2f} T"
    if abs(value) >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f} B"
    if abs(value) >= 1_000_000:
        return f"${value / 1_000_000:.1f} M"

    return f"${value:,.0f}"


def percent_change(current, previous):
    if (
        previous is None
        or pd.isna(previous)
        or pd.isna(current)
        or previous == 0
    ):
        return None

    return (current - previous) / abs(previous) * 100


def delta_html(delta, unit="%", increase_bad=False):
    if delta is None or pd.isna(delta):
        return '<div class="delta-neutral">이전 값 없음</div>'

    up = delta >= 0
    arrow = "▲" if up else "▼"

    if increase_bad:
        css = "delta-negative" if up else "delta-positive"
    else:
        css = "delta-positive" if up else "delta-negative"

    return (
        f'<div class="{css}">'
        f'{arrow} {abs(delta):.1f}{unit}'
        '</div>'
    )


def ranking_value_format(metric, value):
    if pd.isna(value):
        return "-"

    if metric in ["GDP", "군사비"]:
        return money_format(value)

    if metric in ["군사비/GDP", "무기수입 점유율"]:
        return f"{value:.2f}%"

    return f"{value:.1f}"


# current_usd / gdp_calculated 는 '백만 USD' 단위입니다.
def usd_m_text(value):
    if pd.isna(value):
        return "-"

    value = float(value)
    size = abs(value)

    if size >= 1_000_000:
        return f"${value / 1_000_000:.2f}T"

    if size >= 1_000:
        return f"${value / 1_000:.1f}B"

    return f"${value:,.0f}M"


def p4_value_text(label, value):
    """국가 카드에 표시할 단위 및 결측 처리."""
    if value is None or pd.isna(value):
        return "자료 없음"
    setting = P4_INDICATORS[label]
    v = float(value) / setting["scale"]
    digits = setting["precision"]
    return f"{v:,.{digits}f} {setting['unit']}"
