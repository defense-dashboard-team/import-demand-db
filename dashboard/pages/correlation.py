"""상관분석 화면 (page3) : 버블차트 + 상관계수 히트맵, 아래에 선택 국가 시계열과 유사 국가.

버블을 클릭하면 selected_country가 바뀌고 rerun되어 시계열·유사 국가·국가 칩이 같이 바뀜.
"""
import html

import streamlit as st

from dashboard.analysis.similarity import find_similar_countries
from dashboard.charts.bubble import make_bubble
from dashboard.charts.corr_heatmap import make_corr_heatmap
from dashboard.charts.country_line import make_page2_line
from dashboard.charts.events import extract_selected_point
from dashboard.charts.trend import trend_year_span
from dashboard.config import RISK_START, X_COL
from dashboard.layout.page_strip import render_page_strip
from dashboard.metrics import PAGE2_METRIC, SIM_TOP_N
from dashboard.state import deselect_country, sync_clicked_country
from dashboard.utils.formatting import josa
from dashboard.utils.html import render_html, scroll_to_bottom_script


def render_correlation_view(dataset, sel):
    """2페이지: 버블차트/상관관계 → 토글로 시계열/유사국가 비교."""
    df = dataset.df
    country_to_iso3 = dataset.country_to_iso3
    country_display = dataset.country_display
    country, has_country = sel.country, sel.has_country
    sel_iso, chosen_name = sel.sel_iso, sel.chosen_name
    year = sel.selected_year

    # 2페이지에서만 상단 필터 아래 여백과 국가 칩의 높이를 축소합니다.
    # 지표 선택과 국가 칩을 같은 행에 배치하므로 아래 전체 콘텐츠도 함께 위로 이동합니다.
    st.html("""
    <style>
    .stApp .st-key-top_filters {
        margin-bottom: 2px !important;
    }
    .stApp .page-strip.page-strip-chip-only {
        min-height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        justify-content: flex-end;
    }
    .stApp .page-strip-chip-only .page-country-chip {
        padding: 5px 11px 5px 8px;
    }
    </style>
    """)

    # 기존 1·2번 버블차트는 탭으로 전환; 마지막 선택을 기억합니다.
    if "page3_metric_view" not in st.session_state:
        st.session_state.page3_metric_view = "분쟁위험도"
    if "page3_size_col" not in st.session_state:
        st.session_state.page3_size_col = "gdp_calculated"

    # 분쟁 위험도가 존재하지 않는 연도는 사용 가능한 무기 수입 지표로 전환합니다.
    if year < RISK_START and st.session_state.page3_metric_view == "분쟁위험도":
        st.session_state.page3_metric_view = "무기 수입 점유율"
        st.info(
            f"분쟁위험도는 {RISK_START}년부터 제공됩니다. "
            "선택한 연도에서는 무기 수입 점유율을 보여줍니다."
        )

    # 지표 선택과 국가 칩을 같은 행에 배치하여 빈 세로 공간을 없앱니다.
    selector_col, country_chip_col = st.columns([1.08, 1], gap="small")
    with selector_col:
        metric_label = st.segmented_control(
            "버블차트 선택",
            options=(
                ["무기 수입 점유율"] if year < RISK_START
                else ["분쟁위험도", "무기 수입 점유율"]
            ),
            selection_mode="single",
            key="page3_metric_view",
            label_visibility="collapsed",
        ) or "분쟁위험도"
    with country_chip_col:
        render_page_strip("page3", sel, show_country=True)

    metric = "risk" if metric_label == "분쟁위험도" else "tiv"
    # 버블 지표와 유사도 기준을 항상 같이 바꿉니다.
    st.session_state.sim_basis = metric
    sim_basis = metric
    if st.session_state.get("page3_prev_metric") != metric:
        st.session_state.page3_prev_metric = metric
        st.session_state.pop("last_click_risk", None)
        st.session_state.pop("last_click_tiv", None)
        st.session_state.page3_chart_revision = st.session_state.get("page3_chart_revision", 0) + 1

    if st.session_state.get("page3_last_year") != year:
        st.session_state.page3_last_year = year
        st.session_state.pop("last_click_risk", None)
        st.session_state.pop("last_click_tiv", None)

    # 상단 필터에서 선택한 국가 및 현재 버블 지표를 동일하게 사용합니다.
    sim_table, sim_other = (None, None)
    if sel_iso:
        sim_table, sim_other = find_similar_countries(df, year, metric, sel_iso)
    similar_isos = (
        [] if sim_table is None else
        sim_table.loc[sim_table["순위"] > 0, "Iso3"].tolist()
    )
    size_col = st.session_state.page3_size_col
    size_label = "GDP" if size_col == "gdp_calculated" else "군사비"
    bubble_title = (
        "GDP 대비 군사비 × 분쟁위험도" if metric == "risk"
        else "GDP 대비 군사비 × 무기수입 점유율"
    )
    bubble_n = int(df[
        (df["Year"] == year) & df[X_COL].notna() &
        df[PAGE2_METRIC[metric]["col"]].notna() &
        df[size_col].notna()
    ].shape[0])

    # 동일 헤더(66px)와 동일 Plotly 높이를 적용하여 상단 두 카드 높이를 맞춥니다.
    CHART_H = 388
    bubble_left, corr_right = st.columns([1.08, 1], gap="small")
    with bubble_left:
        with st.container(border=True, key="card_p3_bubble_selected"):
            # 원본 코드에 있던 버블 크기 변경 기능 유지
            render_html('<div class="bubble-size-anchor"></div>')
            size_col = st.radio(
                "버블 크기",
                options=["gdp_calculated", "current_usd"],
                format_func=lambda c: "GDP" if c == "gdp_calculated" else "군사비",
                horizontal=True,
                key="page3_size_col",
                label_visibility="collapsed",
            )
            size_label = "GDP" if size_col == "gdp_calculated" else "군사비"
            render_html(
                '<div class="panel-head has-control">'
                f'<div class="panel-title-inline">{html.escape(bubble_title)}</div>'
                f'<div class="panel-note">{year}년 · {bubble_n}개국 · '
                f'버블 크기는 {size_label}</div></div>'
            )
            fig_bubble = make_bubble(
                df, year, metric, size_col=size_col,
                highlight=sel_iso, similar=similar_isos,
                country_display=country_display,
            )
            fig_bubble.update_layout(height=CHART_H)
            bubble_event = st.plotly_chart(
                fig_bubble, use_container_width=True,
                on_select="rerun", selection_mode="points",
                key=(f"page2_bubble_{metric}_{year}_{size_col}_"
                     f"{st.session_state.map_widget_version}_"
                     f"{st.session_state.page3_chart_revision}"),
                config={
                    "displayModeBar": False, "displaylogo": False,
                    "scrollZoom": False, "doubleClick": False, "responsive": True,
                },
            )
            # 버블 클릭 ↔ 상단 국가 선택 ↔ 1페이지 지도 연동 (기존 동작)
            point = extract_selected_point(bubble_event)
            clicked_iso = None
            if point is not None:
                try:
                    cd = point.get("customdata")
                    clicked_iso = cd[1] if cd else None
                except (TypeError, ValueError, IndexError, KeyError):
                    clicked_iso = None
            if clicked_iso and st.session_state.get(f"last_click_{metric}") != clicked_iso:
                st.session_state[f"last_click_{metric}"] = clicked_iso
                found = df.loc[df["Iso3"] == clicked_iso, "Country"]
                clicked_name = found.iloc[0] if not found.empty else None
                if clicked_name == st.session_state.selected_country:
                    deselect_country()
                else:
                    sync_clicked_country(clicked_name, country_to_iso3)

            if size_col == "current_usd":
                render_html(
                    '<div class="panel-foot panel-warn">'
                    '⚠ 군사비는 가로축(군사비/GDP)과 상관이 있어 정보가 겹칠 수 있습니다.'
                    '</div>'
                )

    with corr_right:
        with st.container(border=True, key="card_p3_corr"):
            corr_extra = (
                f" · {year}년은 분쟁위험도가 없어 해당 지표 제외"
                if year < RISK_START else ""
            )
            render_html(
                '<div class="panel-head">'
                '<div class="panel-title-inline">주요 지표 간 상관관계</div>'
                f'<div class="panel-note">{year}년 · 스피어만 상관계수 · '
                f'* p&lt;0.05 ** p&lt;0.01 *** p&lt;0.001{corr_extra}'
                '</div></div>'
            )
            fig_corr, corr_n = make_corr_heatmap(
                df, year, method="spearman", height=CHART_H,
            )
            st.plotly_chart(
                fig_corr, use_container_width=True,
                key=f"page3_corr_{year}_spearman",
                config={
                    "displayModeBar": False, "displaylogo": False,
                    "scrollZoom": False, "doubleClick": False, "responsive": True,
                },
            )
            if size_col == "current_usd":
                render_html('<div class="panel-foot">&nbsp;</div>')

    # 토글이 꺼져 있을 때는 상단 버블·상관관계만 보여줍니다.
    st.markdown(
        """<style>
        .st-key-card_p3_sim .similarity-table thead th {
            font-size: 10px !important; padding: 4px 3px !important;
            white-space: normal !important; line-height: 1.2;
        }
        .st-key-card_p3_sim .similarity-table tbody td {
            font-size: 11px !important; padding: 3px !important; height: 40px;
        }
        .st-key-card_p3_sim .sim-progress-bg { min-width: 22px; height: 10px; }
        .st-key-card_p3_sim .sim-score { min-width: 33px; font-size: 11px; }
        .st-key-card_p3_sim .panel-caption { font-size: 11px; }
        </style>""",
        unsafe_allow_html=True,
    )
    show_details = st.toggle(
        "시계열 추이 · 유사 국가 비교 펼치기",
        value=False,
        key="page3_details_open",
        on_change=lambda: st.session_state.update(p3_scroll_bottom=True),
    )
    if show_details:
        SIM_BODY_H = 368
        detail_left, detail_right = st.columns([1.08, 1], gap="small")
        with detail_left:
            with st.container(border=True, key="card_p3_line_selected"):
                line_other = "분쟁위험도" if metric == "risk" else "무기수입 점유율"
                line_span = trend_year_span(df, sel_iso, metric) if has_country else ""
                line_head = (
                    f"{html.escape(country_display(country))} · " if has_country else ""
                )
                render_html(
                    '<div class="panel-head">'
                    f'<div class="panel-title-inline">{line_head}군사비와 '
                    f'{html.escape(line_other)} 동반 추이</div>'
                    f'<div class="panel-note">좌축 군사비 · 우축 {html.escape(line_other)}'
                    + (f' · {html.escape(line_span)}' if line_span else "")
                    + '</div></div>'
                )
                fig_line = make_page2_line(
                    df, sel_iso, metric,
                    year_min=dataset.year_min, year_max=dataset.year_max,
                )
                fig_line.update_layout(height=SIM_BODY_H)
                st.plotly_chart(
                    fig_line, use_container_width=True,
                    key=f"page2_line_{metric}_{sel_iso}_{year}",
                    config={
                        "displayModeBar": False, "displaylogo": False,
                        "scrollZoom": False, "doubleClick": False, "responsive": True,
                    },
                )

        with detail_right:

            with st.container(border=True, key="card_p3_sim"):

                basis_label = (
                    PAGE2_METRIC[
                        sim_basis
                    ]["label"]
                )

                render_html(
                    f"""
                    <div class="panel-head">
                        <div class="panel-title-inline">
                            유사 국가 비교
                        </div>

                        <div class="panel-note">
                            {
                                html.escape(josa(country_display(country), "과", "와"))
                                if has_country
                                else "선택 국가와"
                            }
                            지표가 비슷한 상위 {SIM_TOP_N}개국 ·
                            군사비/GDP · {html.escape(basis_label)} · GDP 기준
                        </div>
                    </div>
                    """
                )

                # 표/안내문을 히트맵과 같은 높이의 상자 하나에 담습니다.
                sim_body = ""

                if not has_country:

                    sim_body = (
                        '<div class="panel-empty">'
                        "국가가 선택되지 않았습니다.<br>"
                        "위 버블차트에서 버블을 클릭하거나<br>"
                        "상단 국가 선택박스에서 국가를 선택하세요."
                        "</div>"
                    )

                elif (
                    sim_table is None
                    or sim_table.empty
                ):

                    sim_body = (
                        '<div class="panel-empty">'
                        f"{year}년 {html.escape(basis_label)} 기준으로<br>"
                        f"{html.escape(str(chosen_name))}의 유사 국가를 "
                        "계산할 수 없습니다."
                        "</div>"
                    )

                else:

                    # ------------------------------------------------
                    # 처음 디자인처럼 compact한 고정 표로 표시
                    # - 드래그/스크롤 없음
                    # - 빈 값이 있는 지표 열은 아예 표시하지 않음
                    # ------------------------------------------------

                    show = sim_table.copy()

                    # 핵심 열에 빈 값이 있는 행은 제외
                    required_cols = [
                        "순위",
                        "Country",
                        "유사도",
                        X_COL,
                    ]

                    show = (
                        show
                        .dropna(subset=required_cols)
                        .head(SIM_TOP_N + 1)
                        .copy()
                    )

                    display_metrics = []

                    # 첨부된 처음 디자인처럼
                    # TIV / 분쟁위험도 / 군사비-GDP 순으로 구성하되
                    # 해당 연도에 빈 값이 존재하는 열은 숨김
                    for label, col, fmt in [
                        (
                            "무기수입 점유율",
                            "TIV_5Y_Share",
                            ".2f",
                        ),
                        (
                            "분쟁 위험도",
                            "human_hazard_score",
                            ".1f",
                        ),
                        (
                            "군사비/GDP",
                            X_COL,
                            ".2f",
                        ),
                    ]:

                        if (
                            col in show.columns
                            and not show.empty
                            and show[col].notna().all()
                        ):
                            display_metrics.append(
                                (
                                    label,
                                    col,
                                    fmt,
                                )
                            )

                    headers = [
                        "순위",
                        "국가",
                        "유사도(%)",
                    ] + [
                        item[0]
                        for item in display_metrics
                    ]

                    # 열 폭(%) : 순위는 좁게, 국가명·유사도는 넓게,
                    # 나머지 지표 열은 남은 폭을 똑같이 나눕니다.
                    rank_w, country_w, score_w = 6, 26, 24

                    if display_metrics:
                        metric_w = (
                            100 - rank_w - country_w - score_w
                        ) / len(display_metrics)
                    else:
                        metric_w = 0
                        country_w, score_w = 50, 44

                    colgroup_html = (
                        "<colgroup>"
                        f'<col style="width:{rank_w}%">'
                        f'<col style="width:{country_w}%">'
                        f'<col style="width:{score_w}%">'
                        + "".join(
                            f'<col style="width:{metric_w:.2f}%">'
                            for _ in display_metrics
                        )
                        + "</colgroup>"
                    )

                    header_html = "".join(
                        f"<th>{html.escape(str(header))}</th>"
                        for header in headers
                    )

                    rows_html = ""

                    for _, row in show.iterrows():

                        is_base = int(row["순위"]) == 0

                        similarity = float(
                            row["유사도"]
                        )

                        similarity_width = max(
                            0.0,
                            min(
                                similarity,
                                100.0,
                            ),
                        )

                        country_name = html.escape(
                            country_display(row["Country"])
                        )

                        score_cell = (
                            '<td class="sim-score-cell">'
                            '<div class="sim-base-tag">기준</div>'
                            '</td>'
                            if is_base
                            else (
                                '<td class="sim-score-cell">'
                                '<div class="sim-score-line">'
                                '<div class="sim-progress-bg">'
                                f'<div class="sim-progress-bar" style="width:{similarity_width:.1f}%"></div>'
                                '</div>'
                                f'<div class="sim-score">{similarity:.1f}</div>'
                                '</div>'
                                '</td>'
                            )
                        )

                        cells = [
                            (
                                '<td class="sim-rank">'
                                + ("–" if is_base else f'{int(row["순위"])}')
                                + '</td>'
                            ),
                            (
                                '<td class="sim-country">'
                                f'{country_name}'
                                '</td>'
                            ),
                            score_cell,
                        ]

                        for _, col, fmt in display_metrics:
                            cells.append(
                                '<td>'
                                + format(
                                    float(row[col]),
                                    fmt,
                                )
                                + '</td>'
                            )

                        rows_html += (
                            '<tr class="sim-base-row">'
                            if is_base
                            else '<tr>'
                        )
                        rows_html += ''.join(cells) + '</tr>'

                    if show.empty:

                        sim_body = (
                            '<div class="panel-empty">'
                            "빈 값을 제외하면 표시할 수 있는<br>"
                            "유사 국가 데이터가 없습니다."
                            "</div>"
                        )

                    else:

                        sim_body = (
                            '<div class="similarity-wrap">'
                            '<table class="similarity-table">'
                            + colgroup_html
                            + '<thead><tr>'
                            + header_html
                            + '</tr></thead>'
                            '<tbody>'
                            + rows_html
                            + '</tbody>'
                            '</table>'
                            '</div>'
                        )

                    sim_body += (
                        '<div class="panel-caption">'
                        "맨 윗줄이 기준 국가 · "
                        "버블차트 주황 테두리는 유사 국가, "
                        "빨간 테두리는 선택 국가 (다시 클릭하면 해제)"
                        "</div>"
                    )

                render_html(
                    f'<div class="panel-body" style="height:{SIM_BODY_H}px">'
                    f"{sim_body}"
                    "</div>"
                )

        # 토글을 막 켰을 때만 펼친 그래프가 보이도록 화면 맨 아래로 이동합니다.
        if st.session_state.pop("p3_scroll_bottom", False):
            scroll_to_bottom_script()
