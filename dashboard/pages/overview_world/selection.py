"""전세계 탭의 선택 국가 : 상단 필터에서 고른 국가를 지도에 맞추고, 지도 클릭을 선택에 반영."""
import streamlit as st

from dashboard.config import COUNTRY_COL, ISO_COL
from dashboard.state import sync_clicked_country
from dashboard.utils.world_format import country_name_korean


def remember_selected_country(year_df, country_to_iso3):
    # ============================================================
    # 20. 선택 국가 기본값
    # ============================================================

    available_isos = set(
        year_df[ISO_COL]
        .dropna()
        .astype(str)
    )


    # 2·3페이지와 공유하는 선택 국가(영문 국가명)를 ISO 코드로 바꿉니다.
    current_iso = country_to_iso3.get(
        st.session_state.selected_country
    )

    if current_iso:
        current_iso = str(current_iso).upper()


    # 선택 국가가 없거나 이 연도에 데이터가 없으면 선택 없이 표시합니다.
    if current_iso not in available_isos:
        current_iso = None


    st.session_state[
        "selected_country_iso"
    ] = current_iso


    if current_iso:

        row = year_df[
            year_df[ISO_COL]
            == current_iso
        ]


        if not row.empty:

            current_name = (
                row.iloc[0][COUNTRY_COL]
            )


            st.session_state[
                "selected_country_name"
            ] = current_name


            st.session_state[
                "selected_country_name_ko"
            ] = country_name_korean(
                current_iso,
                current_name,
            )


def get_selected_points(event):

    try:
        return event.selection.points

    except Exception:

        try:
            return event["selection"]["points"]

        except Exception:
            return []


def handle_map_click(map_event, year_df, country_to_iso3):
    selected_points = get_selected_points(
        map_event
    )


    if selected_points:

        point = selected_points[-1]

        clicked_iso = None


        # Choropleth location
        try:
            clicked_iso = point.get(
                "location"
            )
        except Exception:
            pass


        # customdata fallback
        if not clicked_iso:

            try:

                customdata = (
                    point.get(
                        "customdata"
                    )
                )


                if (
                    customdata
                    and len(customdata) >= 4
                ):

                    clicked_iso = (
                        customdata[3]
                    )

            except Exception:
                pass


        if clicked_iso:

            clicked_iso = (
                str(clicked_iso)
                .upper()
            )


            previous_iso = (
                st.session_state
                .get(
                    "selected_country_iso"
                )
            )


            if (
                clicked_iso
                != previous_iso
            ):

                selected_row = (
                    year_df[
                        year_df[ISO_COL]
                        == clicked_iso
                    ]
                )


                if not selected_row.empty:

                    clicked_name = (
                        selected_row
                        .iloc[0][
                            COUNTRY_COL
                        ]
                    )


                    clicked_name_ko = (
                        country_name_korean(
                            clicked_iso,
                            clicked_name,
                        )
                    )


                    st.session_state[
                        "selected_country_iso"
                    ] = clicked_iso


                    st.session_state[
                        "selected_country_name"
                    ] = clicked_name


                    st.session_state[
                        "selected_country_name_ko"
                    ] = clicked_name_ko


                    # 2·3페이지와 사이드바에도 같은 국가를 반영하고
                    # 제목 오른쪽의 현재 선택 국가를 즉시 갱신
                    sync_clicked_country(clicked_name, country_to_iso3)
                    st.rerun()
