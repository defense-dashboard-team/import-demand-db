"""1페이지 전세계 화면용 데이터 (연도별 국가 집계, 지도 색상 값, 상위 10개국)."""
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.config import (
    COUNTRY_COL,
    GDP_COL,
    ISO_COL,
    MIL_COL,
    RISK_COL,
    SHARE_GDP_COL,
    TIV_SHARE_COL,
    TIV_SUM_COL,
    YEAR_COL,
)
from dashboard.data.loader import load_integrate_raw
from dashboard.utils.world_format import country_name_korean


def load_world_data():
    """integrate 원본을 전세계 화면용으로 정리 (필수 컬럼 확인, 숫자형 변환)"""
    # 2·3페이지와 같은 공용 로더 (AWS DB integrate 테이블, 없으면 CSV)
    df = load_integrate_raw()[0]

    # ============================================================
    # 8. 필요한 컬럼 확인
    # ============================================================

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

    if missing_columns:
        st.error("CSV에 필요한 컬럼이 없습니다.")
        st.write("없는 컬럼:", missing_columns)
        st.write("현재 CSV 컬럼:", df.columns.tolist())
        st.stop()


    # ============================================================
    # 9. 숫자형 변환
    # ============================================================

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


def tiv_share_is_fraction(df):
    # ============================================================
    # 11. 무기 수입 점유율 단위 판단
    # ============================================================

    tiv_share_values = df[TIV_SHARE_COL].dropna().abs()

    if not tiv_share_values.empty:
        TIV_SHARE_IS_FRACTION = tiv_share_values.quantile(0.95) <= 1
    else:
        TIV_SHARE_IS_FRACTION = False

    return TIV_SHARE_IS_FRACTION


# ============================================================
# 19. 국가-연도 단위 데이터
# ============================================================

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


def metric_column(selected_metric):
    # ========================================================
    # 25. 선택 지표 설정
    # ========================================================

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


def build_map_data(year_df, selected_metric, selected_column, selected_value_format):
    # ========================================================
    # 26. 지도용 데이터
    # ========================================================

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


    # ========================================================
    # 27. 지도 색상 스케일
    #
    # GDP / 군사비 / 무기 수입 점유율은 국가별 격차가 매우 커서
    # 단순 0~최대값 선형 스케일을 쓰면 일부 상위 국가만 진하게 보입니다.
    #
    # 따라서 지도 색상에만 log1p 정규화를 적용합니다.
    # 실제 데이터 값 자체는 전혀 바꾸지 않습니다.
    #
    # 분쟁위험도는 값의 범위가 상대적으로 좁기 때문에 선형 스케일을 유지합니다.
    # ========================================================

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


    # ========================================================
    # 28. 백분위
    # ========================================================

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


    map_df[
        "display_value"
    ] = (
        map_df[
            selected_column
        ]
        .apply(
            selected_value_format
        )
    )

    return map_df, max_value, color_max, USE_LOG_COLOR_SCALE


def top10_countries(map_df, selected_column):
    # 34. TOP10
    # ========================================================

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
