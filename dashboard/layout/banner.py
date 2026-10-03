"""맨 위 전투기 배너 (현재 페이지 제목 표시)."""
import base64
from functools import lru_cache
import html

import streamlit as st

from dashboard.config import ASSETS_DIR, PAGE_TITLES
from dashboard.utils.html import render_html


@lru_cache(maxsize=None)
def jet_image_base64():
    """배너 이미지를 HTML에 바로 넣을 수 있게 base64로 읽음"""
    image = (ASSETS_DIR / "jet_banner.jpg").read_bytes()
    return base64.b64encode(image).decode("ascii")


def data_year_text(dataset):
    """배너에 표시할 데이터 기준연도 (DB 데이터에서 자동 계산)"""
    df, COL = dataset.df, dataset.COL
    min_year = int(df[COL["year"]].min())
    max_year = int(df[COL["year"]].max())

    text = f"데이터 {min_year}–{max_year}"

    risk_years = df.loc[df[COL["risk"]].notna(), COL["year"]]

    if not risk_years.empty:
        text += (
            f" · 분쟁위험도 {int(risk_years.min())}"
            f"–{int(risk_years.max())}"
        )

    return text


def render_banner(page_key, dataset):
    """기존 전투기 이미지 위 왼쪽 상단에 현재 페이지의 흰 제목을 표시합니다."""
    selected_name = st.session_state.get("selected_country")
    page_title = PAGE_TITLES.get(page_key, PAGE_TITLES["page1"]).format(
        country=dataset.country_display(selected_name) if selected_name else ""
    ).strip()
    render_html(
        f"""
        <div class="main-header">
            <img
                class="header-jet"
                src="data:image/jpeg;base64,{jet_image_base64()}"
            >
            <div class="header-image-overlay"></div>
            <div class="header-copy header-page-title">
                <div class="main-title">{html.escape(page_title)}</div>
            </div>
        </div>
        """
    )
