"""세션 상태: 초기값, 선택 검증, 현재 선택값 계산, 국가 선택 연동"""
import streamlit as st

from dashboard.common.countries import country_display
from dashboard.context import ctx
from dashboard.db.dataset import get_country_year


def init_session_state():
    if "selected_country" not in st.session_state:
        st.session_state.selected_country = ctx.default_country

    if "selected_year" not in st.session_state:
        st.session_state.selected_year = ctx.default_year

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


def extract_selected_point(event):
    try:
        points = event.selection.points
    except Exception:
        try:
            points = event["selection"]["points"]
        except Exception:
            return None

    if not points:
        return None

    return points[-1]


def deselect_country():
    """버블 재클릭 / 사이드바 '선택 안 함' 으로 국가 선택을 해제합니다."""
    st.session_state.selected_country = None

    st.session_state.country_widget_version += 1
    st.session_state.search_widget_version += 1
    st.session_state.map_widget_version += 1

    st.session_state.pop("last_click_risk", None)
    st.session_state.pop("last_click_tiv", None)

    st.rerun()


def sync_clicked_country(country_name):
    """
    지도/버블에서 선택한 국가를
    1페이지, 2페이지, 사이드바에 모두 공통 반영합니다.
    """
    if (
        country_name
        and country_name in ctx.country_to_iso3
        and country_name != st.session_state.selected_country
    ):
        st.session_state.selected_country = country_name

        st.session_state.country_widget_version += 1
        st.session_state.search_widget_version += 1
        st.session_state.map_widget_version += 1

        st.session_state.pop("last_click_risk", None)
        st.session_state.pop("last_click_tiv", None)

        st.rerun()


def validate_selection():
    # 기간/국가 데이터가 갱신되더라도 위젯에 잘못된 과거 선택지가 남지 않게 합니다.
    if int(st.session_state.selected_year) not in ctx.years:
        st.session_state.selected_year = ctx.default_year
    if (
        st.session_state.selected_country is not None
        and st.session_state.selected_country not in ctx.countries
    ):
        st.session_state.selected_country = ctx.default_country

    # 국가별 탭에서 국가를 비운 상태면 원래의 기본 선택 국가로 전환합니다.
    if (
        st.session_state.app_page == "page1"
        and st.session_state.overview_mode == "국가별"
        and st.session_state.selected_country is None
    ):
        st.session_state.selected_country = ctx.default_country
        st.session_state.country_widget_version += 1
        st.session_state.search_widget_version += 1
        st.rerun()


def update_current_selection():
    """상단 필터가 그려진 뒤 호출. 현재 선택(국가/연도)에 따른 값을 ctx에 채운다."""
    ctx.country = st.session_state.selected_country
    ctx.has_country = ctx.country is not None

    ctx.selected_year = int(st.session_state.selected_year)
    ctx.selected_metric = st.session_state.selected_metric

    ctx.metric_settings = ctx.METRIC_CONFIG[ctx.selected_metric]
    ctx.selected_metric_col = ctx.metric_settings["column"]

    ctx.current = (
        get_country_year(ctx.country, ctx.selected_year)
        if ctx.has_country
        else None
    )

    # 선택 국가가 반드시 필요한 화면에서만 데이터 유무를 막습니다.
    if (
        ctx.has_country
        and ctx.current is None
        and st.session_state.app_page == "page1"
        and st.session_state.overview_mode == "국가별"
    ):
        st.warning(
            f"{country_display(ctx.country)}의 "
            f"{ctx.selected_year}년 데이터가 없습니다."
        )
        st.stop()

    ctx.previous = (
        get_country_year(ctx.country, ctx.selected_year - 1)
        if ctx.has_country
        else None
    )

    ctx.five_year_ago = (
        get_country_year(ctx.country, ctx.selected_year - 5)
        if ctx.has_country
        else None
    )

    ctx.iso3 = (
        ctx.current[ctx.COL["iso3"]]
        if ctx.current is not None
        else (ctx.country_to_iso3.get(ctx.country, "") if ctx.has_country else "")
    )

    ctx.min_year = int(ctx.df[ctx.COL["year"]].min())
    ctx.max_year = int(ctx.df[ctx.COL["year"]].max())

    # 전 페이지 공통 선택값
    ctx.year = ctx.selected_year
    ctx.chosen_name = country_display(ctx.country) if ctx.has_country else None
    ctx.sel_iso = ctx.country_to_iso3.get(ctx.country) if ctx.has_country else None
