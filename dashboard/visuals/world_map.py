"""1페이지 세계지도: 색상 단계, 지도 figure, 범례 표시, 휠 줌 보조 스크립트"""
import html

import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from dashboard.db.overview import ISO_COL
from dashboard.visuals.world_borders import world_geojson_subset


def map_colorscale(selected_metric):
    # 지도 그라데이션 색상
    # 무기 수입 점유율은 낮은 값도 너무 옅게 보이지 않도록
    # 다른 지표보다 전체적으로 한 단계 진한 파란색을 사용합니다.

    if selected_metric == "무기 수입 점유율":

        MAP_COLORSCALE = [
            [0.00, "#a7d7f0"],
            [0.18, "#72bce4"],
            [0.36, "#429bd3"],
            [0.55, "#237cbd"],
            [0.75, "#125b98"],
            [1.00, "#06386f"],
        ]

    else:

        MAP_COLORSCALE = [
            [0.00, "#d9f0fb"],
            [0.20, "#9bd4ef"],
            [0.40, "#5bb3e0"],
            [0.60, "#278dcc"],
            [0.80, "#1266a9"],
            [1.00, "#073970"],
        ]

    return MAP_COLORSCALE


def make_world_map(map_df, color_max, MAP_COLORSCALE, metric_title, WORLD_GEOJSON_IDS):
    # 한 장만 표시되는 평면 세계지도
    # Plotly Geo 투영을 사용해 좌우에 세계가 반복 출력되지 않습니다.
    # 국가 선택(3개의 GeoJSON 레이어/클릭 이벤트)은 원본 그대로 유지합니다.
    # 드래그 이동 및 커서 중심 확대는 줌한 화면에서 계속 유지합니다.

    fig_map = go.Figure()

    # 레이어별로 필요한 나라만 담은 국경선 (전송량 절감)
    data_isos = tuple(sorted(set(map_df[ISO_COL])))
    empty_isos = tuple(sorted(set(WORLD_GEOJSON_IDS) - set(data_isos)))

    # 데이터가 없는 국가도 회색으로 보이게 하는 기본 국가 레이어

    fig_map.add_trace(

        go.Choropleth(

            geojson=
                world_geojson_subset(empty_isos),

            featureidkey=
                "id",

            locations=
                list(empty_isos),

            z=
                [0] * len(
                    empty_isos
                ),

            zmin=
                0,

            zmax=
                1,

            colorscale=[
                [0, "#e5e9ed"],
                [1, "#e5e9ed"],
            ],

            showscale=
                False,

            marker=dict(
                line=dict(
                    color="white",
                    width=0.55,
                )
            ),

            hoverinfo=
                "skip",
        )
    )

    # 실제 데이터 히트맵 레이어

    fig_map.add_trace(

        go.Choropleth(

            geojson=
                world_geojson_subset(data_isos),

            featureidkey=
                "id",

            locations=
                map_df[
                    ISO_COL
                ],

            z=
                map_df[
                    "color_value"
                ],

            zmin=
                0,

            zmax=
                color_max,

            colorscale=
                MAP_COLORSCALE,

            showscale=
                False,

            marker=dict(
                line=dict(
                    color="white",
                    width=0.55,
                )
            ),

            customdata=(
                map_df[
                    [
                        "Country_KO",
                        "display_value",
                        "rank_percentile",
                        ISO_COL,
                    ]
                ]
                .values
                .tolist()
            ),

            hovertemplate=(

                "<b>%{customdata[0]}</b>"

                "<br>"

                + metric_title

                + ": %{customdata[1]}"

                "<br>전체 국가 중 상위 "

                "%{customdata[2]:.1f}%"

                "<br>"

                "국가코드: %{customdata[3]}"

                "<extra></extra>"
            ),
        )
    )

    # 현재 선택 국가 외곽선 강조

    selected_iso = (
        st.session_state
        .get(
            "selected_country_iso"
        )
    )

    if (
        selected_iso
        and
        selected_iso in set(
            map_df[
                ISO_COL
            ]
        )
    ):

        fig_map.add_trace(

            go.Choropleth(

                geojson=
                    world_geojson_subset((selected_iso,)),

                featureidkey=
                    "id",

                locations=[
                    selected_iso
                ],

                z=[
                    1
                ],

                zmin=
                    0,

                zmax=
                    1,

                colorscale=[
                    [
                        0,
                        "rgba(255,157,0,0.16)"
                    ],
                    [
                        1,
                        "rgba(255,157,0,0.16)"
                    ],
                ],

                showscale=
                    False,

                marker=dict(
                    line=dict(
                        color="#ff9d00",
                        width=2.5,
                    )
                ),

                hoverinfo=
                    "skip",
            )
        )

    # 한 화면에 세계 전체가 들어오는 단일 지도 뷰
    # - 비율에 맞춰 축소/확대하므로 가변 너비에서도 국가가 겹치지 않음
    # - Miller 평면 투영: 세계 전체를 유지하면서 Mercator보다 좌우로 넓게 표시
    # - 경도 -180~180°, 위도 -85~85°: 첫 화면 세계 전체 유지
    # - 휠 zoom은 커서 위치 기준, 확대된 화면은 마우스로 드래그 가능
    fig_map.update_layout(
        geo=dict(
            scope="world",
            projection=dict(type="miller"),
            center=dict(lat=0, lon=0),
            lonaxis=dict(range=[-180, 180]),
            lataxis=dict(range=[-85, 85]),
            bgcolor="rgba(0,0,0,0)",
            showframe=False,
            showcoastlines=False,
            showcountries=False,
            showland=True,
            landcolor="#e5e9ed",
            showocean=True,
            oceancolor="#f5faff",
            uirevision=f"world-view-{st.session_state.world_map_reset_version}",
        ),
        # 우측 Top10의 .top10-wrapper(455px)와 같은 본문 높이
        height=455,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode="pan",  # 확대 시 Plotly 기본 드래그 이동과 커서 기준 휠 줌 사용
        clickmode="event+select",
        uirevision=f"world-view-{st.session_state.world_map_reset_version}",
    )

    return fig_map


def legend_marker(map_df, color_max, selected_column, selected_value_format):
    # 범례 막대에 선택 국가 위치 표시
    # 지도 색과 같은 기준(color_value / color_max)으로 위치를 정하므로
    # 범례에서 가리키는 색 = 지도에서 그 나라의 색이 됩니다.

    legend_marker_html = ""

    marker_rows = map_df[
        map_df[ISO_COL]
        == st.session_state.get("selected_country_iso")
    ]

    if not marker_rows.empty:

        marker_row = marker_rows.iloc[0]

        marker_pos = min(
            max(
                float(marker_row["color_value"]) / color_max,
                0.0,
            ),
            1.0,
        )

        # 막대 위쪽이 최댓값, 아래쪽이 0
        marker_top = (1 - marker_pos) * 100

        legend_marker_html = f"""
            <div class="legend-marker" style="top:{marker_top:.2f}%;"></div>
            <div class="legend-marker-label" style="top:{marker_top:.2f}%;">
                <div class="legend-marker-name">
                    {html.escape(str(marker_row["Country_KO"]))}
                </div>
                <div class="legend-marker-value">
                    {selected_value_format(marker_row[selected_column])}
                </div>
            </div>
            """

    return legend_marker_html


def render_wheel_zoom_script():
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
