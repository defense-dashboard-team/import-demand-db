"""전세계 탭 오른쪽 카드 : 선택 지표 상위 10개국 막대."""
import pandas as pd
import streamlit as st

from dashboard.config import COUNTRY_COL, ISO_COL
from dashboard.data.world import top10_countries
from dashboard.utils.html import p1_html
from dashboard.utils.world_format import country_flag_html, country_name_korean


# ========================================================
# 35. TOP10 HTML
# ========================================================

def create_top10_html(top10, selected_column, selected_value_format):

    if top10.empty:

        return """
                <div>
                    표시할 데이터가 없습니다.
                </div>
                """


    top_max = (
        top10[
            selected_column
        ]
        .max()
    )


    rows = ""


    for rank, (_, row) in enumerate(
        top10.iterrows(),
        start=1,
    ):

        country_name = (
            country_name_korean(
                row[ISO_COL],
                row[COUNTRY_COL],
            )
        )


        flag = (
            country_flag_html(
                row[ISO_COL]
            )
        )


        value = (
            row[
                selected_column
            ]
        )


        display_value = (
            selected_value_format(
                value
            )
        )


        if (
            pd.notna(top_max)
            and top_max != 0
        ):

            width = (
                value
                / top_max
                * 100
            )

        else:

            width = 0


        width = max(
            0,
            min(
                float(width),
                100,
            ),
        )


        rows += f"""
                <div class="top10-row">

                    <div class="p1-rank-number">
                        {rank}
                    </div>

                    <div>
                        {flag}
                    </div>

                    <div
                        class="p1-country-name"
                        title="{country_name}"
                    >
                        {country_name}
                    </div>

                    <div class="top10-bar-background">

                        <div
                            class="top10-bar-fill"
                            style="
                                width:{width:.2f}%;
                            "
                        >
                        </div>

                    </div>

                    <div class="top10-value">
                        {display_value}
                    </div>

                </div>
                """


    return f"""
            <div class="top10-wrapper">
                {rows}
            </div>
            """


def render_top10(map_df, selected_column, metric_title, selected_year, selected_value_format):
    top10 = top10_countries(map_df, selected_column)

    with st.container(
        border=True,
        key="card_p1_top10",
    ):

        p1_html(
        f"""
                <div class="chart-title">
                    {metric_title} 상위 10개국 ({selected_year})
                </div>

                <div class="chart-description">
                    막대 길이는 1위 국가 대비 비율입니다.
                </div>

                {create_top10_html(top10, selected_column, selected_value_format)}
                """
        )
