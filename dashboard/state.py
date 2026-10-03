"""화면끼리 공유하는 선택 상태 (연도, 국가, 현재 페이지).

값은 전부 st.session_state에 있고, 여기 함수들은 그걸 초기화하거나 바꾸거나 읽어서 정리함.
지도·버블을 클릭했을 때 다른 차트가 같이 바뀌는 것도 selected_country 하나를 같이 보기 때문.
"""
from dataclasses import dataclass

import streamlit as st


def init_session_state(dataset):
    """session_state 기본값. 이미 값이 있으면 건드리지 않음."""
    default_year = dataset.default_year

    if "selected_country" not in st.session_state:
        st.session_state.selected_country = None

    if "selected_year" not in st.session_state:
        st.session_state.selected_year = default_year

    if "selected_metric" not in st.session_state:
        st.session_state.selected_metric = "군사비"

    if "country_widget_version" not in st.session_state:
        st.session_state.country_widget_version = 0

    if "search_widget_version" not in st.session_state:
        st.session_state.search_widget_version = 0

    if "year_widget_version" not in st.session_state:
        st.session_state.year_widget_version = 0

    if "map_widget_version" not in st.session_state:
        st.session_state.map_widget_version = 0

    # 세계지도 자동 복귀 전용 상태(국가/연도 및 다른 차트에는 영향 없음)
    if "world_map_reset_version" not in st.session_state:
        st.session_state.world_map_reset_version = 0

    if "app_page" not in st.session_state:
        st.session_state.app_page = "page1"

    # 1페이지에서 선택하는 라벨: 선택 상태는 다른 화면으로 이동해도 유지합니다.
    if "overview_mode" not in st.session_state:
        st.session_state.overview_mode = "전세계"

    # 기존 버전에서 2페이지를 열어 둔 사용자는 국가별 화면으로 이어집니다.
    if st.session_state.app_page == "page2":
        st.session_state.app_page = "page1"
        st.session_state.overview_mode = "국가별"

    if "sim_basis" not in st.session_state:
        st.session_state.sim_basis = "risk"

    if "trend_metric" not in st.session_state:
        st.session_state.trend_metric = "milex"


def go_to_page(page_key):
    """페이지를 바꾸고, 새 화면을 맨 위에서 시작하도록 표시합니다."""
    st.session_state.app_page = page_key
    st.session_state.scroll_to_top = True
    st.rerun()


def deselect_country():
    """버블 재클릭 / 사이드바 '선택 안 함' 으로 국가 선택을 해제합니다."""
    st.session_state.selected_country = None

    st.session_state.country_widget_version += 1
    st.session_state.search_widget_version += 1
    st.session_state.map_widget_version += 1

    st.session_state.pop("last_click_risk", None)
    st.session_state.pop("last_click_tiv", None)

    st.rerun()


def sync_clicked_country(country_name, country_to_iso3):
    """
    지도/버블에서 선택한 국가를
    1페이지, 2페이지, 사이드바에 모두 공통 반영합니다.
    """
    if (
        country_name
        and country_name in country_to_iso3
        and country_name != st.session_state.selected_country
    ):
        st.session_state.selected_country = country_name

        st.session_state.country_widget_version += 1
        st.session_state.search_widget_version += 1
        st.session_state.map_widget_version += 1

        st.session_state.pop("last_click_risk", None)
        st.session_state.pop("last_click_tiv", None)

        st.rerun()


def validate_selection(dataset):
    """session_state에 남아 있는 연도·국가가 지금 데이터에 없으면 기본값으로 되돌림"""
    years, default_year = dataset.years, dataset.default_year
    countries, default_country = dataset.countries, dataset.default_country

    # 기간/국가 데이터가 갱신되더라도 위젯에 잘못된 과거 선택지가 남지 않게 합니다.
    if int(st.session_state.selected_year) not in years:
        st.session_state.selected_year = default_year
    if (
        st.session_state.selected_country is not None
        and st.session_state.selected_country not in countries
    ):
        st.session_state.selected_country = default_country


@dataclass
class Selection:
    """상단 필터에서 고른 연도·국가와 거기서 바로 나오는 값"""
    country: object         # 데이터 원본 국가명 (선택 안 했으면 None)
    has_country: bool
    selected_year: int
    current: object         # 선택 국가의 선택 연도 행 (없으면 None)
    previous: object        # 1년 전 행
    five_year_ago: object   # 5년 전 행
    iso3: str
    chosen_name: object     # 화면 표시용 한글 국가명
    sel_iso: object


def current_selection(dataset):
    """
    session_state의 연도·국가로 현재 선택값을 계산함.
    위젯 변경은 rerun 후에 반영되므로 상단 필터를 그린 다음에 불러야 함.
    """
    COL = dataset.COL
    country_to_iso3 = dataset.country_to_iso3
    country_display = dataset.country_display
    get_country_year = dataset.get_country_year

    country = st.session_state.selected_country
    has_country = country is not None

    selected_year = int(st.session_state.selected_year)

    current = (
        get_country_year(country, selected_year)
        if has_country
        else None
    )

    # 선택 국가가 반드시 필요한 화면에서만 데이터 유무를 막습니다.
    if (
        has_country
        and current is None
        and st.session_state.app_page == "page1"
        and st.session_state.overview_mode == "국가별"
    ):
        st.warning(
            f"{country_display(country)}의 "
            f"{selected_year}년 데이터가 없습니다."
        )
        st.stop()

    previous = (
        get_country_year(country, selected_year - 1)
        if has_country
        else None
    )

    five_year_ago = (
        get_country_year(country, selected_year - 5)
        if has_country
        else None
    )

    iso3 = (
        current[COL["iso3"]]
        if current is not None
        else (country_to_iso3.get(country, "") if has_country else "")
    )

    # 전 페이지 공통 선택값
    chosen_name = country_display(country) if has_country else None
    sel_iso = country_to_iso3.get(country) if has_country else None

    return Selection(
        country=country,
        has_country=has_country,
        selected_year=selected_year,
        current=current,
        previous=previous,
        five_year_ago=five_year_ago,
        iso3=iso3,
        chosen_name=chosen_name,
        sel_iso=sel_iso,
    )
