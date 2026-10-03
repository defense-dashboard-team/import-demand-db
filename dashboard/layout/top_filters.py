"""배너 아래 연도·국가 선택 상자. 고른 값은 session_state에 넣어 모든 화면이 같이 씀."""
import streamlit as st

from dashboard.config import COUNTRY_NONE, COUNTRY_NONE_LABEL
from dashboard.utils.countries import country_english


def render_top_filters(dataset, show_country=True):
    """연도·국가 선택 상자. 값이 바뀌면 session_state에 넣고 바로 rerun함.
    show_country=False 이면 연도만 표시 (국가를 고를 필요가 없는 화면)."""
    years, countries = dataset.years, dataset.countries
    country_to_iso3 = dataset.country_to_iso3
    country_display = dataset.country_display

    with st.container(key="top_filters"):
        year_col, country_col, _ = st.columns([0.8, 2.2, 2.4], gap="medium")

        with year_col:
            st.markdown("**연도**")
            top_year = st.selectbox(
                "연도 선택",
                years,
                index=years.index(int(st.session_state.selected_year)),
                key=f"year_select_{st.session_state.year_widget_version}",
                label_visibility="collapsed",
            )
            if int(top_year) != int(st.session_state.selected_year):
                st.session_state.selected_year = int(top_year)
                st.session_state.map_widget_version += 1
                st.session_state.pop("last_click_risk", None)
                st.session_state.pop("last_click_tiv", None)
                st.rerun()

        if not show_country:
            return

        with country_col:
            st.markdown("**국가**")

            # 선택 상자에 한글·영문·ISO3를 함께 표시해 입력만으로 검색되게 합니다.
            # (별도의 검색 상자를 두지 않습니다.)
            def country_option_label(country_name):
                if country_name == COUNTRY_NONE:
                    return COUNTRY_NONE_LABEL
                return (
                    f"{country_display(country_name)} · "
                    f"{country_english(country_name)} "
                    f"({country_to_iso3.get(country_name, '')})"
                )

            country_options = [COUNTRY_NONE] + countries
            top_country = st.selectbox(
                "국가 선택",
                country_options,
                index=(
                    country_options.index(st.session_state.selected_country)
                    if st.session_state.selected_country is not None
                    else None
                ),
                placeholder="국가 선택 또는 입력",
                format_func=country_option_label,
                key=f"country_select_{st.session_state.country_widget_version}",
                label_visibility="collapsed",
            )
            picked_country = None if top_country in (None, COUNTRY_NONE) else top_country
            if picked_country != st.session_state.selected_country:
                st.session_state.selected_country = picked_country
                st.session_state.map_widget_version += 1
                st.session_state.pop("last_click_risk", None)
                st.session_state.pop("last_click_tiv", None)
                st.rerun()
