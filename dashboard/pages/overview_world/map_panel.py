"""전세계 탭 왼쪽 카드 : 제목 + 현재 선택 국가, 세계지도, 범례."""
import streamlit as st
import streamlit.components.v1 as components

from dashboard.charts.world_map import make_world_map, map_colorscale
from dashboard.pages.overview_world.legend import render_legend
from dashboard.pages.overview_world.selection import handle_map_click
from dashboard.utils.formatting import josa
from dashboard.utils.html import p1_html
from dashboard.utils.world_format import country_flag_html


def render_map_panel(
    map_df,
    year_df,
    selected_metric,
    selected_column,
    metric_title,
    selected_year,
    max_value,
    color_max,
    USE_LOG_COLOR_SCALE,
    selected_value_format,
    country_to_iso3,
):
    with st.container(
        border=True,
        key="card_p1_map",
    ):

        current_country_ko = (
            st.session_state
            .get(
                "selected_country_name_ko",
                "국가 미선택",
            )
        )


        current_country_iso = (
            st.session_state
            .get(
                "selected_country_iso",
                "",
            )
        )


        current_flag = (
            country_flag_html(
                current_country_iso
            )
            if current_country_iso
            else """
                    <span class="flag-placeholder">
                        🌐
                    </span>
                    """
        )


        # 세계지도 제목 오른쪽에 현재 선택
        p1_html(
        f"""
                <div class="map-heading">

                    <div class="chart-title">
                        전 세계 {metric_title} 분포 ({selected_year})
                    </div>

                    <div class="current-country-pill">

                        <span>
                            현재 선택 :
                        </span>

                        <span>
                            {current_flag}
                        </span>

                        <span>
                            {current_country_ko}
                            {
                                f"({current_country_iso})"
                                if current_country_iso
                                else ""
                            }
                        </span>

                    </div>

                </div>
                """
        )


        p1_html(
        f"""
                <div class="chart-description">
                    색이 진할수록 {josa(metric_title, "이", "가")} 큽니다.
                    국가를 클릭하면 선택됩니다.
                </div>
                """
        )


        map_plot_col, legend_col = st.columns(
            [
                9.5,
                1.8,
            ],
            gap="small",
        )


        # ------------------------------------------------
        # 지도
        # ------------------------------------------------

        with map_plot_col:

            fig_map = make_world_map(
                map_df,
                metric_title,
                color_max,
                map_colorscale(selected_metric),
                selected_iso=st.session_state.get("selected_country_iso"),
                reset_version=st.session_state.world_map_reset_version,
            )

            # 사용자가 직접 누르는 지도 초기화 버튼은 표시하지 않습니다.
            # 아래의 숨겨진 버튼은 조작 종료 2초 후에만 JS가 클릭합니다.

            map_event = st.plotly_chart(

                fig_map,

                use_container_width=True,

                config={
                    # 기본 Geo 휠 줌은 포인터 위치를 중심으로 확대합니다.
                    # 화면의 +/- 버튼은 기존 요청대로 표시하지 않습니다.
                    "displayModeBar": False,
                    "scrollZoom": True,
                    "doubleClick": False,
                },

                key=(
                    f"world_map_"
                    f"{selected_year}_"
                    f"{selected_column}_"
                    f"{st.session_state.world_map_reset_version}"
                ),

                on_select="rerun",

                selection_mode="points",
            )


            # 확대된 지도를 직접 드래그할 수 있도록 Plotly의 pan을 사용합니다.
            # Plotly의 Geo D3 줌은 휠 이벤트가 발생한 커서 위치를 기준으로
            # 확대/축소합니다. 아래 스크립트는 초기(1x) 지도만 고정하고,
            # 국가 경계 위에서도 휠이 바다 배경과 똑같이 작동하게 합니다.
            # 기존 국가 클릭/선택은 가로채지 않습니다.
            components.html(
                """
                        <script>
                        (() => {
                          let w, d;
                          try { w = window.parent; d = w.document; }
                          catch (_) { return; }
                          try { w.__dashboardGeoInteractions?.(); } catch (_) {}
                          const removed = [];
                          const listen = (target, type, fn, opts) => {
                            target.addEventListener(type, fn, opts);
                            removed.push(() => target.removeEventListener(type, fn, opts));
                          };
                          const isWorld = gd => !!(
                            gd && gd._fullLayout?.geo &&
                            (gd.data || []).some(t => t.type === 'choropleth') &&
                            gd.closest('[class*="st-key-card_p1_map"]')
                          );
                          let initialViewDrag = false;
                          // 처음 화면에서는 지도 전체가 화면 밖으로 이동하지 않게 합니다.
                          // 사용자가 휠로 확대하면 pan을 제한하지 않습니다.
                          listen(d, 'mousedown', e => {
                            if (e.button !== 0) return;
                            const gd = e.target.closest?.('.js-plotly-plot');
                            const scale = Number(gd?._fullLayout?.geo?.projection?.scale ?? 1);
                            initialViewDrag = !!(isWorld(gd) && scale <= 1.015);
                            // 국가 도형에서 드래그를 시작해도 바다 배경의 D3 pan에
                            // 동일한 시작점을 전달합니다. 원래 클릭은 차단하지 않습니다.
                            if (!initialViewDrag && isWorld(gd)) {
                              const bg = gd._fullLayout.geo._subplot?.bgRect?.node?.();
                              if (bg && e.target !== bg &&
                                  gd.querySelector('.geo')?.contains(e.target)) {
                                bg.dispatchEvent(new w.MouseEvent('mousedown', {
                                  view: w,
                                  bubbles: true,
                                  cancelable: true,
                                  button: e.button,
                                  buttons: e.buttons,
                                  clientX: e.clientX,
                                  clientY: e.clientY,
                                  screenX: e.screenX,
                                  screenY: e.screenY,
                                  ctrlKey: e.ctrlKey,
                                  shiftKey: e.shiftKey,
                                  altKey: e.altKey,
                                  metaKey: e.metaKey,
                                }));
                              }
                            }
                          }, true);
                          listen(w, 'mousemove', e => {
                            if (initialViewDrag && (e.buttons & 1)) {
                              e.stopImmediatePropagation();
                            }
                          }, true);
                          listen(w, 'mouseup', () => { initialViewDrag = false; }, true);
                          listen(w, 'blur', () => { initialViewDrag = false; }, true);

                          // 경계선 또는 국가 도형에 커서가 있어도 Plotly의 기본
                          // D3 휠 줌 핸들러가 커서의 실제 위치로 확대하도록 전달합니다.
                          // 배경 위에서 발생한 기존 Wheel 이벤트는 그대로 둡니다.
                          listen(d, 'wheel', e => {
                            const gd = e.target.closest?.('.js-plotly-plot');
                            if (!isWorld(gd) || !e.deltaY) return;
                            const bg = gd._fullLayout.geo._subplot?.bgRect?.node?.();
                            if (!bg || e.target === bg) return;
                            if (e.cancelable) e.preventDefault();
                            e.stopImmediatePropagation();
                            bg.dispatchEvent(new w.WheelEvent('wheel', {
                              view: w,
                              bubbles: true,
                              cancelable: true,
                              clientX: e.clientX,
                              clientY: e.clientY,
                              screenX: e.screenX,
                              screenY: e.screenY,
                              deltaX: e.deltaX,
                              deltaY: e.deltaY,
                              deltaMode: e.deltaMode,
                              ctrlKey: e.ctrlKey,
                              shiftKey: e.shiftKey,
                              altKey: e.altKey,
                              metaKey: e.metaKey,
                            }));
                          }, {capture: true, passive: false});
                          w.__dashboardGeoInteractions = () => {
                            initialViewDrag = false;
                            removed.forEach(dispose => { try { dispose(); } catch (_) {} });
                          };
                        })();
                        </script>
                        """,
                height=0,
            )

            handle_map_click(map_event, year_df, country_to_iso3)


        # ------------------------------------------------
        # 그라데이션 + 경계선 숫자 범례
        # ------------------------------------------------

        with legend_col:

            render_legend(
                map_df,
                selected_column,
                metric_title,
                selected_year,
                max_value,
                color_max,
                USE_LOG_COLOR_SCALE,
                selected_value_format,
            )
