"""국가별 탭의 지표 추이 차트 (큰 차트와 썸네일이 같이 씀)."""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.charts.theme import CHART_FONT, empty_figure
from dashboard.metrics import TREND_METRICS
from dashboard.utils.formatting import usd_m_text


def trend_slice(data, iso, metric):
    """
    선택 국가 · 선택 지표에서 값이 존재하는 구간만 잘라 돌려줍니다.
    지표마다 데이터 시작 연도가 달라 x축 범위를 각각 계산합니다.
    """
    setting = TREND_METRICS[metric]

    d = data[data["Iso3"] == iso].sort_values("Year")

    if d.empty:
        return None, None, None

    col = setting["col"]

    if col not in d.columns:
        return None, None, None

    valid = d[d[col].notna()]

    if valid.empty:
        return None, None, None

    y0 = int(valid["Year"].min())
    y1 = int(valid["Year"].max())

    d = d[(d["Year"] >= y0) & (d["Year"] <= y1)]

    return d, y0, y1


def trend_year_span(data, iso, metric):
    _, y0, y1 = trend_slice(data, iso, metric)

    if y0 is None:
        return ""

    return f"{y0}–{y1}"


def make_trend_figure(
    data,
    iso,
    metric,
    compact=False,
    height=460,
    mark_year=None,
):
    setting = TREND_METRICS[metric]

    if not iso:
        return empty_figure("국가를 선택하세요.", height=height)

    d, y0, y1 = trend_slice(data, iso, metric)

    if d is None:
        return empty_figure(
            f"{setting['short']} 데이터가 없습니다.",
            height=height,
        )

    name = d["Country"].iloc[0]
    col = setting["col"]
    is_money = metric in ["milex", "gdp"]

    use_second = (
        setting["kind"] == "bar_line"
        and setting["sub_col"] in d.columns
    )

    fig = make_subplots(
        specs=[[{"secondary_y": use_second}]]
    )

    # 선택 연도가 그래프 범위 안에 있는지
    mark = (
        int(mark_year)
        if mark_year is not None and y0 <= int(mark_year) <= y1
        else None
    )

    if is_money:
        hover_main = (
            setting["short"].split(" · ")[0]
            + " %{customdata}<extra></extra>"
        )
        custom = [usd_m_text(v) for v in d[col]]
    else:
        hover_main = (
            setting["short"]
            + " %{y:.3f}<extra></extra>"
        )
        custom = None

    if setting["kind"] in ["bar", "bar_line"]:
        fig.add_trace(
            go.Bar(
                x=d["Year"],
                y=d[col],
                name=setting["short"].split(" · ")[0],
                marker=dict(
                    color=setting["color"],
                    # 선택 연도 막대에만 주황 테두리 (다른 막대는 그대로)
                    line=dict(
                        color="#E09A00",
                        width=(
                            [
                                (2.5 if compact else 4)
                                if yr == mark
                                else 0
                                for yr in d["Year"]
                            ]
                            if mark is not None
                            else 0
                        ),
                    ),
                ),
                customdata=custom,
                hovertemplate=hover_main,
            ),
            secondary_y=False,
        )
    else:
        fig.add_trace(
            go.Scatter(
                x=d["Year"],
                y=d[col],
                name=setting["short"],
                mode="lines+markers",
                connectgaps=False,
                line=dict(color=setting["color"], width=2.4),
                marker=dict(size=5 if not compact else 3),
                fill="tozeroy",
                fillcolor="rgba(31,111,235,0.10)"
                if metric == "tiv"
                else "rgba(108,92,231,0.10)",
                hovertemplate=hover_main,
            ),
            secondary_y=False,
        )

    if use_second:
        fig.add_trace(
            go.Scatter(
                x=d["Year"],
                y=d[setting["sub_col"]],
                name="군사비/GDP (%)",
                mode="lines+markers",
                connectgaps=False,
                line=dict(color=setting["accent"], width=2.2),
                marker=dict(size=5 if not compact else 3),
                hovertemplate=(
                    "군사비/GDP %{y:.2f}%"
                    "<extra></extra>"
                ),
            ),
            secondary_y=True,
        )

    span = max(1, y1 - y0)
    dtick = 2 if span <= 14 else (5 if compact else 3)

    fig.update_xaxes(
        title_text=None if compact else "연도",
        hoverformat="d",
        dtick=dtick,
        fixedrange=True,
        range=[y0 - 0.6, y1 + 0.6],
        tickfont=dict(size=9 if compact else 11),
        showgrid=False,
    )

    fig.update_yaxes(
        title_text=None if compact else setting["y_title"],
        secondary_y=False,
        rangemode="tozero",
        fixedrange=True,
        tickformat="~s" if is_money else None,
        tickfont=dict(size=9 if compact else 11),
        color=setting["color"] if use_second else None,
    )

    if use_second:
        fig.update_yaxes(
            title_text=None if compact else setting["y2_title"],
            secondary_y=True,
            showgrid=False,
            rangemode="tozero",
            fixedrange=True,
            ticksuffix="%",
            tickfont=dict(size=9 if compact else 11),
            color=setting["accent"],
        )

    # 상단 필터에서 고른 연도를 강조합니다.
    # - 해당 연도 구간을 옅은 노란 띠로 칠하고
    # - 선그래프는 그 연도의 점을 크게 (흰 테두리)
    # - 막대는 위에서 해당 막대에 주황 테두리
    if mark is not None:
        fig.add_vrect(
            x0=mark - 0.5,
            x1=mark + 0.5,
            fillcolor="rgba(255, 184, 28, 0.16)",
            line_width=0,
            layer="below",
        )

        row = d[d["Year"] == mark]

        line_points = []

        if setting["kind"] not in ["bar", "bar_line"]:
            line_points.append((col, setting["color"], False))

        if use_second:
            line_points.append(
                (setting["sub_col"], setting["accent"], True)
            )

        for point_col, point_color, on_second in line_points:

            if row.empty or pd.isna(row[point_col].iloc[0]):
                continue

            fig.add_trace(
                go.Scatter(
                    x=[mark],
                    y=[row[point_col].iloc[0]],
                    mode="markers",
                    marker=dict(
                        size=8 if compact else 13,
                        color=point_color,
                        line=dict(
                            color="white",
                            width=1.5 if compact else 2.5,
                        ),
                    ),
                    showlegend=False,
                    hoverinfo="skip",
                ),
                secondary_y=on_second,
            )

        if not compact:
            fig.add_annotation(
                x=mark,
                y=1.0,
                yref="paper",
                yanchor="bottom",
                text=f"<b>{mark}</b>",
                showarrow=False,
                font=dict(size=11, color="white"),
                bgcolor="#E09A00",
                borderpad=3,
            )

    if compact:
        fig.update_layout(
            showlegend=False,
            height=height,
            margin=dict(l=34, r=30, t=6, b=20),
            bargap=0.25,
        )
    else:
        # 제목은 패널 헤더(HTML)에서 한 번만 표시합니다.
        fig.update_layout(
            showlegend=True,
            legend=dict(
                orientation="h",
                y=1.02,
                x=0,
                yanchor="bottom",
            ),
            height=height,
            margin=dict(l=68, r=70, t=34, b=52),
            bargap=0.3,
        )

    fig.update_layout(
        template="dash_clean",
        font=dict(
            family=CHART_FONT,
            size=12,
        ),
        hovermode="x unified" if not compact else "closest",
        dragmode=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    return fig
