"""페이지 이동 : 사이드바 메뉴와 화면 아래 다음 페이지 버튼."""
import html

import streamlit as st

from dashboard.config import DASH_TITLE, PAGE_NAV_LABELS, PAGE_ORDER
from dashboard.state import go_to_page
from dashboard.utils.html import render_html


def render_sidebar():
    """왼쪽 사이드바 : 대시보드 이름 + 화면 선택 버튼 (모든 페이지에서 항상 표시)"""
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


def render_next_page_button(label, page_key, key):
    """화면 아래 오른쪽의 다음 페이지 버튼"""
    _, next_page_col = st.columns([8, 2])
    with next_page_col:
        if st.button(
            label,
            use_container_width=True,
            key=key,
        ):
            go_to_page(page_key)
