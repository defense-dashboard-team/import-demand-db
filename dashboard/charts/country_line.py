"""상관분석 화면 선택 국가 시계열 (좌축 군사비, 우축 분쟁위험도 또는 무기수입 점유율)."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.charts.theme import CHART_FONT, empty_figure, MILEX_COLOR
from dashboard.config import MILEX_COL, RISK_START
from dashboard.metrics import PAGE2_METRIC


def make_page2_line(
    data,
    iso,
    metric="risk",
    *,
    year_min,
    year_max,
):
    m = PAGE2_METRIC[metric]

    d = data[
        data["Iso3"] == iso
    ].sort_values("Year")

    if d.empty:
        return empty_figure(
            "국가가 선택되지 않았습니다.<br>"
            "왼쪽 버블차트에서 버블을 클릭하거나<br>"
            "사이드바에서 국가를 선택하세요."
        )

    name = d[
        "Country"
    ].iloc[0]

    full = pd.DataFrame(
        {
            "Year":
                range(
                    year_min,
                    year_max + 1,
                )
        }
    )

    d = full.merge(
        d,
        on="Year",
        how="left",
    )

    fig = make_subplots(
        specs=[
            [
                {
                    "secondary_y":
                        True
                }
            ]
        ]
    )

    fig.add_trace(
        go.Scatter(
            x=d["Year"],
            y=d[MILEX_COL],
            name="군사비",
            mode="lines+markers",
            connectgaps=False,
            line=dict(
                color=MILEX_COLOR,
                width=2,
            ),
            marker=dict(size=4),
            hovertemplate=(
                "%{x}년<br>"
                "군사비 "
                "%{y:,.0f}"
                "<extra></extra>"
            ),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=d["Year"],
            y=d[m["col"]],
            name=m["label"],
            mode="lines+markers",
            connectgaps=False,
            line=dict(
                color=m["color"],
                width=2,
                dash="dot",
            ),
            marker=dict(size=4),
            hovertemplate=(
                "%{x}년<br>"
                + m["label"]
                + " %{y:"
                + m["fmt"]
                + "}"
                "<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    if metric == "risk":
        fig.add_vrect(
            x0=year_min - 0.5,
            x1=RISK_START - 0.5,
            fillcolor="#000000",
            opacity=0.05,
            line_width=0,
        )

        fig.add_annotation(
            x=(
                year_min
                + RISK_START
            ) / 2,
            y=1.0,
            yref="paper",
            text=(
                "위험도 미제공 "
                f"(~{RISK_START - 1})"
            ),
            showarrow=False,
            font=dict(
                size=10,
                color="#7A8794",
            ),
        )

    fig.update_xaxes(
        title_text="연도",
        dtick=2,
        fixedrange=True,
        range=[
            year_min - 0.5,
            year_max + 0.5,
        ],
    )

    fig.update_yaxes(
        title_text="군사비",
        color=MILEX_COLOR,
        secondary_y=False,
        rangemode="tozero",
        fixedrange=True,
    )

    fig.update_yaxes(
        title_text=m["label"],
        color=m["color"],
        secondary_y=True,
        showgrid=False,
        tickformat=m["fmt"],
        fixedrange=True,
    )

    # 제목은 패널 헤더(HTML)에서 한 번만 표시합니다.
    fig.update_layout(
        legend=dict(
            orientation="h",
            y=1.02,
            x=0,
            yanchor="bottom",
        ),
        height=368,
        margin=dict(
            l=60,
            r=70,
            t=22,
            b=48,
        ),
        template="dash_clean",
        font=dict(
            family=CHART_FONT,
            size=12,
        ),
        hovermode="closest",
        dragmode=False,
    )

    return fig
