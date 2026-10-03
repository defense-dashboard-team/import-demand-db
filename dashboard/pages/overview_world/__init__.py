"""1페이지 전세계 탭 : KPI 4개, 세계지도 + 범례, 상위 10개국.

(재원님 app_1page.py를 옮긴 것)
지도에서 국가를 클릭하면 selected_country가 바뀌어 다른 화면과 상단 필터에도 반영됨.
"""
import streamlit as st

from dashboard.data.world import (
    build_map_data,
    create_country_year_data,
    load_world_data,
    metric_column,
    tiv_share_is_fraction,
)
from dashboard.pages.overview_world.kpi import render_kpis
from dashboard.pages.overview_world.map_panel import render_map_panel
from dashboard.pages.overview_world.selection import remember_selected_country
from dashboard.pages.overview_world.top10 import render_top10
from dashboard.styles import inject_page1_css
from dashboard.utils.html import p1_html
from dashboard.utils.world_format import make_value_format


def render_page1(dataset):
    """데이터 준비 → KPI → 지표 선택 → 지도 카드 / Top10 카드 순서로 그림"""
    df = load_world_data()

    inject_page1_css()

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

    remember_selected_country(year_df, dataset.country_to_iso3)

    render_kpis(year_df, previous_df, selected_year)

    # ============================================================
    # 24. 지도 + 범례 + TOP10 전체 큰 틀
    # ============================================================

    with st.container(
        border=True,
        key="plain_p1_outer",
    ):

        selected_metric = render_metric_selector()

        selected_column, metric_title = metric_column(selected_metric)

        selected_value_format = make_value_format(
            selected_metric,
            tiv_share_is_fraction(df),
        )

        map_df, max_value, color_max, USE_LOG_COLOR_SCALE = build_map_data(
            year_df,
            selected_metric,
            selected_column,
            selected_value_format,
        )

        # ========================================================
        # 36. 지도 / TOP10 본문
        # ========================================================

        map_area, top10_area = st.columns(
            [
                2.06,
                1,
            ],
            gap="small",
        )


        # ========================================================
        # 왼쪽 - 세계지도
        # ========================================================

        with map_area:

            render_map_panel(
                map_df,
                year_df,
                selected_metric,
                selected_column,
                metric_title,
                selected_year,
                max_value,
                color_max,
                USE_LOG_COLOR_SCALE,
                selected_value_format,
                dataset.country_to_iso3,
            )

        # ========================================================
        # 오른쪽 - TOP10
        # ========================================================

        with top10_area:

            render_top10(
                map_df,
                selected_column,
                metric_title,
                selected_year,
                selected_value_format,
            )


def render_metric_selector():
    # ========================================================
    # 24-1. 분석 지표 선택
    # 전 세계 분포 영역의 왼쪽 상단
    # ========================================================

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
