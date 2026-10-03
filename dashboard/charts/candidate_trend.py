"""조건별 대상국 탐색 화면의 추출 국가 비교 시계열."""
import pandas as pd
import plotly.graph_objects as go

from dashboard.analysis.candidates import p4_value_text
from dashboard.charts.theme import CHART_FONT, empty_figure
from dashboard.metrics import P4_COUNTRY_COLORS, P4_INDICATORS


def p4_trend_chart(source, shortlist_isos, label, active_iso, chosen_year, log_axis,
                   country_display):
    """한 지표에 추출 국가를 겹쳐 그리고 선택 국가만 굵게 강조합니다."""
    spec = P4_INDICATORS[label]
    column = spec["column"]
    kind = spec["kind"]
    use_log = log_axis and kind == "money"

    valid_years = source.loc[source[column].notna(), "Year"]
    if valid_years.empty:
        return empty_figure("시계열 자료가 없습니다.", height=300)
    first_year, last_year = int(valid_years.min()), int(valid_years.max())

    chart = go.Figure()
    has_points = False
    # 강조 국가를 마지막에 그려 다른 선 위에 오도록 합니다.
    plot_order = [iso for iso in shortlist_isos if iso != active_iso] + [active_iso]

    for iso in plot_order:
        d = source.loc[
            (source["Iso3"] == iso) & source["Year"].between(first_year, last_year),
            ["Year", "Country", column],
        ].sort_values("Year")
        values = pd.to_numeric(d[column], errors="coerce")
        if use_log:
            values = values.where(values > 0)
        if not values.notna().any():
            continue
        has_points = True

        emph = iso == active_iso
        color = P4_COUNTRY_COLORS[shortlist_isos.index(iso) % len(P4_COUNTRY_COLORS)]
        # 금액은 10억 USD로 그리고, 마우스를 올리면 읽기 쉬운 금액으로 보여 줍니다.
        y = values / 1000 if kind == "money" else values
        hover_text = [p4_value_text(label, v) for v in values]
        chart.add_trace(go.Scatter(
            x=d["Year"], y=y,
            name=country_display(d.iloc[0]["Country"]),
            mode="lines+markers" if emph else "lines",
            connectgaps=False,
            line={"color": color, "width": 3.4 if emph else 1.4},
            marker={"size": 5},
            opacity=1.0 if emph else 0.38,
            customdata=hover_text,
            hovertemplate="%{fullData.name}<br>%{x}년 · %{customdata}<extra></extra>",
        ))

    if not has_points:
        return empty_figure("추출 국가의 시계열 자료가 없습니다.", height=300)

    y_title = {"money": "10억 USD", "share": "%", "score": "점 (0~10)"}[kind]
    if use_log:
        y_title += " · 로그"
    yaxis = {"title": y_title, "fixedrange": True, "automargin": True}
    if use_log:
        # 10배 간격(1, 10, 100 …)에만 눈금·격자를 둬서 로그 축 격자가 촘촘해지지 않게
        yaxis.update(type="log", dtick=1, tickformat=",~g", minor={"showgrid": False})
    elif kind == "score":
        yaxis.update(range=[0, 10])
    else:
        yaxis.update(rangemode="tozero",
                     tickformat=",.0f" if kind == "money" else ",.3~g")

    span = last_year - first_year
    chart.update_layout(
        template="dash_clean", height=300,
        font={"family": CHART_FONT, "size": 11},
        margin={"l": 54, "r": 12, "t": 12, "b": 30},
        xaxis={"title": None, "range": [first_year - .5, last_year + .5],
               "fixedrange": True, "dtick": 1 if span <= 10 else 5},
        yaxis=yaxis,
        showlegend=False,
        hovermode="closest", dragmode=False,
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    )
    if first_year <= int(chosen_year) <= last_year:
        chart.add_vline(x=int(chosen_year), line_width=1,
                        line_dash="dot", line_color="#C99B45", opacity=0.8)
    return chart
