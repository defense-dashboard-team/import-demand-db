"""1페이지 상위 10개국 막대 목록 (HTML)"""
import pandas as pd

from dashboard.common.countries import country_flag_html, country_name_korean
from dashboard.db.overview import COUNTRY_COL, ISO_COL


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
