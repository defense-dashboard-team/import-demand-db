"""조건별 대상국 탐색 화면 (page4) : 지표 구간·우선순위로 최대 5개국을 뽑아 비교."""
import html

import numpy as np
import streamlit as st

from dashboard.analysis.candidates import p4_candidate_pool, p4_sort_candidates, p4_value_text
from dashboard.charts.candidate_trend import p4_trend_chart
from dashboard.config import RISK_START
from dashboard.layout.page_strip import render_page_strip
from dashboard.metrics import (
    P4_COUNTRY_COLORS,
    P4_DEFAULT_PRIORITY,
    P4_DIRECTIONS,
    P4_INDICATORS,
    P4_INPUT_UNITS,
    P4_RANGE_MODES,
)
from dashboard.utils.countries import flag_html
from dashboard.utils.html import render_html


def render_page4(dataset, sel):
    """우선순위와 구간으로 최대 5개국을 추출·비교하는 세 번째 화면."""
    df = dataset.df
    country_to_iso3 = dataset.country_to_iso3
    country_display = dataset.country_display
    selected_year = sel.selected_year

    render_page_strip("page4", sel)
    st.markdown("""<style>
    .st-key-card_p4_filter [data-testid="stHorizontalBlock"] {column-gap: 1.3rem !important;}
    .st-key-card_p4_filter [data-testid="stSlider"] {padding: 4px 10px 0 !important;}
    .st-key-card_p4_filter [data-testid="stRadio"] label p {font-size: 13px !important;}
    .p4-filter-range {font-size: 12px; color: #52667D; line-height: 1.5; min-height: 36px;
        padding-left: 6px;}
    .st-key-card_p4_filter [data-testid="stMarkdownContainer"]:has(.p4-filter-range) {
        margin-bottom: 0 !important;
    }
    .p4-result-title {color: #12365e; font-size: 16px; font-weight: 700; margin: 4px 0 2px;}
    .stApp [class*="st-key-card_p4_country_"] {
        position: relative; padding: 11px 15px !important; cursor: pointer;
        transition: box-shadow .15s, border-color .15s;
    }
    /* Streamlit 글자 영역의 기본 음수 여백(-1rem)을 없애 카드 위아래 여백을 같게 */
    .stApp [class*="st-key-card_p4_country_"] [data-testid="stMarkdownContainer"] {
        margin-bottom: 0 !important;
    }
    .stApp [class*="st-key-card_p4_country_"]:hover {
        border-color: #9DBDF0 !important; box-shadow: 0 4px 14px rgba(31, 111, 235, .12);
    }
    .stApp [class*="st-key-card_p4_country_"] [data-testid="stElementContainer"]:has(.stButton) {
        position: absolute !important; inset: 0; z-index: 3; margin: 0 !important;
        width: 100% !important; max-width: none !important; height: 100% !important;
    }
    .stApp [class*="st-key-card_p4_country_"] .stButton,
    .stApp [class*="st-key-card_p4_country_"] .stButton > button {
        width: 100% !important; height: 100% !important; opacity: 0; cursor: pointer;
    }
    .p4-card-head {display: flex; align-items: center; gap: 9px;
        padding: 0 2px 7px; margin-bottom: 6px; border-bottom: 1px solid #E6ECF3;}
    .p4-card-rank {color: #6B7C90; font-size: 13px; font-weight: 800;}
    .p4-card-flag {width: 30px; height: auto; border-radius: 3px;
        box-shadow: 0 0 0 1px rgba(0, 0, 0, 0.10);}
    .p4-card-name {color: #0B2545; font-size: 15px; font-weight: 800;
        letter-spacing: -0.3px; line-height: 1.25; min-width: 0; white-space: nowrap;
        overflow: hidden; text-overflow: ellipsis;}
    /* 구간 기준 · 금액 축 라디오를 각 영역 오른쪽 끝에 붙입니다. */
    .st-key-p4_mode_box, [class*="st-key-p4_axis_box"] {align-items: flex-end;}
    .st-key-p4_mode_box [data-testid="stRadio"],
    [class*="st-key-p4_axis_box"] [data-testid="stRadio"],
    [class*="st-key-p4_axis_box"] [data-testid="stCheckbox"] {width: auto !important;}
    .st-key-p4_mode_box [role="radiogroup"],
    [class*="st-key-p4_axis_box"] [role="radiogroup"] {justify-content: flex-end;}
    .p4-card-head .p4-card-iso {margin-left: auto; color: #6B7C90; font-size: 12px;
        font-weight: 700; letter-spacing: 0.3px;}
    .p4-metrics {display: grid; grid-template-columns: 1fr; gap: 2px; padding: 0 2px;}
    .p4-m {display: flex; align-items: baseline; justify-content: space-between;
        gap: 6px; line-height: 1.3; white-space: nowrap;}
    .p4-m span {color: #64748B; font-size: 12px;}
    .p4-m b {color: #12365e; font-size: 13px; font-weight: 800;}
    /* 카드 목록을 오른쪽 그래프 4개(차트 300px × 2줄 + 제목·여백)와 같은 높이로 맞추고
       남는 공간은 카드 사이 간격으로 나눕니다. */
    .st-key-p4_country_list {min-height: 783px; display: flex; flex-direction: column;
        justify-content: space-between; gap: 10px;}
    /* 마우스를 올리면 나타나는 안내 말풍선 */
    .p4-tip {position: relative; display: inline-block; cursor: help;}
    .p4-tip-icon {color: #94A3B8; font-size: 14px; font-weight: 600; margin-left: 2px;}
    .p4-tip:hover::after {
        content: attr(data-tip); position: absolute; left: 0; top: calc(100% + 6px);
        z-index: 20; width: max-content; max-width: 360px; padding: 8px 12px;
        background: #0F172A; color: #fff; font-size: 12px; line-height: 1.5;
        border-radius: 8px; box-shadow: 0 4px 14px rgba(15, 23, 42, .2);
    }
    [class*="st-key-p4_axis_box"] {position: relative;}
    [class*="st-key-p4_axis_box"] [data-testid="stElementContainer"]:has(.p4-log-tip) {
        position: absolute !important; right: 0; top: calc(100% + 4px); width: 280px !important;
        z-index: 20; pointer-events: none; opacity: 0; transition: opacity .12s;
    }
    [class*="st-key-p4_axis_box"]:hover [data-testid="stElementContainer"]:has(.p4-log-tip) {opacity: 1;}
    .p4-log-tip {padding: 8px 12px; background: #0F172A; color: #fff; font-size: 12px;
        line-height: 1.5; border-radius: 8px; box-shadow: 0 4px 14px rgba(15, 23, 42, .2);}
    </style>""", unsafe_allow_html=True)

    year_data = p4_candidate_pool(df, selected_year)
    available = [label for label, spec in P4_INDICATORS.items()
                 if year_data[spec["column"]].notna().any()]
    if not available:
        st.warning(f"{selected_year}년에 사용할 수 있는 지표가 없습니다. 다른 연도를 선택해 주세요.")
        return
    if "분쟁위험도" not in available:
        st.info(f"분쟁위험도는 {RISK_START}년부터 제공되어 {selected_year}년에는 선택 목록에서 제외했습니다.")
    # 결측치는 0으로 치환해 모든 지표가 같은 국가 수로 비교되게 합니다.
    available_columns = [P4_INDICATORS[label]["column"] for label in available]
    year_data = year_data.copy()
    year_data[available_columns] = year_data[available_columns].fillna(0)

    # --------------------------------------------------------
    # 1. 우선순위 · 정렬 방향 · 구간
    # --------------------------------------------------------
    with st.container(border=True, key="card_p4_filter"):
        title_col, mode_col = st.columns([4, 1], vertical_alignment="top")
        with title_col:
            render_html(
                '<div class="p4-tip" data-tip="처음 설정된 지표 순서는 중요도를 뜻하지 않습니다. '
                '탐색 목적에 맞게 우선순위를 직접 바꿔 보세요.">'
                '<div class="panel-title-inline">탐색 조건 <span class="p4-tip-icon">ⓘ</span></div>'
                f'<div class="panel-note">{selected_year}년 {len(year_data)}개국 기준 '
                '(결측치는 0으로 처리) · 우선순위 순서대로 정렬</div>'
                '</div>'
            )
        with mode_col:
            with st.container(key="p4_mode_box"):
                range_mode = st.radio(
                    "구간 기준", P4_RANGE_MODES, horizontal=True,
                    key="p4_range_mode", label_visibility="collapsed",
                )

        defaults = [x for x in P4_DEFAULT_PRIORITY if x in available]
        slots = st.columns(4, gap="small")
        priorities, ranges, directions = [], {}, {}
        # 앞 순위 조건을 통과한 국가만 다음 순위로 넘깁니다.
        # 백분위는 매 순위마다 "남은 국가들 안에서" 다시 계산합니다.
        pool = year_data

        for position in range(1, 5):
            remaining = [x for x in available if x not in priorities]
            if not remaining:
                break
            with slots[position - 1]:
                if position == 1:
                    label = st.selectbox(
                        "1순위 · 필수", options=available,
                        index=available.index(defaults[0]),
                        key=f"p4_priority_1_{selected_year}",
                    )
                else:
                    options = ["선택 안 함"] + remaining
                    prefer = defaults[position - 1] if position - 1 < len(defaults) else None
                    # 앞 순위가 바뀌면 선택지가 달라지므로 위젯을 새로 만듭니다.
                    label = st.selectbox(
                        f"{position}순위 · 선택", options,
                        index=options.index(prefer) if prefer in options else 0,
                        key=f"p4_priority_{position}_{selected_year}_{'_'.join(priorities)}",
                    )
                    if label == "선택 안 함":
                        continue

                priorities.append(label)
                column = P4_INDICATORS[label]["column"]
                values = pool[column].dropna()

                directions[label] = st.radio(
                    f"{label} 정렬", P4_DIRECTIONS, horizontal=True,
                    key=f"p4_direction_{label}",
                    label_visibility="collapsed",
                )

                if values.empty:
                    pool = pool.iloc[:0]
                    st.markdown(
                        '<div class="p4-filter-range">앞 순위 조건을 만족하는 국가가 없습니다.</div>',
                        unsafe_allow_html=True,
                    )
                    continue

                if range_mode == "백분위":
                    low, high = st.slider(
                        f"{label} 백분위 구간",
                        min_value=0, max_value=100, value=(0, 100), step=5,
                        format="%d%%",
                        key=f"p4_range_{label}_{selected_year}",
                        label_visibility="collapsed",
                    )
                    value_low = values.quantile(low / 100)
                    value_high = values.quantile(high / 100)
                    pct = pool[column].rank(pct=True, method="average") * 100
                    keep = pct.notna() & pct.between(low - 1e-9, high + 1e-9)
                else:
                    unit, scale = P4_INPUT_UNITS[P4_INDICATORS[label]["kind"]]
                    all_values = year_data[column].dropna()
                    digits = 3 if P4_INDICATORS[label]["kind"] == "share" else 1
                    factor = 10 ** digits
                    slider_min = float(np.floor(float(all_values.min()) / scale * factor) / factor)
                    slider_max = float(np.ceil(float(all_values.max()) / scale * factor) / factor)
                    if slider_max <= slider_min:
                        slider_max = slider_min + 1 / factor
                    step = max(round((slider_max - slider_min) / 500, digits), 1 / factor)
                    low, high = st.slider(
                        f"{label} 실제 값 구간 ({unit})",
                        min_value=slider_min, max_value=slider_max,
                        value=(slider_min, slider_max), step=float(step),
                        format=f"%.{digits}f",
                        key=f"p4_value_{label}_{selected_year}",
                        label_visibility="collapsed",
                    )
                    value_low, value_high = float(low) * scale, float(high) * scale
                    keep = pool[column].notna() & pool[column].between(
                        value_low - 1e-9, value_high + 1e-9)

                before = len(pool)
                pool = pool.loc[keep]
                st.markdown(
                    '<div class="p4-filter-range">'
                    f'{html.escape(p4_value_text(label, value_low))} ~ '
                    f'{html.escape(p4_value_text(label, value_high))}'
                    f'<br>{before}개국 중 {len(pool)}개국</div>',
                    unsafe_allow_html=True,
                )

    # --------------------------------------------------------
    # 2. 추출 국가 + 지표별 추이
    # --------------------------------------------------------
    shortlist, total = p4_sort_candidates(pool, priorities, directions, top_n=5)
    if total == 0:
        st.warning("선택한 구간을 모두 만족하는 국가가 없습니다. 구간을 넓히거나 지표 수를 줄여 주세요.")
        return

    isos = shortlist["Iso3"].astype(str).tolist()
    # 상단 국가 선택이 추출 결과에 있으면 그 국가를, 아니면 1위 국가를 강조합니다.
    old_global = st.session_state.get("p4_last_global_country")
    if old_global != st.session_state.selected_country:
        st.session_state.p4_last_global_country = st.session_state.selected_country
        external_iso = country_to_iso3.get(st.session_state.selected_country)
        if external_iso in isos:
            st.session_state.p4_highlight_iso = external_iso
    if st.session_state.get("p4_highlight_iso") not in isos:
        st.session_state.p4_highlight_iso = isos[0]
    active_iso = st.session_state.p4_highlight_iso

    render_html(
        f'<div class="p4-result-title">{selected_year}년 · 조건을 만족하는 '
        f'{total}개국 중 상위 {len(shortlist)}개</div>'
    )

    if len(shortlist) < 5:
        st.markdown(
            "<style>.st-key-p4_country_list {min-height: 0 !important; "
            "justify-content: flex-start !important;}</style>",
            unsafe_allow_html=True,
        )

    card_colors = {
        iso: P4_COUNTRY_COLORS[i % len(P4_COUNTRY_COLORS)] for i, iso in enumerate(isos)
    }
    card_css = "".join(
        f".stApp .stVerticalBlock.st-key-card_p4_country_{iso} "
        f"{{border-left: 5px solid {color} !important;}}"
        for iso, color in card_colors.items()
    )
    st.markdown(
        f"""<style>
        {card_css}
        .stApp .stVerticalBlock.st-key-card_p4_country_{active_iso} {{
            border: 2px solid #1F6FEB !important;
            border-left: 5px solid {card_colors[active_iso]} !important;
            background: #F3F8FF !important;
        }}
        </style>""",
        unsafe_allow_html=True,
    )

    list_col, graph_col = st.columns([0.87, 3.33], gap="medium")
    with list_col:
        with st.container(key="p4_country_list"):
            for rank, (_, row) in enumerate(shortlist.iterrows(), 1):
                iso = str(row["Iso3"])
                name = str(row["Country"])
                color = P4_COUNTRY_COLORS[(rank - 1) % len(P4_COUNTRY_COLORS)]
                selected = iso == active_iso
                with st.container(border=True, key=f"card_p4_country_{iso}"):
                    metric_order = priorities + [x for x in available if x not in priorities]
                    metrics_html = "".join(
                        f'<div class="p4-m"><span>{html.escape(label)}</span>'
                        f"<b>{html.escape(p4_value_text(label, row[P4_INDICATORS[label]['column']]))}</b></div>"
                        for label in metric_order
                    )
                    st.markdown(
                        '<div class="p4-card">'
                        '<div class="p4-card-head">'
                        f'<span class="p4-card-rank">{rank}</span>'
                        f'{flag_html(iso, "p4-card-flag")}'
                        f'<span class="p4-card-name">{html.escape(country_display(name))}</span>'
                        f'<span class="p4-card-iso">{html.escape(iso)}</span>'
                        '</div>'
                        f'<div class="p4-metrics">{metrics_html}</div>'
                        '</div>',
                        unsafe_allow_html=True,
                    )
                    # 카드 전체를 덮는 투명 버튼: 카드를 누르면 그래프에서 강조됩니다.
                    if st.button(f"{rank}. {country_display(name)} 강조", key=f"p4_choose_{iso}"):
                        st.session_state.p4_highlight_iso = iso
                        st.session_state.p4_last_global_country = name
                        if name != st.session_state.selected_country:
                            st.session_state.selected_country = name
                            st.session_state.country_widget_version += 1
                            st.session_state.map_widget_version += 1
                        st.rerun()

    with graph_col:
        # 그래프도 국가 카드 지표와 같은 순서(사용자 우선순위 → 나머지)로 배치
        chart_order = priorities + [x for x in P4_INDICATORS if x not in priorities]
        for pair in (chart_order[0:2], chart_order[2:4]):
            left, right = st.columns(2, gap="small")
            for container, label in zip([left, right], pair):
                with container:
                    column = P4_INDICATORS[label]["column"]
                    with st.container(border=True, key=f"card_p4_chart_{column}"):
                        log_axis = False
                        if P4_INDICATORS[label]["kind"] == "money":
                            # 금액 그래프만 카드 안 오른쪽 위에서 실제 값/로그 축을 고릅니다.
                            head_col, axis_col = st.columns([1, 1.3], vertical_alignment="center")
                            with head_col:
                                render_html(f'<div class="panel-title-inline">{html.escape(label)}</div>')
                            with axis_col:
                                with st.container(key=f"p4_axis_box_{column}"):
                                    log_axis = st.toggle("로그", key=f"p4_log_{column}")
                                    st.markdown(
                                        '<div class="p4-log-tip">국가 간 규모 차이가 커서 작은 나라의 선이 '
                                        '바닥에 붙어 보일 때, 로그 축으로 바꾸면 증감 흐름을 함께 비교할 수 있어요.</div>',
                                        unsafe_allow_html=True,
                                    )
                        else:
                            render_html(f'<div class="panel-title-inline">{html.escape(label)}</div>')
                        st.plotly_chart(
                            p4_trend_chart(df, isos, label, active_iso, selected_year,
                                           log_axis=log_axis,
                                           country_display=country_display),
                            use_container_width=True,
                            key=f"p4_plot_{P4_INDICATORS[label]['column']}",
                            config={"displayModeBar": False, "displaylogo": False,
                                    "scrollZoom": False, "responsive": True},
                        )

    st.caption(
        "이 화면은 선택한 조건에 따른 탐색을 돕기 위한 것이며, "
        "미래 무기 수요나 실제 수출 가능성을 예측한 순위가 아닙니다."
    )
