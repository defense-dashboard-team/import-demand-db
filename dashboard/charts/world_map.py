"""1페이지 세계지도 (지표 값으로 색칠한 choropleth)."""
import plotly.graph_objects as go

from dashboard.config import ISO_COL
from dashboard.data.world_geojson import load_world_geojson, world_geojson_subset


def map_colorscale(selected_metric):
    # ========================================================
    # 지도 그라데이션 색상
    #
    # 무기 수입 점유율은 낮은 값도 너무 옅게 보이지 않도록
    # 다른 지표보다 전체적으로 한 단계 진한 파란색을 사용합니다.
    # ========================================================

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


def make_world_map(map_df, metric_title, color_max, MAP_COLORSCALE, selected_iso, reset_version):
    WORLD_GEOJSON_IDS = load_world_geojson()[1]

    # ========================================================
    # 31. 한 장만 표시되는 평면 세계지도
    # Plotly Geo 투영을 사용해 좌우에 세계가 반복 출력되지 않습니다.
    # 국가 선택(3개의 GeoJSON 레이어/클릭 이벤트)은 원본 그대로 유지합니다.
    # 드래그 이동 및 커서 중심 확대는 줌한 화면에서 계속 유지합니다.
    # ========================================================

    fig_map = go.Figure()

    # 레이어별로 필요한 나라만 담은 국경선 (전송량 절감)
    data_isos = tuple(sorted(set(map_df[ISO_COL])))
    empty_isos = tuple(sorted(set(WORLD_GEOJSON_IDS) - set(data_isos)))


    # --------------------------------------------------------
    # 데이터가 없는 국가도 회색으로 보이게 하는 기본 국가 레이어
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # 실제 데이터 히트맵 레이어
    # --------------------------------------------------------

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


    # ========================================================
    # 32. 현재 선택 국가 외곽선 강조
    # ========================================================

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


    # ========================================================
    # ========================================================
    # 33. 한 화면에 세계 전체가 들어오는 단일 지도 뷰
    # - 비율에 맞춰 축소/확대하므로 가변 너비에서도 국가가 겹치지 않음
    # - Miller 평면 투영: 세계 전체를 유지하면서 Mercator보다 좌우로 넓게 표시
    # - 경도 -180~180°, 위도 -85~85°: 첫 화면 세계 전체 유지
    # - 휠 zoom은 커서 위치 기준, 확대된 화면은 마우스로 드래그 가능
    # ========================================================
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
            uirevision=f"world-view-{reset_version}",
        ),
        # 우측 Top10의 .top10-wrapper(455px)와 같은 본문 높이
        height=455,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        dragmode="pan",  # 확대 시 Plotly 기본 드래그 이동과 커서 기준 휠 줌 사용
        clickmode="event+select",
        uirevision=f"world-view-{reset_version}",
    )

    return fig_map
