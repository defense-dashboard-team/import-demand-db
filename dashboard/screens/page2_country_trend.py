"""1페이지 [국가별] 탭: 선택 국가 KPI + 지표별 시계열"""
import html

import pandas as pd
import streamlit as st

from dashboard.common.countries import flag_html
from dashboard.common.formatting import (
    delta_html,
    number_format,
    percent_change,
    usd_m_text,
)
from dashboard.common.metrics import TREND_METRICS, TREND_ORDER
from dashboard.context import ctx
from dashboard.db.analysis import trend_year_span
from dashboard.visuals.render import render_html
from dashboard.visuals.trend_chart import make_trend_figure


def render_country_view():
    # ========================================================
    # 2페이지 : 국가별 지표 추이
    # ========================================================

    # 1페이지 제목은 전세계 / 국가별 공통이므로 이곳에서 중복 출력하지 않습니다.

    # --------------------------------------------------------
    # 선택 국가 KPI (1페이지와 동일한 카드)
    # --------------------------------------------------------

    p2_gdp = ctx.current[ctx.COL["gdp"]]
    p2_military = ctx.current[ctx.COL["military"]]
    p2_share = ctx.current[ctx.COL["share_gdp"]]
    p2_tiv = ctx.current[ctx.COL["tiv"]]
    p2_risk = ctx.current[ctx.COL["risk"]]

    p2_gdp_prev = (
        ctx.previous[ctx.COL["gdp"]] if ctx.previous is not None else None
    )
    p2_military_prev = (
        ctx.previous[ctx.COL["military"]] if ctx.previous is not None else None
    )
    p2_share_prev = (
        ctx.previous[ctx.COL["share_gdp"]] if ctx.previous is not None else None
    )
    p2_risk_prev = (
        ctx.previous[ctx.COL["risk"]] if ctx.previous is not None else None
    )
    p2_tiv_old = (
        ctx.five_year_ago[ctx.COL["tiv"]] if ctx.five_year_ago is not None else None
    )

    p2_share_delta = (
        p2_share - p2_share_prev
        if p2_share_prev is not None and not pd.isna(p2_share_prev)
        else None
    )

    p2_tiv_delta = (
        p2_tiv - p2_tiv_old
        if p2_tiv_old is not None and not pd.isna(p2_tiv_old)
        else None
    )

    p2_risk_delta = (
        p2_risk - p2_risk_prev
        if p2_risk_prev is not None and not pd.isna(p2_risk_prev)
        else None
    )

    c1, c2, c3, c4, c5, c6 = st.columns(
        [1.10, 1, 1, 1, 1, 1],
        gap="small",
    )

    with c1:
        render_html(
            f"""
            <div class="kpi-card kpi-lg">
                <div class="kpi-label">선택 국가</div>
                <div class="country-kpi">
                    {flag_html(ctx.iso3, "country-flag-img")}
                    <div class="country-name">
                        {html.escape(ctx.country)} ({ctx.iso3})
                    </div>
                </div>
            </div>
            """
        )

    with c2:
        render_html(
            f"""
            <div class="kpi-card kpi-lg kpi-has-icon">
                <div class="kpi-icon2">💵</div>
                <div class="kpi-text">
                        <div class="kpi-label">GDP ({ctx.selected_year})</div>
                        <div class="kpi-row">
                            <div class="kpi-value">{usd_m_text(p2_gdp)}</div>
                            {delta_html(percent_change(p2_gdp, p2_gdp_prev))}
                        </div>
                </div>
            </div>
            """
        )

    with c3:
        render_html(
            f"""
            <div class="kpi-card kpi-lg kpi-has-icon">
                <div class="kpi-icon2">🛡️</div>
                <div class="kpi-text">
                        <div class="kpi-label">군사비 ({ctx.selected_year})</div>
                        <div class="kpi-row">
                            <div class="kpi-value">{usd_m_text(p2_military)}</div>
                            {delta_html(
                                percent_change(p2_military, p2_military_prev)
                            )}
                        </div>
                </div>
            </div>
            """
        )

    with c4:
        render_html(
            f"""
            <div class="kpi-card kpi-lg kpi-has-icon">
                <div class="kpi-icon2">📊</div>
                <div class="kpi-text">
                        <div class="kpi-label">
                            군사비 / GDP ({ctx.selected_year})
                        </div>
                        <div class="kpi-row">
                            <div class="kpi-value">
                                {number_format(p2_share)} %
                        </div>
                        {delta_html(p2_share_delta, "%p")}
                        </div>
                </div>
            </div>
            """
        )

    with c5:
        render_html(
            f"""
            <div class="kpi-card kpi-lg kpi-has-icon">
                <div class="kpi-icon2">📦</div>
                <div class="kpi-text">
                        <div class="kpi-label">
                            무기수입 점유율 (5년 누적)
                        </div>
                        <div class="kpi-row">
                            <div class="kpi-value">{number_format(p2_tiv)} %</div>
                            {delta_html(p2_tiv_delta, "%p")}
                        </div>
                </div>
            </div>
            """
        )

    with c6:
        render_html(
            f"""
            <div class="kpi-card kpi-lg kpi-has-icon">
                <div class="kpi-icon2">⚠️</div>
                <div class="kpi-text">
                        <div class="kpi-label">
                            분쟁 위험도 ({ctx.selected_year})
                        </div>
                        <div class="kpi-row">
                            <div class="kpi-value kpi-risk">
                                {number_format(p2_risk)}
                        </div>
                        {delta_html(p2_risk_delta, "", increase_bad=True)}
                        </div>
                </div>
            </div>
            """
        )

    # --------------------------------------------------------
    # 메인 그래프 + 썸네일
    # --------------------------------------------------------

    if st.session_state.trend_metric not in TREND_METRICS:
        st.session_state.trend_metric = "milex"

    active = st.session_state.trend_metric

    MAIN_PANEL_H = 672
    THUMB_PANEL_H = 214

    main_col, side_col = st.columns([2.05, 1], gap="small")

    with main_col:

        with st.container(
            border=True,
            height=MAIN_PANEL_H,
            key="card_p2_main",
        ):

            setting = TREND_METRICS[active]

            render_html(
                f"""
                <div class="panel-title">
                    {html.escape(setting['label'])}
                </div>

                <div class="panel-caption">
                    {html.escape(setting['note'])}
                </div>
                """
            )

            st.plotly_chart(
                make_trend_figure(
                    ctx.df,
                    ctx.sel_iso,
                    active,
                    compact=False,
                    height=MAIN_PANEL_H - 130,
                    mark_year=ctx.selected_year,
                ),
                use_container_width=True,
                key=(
                    f"trend_main_{ctx.sel_iso}_{active}_{ctx.selected_year}"
                ),
                config={
                    "displayModeBar": False,
                    "displaylogo": False,
                    "scrollZoom": False,
                    "doubleClick": False,
                    "responsive": True,
                },
            )

    with side_col:

        for key in TREND_ORDER:

            if key == active:
                continue

            with st.container(
                border=True,
                height=THUMB_PANEL_H,
                key=f"card_p2_thumb_{key}",
            ):

                span_text = trend_year_span(ctx.df, ctx.sel_iso, key)

                label = TREND_METRICS[key]["short"]

                if span_text:
                    label = f"{label}  ·  {span_text}"

                if st.button(
                    label,
                    use_container_width=True,
                    type="secondary",
                    key=f"trend_pick_{key}",
                ):
                    st.session_state.trend_metric = key
                    st.rerun()

                st.plotly_chart(
                    make_trend_figure(
                        ctx.df,
                        ctx.sel_iso,
                        key,
                        compact=True,
                        height=THUMB_PANEL_H - 96,
                        mark_year=ctx.selected_year,
                    ),
                    use_container_width=True,
                    key=(
                        f"trend_thumb_{ctx.sel_iso}_{key}_{ctx.selected_year}"
                    ),
                    config={
                        "displayModeBar": False,
                        "displaylogo": False,
                        "scrollZoom": False,
                        "doubleClick": False,
                        "staticPlot": True,
                        "responsive": True,
                    },
                )

    st.caption(
        "작은 그래프 제목을 누르면 큰 그래프로 바뀝니다. "
        "노란 띠는 선택한 연도입니다."
    )
