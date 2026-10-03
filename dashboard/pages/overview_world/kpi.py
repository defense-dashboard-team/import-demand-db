"""전세계 탭 위쪽 KPI 카드 4개 (군사비 총액, 군사비/GDP 중앙값, 무기 수입 규모, 고위험 국가 수)."""
import numpy as np
import pandas as pd
import streamlit as st

from dashboard.config import (
    COUNTRY_COL,
    HIGH_RISK_THRESHOLD,
    MIL_COL,
    RISK_COL,
    SHARE_GDP_COL,
    TIV_SUM_COL,
)
from dashboard.utils.html import p1_html
from dashboard.utils.world_format import (
    count_delta,
    military_to_usd,
    money_format,
    percent_delta,
    percentage_point_delta,
    share_gdp_to_percent,
    tiv_format,
)


# ============================================================
# 22. KPI 카드 출력 함수
# ============================================================

def show_kpi(
    icon,
    title,
    value,
    delta,
    delta_type,
    description,
):

    p1_html(
    f"""
        <div class="p1-kpi-card">
            <div class="p1-kpi-head">
                <div class="kpi-icon">{icon}</div>
                <div class="kpi-name">{title}</div>
            </div>
            <div class="p1-kpi-value-row">
                <div class="p1-kpi-value">{value}</div>
                <div class="delta-{delta_type}">{delta}</div>
            </div>
            <div class="kpi-description">{description}</div>
        </div>
        """
    )


def render_kpis(year_df, previous_df, selected_year):
    # ============================================================
    # 21. KPI 계산
    # ============================================================

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


    # ============================================================
    # 23. KPI 출력
    # ============================================================

    kpi1, kpi2, kpi3, kpi4 = st.columns(
        4,
        gap="small",
    )


    with kpi1:

        show_kpi(
            "🛡️",
            "세계 군사비 총액",
            money_format(
                military_total
            ),
            military_delta_text,
            military_delta_type,
            f"{selected_year}년 전 세계 군사비 합계",
        )


    with kpi2:

        show_kpi(
            "📊",
            "GDP 대비 군사비 중앙값",
            (
                f"{military_gdp_median:.2f}%"
                if pd.notna(military_gdp_median)
                else "-"
            ),
            share_delta_text,
            share_delta_type,
            "분석 국가의 GDP 대비 군사비 비율 중앙값",
        )


    with kpi3:

        show_kpi(
            "📦",
            "세계 무기 수입 규모",
            tiv_format(
                tiv_total
            ),
            tiv_delta_text,
            tiv_delta_type,
            "TIV 기준 최근 5년 누적 무기 수입 규모",
        )


    with kpi4:

        show_kpi(
            "⚠️",
            "고위험 국가 수",
            f"{high_risk_count}개국",
            risk_delta_text,
            risk_delta_type,
            (
                f"분쟁위험도 "
                f"{HIGH_RISK_THRESHOLD:g}점 이상 국가"
            ),
        )


    st.write("")
