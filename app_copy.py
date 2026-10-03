"""수출 유망국 대시보드 실행 파일.

  streamlit run app_copy.py

화면/차트/데이터 코드는 dashboard/ 패키지에 있고, 여기서는 순서대로 호출만 한다.
"""
import streamlit as st

import dashboard.visuals.theme  # noqa: F401  (plotly 기본 템플릿 등록)
from dashboard.context import ctx
from dashboard.db.dataset import load_dataset
from dashboard.screens.common import inject_global_css, render_banner, render_page_strip
from dashboard.screens.page1_overview import render_page1
from dashboard.screens.page2_country_trend import render_country_view
from dashboard.screens.page3_correlation import render_correlation_view
from dashboard.screens.page4_explore import render_page4
from dashboard.screens.sidebar import render_sidebar, render_top_filters
from dashboard.screens.state import (
    go_to_page,
    init_session_state,
    update_current_selection,
    validate_selection,
)
from dashboard.visuals.render import scroll_to_top_script


st.set_page_config(
    page_title="글로벌 방산시장 개요",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# import된 모듈은 rerun 때 다시 실행되지 않는다.
# rerun마다 다시 해야 하는 일(CSS 출력, 데이터/선택값 계산, 화면 그리기)은 전부 아래에서 함수로 호출한다.
inject_global_css()

load_dataset()
init_session_state()

render_sidebar()

# 배너 + 공통 상단 필터
render_banner(st.session_state.app_page)
validate_selection()
render_top_filters()

# 위젯 변경은 rerun 후에 반영되므로, 필터를 그린 다음에 현재 선택값을 계산
update_current_selection()


# 최종 화면 선택
# 1페이지: [전세계] 지도 + Top10 / [국가별] 기존 2페이지
# 2번째 메뉴: 기존 3페이지 상관분석
if st.session_state.pop("scroll_to_top", False):
    scroll_to_top_script()

if st.session_state.app_page == "page1":
    # 1페이지의 고정 제목: 탭을 바꿔도 제목과 전체 패널의 너비는 동일합니다.
    render_page_strip("page1")

    # 전세계 지도/Top10과 국가별 KPI/추이 모두 같은 흰색 바깥 패널에 표시합니다.
    with st.container(border=True, key="overview_frame"):
        # 프레임의 좌측 상단에 붙는 책갈피 모양의 전환 탭.
        with st.container(key="overview_bookmarks"):
            view_mode = st.segmented_control(
                "분석 범위",
                options=["전세계", "국가별"],
                default="전세계",
                selection_mode="single",
                key="overview_mode",
                label_visibility="collapsed",
            ) or "전세계"

        if view_mode == "국가별":
            # 국가가 없는 상태에서 처음 국가별 탭을 누른 경우:
            # 같은 선택 국가를 상단 필터에도 반영하고 데이터를 다시 계산합니다.
            if st.session_state.selected_country is None:
                st.session_state.selected_country = ctx.default_country
                st.session_state.country_widget_version += 1
                st.session_state.search_widget_version += 1
                st.rerun()
            render_country_view()
        else:
            render_page1()

    # 페이지 이동은 어느 탭에서든 패널 아래 동일한 위치에 표시합니다.
    _, next_page_col = st.columns([8, 2])
    with next_page_col:
        if st.button(
            "상관분석 →",
            use_container_width=True,
            key="go_page_3",
        ):
            go_to_page("page3")

elif st.session_state.app_page == "page3":
    render_correlation_view()
    _, page4_nav = st.columns([8, 2])
    with page4_nav:
        if st.button("조건별 국가 탐색 →", use_container_width=True, key="go_page_4"):
            go_to_page("page4")

elif st.session_state.app_page == "page4":
    render_page4()
