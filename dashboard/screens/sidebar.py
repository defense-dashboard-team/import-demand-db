"""사이드바(화면 선택)와 상단 필터(연도/국가/검색)"""
import html

import streamlit as st

from dashboard.common.config import (
    COUNTRY_NONE,
    COUNTRY_NONE_LABEL,
    DASH_TITLE,
    PAGE_NAV_LABELS,
    PAGE_ORDER,
)
from dashboard.common.countries import country_display, country_english
from dashboard.context import ctx
from dashboard.screens.state import go_to_page
from dashboard.visuals.render import render_html


def render_sidebar():
    with st.sidebar:
        render_html(
            f"""
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">{html.escape(DASH_TITLE)}</div>
        </div>
        """
        )
        st.markdown("### 화면 선택")
        for page_key in PAGE_ORDER:
            if st.button(
                PAGE_NAV_LABELS[page_key],
                use_container_width=True,
                type="primary" if st.session_state.app_page == page_key else "secondary",
                key=f"nav_{page_key}",
            ):
                if st.session_state.app_page != page_key:
                    go_to_page(page_key)


def render_top_filters():
    """연도/국가/검색은 모든 화면에서 같은 session_state를 씀"""
    with st.container(key="top_filters"):
        year_col, country_col, search_col = st.columns([0.90, 1.65, 2.10], gap="medium")

        with year_col:
            st.markdown("**연도 선택**")
            top_year = st.selectbox(
                "연도 선택",
                ctx.years,
                index=ctx.years.index(int(st.session_state.selected_year)),
                key=f"year_select_{st.session_state.year_widget_version}",
                label_visibility="collapsed",
            )
            if int(top_year) != int(st.session_state.selected_year):
                st.session_state.selected_year = int(top_year)
                st.session_state.map_widget_version += 1
                st.session_state.pop("last_click_risk", None)
                st.session_state.pop("last_click_tiv", None)
                st.rerun()

        with country_col:
            st.markdown("**국가 선택**")
            country_options = [COUNTRY_NONE] + ctx.countries
            top_country = st.selectbox(
                "국가 선택",
                country_options,
                index=country_options.index(
                    st.session_state.selected_country
                    if st.session_state.selected_country is not None
                    else COUNTRY_NONE
                ),
                format_func=lambda c: (
                    COUNTRY_NONE_LABEL if c == COUNTRY_NONE
                    else f"{country_display(c)} ({ctx.country_to_iso3.get(c, '')})"
                ),
                key=f"country_select_{st.session_state.country_widget_version}",
                label_visibility="collapsed",
            )
            picked_country = None if top_country == COUNTRY_NONE else top_country
            if picked_country != st.session_state.selected_country:
                st.session_state.selected_country = picked_country
                st.session_state.search_widget_version += 1
                st.session_state.map_widget_version += 1
                st.session_state.pop("last_click_risk", None)
                st.session_state.pop("last_click_tiv", None)
                st.rerun()

        with search_col:
            st.markdown("**국가 검색**")

            def search_label(country_name):
                return (
                    f"{country_display(country_name)} · "
                    f"{country_english(country_name)} "
                    f"({ctx.country_to_iso3.get(country_name, '')})"
                )

            search_to_country = {search_label(c): c for c in ctx.countries}
            searched_country = st.selectbox(
                "국가 검색",
                list(search_to_country),
                index=None,
                placeholder="🔍 한글·영문 국가명 또는 ISO3 검색...",
                key=f"country_search_{st.session_state.search_widget_version}",
                label_visibility="collapsed",
            )
            if searched_country is not None:
                found_country = search_to_country[searched_country]
                if found_country != st.session_state.selected_country:
                    st.session_state.selected_country = found_country
                    st.session_state.country_widget_version += 1
                    st.session_state.search_widget_version += 1
                    st.session_state.map_widget_version += 1
                    st.session_state.pop("last_click_risk", None)
                    st.session_state.pop("last_click_tiv", None)
                    st.rerun()
