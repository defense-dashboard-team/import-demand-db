"""현재 선택 국가를 보여 주는 칩 (상관분석 화면 오른쪽 위)."""
import html

from dashboard.config import PAGE_TITLES
from dashboard.utils.countries import flag_html
from dashboard.utils.html import render_html


def render_page_strip(page_key, sel, show_country=False):
    """
    좌측 상단 'N 페이지' 탭 대신
    현재 화면이 무엇인지 내용으로 알려 주는 스트립입니다.
    show_country=True이면 오른쪽에 현재 선택 국가를 칩으로 붙입니다.
    """
    has_country, iso3 = sel.has_country, sel.iso3

    title = PAGE_TITLES[page_key].format(
        country=sel.chosen_name if has_country else ""
    ).strip()

    chip = (
        f"""
        <div class="page-country-chip">
            {flag_html(iso3, "page-chip-flag")}
            <span class="page-chip-name">
                {html.escape(sel.chosen_name)}
            </span>
            <span class="page-chip-iso">{html.escape(str(iso3))}</span>
        </div>
        """
        if show_country and has_country
        else ""
    )

    # 페이지 제목은 전투기 배너로 이동했습니다. 상관분석의 국가 칩만 유지합니다.
    if chip:
        render_html(f'<div class="page-strip page-strip-chip-only">{chip}</div>')
