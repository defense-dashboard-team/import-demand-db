"""상관분석 화면 버블차트 (군사비/GDP × 분쟁위험도 또는 무기수입 점유율)."""
import numpy as np
import plotly.graph_objects as go

from dashboard.charts.theme import BASE_LAYOUT, BUBBLE_MAX, BUBBLE_MIN, empty_figure, RED, SIM_EDGE
from dashboard.config import MILEX_COL, RISK_START, SIZE_COL, X_COL
from dashboard.metrics import PAGE2_METRIC


def bubble_size(values):
    v = np.sqrt(
        np.clip(
            values.astype(float),
            0,
            None,
        )
    )

    lo = np.nanmin(v)
    hi = np.nanmax(v)

    if hi == lo:
        return np.full(
            len(v),
            (
                BUBBLE_MIN
                + BUBBLE_MAX
            ) / 2,
        )

    return (
        BUBBLE_MIN
        + (v - lo)
        / (hi - lo)
        * (
            BUBBLE_MAX
            - BUBBLE_MIN
        )
    )


def make_bubble(
    data,
    year,
    metric="risk",
    size_col=SIZE_COL,
    highlight=None,
    similar=None,
    *,
    country_display,
):
    m = PAGE2_METRIC[metric]

    if (
        metric == "risk"
        and
        year < RISK_START
    ):
        return empty_figure(
            f"분쟁위험도(INFORM)는 "
            f"{RISK_START}년부터 제공됩니다.<br>"
            f"{RISK_START}년 이후를 선택하거나 "
            "TIV 차트를 이용하세요."
        )

    d = data[
        data["Year"] == year
    ].dropna(
        subset=[
            X_COL,
            m["col"],
            size_col,
        ]
    )

    d = d[
        (d[X_COL] > 0)
        &
        (d[size_col] > 0)
    ]

    if d.empty:
        return empty_figure(
            f"{year}년 데이터가 없습니다."
        )

    y = (
        d[m["col"]]
        .clip(lower=0.004)
        if m["log_y"]
        else d[m["col"]]
    )

    if m["log_color"]:
        cvals = np.log10(
            d[m["col"]]
            .clip(lower=0.004)
        )

        color_ticks = [
            0.004,
            0.01,
            0.1,
            1,
            10,
        ]

        colorbar = dict(
            title=dict(
                text=m["label"],
                side="right",
            ),
            thickness=12,
            len=0.75,
            tickvals=np.log10(
                color_ticks
            ),
            ticktext=[
                "0",
                "0.01",
                "0.1",
                "1",
                "10",
            ],
        )

    else:
        cvals = d[m["col"]]

        colorbar = dict(
            title=dict(
                text=m["label"],
                side="right",
            ),
            thickness=12,
            len=0.75,
        )
    sim_set = set(similar or [])

    fig = go.Figure(
        go.Scatter(
            x=d[X_COL],
            y=y,
            mode="markers",
            customdata=np.stack(
                [
                    d["Country"].map(country_display),
                    d["Iso3"],
                    d[SIZE_COL],
                    d[MILEX_COL],
                    d[m["col"]],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "GDP 대비 군사비 "
                "%{x:.2f}%<br>"
                + m["label"]
                + " %{customdata[4]:"
                + m["fmt"]
                + "}<br>"
                "GDP "
                "%{customdata[2]:,.0f}<br>"
                "군사비 "
                "%{customdata[3]:,.0f}"
                "<extra></extra>"
            ),
            marker=dict(
                size=bubble_size(
                    d[size_col]
                ),
                sizemode="diameter",
                color=cvals,
                colorscale=m["scale"],
                showscale=True,
                colorbar=colorbar,
                opacity=(
                    0.72
                    if highlight is None
                    else [
                        1.0
                        if iso == highlight
                        else (
                            0.85
                            if iso in sim_set
                            else 0.18
                        )
                        for iso in d["Iso3"]
                    ]
                ),
                line=dict(
                    width=[
                        3.0
                        if iso == highlight
                        else (
                            2.2
                            if iso in sim_set
                            else 0.5
                        )
                        for iso in d["Iso3"]
                    ],
                    color=[
                        RED
                        if iso == highlight
                        else (
                            SIM_EDGE
                            if iso in sim_set
                            else "rgba(60,60,60,0.35)"
                        )
                        for iso in d["Iso3"]
                    ],
                ),
            ),
            selected=dict(
                marker=dict(
                    opacity=0.95
                )
            ),
            unselected=dict(
                marker=dict(
                    opacity=0.25
                )
            ),
        )
    )

    # 제목은 패널 헤더(HTML)에서 한 번만 표시합니다.
    fig.update_layout(
        xaxis=dict(
            title="GDP 대비 군사비 (%)",
            type="log",
            fixedrange=True,
            tickvals=[
                0.2,
                0.5,
                1,
                2,
                5,
                10,
                20,
                40,
            ],
            ticktext=[
                "0.2",
                "0.5",
                "1",
                "2",
                "5",
                "10",
                "20",
                "40",
            ],
        ),
        yaxis=dict(
            title=m["label"],
            fixedrange=True,
            type=(
                "log"
                if m["log_y"]
                else "linear"
            ),
            tickvals=m["yticks"],
            ticktext=m["ytext"],
        ),
        height=368,
        dragmode=False,
        **BASE_LAYOUT,
    )

    fig.update_layout(margin=dict(l=58, r=70, t=22, b=48))

    return fig
