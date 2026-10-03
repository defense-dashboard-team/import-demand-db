"""1페이지 [전세계] 탭: KPI, 세계지도, 범례, 상위 10개국"""
from functools import partial
from textwrap import dedent

import pandas as pd
import streamlit as st

from dashboard.common.countries import country_flag_html, country_name_korean, josa
from dashboard.common.overview_format import (
    format_selected_value,
    money_format,
    tiv_format,
)
from dashboard.context import ctx
from dashboard.db.overview import (
    build_map_frame,
    clean_overview_data,
    compute_overview_kpis,
    COUNTRY_COL,
    create_country_year_data,
    detect_tiv_share_fraction,
    HIGH_RISK_THRESHOLD,
    ISO_COL,
    legend_value_texts,
    load_overview_raw,
    metric_column,
    missing_overview_columns,
    top10_frame,
)
from dashboard.screens.state import sync_clicked_country
from dashboard.visuals.render import read_asset, style_block
from dashboard.visuals.top10 import create_top10_html
from dashboard.visuals.world_borders import load_world_geojson
from dashboard.visuals.world_map import (
    legend_marker,
    make_world_map,
    map_colorscale,
    render_wheel_zoom_script,
)


def p1_html(code):
    code = dedent(code).strip()

    if hasattr(st, "html"):
        st.html(code)
    else:
        st.markdown(code, unsafe_allow_html=True)


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


def resolve_selected_country(year_df):
    """다른 화면과 공유하는 선택 국가를 이 연도 데이터 기준으로 정해 session_state에 기록"""
    # 선택 국가 기본값

    available_isos = set(
        year_df[ISO_COL]
        .dropna()
        .astype(str)
    )

    # 2·3페이지와 공유하는 선택 국가(영문 국가명)를 ISO 코드로 바꿉니다.
    current_iso = ctx.country_to_iso3.get(
        st.session_state.selected_country
    )

    if current_iso:
        current_iso = str(current_iso).upper()

    # 선택 국가가 없거나 이 연도에 데이터가 없으면 기본 국가로 표시
    if (
        not current_iso
        or current_iso not in available_isos
    ):

        default_iso = ctx.country_to_iso3.get(ctx.default_country)
        default_iso = str(default_iso).upper() if default_iso else None

        if default_iso in available_isos:
            current_iso = default_iso

        elif "ISR" in available_isos:
            current_iso = "ISR"

        elif available_isos:
            current_iso = sorted(
                available_isos
            )[0]

        else:
            current_iso = None

    st.session_state[
        "selected_country_iso"
    ] = current_iso

    if current_iso:

        row = year_df[
            year_df[ISO_COL]
            == current_iso
        ]

        if not row.empty:

            current_name = (
                row.iloc[0][COUNTRY_COL]
            )

            st.session_state[
                "selected_country_name"
            ] = current_name

            st.session_state[
                "selected_country_name_ko"
            ] = country_name_korean(
                current_iso,
                current_name,
            )


def render_kpis(
    selected_year,
    military_total,
    military_delta_text,
    military_delta_type,
    military_gdp_median,
    share_delta_text,
    share_delta_type,
    tiv_total,
    tiv_delta_text,
    tiv_delta_type,
    high_risk_count,
    risk_delta_text,
    risk_delta_type,
):
    # KPI 출력

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


def render_metric_selector():
    # 분석 지표 선택
    # 전 세계 분포 영역의 왼쪽 상단

    selector_left, selector_right = st.columns(
        [
            1.72,
            1,
        ],
        gap="small",
    )

    with selector_left:

        selector_label_col, selector_control_col = st.columns(
            [
                0.85,
                4.15,
            ],
            gap="small",
        )

        with selector_label_col:

            p1_html(
            """
                <div class="metric-selector-label">
                    분석 지표 선택
                </div>
                """
            )

        with selector_control_col:

            selected_metric = st.segmented_control(
                "분석 지표",
                [
                    "GDP",
                    "군사비",
                    "분쟁위험도",
                    "무기 수입 점유율",
                ],
                default="군사비",
                selection_mode="single",
                label_visibility="collapsed",
                key="global_metric_selector",
            )

            # 단일 선택 컨트롤이므로 혹시 None이 들어오면 군사비로 복구
            if selected_metric is None:
                selected_metric = "군사비"

    return selected_metric


def render_map_heading(metric_title, selected_year):
    current_country_ko = (
        st.session_state
        .get(
            "selected_country_name_ko",
            "국가 미선택",
        )
    )

    current_country_iso = (
        st.session_state
        .get(
            "selected_country_iso",
            "",
        )
    )

    current_flag = (
        country_flag_html(
            current_country_iso
        )
        if current_country_iso
        else """
                    <span class="flag-placeholder">
                        🌐
                    </span>
                    """
    )

    # 세계지도 제목 오른쪽에 현재 선택
    p1_html(
    f"""
                <div class="map-heading">

                    <div class="chart-title">
                        전 세계 {metric_title} 분포 ({selected_year})
                    </div>

                    <div class="current-country-pill">

                        <span>
                            현재 선택 :
                        </span>

                        <span>
                            {current_flag}
                        </span>

                        <span>
                            {current_country_ko}
                            {
                                f"({current_country_iso})"
                                if current_country_iso
                                else ""
                            }
                        </span>

                    </div>

                </div>
                """
    )

    p1_html(
    f"""
                <div class="chart-description">
                    색이 진할수록 {josa(metric_title, "이", "가")} 큽니다.
                    국가를 클릭하면 선택됩니다.
                </div>
                """
    )


def handle_map_click(map_event, year_df):
    """지도에서 누른 국가를 선택 국가로 반영 (다른 화면, 상단 필터와 공유)"""
    # 지도 클릭 이벤트

    def get_selected_points(event):

        try:
            return event.selection.points

        except Exception:

            try:
                return event["selection"]["points"]

            except Exception:
                return []

    selected_points = get_selected_points(
        map_event
    )

    if selected_points:

        point = selected_points[-1]

        clicked_iso = None

        # Choropleth location
        try:
            clicked_iso = point.get(
                "location"
            )
        except Exception:
            pass

        # customdata fallback
        if not clicked_iso:

            try:

                customdata = (
                    point.get(
                        "customdata"
                    )
                )

                if (
                    customdata
                    and len(customdata) >= 4
                ):

                    clicked_iso = (
                        customdata[3]
                    )

            except Exception:
                pass

        if clicked_iso:

            clicked_iso = (
                str(clicked_iso)
                .upper()
            )

            previous_iso = (
                st.session_state
                .get(
                    "selected_country_iso"
                )
            )

            if (
                clicked_iso
                != previous_iso
            ):

                selected_row = (
                    year_df[
                        year_df[ISO_COL]
                        == clicked_iso
                    ]
                )

                if not selected_row.empty:

                    clicked_name = (
                        selected_row
                        .iloc[0][
                            COUNTRY_COL
                        ]
                    )

                    clicked_name_ko = (
                        country_name_korean(
                            clicked_iso,
                            clicked_name,
                        )
                    )

                    st.session_state[
                        "selected_country_iso"
                    ] = clicked_iso

                    st.session_state[
                        "selected_country_name"
                    ] = clicked_name

                    st.session_state[
                        "selected_country_name_ko"
                    ] = clicked_name_ko

                    # 2·3페이지와 사이드바에도 같은 국가를 반영하고
                    # 제목 오른쪽의 현재 선택 국가를 즉시 갱신
                    sync_clicked_country(clicked_name)
                    st.rerun()


def render_legend(
    metric_title,
    selected_year,
    legend_marker_html,
    legend_100_text,
    legend_75_text,
    legend_50_text,
    legend_25_text,
    legend_0_text,
):
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


def render_page1():
    WORLD_GEOJSON, WORLD_GEOJSON_IDS = load_world_geojson()

    df = load_overview_raw()

    missing_columns = missing_overview_columns(df)

    if missing_columns:
        st.error("CSV에 필요한 컬럼이 없습니다.")
        st.write("없는 컬럼:", missing_columns)
        st.write("현재 CSV 컬럼:", df.columns.tolist())
        st.stop()

    df = clean_overview_data(df)
    TIV_SHARE_IS_FRACTION = detect_tiv_share_fraction(df)

    p1_html(style_block(read_asset("page1_overview.css")))

    # 1페이지: 사이드바 연도와 완전히 공유하는 전세계 화면
    # 1페이지 제목은 공통 바깥 틀 위에서 한 번만 표시합니다.
    selected_year = int(st.session_state.selected_year)

    year_df = create_country_year_data(
        df,
        selected_year,
    )

    previous_df = create_country_year_data(
        df,
        selected_year - 1,
    )

    resolve_selected_country(year_df)

    kpis = compute_overview_kpis(year_df, previous_df)
    render_kpis(selected_year=selected_year, **kpis)

    # 지도 + 범례 + TOP10 전체 큰 틀
    with st.container(
        border=True,
        key="plain_p1_outer",
    ):

        selected_metric = render_metric_selector()
        selected_column, metric_title = metric_column(selected_metric)

        map_df, max_value, color_max, USE_LOG_COLOR_SCALE = build_map_frame(
            year_df, selected_column, selected_metric,
        )

        # 선택 지표에 맞는 표시 형식 (지도 툴팁, 범례, Top10에서 같이 씀)
        selected_value_format = partial(
            format_selected_value,
            selected_metric=selected_metric,
            tiv_share_is_fraction=TIV_SHARE_IS_FRACTION,
        )

        map_df[
            "display_value"
        ] = (
            map_df[
                selected_column
            ]
            .apply(
                selected_value_format
            )
        )

        (
            legend_0_text,
            legend_25_text,
            legend_50_text,
            legend_75_text,
            legend_100_text,
        ) = legend_value_texts(
            USE_LOG_COLOR_SCALE, color_max, max_value, selected_value_format,
        )

        legend_marker_html = legend_marker(
            map_df, color_max, selected_column, selected_value_format,
        )

        fig_map = make_world_map(
            map_df, color_max, map_colorscale(selected_metric),
            metric_title, WORLD_GEOJSON_IDS,
        )

        top10 = top10_frame(map_df, selected_column)

        # 지도 / TOP10 본문

        map_area, top10_area = st.columns(
            [
                2.06,
                1,
            ],
            gap="small",
        )

        # 왼쪽 - 세계지도

        with map_area:

            with st.container(
                border=True,
                key="card_p1_map",
            ):

                render_map_heading(metric_title, selected_year)

                map_plot_col, legend_col = st.columns(
                    [
                        9.5,
                        1.8,
                    ],
                    gap="small",
                )

                # 지도

                with map_plot_col:

                    # 사용자가 직접 누르는 지도 초기화 버튼은 표시하지 않습니다.
                    # 아래의 숨겨진 버튼은 조작 종료 2초 후에만 JS가 클릭합니다.

                    map_event = st.plotly_chart(

                        fig_map,

                        use_container_width=True,

                        config={
                            # 기본 Geo 휠 줌은 포인터 위치를 중심으로 확대합니다.
                            # 화면의 +/- 버튼은 기존 요청대로 표시하지 않습니다.
                            "displayModeBar": False,
                            "scrollZoom": True,
                            "doubleClick": False,
                        },

                        key=(
                            f"world_map_"
                            f"{selected_year}_"
                            f"{selected_column}_"
                            f"{st.session_state.world_map_reset_version}"
                        ),

                        on_select="rerun",

                        selection_mode="points",
                    )

                    render_wheel_zoom_script()
                    handle_map_click(map_event, year_df)

                # 그라데이션 + 경계선 숫자 범례

                with legend_col:

                    render_legend(
                        metric_title, selected_year, legend_marker_html,
                        legend_100_text, legend_75_text, legend_50_text,
                        legend_25_text, legend_0_text,
                    )

        # 오른쪽 - TOP10

        with top10_area:

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
