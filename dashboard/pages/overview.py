"""1페이지 틀 : 전세계 / 국가별 탭을 고르고 해당 화면을 그림."""
import streamlit as st

from dashboard.layout.page_strip import render_page_strip
from dashboard.pages.overview_country import render_country_view
from dashboard.pages.overview_world import render_page1


def render_overview(dataset, sel):
    """page1 : 바깥 흰 패널 안에 전세계(render_page1) 또는 국가별(render_country_view) 화면을 넣음"""
    # 1페이지의 고정 제목: 탭을 바꿔도 제목과 전체 패널의 너비는 동일합니다.
    render_page_strip("page1", sel)

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
                st.info("위에서 국가를 선택하거나 입력하면 국가별 지표가 표시됩니다.")
            else:
                render_country_view(dataset, sel)
        else:
            render_page1(dataset)
