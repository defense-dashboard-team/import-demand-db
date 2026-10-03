"""1페이지(전세계) 데이터: 정리, 국가-연도 집계, KPI, 지도용 표"""
import numpy as np
import pandas as pd

from dashboard.common.countries import country_name_korean
from dashboard.common.overview_format import (
    count_delta,
    military_to_usd,
    percent_delta,
    percentage_point_delta,
    share_gdp_to_percent,
)
from dashboard.db.connection import load_integrate_raw


HIGH_RISK_THRESHOLD = 7.0

# 원본 테이블 컬럼
COUNTRY_COL = "Country"
ISO_COL = "Iso3"
YEAR_COL = "Year"

MIL_COL = "current_usd"
GDP_COL = "gdp_calculated"

TIV_SHARE_COL = "TIV_5Y_Share"
TIV_SUM_COL = "TIV_5Y_Sum"

RISK_COL = "human_hazard_score"
SHARE_GDP_COL = "share_gdp"


def load_overview_raw():
    # 2·3페이지와 같은 공용 로더 (AWS DB integrate 테이블, 없으면 CSV)
    return load_integrate_raw()[0]


def missing_overview_columns(df):
    required_columns = [
        COUNTRY_COL,
        ISO_COL,
        YEAR_COL,
        MIL_COL,
        GDP_COL,
        TIV_SHARE_COL,
        TIV_SUM_COL,
        RISK_COL,
        SHARE_GDP_COL,
    ]

    missing_columns = [col for col in required_columns if col not in df.columns]

    return missing_columns


def clean_overview_data(df):
    numeric_columns = [
        YEAR_COL,
        MIL_COL,
        GDP_COL,
        TIV_SHARE_COL,
        TIV_SUM_COL,
        RISK_COL,
        SHARE_GDP_COL,
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df = df.dropna(
        subset=[
            COUNTRY_COL,
            ISO_COL,
            YEAR_COL,
        ]
    ).copy()

    df[YEAR_COL] = df[YEAR_COL].astype(int)

    df[ISO_COL] = (
        df[ISO_COL]
        .astype(str)
        .str.upper()
        .str.strip()
    )

    return df


def detect_tiv_share_fraction(df):
    """무기 수입 점유율이 0~1 비율로 들어왔는지 (그러면 표시할 때 100을 곱함)"""
    # 무기 수입 점유율 단위 판단

    tiv_share_values = df[TIV_SHARE_COL].dropna().abs()

    if not tiv_share_values.empty:
        TIV_SHARE_IS_FRACTION = tiv_share_values.quantile(0.95) <= 1
    else:
        TIV_SHARE_IS_FRACTION = False

    return TIV_SHARE_IS_FRACTION


def create_country_year_data(source_df, year):

    temp = (
        source_df[
            source_df[YEAR_COL]
            == year
        ]
        .copy()
    )

    temp = (
        temp
        .groupby(
            [
                COUNTRY_COL,
                ISO_COL,
            ],
            as_index=False,
        )
        .agg({
            MIL_COL: "mean",
            GDP_COL: "mean",
            TIV_SHARE_COL: "mean",
            TIV_SUM_COL: "mean",
            RISK_COL: "mean",
            SHARE_GDP_COL: "mean",
        })
    )

    return temp


def compute_overview_kpis(year_df, previous_df):
    # 세계 군사비 총액

    military_total = military_to_usd(
        year_df[MIL_COL]
        .sum(
            min_count=1
        )
    )

    previous_military_total = military_to_usd(
        previous_df[MIL_COL]
        .sum(
            min_count=1
        )
    )

    military_delta_text, military_delta_type = percent_delta(
        military_total,
        previous_military_total,
    )

    # GDP 대비 군사비 중앙값

    share_values = share_gdp_to_percent(
        year_df[SHARE_GDP_COL]
    )

    previous_share_values = share_gdp_to_percent(
        previous_df[SHARE_GDP_COL]
    )

    military_gdp_median = (
        share_values.median()
        if not share_values.empty
        else np.nan
    )

    previous_military_gdp_median = (
        previous_share_values.median()
        if not previous_share_values.empty
        else np.nan
    )

    share_delta_text, share_delta_type = percentage_point_delta(
        military_gdp_median,
        previous_military_gdp_median,
    )

    # 세계 무기 수입 규모

    tiv_total = (
        year_df[TIV_SUM_COL]
        .sum(
            min_count=1
        )
    )

    previous_tiv_total = (
        previous_df[TIV_SUM_COL]
        .sum(
            min_count=1
        )
    )

    tiv_delta_text, tiv_delta_type = percent_delta(
        tiv_total,
        previous_tiv_total,
    )

    # 고위험 국가 수

    high_risk_count = (
        year_df.loc[
            year_df[RISK_COL]
            >= HIGH_RISK_THRESHOLD,
            COUNTRY_COL,
        ]
        .nunique()
    )

    previous_high_risk_count = (
        previous_df.loc[
            previous_df[RISK_COL]
            >= HIGH_RISK_THRESHOLD,
            COUNTRY_COL,
        ]
        .nunique()
    )

    # 고위험 국가 수는 늘어나면 위험 신호이므로 증가 = 빨강
    risk_delta_text, risk_delta_type = count_delta(
        high_risk_count,
        previous_high_risk_count,
        len(previous_df) > 0,
    )

    risk_delta_type = {
        "up": "risk-up",
        "down": "risk-down",
    }.get(risk_delta_type, risk_delta_type)

    return dict(
        military_total=military_total,
        military_delta_text=military_delta_text,
        military_delta_type=military_delta_type,
        military_gdp_median=military_gdp_median,
        share_delta_text=share_delta_text,
        share_delta_type=share_delta_type,
        tiv_total=tiv_total,
        tiv_delta_text=tiv_delta_text,
        tiv_delta_type=tiv_delta_type,
        high_risk_count=high_risk_count,
        risk_delta_text=risk_delta_text,
        risk_delta_type=risk_delta_type,
    )


def metric_column(selected_metric):
    """선택한 지표 -> (데이터 컬럼, 화면 제목)"""
    if selected_metric == "GDP":

        selected_column = GDP_COL
        metric_title = "GDP"

    elif selected_metric == "군사비":

        selected_column = MIL_COL
        metric_title = "군사비"

    elif selected_metric == "분쟁위험도":

        selected_column = RISK_COL
        metric_title = "분쟁위험도"

    else:

        selected_column = TIV_SHARE_COL
        metric_title = "무기 수입 점유율"

    return selected_column, metric_title


def build_map_frame(year_df, selected_column, selected_metric):
    # 지도용 데이터

    map_df = (
        year_df[
            [
                COUNTRY_COL,
                ISO_COL,
                selected_column,
            ]
        ]
        .dropna(
            subset=[
                ISO_COL,
                selected_column,
            ]
        )
        .copy()
    )

    map_df[
        "Country_KO"
    ] = map_df.apply(
        lambda row:
        country_name_korean(
            row[ISO_COL],
            row[COUNTRY_COL],
        ),
        axis=1,
    )

    # 지도에서는 0보다 작은 값이 있을 경우
    # 색상 스케일 왜곡을 막기 위해 0으로 제한
    map_df[
        "map_value"
    ] = (
        map_df[
            selected_column
        ]
        .astype(float)
        .clip(
            lower=0
        )
    )

    # 지도 색상 스케일
    # GDP / 군사비 / 무기 수입 점유율은 국가별 격차가 매우 커서
    # 단순 0~최대값 선형 스케일을 쓰면 일부 상위 국가만 진하게 보입니다.
    # 따라서 지도 색상에만 log1p 정규화를 적용합니다.
    # 실제 데이터 값 자체는 전혀 바꾸지 않습니다.
    # 분쟁위험도는 값의 범위가 상대적으로 좁기 때문에 선형 스케일을 유지합니다.

    max_value = (
        map_df[
            "map_value"
        ]
        .max()
    )

    if (
        pd.isna(max_value)
        or max_value <= 0
    ):
        max_value = 1.0

    USE_LOG_COLOR_SCALE = (
        selected_metric
        in [
            "GDP",
            "군사비",
            "무기 수입 점유율",
        ]
    )

    if USE_LOG_COLOR_SCALE:

        map_df[
            "color_value"
        ] = np.log1p(
            map_df[
                "map_value"
            ]
        )

        color_max = float(
            np.log1p(
                max_value
            )
        )

    else:

        map_df[
            "color_value"
        ] = map_df[
            "map_value"
        ]

        color_max = float(
            max_value
        )

    if (
        not np.isfinite(
            color_max
        )
        or color_max <= 0
    ):
        color_max = 1.0

    # 백분위

    map_df[
        "rank_percentile"
    ] = (
        map_df[
            selected_column
        ]
        .rank(
            ascending=False,
            method="average",
            pct=True,
        )
        * 100
    )

    return map_df, max_value, color_max, USE_LOG_COLOR_SCALE


def legend_value_texts(USE_LOG_COLOR_SCALE, color_max, max_value, selected_value_format):
    # 범례 경계값
    # 색상바의 0%, 25%, 50%, 75%, 100% 위치에 해당하는
    # "실제 데이터 값"을 표시합니다.
    # GDP/군사비/TIV는 로그 정규화된 색상축을 역변환하므로
    # 지도에서 보이는 색상과 범례 경계값이 정확히 일치합니다.

    color_positions = [
        0.00,
        0.25,
        0.50,
        0.75,
        1.00,
    ]

    if USE_LOG_COLOR_SCALE:

        legend_values = [
            float(
                np.expm1(
                    position
                    * color_max
                )
            )
            for position in color_positions
        ]

    else:

        legend_values = [
            float(
                position
                * max_value
            )
            for position in color_positions
        ]

    (
        legend_0,
        legend_25,
        legend_50,
        legend_75,
        legend_100,
    ) = legend_values

    legend_0_text = selected_value_format(
        legend_0
    )

    legend_25_text = selected_value_format(
        legend_25
    )

    legend_50_text = selected_value_format(
        legend_50
    )

    legend_75_text = selected_value_format(
        legend_75
    )

    legend_100_text = selected_value_format(
        legend_100
    )

    return legend_0_text, legend_25_text, legend_50_text, legend_75_text, legend_100_text


def top10_frame(map_df, selected_column):
    top10 = (
        map_df
        .sort_values(
            selected_column,
            ascending=False,
        )
        .head(10)
        .copy()
    )

    return top10
