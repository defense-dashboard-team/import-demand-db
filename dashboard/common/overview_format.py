"""1페이지(전세계) 전용 표시 형식. formatting.py와 단위 표기가 달라서 따로 둠"""
import numpy as np
import pandas as pd


# 현재 current_usd가 SIPRI의 million USD 단위인 경우 True
MILITARY_VALUES_ARE_MILLION_USD = True


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


def tiv_share_format(value, is_fraction):
    if pd.isna(value):
        return "-"

    value = float(value)

    if is_fraction:
        value *= 100

    return f"{value:.2f}%"


def share_gdp_to_percent(series):
    result = series.dropna().copy()

    if result.empty:
        return result

    if result.abs().median() <= 1:
        result *= 100

    return result


# KPI 전년 대비: 증가 = 빨강, 감소 = 초록, 동일 = 회색
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


def format_selected_value(value, selected_metric, tiv_share_is_fraction):

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
