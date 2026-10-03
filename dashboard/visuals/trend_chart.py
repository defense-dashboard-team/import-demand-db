"""시계열 그래프 (국가별 추이, 상관분석 상세, 조건별 탐색)"""
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard.common.config import MILEX_COL, RISK_START
from dashboard.common.countries import country_display
from dashboard.common.formatting import usd_m_text
from dashboard.common.metrics import (
    P4_INDICATORS,
    P4_MUTED_COLORS,
    PAGE2_METRIC,
    TREND_METRICS,
)
from dashboard.context import ctx
from dashboard.db.analysis import trend_slice
from dashboard.visuals.theme import CHART_FONT, empty_figure, MILEX_COLOR


def make_page2_line(
    data,
    iso,
    metric="risk",
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
                    ctx.YEAR_MIN,
                    ctx.YEAR_MAX + 1,
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
            x0=ctx.YEAR_MIN - 0.5,
            x1=RISK_START - 0.5,
            fillcolor="#000000",
            opacity=0.05,
            line_width=0,
        )

        fig.add_annotation(
            x=(
                ctx.YEAR_MIN
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
            ctx.YEAR_MIN - 0.5,
            ctx.YEAR_MAX + 0.5,
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


def p4_trend_chart(source, selected_isos, label, active_iso, chosen_year):
    """해당 지표 하나에 최대 5개국을 중첩 표시, 선택 국가만 선명하게 강조."""
    spec = P4_INDICATORS[label]
    column = spec["column"]
    chart = go.Figure()
    subset = source.loc[source["Iso3"].isin(selected_isos)].copy()
    # 분쟁위험도는 2017~2025년만 표시합니다. 나머지 지표의 기존 범위는 유지합니다.
    first_year, last_year = (
        (2017, 2025) if label == "분쟁위험도"
        else (int(source["Year"].min()), int(source["Year"].max()))
    )
    span = pd.DataFrame({"Year": list(range(first_year, last_year + 1))})
    has_visible_points = False

    # 비강조 국가부터 그리고 마지막에 강조 국가를 얹어 가독성 확보
    plot_order = [iso for iso in selected_isos if iso != active_iso]
    if active_iso in selected_isos:
        plot_order.append(active_iso)

    for iso in plot_order:
        d = subset[
            (subset["Iso3"] == iso)
            & subset["Year"].between(first_year, last_year)
        ].sort_values("Year")
        if d.empty:
            continue
        name = country_display(d.iloc[0]["Country"])
        d = span.merge(d[["Year", column]], on="Year", how="left")
        vals = pd.to_numeric(d[column], errors="coerce")
        if not vals.notna().any():
            continue
        has_visible_points = True
        emph = iso == active_iso
        color = (
            "#125CB0" if emph
            else P4_MUTED_COLORS[selected_isos.index(iso) % len(P4_MUTED_COLORS)]
        )
        chart.add_trace(go.Scatter(
            x=d["Year"], y=vals,
            name=name, mode="lines+markers" if emph else "lines",
            connectgaps=False,
            line={"color": color, "width": 3.5 if emph else 1.6},
            marker={"size": 5 if emph else 2},
            opacity=1.0 if emph else 0.46,
            hovertemplate=(
                "%{fullData.name}<br>%{x}년 · %{y:,.2f} "
                + ("백만 USD" if label in ["GDP", "군사비"] else spec["unit"])
                + "<extra></extra>"
            ),
        ))

    if not has_visible_points:
        empty = empty_figure("선택 국가의 시계열 자료가 없습니다.", height=320)
        if label == "분쟁위험도":
            empty.update_xaxes(
                visible=True, range=[2016.5, 2025.5],
                tickmode="array", tickvals=list(range(2017, 2026)),
                tickangle=-45, tickfont={"size": 9},
            )
        return empty

    # 기존 원자료의 GDP·군사비는 백만 USD. 범위 설정 패널만 10억 USD로 환산.
    y_unit = "백만 USD" if label in ["GDP", "군사비"] else spec["unit"]
    xaxis_options = {
        "title": None, "range": [first_year - .5, last_year + .5],
        "fixedrange": True,
    }
    if label == "분쟁위험도":
        xaxis_options.update(
            tickmode="array", tickvals=list(range(2017, 2026)),
            tickangle=-45, tickfont={"size": 9},
        )
    else:
        xaxis_options.update(tickmode="linear", dtick=5)

    chart.update_layout(
        template="dash_clean", height=320,
        font={"family": CHART_FONT, "size": 11},
        margin={"l": 54, "r": 12, "t": 32, "b": 34},
        xaxis=xaxis_options,
        yaxis={"title": y_unit, "tickformat": ",.2~s", "rangemode": "tozero",
               "fixedrange": True, "automargin": True},
        legend={"orientation": "h", "y": 1.03, "x": 0,
                "yanchor": "bottom", "font": {"size": 10},
                "itemclick": False, "itemdoubleclick": False},
        showlegend=(label == "GDP"),
        hovermode="closest", dragmode=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    if first_year <= int(chosen_year) <= last_year:
        chart.add_vline(x=int(chosen_year), line_width=1,
                        line_dash="dot", line_color="#C99B45", opacity=0.7)
    return chart
