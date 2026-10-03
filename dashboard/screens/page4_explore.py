"""조건별 무기 수출 대상국 탐색 화면"""
import html

import numpy as np
import pandas as pd
import streamlit as st

from dashboard.common.countries import country_display, get_flag_url
from dashboard.common.formatting import p4_value_text
from dashboard.common.metrics import P4_DEFAULT_PRIORITY, P4_INDICATORS
from dashboard.context import ctx
from dashboard.db.analysis import p4_candidate_pool, p4_filter_candidates
from dashboard.screens.common import render_page_strip
from dashboard.visuals.trend_chart import p4_trend_chart


def render_page4():
    """사용자 우선순위와 구간으로 최대 5개국을 추출·비교하는 세 번째 화면."""
    render_page_strip("page4")
    st.markdown("""<style>
    .st-key-p4_country_list [data-testid="stVerticalBlockBorderWrapper"] {
        border-color: #E1E9F3 !important; border-radius: 10px !important;
    }
    .st-key-p4_country_list .stButton > button {
        text-align: left; justify-content: flex-start; min-height: 40px;
        white-space: normal; font-weight: 700;
    }
    .p4-caption {font-size:12px;color:#60748C;line-height:1.5;}
    .p4-country-value {font-size:12px;color:#52667D;line-height:1.35;}
    .p4-selection-note {background:#F0F6FC;border-left:3px solid #236CB7;
        padding:8px 12px;border-radius:4px;font-size:12px;color:#2D5075;}
    /* 3페이지: 빨간 슬라이더 현재값이 지표명/이웃 열과 겹치지 않도록 공간 확보 */
    .st-key-p4_filter_frame [data-testid="stVerticalBlock"] {gap: .40rem;}
    .st-key-p4_filter_frame [data-testid="stHorizontalBlock"] {column-gap: 1.3rem !important;}
    .st-key-p4_filter_frame [data-testid="stSlider"] {
        box-sizing: border-box;
        padding: 27px 17px 3px !important;
        margin-top: 10px !important;
        min-width: 0;
    }
    .st-key-p4_filter_frame [data-testid="stSlider"] [data-baseweb="slider"] {
        box-sizing: border-box;
        min-width: 0;
    }
    .st-key-p4_filter_frame .p4-filter-heading {
        font-size: 12px; font-weight: 700; color: #34516F;
        margin: 0 0 13px; padding-top: 5px;
        white-space: normal; line-height: 1.5;
        overflow-wrap: anywhere;
    }
    /* 빨간 값 표시가 긴 GDP/군사비에도 옆 열로 튀어나가지 않도록 축소 */
    .st-key-p4_filter_frame [data-testid="stSlider"] [data-testid="stSliderThumbValue"],
    .st-key-p4_filter_frame [data-testid="stSlider"] [data-testid="stThumbValue"] {
        font-size: 11px !important;
        white-space: nowrap;
    }
    </style>""", unsafe_allow_html=True)

    year_data = p4_candidate_pool(ctx.df, ctx.selected_year)
    available = [label for label, spec in P4_INDICATORS.items()
                 if year_data[spec["column"]].notna().any()]
    if not available:
        st.warning(f"{ctx.selected_year}년에 사용할 수 있는 지표가 없습니다.")
        return
    if "분쟁위험도" not in available:
        st.info(f"{ctx.selected_year}년에는 분쟁위험도 데이터가 없어 선택 목록에서 제외했습니다.")

    with st.container(border=True, key="p4_filter_frame"):
        st.markdown("#### 1. 지표 우선순위와 허용 범위")
        st.caption("왼쪽부터 우선순위 순서입니다. 선택한 모든 범위를 만족하는 국가를 추출합니다.")
        available_defaults = [x for x in P4_DEFAULT_PRIORITY if x in available]
        priority_slots = st.columns(4, gap="small")
        priorities = []
        with priority_slots[0]:
            first = st.selectbox(
                "1순위 · 필수", options=available,
                index=available.index(available_defaults[0]),
                key=f"p4_priority_1_{ctx.selected_year}",
            )
            priorities.append(first)
        for position in range(2, 5):
            remaining = [x for x in available if x not in priorities]
            if not remaining:
                break
            opts = ["선택 안 함"] + remaining
            prefer = available_defaults[position-1] if position-1 < len(available_defaults) else None
            default_idx = opts.index(prefer) if prefer in opts else 0
            # 선행 선택이 달라지면 종속 위젯의 옵션도 새로 생성
            key = f"p4_priority_{position}_{ctx.selected_year}_{'_'.join(priorities)}"
            with priority_slots[position-1]:
                picked = st.selectbox(f"{position}순위 · 선택", opts,
                                      index=default_idx, key=key)
            if picked != "선택 안 함":
                priorities.append(picked)

        # 각 지표의 허용 범위와 정렬을 한 줄에 모아 설정 패널 높이를 줄입니다.
        filter_cols = st.columns(4, gap="small")
        ranges, directions = {}, {}
        for idx, label in enumerate(priorities):
            spec = P4_INDICATORS[label]
            vals = pd.to_numeric(year_data[spec["column"]], errors="coerce")
            valid = vals.dropna() / spec["scale"]
            if valid.empty:
                continue
            min_v, max_v = float(valid.min()), float(valid.max())
            # 실제 단위 그대로 범위 슬라이더 사용. 극단값이 포함돼도
            # 정밀도를 잃지 않도록 데이터 범위에 맞춰 표시 자릿수를 정함.
            precision = int(spec["precision"])
            factor = 10 ** precision
            slider_min = float(np.floor(min_v * factor) / factor)
            slider_max = float(np.ceil(max_v * factor) / factor)
            if slider_max <= slider_min:
                slider_max = slider_min + 1.0 / factor
            step = max((slider_max - slider_min) / 400.0, 1.0 / factor)
            # Streamlit의 숫자 슬라이더 기본값은 전체 구간 -> 첫 화면에서 과도한 필터 방지
            with filter_cols[idx]:
                st.markdown(
                    f'<div class="p4-filter-heading">'
                    f'{idx+1}순위 · {html.escape(label)} ({html.escape(spec["unit"])})'
                    f'</div>', unsafe_allow_html=True,
                )
                low_high = st.slider(
                    f"{label} 범위 ({spec['unit']})",
                    min_value=slider_min, max_value=slider_max,
                    value=(slider_min, slider_max),
                    step=float(step), format=f"%.{precision}f",
                    key=f"p4_range_{label}_{ctx.selected_year}",
                    label_visibility="collapsed",
                )
                # 범위 선택값을 슬라이더 아래에도 한 줄로 표시해 숫자를 쉽게 확인합니다.
                st.caption(
                    f"선택: {low_high[0]:,.{precision}f} ~ "
                    f"{low_high[1]:,.{precision}f} {spec['unit']}"
                )
                direction = st.selectbox(
                    f"{label} 정렬 방향",
                    ["높은 값 우선", "낮은 값 우선"],
                    key=f"p4_direction_compact_{label}",
                    label_visibility="collapsed",
                )
                ranges[label] = tuple(map(float, low_high))
                directions[label] = direction
        if len(priorities) < 4:
            st.caption("필요한 지표만 선택할 수 있습니다. 분쟁위험도는 자료가 있는 연도에만 선택할 수 있습니다.")

    shortlist, total = p4_filter_candidates(year_data, priorities, ranges, directions, top_n=5)
    st.markdown("#### 2. 조건에 맞는 국가와 지표별 추이")
    if total == 0:
        st.warning("선택한 구간을 모두 충족하는 국가가 없습니다. 구간을 넓히거나 우선순위 지표를 줄여 주세요.")

        return

    isos = shortlist["Iso3"].astype(str).tolist()
    # 페이지 방문 직후에는 첫 번째 추출 국가가 강조됩니다. 상단 국가 선택기
    # 또는 아래 카드로 국가를 변경하면 추출 결과에 있을 때 같이 강조합니다.
    old_global = st.session_state.get("p4_last_global_country")
    if old_global != st.session_state.selected_country:
        st.session_state.p4_last_global_country = st.session_state.selected_country
        external_iso = ctx.country_to_iso3.get(st.session_state.selected_country)
        if external_iso in isos:
            st.session_state.p4_highlight_iso = external_iso
    if st.session_state.get("p4_highlight_iso") not in isos:
        st.session_state.p4_highlight_iso = isos[0]
    active_iso = st.session_state.p4_highlight_iso
    st.caption(
        f"{ctx.selected_year}년 · 조건에 일치하는 {total}개 국가 중 "
        f"{len(shortlist)}개 표시 · 정렬: " + " → ".join(priorities)
    )

    list_col, graph_col = st.columns([1.03, 3.25], gap="medium")
    with list_col:
        with st.container(key="p4_country_list"):
            st.markdown("**추출 국가 (최대 5개)**")
            st.caption("국가를 누르면 오른쪽 4개 그래프의 해당 국가가 강조됩니다.")
            for rank, (_, row) in enumerate(shortlist.iterrows(), 1):
                iso = str(row["Iso3"])
                name = str(row["Country"])
                shown = country_display(name)
                selected = active_iso == iso
                with st.container(border=True, key=f"p4_country_{iso}"):
                    flag_col, name_col = st.columns([0.18, 0.82], gap="small",
                                                     vertical_alignment="center")
                    with flag_col:
                        url = get_flag_url(iso)
                        if url:
                            st.markdown(
                                f'<img src="{html.escape(url)}" width="37" '
                                f'height="25" style="object-fit:cover;border:1px solid #ddd;border-radius:3px" '
                                f'alt="{html.escape(iso)}">',
                                unsafe_allow_html=True,
                            )
                        else:
                            st.write("🌐")
                    with name_col:
                        if st.button(
                            f"{rank}. {shown}  {'✓' if selected else '↗'}",
                            type="primary" if selected else "secondary",
                            use_container_width=True,
                            key=f"p4_choose_{iso}",
                        ):
                            st.session_state.p4_highlight_iso = iso
                            st.session_state.p4_last_global_country = name
                            if name != st.session_state.selected_country:
                                st.session_state.selected_country = name
                                st.session_state.country_widget_version += 1
                                st.session_state.search_widget_version += 1
                                st.session_state.map_widget_version += 1
                            st.rerun()
                    primary_metric = priorities[0]
                    st.markdown(
                        '<div class="p4-country-value">'
                        f'{html.escape(primary_metric)}: '
                        f'<b>{html.escape(p4_value_text(primary_metric, row[P4_INDICATORS[primary_metric]["column"]]))}</b>'
                        '</div>', unsafe_allow_html=True,
                    )
    with graph_col:
        st.markdown(
            '<div class="p4-selection-note">'
            f'<b>{html.escape(country_display(shortlist.loc[shortlist["Iso3"] == active_iso, "Country"].iloc[0]))}</b>'
            ' 선택 · 진한 파란색 선으로 강조 · 다른 국가들은 연한 선으로 표시'
            '</div>', unsafe_allow_html=True,
        )
        metrics_2x2 = [["GDP", "군사비"], ["분쟁위험도", "무기 수입 점유율"]]
        for metric_pair in metrics_2x2:
            left, right = st.columns(2, gap="small")
            for container, label in zip([left, right], metric_pair):
                with container:
                    with st.container(border=True, key=f"p4_chart_{P4_INDICATORS[label]['column']}"):
                        st.markdown(f"**{label}**")
                        fig = p4_trend_chart(ctx.df, isos, label, active_iso, ctx.selected_year)
                        st.plotly_chart(
                            fig, use_container_width=True,
                            key=f"p4_plot_{P4_INDICATORS[label]['column']}_{'_'.join(isos)}_{active_iso}",
                            config={"displayModeBar": False, "displaylogo": False,
                                    "scrollZoom": False, "responsive": True},
                        )
    st.caption("이 화면은 선택 조건에 따른 탐색을 지원하며, 추출 순서는 사용자가 지정한 정렬 기준입니다. 미래 무기 수요나 실제 수출 가능성을 예측한 순위가 아닙니다.")
