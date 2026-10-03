"""세계지도 오른쪽 색상 범례 (경계값 5개 + 선택 국가 위치 표시)."""
import html

import numpy as np
import streamlit as st

from dashboard.config import ISO_COL
from dashboard.utils.html import p1_html


def legend_tick_texts(max_value, color_max, USE_LOG_COLOR_SCALE, selected_value_format):
    # ========================================================
    # 30. 범례 경계값
    #
    # 색상바의 0%, 25%, 50%, 75%, 100% 위치에 해당하는
    # "실제 데이터 값"을 표시합니다.
    #
    # GDP/군사비/TIV는 로그 정규화된 색상축을 역변환하므로
    # 지도에서 보이는 색상과 범례 경계값이 정확히 일치합니다.
    # ========================================================

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


def selected_country_marker(map_df, selected_column, color_max, selected_value_format):
    # ========================================================
    # 28-1. 범례 막대에 선택 국가 위치 표시
    #
    # 지도 색과 같은 기준(color_value / color_max)으로 위치를 정하므로
    # 범례에서 가리키는 색 = 지도에서 그 나라의 색이 됩니다.
    # ========================================================

    legend_marker_html = ""

    marker_rows = map_df[
        map_df[ISO_COL]
        == st.session_state.get("selected_country_iso")
    ]

    if not marker_rows.empty:

        marker_row = marker_rows.iloc[0]

        marker_pos = min(
            max(
                float(marker_row["color_value"]) / color_max,
                0.0,
            ),
            1.0,
        )

        # 막대 위쪽이 최댓값, 아래쪽이 0
        marker_top = (1 - marker_pos) * 100

        legend_marker_html = f"""
            <div class="legend-marker" style="top:{marker_top:.2f}%;"></div>
            <div class="legend-marker-label" style="top:{marker_top:.2f}%;">
                <div class="legend-marker-name">
                    {html.escape(str(marker_row["Country_KO"]))}
                </div>
                <div class="legend-marker-value">
                    {selected_value_format(marker_row[selected_column])}
                </div>
            </div>
            """

    return legend_marker_html


def render_legend(
    map_df,
    selected_column,
    metric_title,
    selected_year,
    max_value,
    color_max,
    USE_LOG_COLOR_SCALE,
    selected_value_format,
):
    (
        legend_0_text,
        legend_25_text,
        legend_50_text,
        legend_75_text,
        legend_100_text,
    ) = legend_tick_texts(
        max_value,
        color_max,
        USE_LOG_COLOR_SCALE,
        selected_value_format,
    )

    legend_marker_html = selected_country_marker(
        map_df,
        selected_column,
        color_max,
        selected_value_format,
    )

    p1_html(
    f"""
                    <div class="legend-title">
                        {metric_title}
                    </div>

                    <div class="legend-subtitle">
                        {selected_year}년 전 세계 국가 기준
                    </div>


                    <div class="legend-scale">

                        <div class="legend-gradient">
                        </div>

                        {legend_marker_html}


                        <!-- 100% / 최대값 -->
                        <div
                            class="
                                legend-tick
                                legend-max-line
                            "
                        >
                        </div>

                        <div
                            class="
                                legend-tick-label
                                legend-max-label
                            "
                        >
                            {legend_100_text}
                        </div>


                        <!-- 75% -->
                        <div
                            class="
                                legend-tick
                                legend-75-line
                            "
                        >
                        </div>

                        <div
                            class="
                                legend-tick-label
                                legend-75-label
                            "
                        >
                            {legend_75_text}
                        </div>


                        <!-- 50% -->
                        <div
                            class="
                                legend-tick
                                legend-50-line
                            "
                        >
                        </div>

                        <div
                            class="
                                legend-tick-label
                                legend-50-label
                            "
                        >
                            {legend_50_text}
                        </div>


                        <!-- 25% -->
                        <div
                            class="
                                legend-tick
                                legend-25-line
                            "
                        >
                        </div>

                        <div
                            class="
                                legend-tick-label
                                legend-25-label
                            "
                        >
                            {legend_25_text}
                        </div>


                        <!-- 0 -->
                        <div
                            class="
                                legend-tick
                                legend-zero-line
                            "
                        >
                        </div>

                        <div
                            class="
                                legend-tick-label
                                legend-zero-label
                            "
                        >
                            {legend_0_text}
                        </div>

                    </div>
                    """
    )
