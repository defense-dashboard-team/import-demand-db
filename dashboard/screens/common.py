"""전 페이지 공통: CSS, 상단 배너, 페이지 스트립"""
import base64
import html

import streamlit as st

from dashboard.common.config import ASSETS_DIR, PAGE_TITLES
from dashboard.common.countries import country_display, flag_html
from dashboard.context import ctx
from dashboard.visuals.render import read_asset, render_html, style_block


# 상단 제트기 배너 이미지 (전 페이지 공통)
JET_IMAGE_BASE64 = base64.b64encode(
    (ASSETS_DIR / "jet_banner.jpg").read_bytes()
).decode("ascii")

# 전 페이지 공통 CSS. 뒤에 오는 파일이 앞의 스타일을 덮어쓰므로 순서를 바꾸면 안 됨
GLOBAL_CSS_FILES = [
    "common_base.css",       # 기본 레이아웃, 카드, KPI, 표
    "overview_frame.css",    # 1페이지 전세계/국가별 공통 패널과 책갈피 탭
    "common_theme.css",      # 디자인 정리 레이어 (글꼴, 카드 그림자, 제목 통일)
    "top_filters.css",       # 상단 연도/국가/검색 선택박스
]


def inject_global_css():
    for name in GLOBAL_CSS_FILES:
        st.html(style_block(read_asset(name)))


def data_year_text():
    """배너에 표시할 데이터 기준연도 (DB 데이터에서 자동 계산)"""
    text = f"데이터 {ctx.min_year}–{ctx.max_year}"

    risk_years = ctx.df.loc[ctx.df[ctx.COL["risk"]].notna(), ctx.COL["year"]]

    if not risk_years.empty:
        text += (
            f" · 분쟁위험도 {int(risk_years.min())}"
            f"–{int(risk_years.max())}"
        )

    return text


def render_banner(page_key):
    """기존 전투기 이미지 위 왼쪽 상단에 현재 페이지의 흰 제목을 표시합니다."""
    selected_name = st.session_state.get("selected_country")
    page_title = PAGE_TITLES.get(page_key, PAGE_TITLES["page1"]).format(
        country=country_display(selected_name) if selected_name else ""
    ).strip()
    render_html(
        f"""
        <div class="main-header">
            <img
                class="header-jet"
                src="data:image/jpeg;base64,{JET_IMAGE_BASE64}"
            >
            <div class="header-image-overlay"></div>
            <div class="header-copy header-page-title">
                <div class="main-title">{html.escape(page_title)}</div>
            </div>
        </div>
        """
    )


def render_page_strip(page_key, show_country=False):
    """
    좌측 상단 'N 페이지' 탭 대신
    현재 화면이 무엇인지 내용으로 알려 주는 스트립입니다.
    show_country=True이면 오른쪽에 현재 선택 국가를 칩으로 붙입니다.
    """
    title = PAGE_TITLES[page_key].format(
        country=country_display(ctx.country) if ctx.has_country else ""
    ).strip()

    chip = (
        f"""
        <div class="page-country-chip">
            {flag_html(ctx.iso3, "page-chip-flag")}
            <span class="page-chip-name">
                {html.escape(country_display(ctx.country))}
            </span>
            <span class="page-chip-iso">{html.escape(str(ctx.iso3))}</span>
        </div>
        """
        if show_country and ctx.has_country
        else ""
    )

    # 페이지 제목은 전투기 배너로 이동했습니다. 상관분석의 국가 칩만 유지합니다.
    if chip:
        render_html(f'<div class="page-strip page-strip-chip-only">{chip}</div>')
