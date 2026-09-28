import os
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# =========================================================
# 1. 페이지 설정
# =========================================================

st.set_page_config(
    page_title="방산시장 분석 대시보드",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =========================================================
# 2. 경로 / 데이터 설정
# =========================================================

BASE_DIR = Path(__file__).parent

CSV_CANDIDATES = [
    BASE_DIR / "integrate_new.csv",
    BASE_DIR / "Integrate_new.csv",
    BASE_DIR.parent / "data" / "integrate_new.csv",
    BASE_DIR.parent / "data" / "Integrate_new.csv",
]

USE_DB = os.getenv("USE_DB", "false").lower() == "true"
DB_URL = os.getenv("DB_URL", "")
SSL_CA = os.getenv("SSL_CA", "")

YEAR_MIN = 2004
YEAR_MAX = 2025
RISK_START = 2017

X_COL = "share_gdp_pct"
SIZE_COL = "gdp_calculated"
MILEX_COL = "current_usd"

MILEX_COLOR = "#2E6F9E"
BUBBLE_MIN = 6
BUBBLE_MAX = 46

BASE_LAYOUT = dict(
    template="plotly_white",
    font=dict(
        family="Malgun Gothic, AppleGothic, NanumGothic, sans-serif",
        size=12,
    ),
    margin=dict(l=60, r=70, t=55, b=55),
    hovermode="closest",
)


# =========================================================
# 3. 데이터 로드
# =========================================================

def find_csv_path():
    for path in CSV_CANDIDATES:
        if path.exists():
            return path
    return CSV_CANDIDATES[0]


@st.cache_data(ttl=3600)
def load_data():
    df = None

    # DB 사용 설정이 켜져 있고 DB_URL이 있을 때만 접속 시도
    if USE_DB and DB_URL:
        try:
            from sqlalchemy import create_engine

            connect_args = {"connect_timeout": 5}
            if SSL_CA:
                connect_args["ssl"] = {"ca": SSL_CA}

            engine = create_engine(
                DB_URL,
                connect_args=connect_args,
            )
            df = pd.read_sql("SELECT * FROM integrate", con=engine)

        except Exception:
            df = None

    # DB 실패 또는 미사용 시 CSV
    if df is None:
        csv_path = find_csv_path()
        df = pd.read_csv(csv_path)

    df.columns = [
        c.strip("\ufeff").strip()
        for c in df.columns
    ]

    numeric_cols = [
        "Year",
        "current_usd",
        "gdp_calculated",
        "share_gdp",
        "TIV_5Y_Sum",
        "TIV_5Y_Share",
        "human_hazard_score",
    ]

    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col],
                errors="coerce",
            )

    required = [
        "Year",
        "Country",
        "Iso3",
        "current_usd",
        "gdp_calculated",
        "share_gdp",
        "TIV_5Y_Share",
        "human_hazard_score",
    ]

    missing = [
        col
        for col in required
        if col not in df.columns
    ]

    if missing:
        raise ValueError(
            "필수 컬럼이 없습니다: "
            + ", ".join(missing)
        )

    df = df.dropna(
        subset=[
            "Year",
            "Country",
            "Iso3",
        ]
    ).copy()

    df["Year"] = df["Year"].astype(int)

    df = df[
        (df["Year"] >= YEAR_MIN)
        &
        (df["Year"] <= YEAR_MAX)
    ].copy()

    indicator_cols = [
        "current_usd",
        "gdp_calculated",
        "share_gdp",
        "TIV_5Y_Share",
        "human_hazard_score",
    ]

    df = df[
        ~df[indicator_cols]
        .isna()
        .all(axis=1)
    ].copy()

    # 기존 두 번째 페이지 코드와 동일한 파생변수
    df["share_gdp_pct"] = df["share_gdp"] * 100

    return df


try:
    df = load_data()

except Exception as e:
    st.error(
        "데이터를 불러오지 못했습니다: "
        f"{type(e).__name__} — {e}"
    )
    st.stop()


# =========================================================
# 4. 공통 국가 코드 매핑
# =========================================================

names = (
    df[["Iso3", "Country"]]
    .drop_duplicates()
    .sort_values("Country")
)

ISO_TO_NAME = dict(
    zip(
        names["Iso3"],
        names["Country"],
    )
)

NAME_TO_ISO = dict(
    zip(
        names["Country"],
        names["Iso3"],
    )
)

NONE_LABEL = "(선택 안 함)"


# =========================================================
# 5. 공통 상태 초기화
# =========================================================

if "sel_year" not in st.session_state:
    st.session_state.sel_year = (
        2025
        if 2025 in df["Year"].unique()
        else int(df["Year"].max())
    )

if "sel_country" not in st.session_state:
    st.session_state.sel_country = NONE_LABEL

if "selected_metric" not in st.session_state:
    st.session_state.selected_metric = "TIV 수입 점유율"

if "map_version" not in st.session_state:
    st.session_state.map_version = 0

if "app_page" not in st.session_state:
    st.session_state.app_page = "1페이지 · 국가별 현황"


# =========================================================
# 6. 지도/버블 클릭으로 전달된 국가를
#    사이드바 위젯 생성 전에 먼저 반영
# =========================================================

if "pending_country" in st.session_state:
    pending_country = st.session_state.pending_country

    if pending_country in NAME_TO_ISO:
        st.session_state.sel_country = pending_country

    del st.session_state.pending_country


# =========================================================
# 7. 공통 사이드바
# =========================================================

with st.sidebar:
    st.header("조회 조건")

    available_years = sorted(
        df["Year"].dropna().unique().tolist(),
        reverse=True,
    )

    st.selectbox(
        "연도 선택",
        options=available_years,
        key="sel_year",
    )

    year_country_options = sorted(
        df.loc[
            df["Year"] == st.session_state.sel_year,
            "Country",
        ]
        .dropna()
        .unique()
        .tolist()
    )

    country_options = (
        [NONE_LABEL]
        + year_country_options
    )

    # 연도를 바꾼 뒤 선택 국가가 그 해에 없으면 초기화
    if (
        st.session_state.sel_country
        != NONE_LABEL
        and
        st.session_state.sel_country
        not in country_options
    ):
        st.session_state.sel_country = NONE_LABEL

    st.selectbox(
        "국가 선택",
        options=country_options,
        key="sel_country",
    )

    st.divider()

    st.caption(
        "지도·버블차트에서 국가를 선택해도 "
        "이 국가 선택값에 자동 반영됩니다."
    )


year = int(st.session_state.sel_year)
chosen_name = st.session_state.sel_country
sel_iso = (
    None
    if chosen_name == NONE_LABEL
    else NAME_TO_ISO.get(chosen_name)
)


# =========================================================
# 8. 페이지 전환
# =========================================================

page = st.radio(
    "페이지",
    options=[
        "1페이지 · 국가별 현황",
        "2페이지 · 복합지표",
    ],
    horizontal=True,
    key="app_page",
)


# =========================================================
# 9. 공통 헬퍼
# =========================================================

def empty_figure(message, height=460):
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(
            size=14,
            color="#7A8794",
        ),
    )

    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        height=height,
        **BASE_LAYOUT,
    )

    return fig


def extract_selected_point(event):
    try:
        points = event.selection.points
    except Exception:
        try:
            points = event["selection"]["points"]
        except Exception:
            return None

    if not points:
        return None

    return points[-1]


def get_clicked_country_from_map(event, map_df):
    point = extract_selected_point(event)

    if point is None:
        return None

    try:
        customdata = point.get("customdata")
        if customdata is not None and len(customdata) > 0:
            return str(customdata[0])
    except Exception:
        pass

    try:
        location = point.get("location")
        if location is not None:
            match = map_df.loc[
                map_df["Iso3"] == location,
                "Country",
            ]
            if not match.empty:
                return match.iloc[0]
    except Exception:
        pass

    return None


def sync_clicked_country(country_name):
    if (
        country_name
        and
        country_name in NAME_TO_ISO
        and
        country_name != st.session_state.sel_country
    ):
        st.session_state.pending_country = country_name
        st.session_state.map_version += 1
        st.rerun()


# =========================================================
# 10. 1페이지 설정
# =========================================================

PAGE1_METRICS = {
    "분쟁 위험도": {
        "column": "human_hazard_score",
        "unit": "점",
    },
    "TIV 수입 점유율": {
        "column": "TIV_5Y_Share",
        "unit": "%",
    },
    "군사비": {
        "column": "current_usd",
        "unit": "백만 US$",
    },
    "GDP": {
        "column": "gdp_calculated",
        "unit": "백만 US$",
    },
}


def change_metric(metric):
    st.session_state.selected_metric = metric
    st.session_state.map_version += 1


def make_page1_map(
    selected_metric,
    selected_country=None,
    height=430,
):
    metric_column = PAGE1_METRICS[
        selected_metric
    ]["column"]

    map_df = df[
        (df["Year"] == year)
        &
        (df[metric_column].notna())
    ].copy()

    map_df = (
        map_df.groupby(
            ["Country", "Iso3"],
            as_index=False,
        )[metric_column]
        .mean()
        .reset_index(drop=True)
    )

    if selected_metric in [
        "GDP",
        "군사비",
    ]:
        map_df["MapValue"] = np.log10(
            map_df[metric_column]
            .clip(lower=1)
        )
        color_column = "MapValue"
    else:
        color_column = metric_column

    fig = px.choropleth(
        map_df,
        locations="Iso3",
        locationmode="ISO-3",
        color=color_column,
        hover_name="Country",
        custom_data=[
            "Country",
            "Iso3",
            metric_column,
        ],
        color_continuous_scale="YlOrRd",
        projection="natural earth",
    )

    if selected_metric == "TIV 수입 점유율":
        fig.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "TIV 수입 점유율: "
                "%{customdata[2]:.2f}%"
                "<extra></extra>"
            )
        )

    elif selected_metric == "분쟁 위험도":
        fig.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "분쟁 위험도: "
                "%{customdata[2]:.2f}점"
                "<extra></extra>"
            )
        )

    elif selected_metric == "군사비":
        fig.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "군사비: "
                "%{customdata[2]:,.0f} 백만 US$"
                "<extra></extra>"
            )
        )

    else:
        fig.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "GDP: "
                "%{customdata[2]:,.0f} 백만 US$"
                "<extra></extra>"
            )
        )

    # 사이드바 / 다른 페이지에서 선택된 국가도
    # 지도에서 클릭한 것처럼 강조
    if selected_country is not None:
        selected_rows = np.where(
            map_df["Country"].values
            == selected_country
        )[0]

        if len(selected_rows) > 0:
            selected_index = int(
                selected_rows[0]
            )

            fig.update_traces(
                selectedpoints=[
                    selected_index
                ],
                selected=dict(
                    marker=dict(
                        opacity=1.0
                    )
                ),
                unselected=dict(
                    marker=dict(
                        opacity=0.12
                    )
                ),
            )

    if selected_metric in [
        "GDP",
        "군사비",
    ]:
        fig.update_coloraxes(
            colorbar_title=(
                f"log10({selected_metric})"
            )
        )
    else:
        fig.update_coloraxes(
            colorbar_title=selected_metric
        )

    fig.update_layout(
        height=height,
        clickmode="event+select",
        hovermode="closest",
        title=(
            f"{year}년 국가별 "
            f"{selected_metric}"
        ),
        geo=dict(
            showframe=False,
            showcoastlines=True,
            coastlinecolor="gray",
            showland=True,
            landcolor="rgb(240,240,240)",
        ),
        margin=dict(
            l=0,
            r=0,
            t=50,
            b=0,
        ),
    )

    return fig, map_df


def make_page1_line(
    country_name,
    selected_metric,
):
    metric_column = PAGE1_METRICS[
        selected_metric
    ]["column"]

    metric_unit = PAGE1_METRICS[
        selected_metric
    ]["unit"]

    country_df = df[
        (df["Country"] == country_name)
        &
        (df[metric_column].notna())
    ].copy()

    country_df = (
        country_df.groupby(
            "Year",
            as_index=False,
        )[metric_column]
        .mean()
        .sort_values("Year")
    )

    if country_df.empty:
        return empty_figure(
            "해당 국가의 시계열 데이터가 없습니다.",
            height=500,
        )

    fig = px.line(
        country_df,
        x="Year",
        y=metric_column,
        markers=True,
        labels={
            "Year": "연도",
            metric_column: (
                f"{selected_metric} "
                f"({metric_unit})"
            ),
        },
    )

    if selected_metric == "TIV 수입 점유율":
        hover = (
            "연도: %{x}<br>"
            "TIV 수입 점유율: "
            "%{y:.2f}%"
            "<extra></extra>"
        )

    elif selected_metric == "분쟁 위험도":
        hover = (
            "연도: %{x}<br>"
            "분쟁 위험도: "
            "%{y:.2f}점"
            "<extra></extra>"
        )

    else:
        hover = (
            "연도: %{x}<br>"
            + selected_metric
            + ": %{y:,.0f} 백만 US$"
            "<extra></extra>"
        )

    fig.update_traces(
        hovertemplate=hover
    )

    fig.update_layout(
        height=500,
        hovermode="x unified",
        xaxis=dict(dtick=1),
        margin=dict(
            l=20,
            r=20,
            t=20,
            b=40,
        ),
    )

    return fig


def make_page1_radar(
    country_name,
):
    indicator_map = {
        "분쟁 위험도":
            "human_hazard_score",
        "TIV 수입 점유율":
            "TIV_5Y_Share",
        "군사비":
            "current_usd",
        "GDP":
            "gdp_calculated",
        "군사비/GDP":
            "share_gdp",
    }

    year_df = df[
        df["Year"] == year
    ].copy()

    year_df = (
        year_df.groupby(
            ["Country", "Iso3"],
            as_index=False,
        )[
            list(
                indicator_map.values()
            )
        ]
        .mean()
    )

    for label, col in indicator_map.items():
        year_df[
            col + "_scaled"
        ] = (
            year_df[col]
            .rank(pct=True)
            * 100
        )

    country_data = year_df[
        year_df["Country"]
        == country_name
    ]

    if country_data.empty:
        return empty_figure(
            "선택 국가의 레이더차트 데이터가 없습니다.",
            height=500,
        )

    country_row = (
        country_data.iloc[0]
    )

    categories = list(
        indicator_map.keys()
    )

    values = [
        country_row[
            indicator_map[label]
            + "_scaled"
        ]
        for label in categories
    ]

    raw_values = [
        country_row[
            indicator_map[label]
        ]
        for label in categories
    ]

    if any(
        pd.isna(value)
        for value in raw_values
    ):
        return empty_figure(
            "레이더차트에 필요한 일부 지표가 없습니다.",
            height=500,
        )

    raw_text = [
        f"{raw_values[0]:,.2f}점",
        f"{raw_values[1]:,.2f}%",
        f"{raw_values[2]:,.0f} 백만 US$",
        f"{raw_values[3]:,.0f} 백만 US$",
        f"{raw_values[4]:,.2f}%",
    ]

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself",
            name=country_name,
            customdata=(
                raw_text
                + [raw_text[0]]
            ),
            hovertemplate=(
                "<b>%{theta}</b><br>"
                "상대점수: "
                "%{r:.1f}점<br>"
                "실제 값: "
                "%{customdata}"
                "<extra></extra>"
            ),
        )
    )

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                tickvals=[
                    0,
                    20,
                    40,
                    60,
                    80,
                    100,
                ],
            )
        ),
        height=500,
        showlegend=True,
        margin=dict(
            l=60,
            r=60,
            t=20,
            b=30,
        ),
    )

    return fig


# =========================================================
# 11. 2페이지 설정
# =========================================================

PAGE2_METRIC = {
    "risk": {
        "col":
            "human_hazard_score",
        "label":
            "분쟁위험도",
        "color":
            "#C1663B",
        "scale":
            "OrRd",
        "fmt":
            ".1f",
        "log_y":
            False,
        "log_color":
            False,
        "yticks":
            None,
        "ytext":
            None,
    },
    "tiv": {
        "col":
            "TIV_5Y_Share",
        "label":
            "TIV 5년 점유율 (%)",
        "color":
            "#2C7A5A",
        "scale":
            "BuGn",
        "fmt":
            ".3f",
        "log_y":
            True,
        "log_color":
            True,
        "yticks":
            [
                0.004,
                0.01,
                0.03,
                0.1,
                0.3,
                1,
                3,
                10,
            ],
        "ytext":
            [
                "0",
                "0.01",
                "0.03",
                "0.1",
                "0.3",
                "1",
                "3",
                "10",
            ],
    },
}


def bubble_size(values):
    v = np.sqrt(
        np.clip(
            values.astype(float),
            0,
            None,
        )
    )

    lo = np.nanmin(v)
    hi = np.nanmax(v)

    if hi == lo:
        return np.full(
            len(v),
            (
                BUBBLE_MIN
                + BUBBLE_MAX
            ) / 2,
        )

    return (
        BUBBLE_MIN
        + (v - lo)
        / (hi - lo)
        * (
            BUBBLE_MAX
            - BUBBLE_MIN
        )
    )


def make_bubble(
    data,
    year,
    metric="risk",
    size_col=SIZE_COL,
    highlight=None,
):
    m = PAGE2_METRIC[metric]

    if (
        metric == "risk"
        and
        year < RISK_START
    ):
        return empty_figure(
            f"분쟁위험도(INFORM)는 "
            f"{RISK_START}년부터 제공됩니다.<br>"
            f"{RISK_START}년 이후를 선택하거나 "
            "TIV 차트를 이용하세요."
        )

    d = data[
        data["Year"] == year
    ].dropna(
        subset=[
            X_COL,
            m["col"],
            size_col,
        ]
    )

    d = d[
        (d[X_COL] > 0)
        &
        (d[size_col] > 0)
    ]

    if d.empty:
        return empty_figure(
            f"{year}년 데이터가 없습니다."
        )

    y = (
        d[m["col"]]
        .clip(lower=0.004)
        if m["log_y"]
        else d[m["col"]]
    )

    if m["log_color"]:
        cvals = np.log10(
            d[m["col"]]
            .clip(lower=0.004)
        )

        color_ticks = [
            0.004,
            0.01,
            0.1,
            1,
            10,
        ]

        colorbar = dict(
            title=dict(
                text=m["label"],
                side="right",
            ),
            thickness=12,
            len=0.75,
            tickvals=np.log10(
                color_ticks
            ),
            ticktext=[
                "0",
                "0.01",
                "0.1",
                "1",
                "10",
            ],
        )

    else:
        cvals = d[m["col"]]

        colorbar = dict(
            title=dict(
                text=m["label"],
                side="right",
            ),
            thickness=12,
            len=0.75,
        )

    fig = go.Figure(
        go.Scatter(
            x=d[X_COL],
            y=y,
            mode="markers",
            customdata=np.stack(
                [
                    d["Country"],
                    d["Iso3"],
                    d[SIZE_COL],
                    d[MILEX_COL],
                    d[m["col"]],
                ],
                axis=-1,
            ),
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "GDP 대비 군사비 "
                "%{x:.2f}%<br>"
                + m["label"]
                + " %{customdata[4]:"
                + m["fmt"]
                + "}<br>"
                "GDP "
                "%{customdata[2]:,.0f}<br>"
                "군사비 "
                "%{customdata[3]:,.0f}"
                "<extra></extra>"
            ),
            marker=dict(
                size=bubble_size(
                    d[size_col]
                ),
                sizemode="diameter",
                color=cvals,
                colorscale=m["scale"],
                showscale=True,
                colorbar=colorbar,
                opacity=(
                    0.72
                    if highlight is None
                    else [
                        0.95
                        if iso == highlight
                        else 0.25
                        for iso in d["Iso3"]
                    ]
                ),
                line=dict(
                    width=[
                        2
                        if iso == highlight
                        else 0.5
                        for iso
                        in d["Iso3"]
                    ],
                    color=[
                        "#111111"
                        if iso == highlight
                        else "rgba(60,60,60,0.4)"
                        for iso
                        in d["Iso3"]
                    ],
                ),
            ),
            selected=dict(
                marker=dict(
                    opacity=0.95
                )
            ),
            unselected=dict(
                marker=dict(
                    opacity=0.25
                )
            ),
        )
    )

    fig.update_layout(
        title=dict(
            text=(
                f"{year}년 · "
                "GDP 대비 군사비 × "
                f"{m['label']} "
                f"(n={len(d)})"
            ),
            font=dict(size=15),
        ),
        xaxis=dict(
            title="GDP 대비 군사비 (%)",
            type="log",
            tickvals=[
                0.2,
                0.5,
                1,
                2,
                5,
                10,
                20,
                40,
            ],
            ticktext=[
                "0.2",
                "0.5",
                "1",
                "2",
                "5",
                "10",
                "20",
                "40",
            ],
        ),
        yaxis=dict(
            title=m["label"],
            type=(
                "log"
                if m["log_y"]
                else "linear"
            ),
            tickvals=m["yticks"],
            ticktext=m["ytext"],
        ),
        height=460,
        **BASE_LAYOUT,
    )

    return fig


def make_page2_line(
    data,
    iso,
    metric="risk",
):
    m = PAGE2_METRIC[metric]

    d = data[
        data["Iso3"] == iso
    ].sort_values("Year")

    if d.empty:
        return empty_figure(
            "국가를 선택하세요."
        )

    name = d[
        "Country"
    ].iloc[0]

    full = pd.DataFrame(
        {
            "Year":
                range(
                    YEAR_MIN,
                    YEAR_MAX + 1,
                )
        }
    )

    d = full.merge(
        d,
        on="Year",
        how="left",
    )

    fig = make_subplots(
        specs=[
            [
                {
                    "secondary_y":
                        True
                }
            ]
        ]
    )

    fig.add_trace(
        go.Scatter(
            x=d["Year"],
            y=d[MILEX_COL],
            name="군사비",
            mode="lines+markers",
            connectgaps=False,
            line=dict(
                color=MILEX_COLOR,
                width=2,
            ),
            marker=dict(size=4),
            hovertemplate=(
                "%{x}년<br>"
                "군사비 "
                "%{y:,.0f}"
                "<extra></extra>"
            ),
        ),
        secondary_y=False,
    )

    fig.add_trace(
        go.Scatter(
            x=d["Year"],
            y=d[m["col"]],
            name=m["label"],
            mode="lines+markers",
            connectgaps=False,
            line=dict(
                color=m["color"],
                width=2,
                dash="dot",
            ),
            marker=dict(size=4),
            hovertemplate=(
                "%{x}년<br>"
                + m["label"]
                + " %{y:"
                + m["fmt"]
                + "}"
                "<extra></extra>"
            ),
        ),
        secondary_y=True,
    )

    if metric == "risk":
        fig.add_vrect(
            x0=YEAR_MIN - 0.5,
            x1=RISK_START - 0.5,
            fillcolor="#000000",
            opacity=0.05,
            line_width=0,
        )

        fig.add_annotation(
            x=(
                YEAR_MIN
                + RISK_START
            ) / 2,
            y=1.0,
            yref="paper",
            text=(
                "위험도 미제공 "
                f"(~{RISK_START - 1})"
            ),
            showarrow=False,
            font=dict(
                size=10,
                color="#7A8794",
            ),
        )

    fig.update_xaxes(
        title_text="연도",
        dtick=2,
        range=[
            YEAR_MIN - 0.5,
            YEAR_MAX + 0.5,
        ],
    )

    fig.update_yaxes(
        title_text="군사비",
        color=MILEX_COLOR,
        secondary_y=False,
        rangemode="tozero",
    )

    fig.update_yaxes(
        title_text=m["label"],
        color=m["color"],
        secondary_y=True,
        showgrid=False,
        tickformat=m["fmt"],
    )

    fig.update_layout(
        title=dict(
            text=f"{name} · 연도별 추이",
            font=dict(size=15),
            y=0.97,
            yanchor="top",
        ),
        legend=dict(
            orientation="h",
            y=1.02,
            x=0,
            yanchor="bottom",
        ),
        height=460,
        margin=dict(
            l=60,
            r=70,
            t=85,
            b=55,
        ),
        template="plotly_white",
        font=dict(
            family=(
                "Malgun Gothic, "
                "AppleGothic, "
                "NanumGothic, "
                "sans-serif"
            ),
            size=12,
        ),
        hovermode="closest",
    )

    return fig


# =========================================================
# 12. 1페이지
# =========================================================

if page == "1페이지 · 국가별 현황":

    st.title(
        "🌍 방산시장 분석 대시보드"
    )

    st.caption(
        "분쟁 위험도 · TIV 수입 점유율 · "
        "군사비 · GDP를 기반으로 "
        "국가별 방산시장 현황을 비교합니다."
    )

    st.subheader(
        "국가별 방산시장 지표"
    )

    button_cols = st.columns(4)

    metric_names = [
        "분쟁 위험도",
        "TIV 수입 점유율",
        "군사비",
        "GDP",
    ]

    for metric_name, col in zip(
        metric_names,
        button_cols,
    ):
        col.button(
            metric_name,
            key=f"metric_{metric_name}",
            type=(
                "primary"
                if st.session_state.selected_metric
                == metric_name
                else "secondary"
            ),
            use_container_width=True,
            on_click=change_metric,
            args=(metric_name,),
        )

    selected_metric = (
        st.session_state.selected_metric
    )

    # ---------------------------------------------
    # 국가 미선택: 큰 지도
    # ---------------------------------------------

    if chosen_name == NONE_LABEL:

        st.markdown(
            """
            ### 분석할 국가를 선택하세요

            세계지도에서 국가를 클릭하거나
            왼쪽 사이드바에서 국가를 선택하면
            상세 분석 화면이 표시됩니다.
            """
        )

        fig_map, map_df = make_page1_map(
            selected_metric=selected_metric,
            selected_country=None,
            height=760,
        )

        map_event = st.plotly_chart(
            fig_map,
            use_container_width=True,
            on_select="rerun",
            selection_mode="points",
            key=(
                "page1_big_map_"
                f"{year}_"
                f"{selected_metric}_"
                f"{st.session_state.map_version}"
            ),
            config={
                "displayModeBar": True,
                "scrollZoom": False,
            },
        )

        clicked_country = (
            get_clicked_country_from_map(
                map_event,
                map_df,
            )
        )

        sync_clicked_country(
            clicked_country
        )

    # ---------------------------------------------
    # 국가 선택: 2 x 2 상세화면
    # ---------------------------------------------

    else:

        st.subheader(
            f"📍 선택 국가 : {chosen_name}"
        )

        top_left, top_right = (
            st.columns(
                [1.25, 1]
            )
        )

        with top_left:

            st.markdown(
                f"### 🌍 "
                f"{selected_metric} 세계지도"
            )

            fig_map, map_df = make_page1_map(
                selected_metric=selected_metric,
                selected_country=chosen_name,
                height=430,
            )

            map_event = st.plotly_chart(
                fig_map,
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key=(
                    "page1_small_map_"
                    f"{year}_"
                    f"{selected_metric}_"
                    f"{chosen_name}_"
                    f"{st.session_state.map_version}"
                ),
                config={
                    "displayModeBar": False,
                    "scrollZoom": False,
                },
            )

            clicked_country = (
                get_clicked_country_from_map(
                    map_event,
                    map_df,
                )
            )

            sync_clicked_country(
                clicked_country
            )

        with top_right:

            st.markdown(
                f"### 📊 {year}년 "
                "TIV 수입 점유율 Top10"
            )

            tiv_top10 = df[
                (df["Year"] == year)
                &
                (
                    df["TIV_5Y_Share"]
                    .notna()
                )
            ].copy()

            tiv_top10 = (
                tiv_top10.groupby(
                    ["Country", "Iso3"],
                    as_index=False,
                )["TIV_5Y_Share"]
                .mean()
                .sort_values(
                    "TIV_5Y_Share",
                    ascending=False,
                )
                .head(10)
            )

            tiv_top10_plot = (
                tiv_top10.sort_values(
                    "TIV_5Y_Share",
                    ascending=True,
                )
            )

            fig_tiv = px.bar(
                tiv_top10_plot,
                x="TIV_5Y_Share",
                y="Country",
                orientation="h",
                text="TIV_5Y_Share",
                labels={
                    "TIV_5Y_Share":
                        "TIV 수입 점유율 (%)",
                    "Country":
                        "",
                },
            )

            fig_tiv.update_traces(
                texttemplate="%{x:.2f}%",
                textposition="outside",
                hovertemplate=(
                    "<b>%{y}</b><br>"
                    "TIV 수입 점유율: "
                    "%{x:.2f}%"
                    "<extra></extra>"
                ),
            )

            fig_tiv.update_layout(
                height=430,
                showlegend=False,
                yaxis_title="",
                xaxis_title=(
                    "TIV 수입 점유율 (%)"
                ),
                margin=dict(
                    l=10,
                    r=80,
                    t=20,
                    b=40,
                ),
            )

            st.plotly_chart(
                fig_tiv,
                use_container_width=True,
                key=f"page1_tiv_top10_{year}",
            )

        st.divider()

        bottom_left, bottom_right = (
            st.columns(2)
        )

        with bottom_left:

            st.markdown(
                f"### 📈 {chosen_name} - "
                f"{selected_metric} 추이"
            )

            st.plotly_chart(
                make_page1_line(
                    chosen_name,
                    selected_metric,
                ),
                use_container_width=True,
                key=(
                    "page1_line_"
                    f"{chosen_name}_"
                    f"{selected_metric}"
                ),
            )

        with bottom_right:

            st.markdown(
                f"### 🎯 {chosen_name} "
                "방산시장 상대지표"
            )

            st.plotly_chart(
                make_page1_radar(
                    chosen_name
                ),
                use_container_width=True,
                key=(
                    "page1_radar_"
                    f"{chosen_name}_"
                    f"{year}"
                ),
            )


# =========================================================
# 13. 2페이지
# =========================================================

else:

    st.title(
        "수출 유망국 탐색 — 복합지표"
    )

    st.caption(
        "GDP 대비 군사비를 기준으로 "
        "분쟁위험도와 무기 수입 실적을 함께 확인합니다. "
        "버블을 클릭하면 선택 국가가 공통 사이드바와 "
        "1페이지에도 함께 반영됩니다."
    )

    # 두 번째 페이지만 사용하는 옵션이므로
    # 공통 사이드바가 아니라 본문에 배치
    size_col = st.radio(
        "버블 크기",
        options=[
            "gdp_calculated",
            "current_usd",
        ],
        format_func=lambda x: {
            "gdp_calculated":
                "GDP",
            "current_usd":
                "군사비",
        }[x],
        horizontal=True,
        key="page2_size_col",
    )

    if year < RISK_START:
        st.info(
            f"분쟁위험도는 {RISK_START}년부터 제공됩니다. "
            "선택한 연도에서는 TIV 차트를 확인하세요."
        )

    for metric in [
        "risk",
        "tiv",
    ]:

        left, right = st.columns(2)

        with left:

            bubble_event = st.plotly_chart(
                make_bubble(
                    df,
                    year,
                    metric,
                    size_col=size_col,
                    highlight=sel_iso,
                ),
                use_container_width=True,
                on_select="rerun",
                selection_mode="points",
                key=f"page2_bubble_{metric}",
            )

            point = extract_selected_point(
                bubble_event
            )

            if point is not None:
                try:
                    customdata = point.get(
                        "customdata"
                    )
                    clicked_iso = (
                        customdata[1]
                        if customdata
                        else None
                    )
                except Exception:
                    clicked_iso = None

                if clicked_iso:
                    clicked_name = (
                        ISO_TO_NAME.get(
                            clicked_iso
                        )
                    )

                    sync_clicked_country(
                        clicked_name
                    )

        with right:

            if sel_iso:

                st.plotly_chart(
                    make_page2_line(
                        df,
                        sel_iso,
                        metric,
                    ),
                    use_container_width=True,
                    key=(
                        "page2_line_"
                        f"{metric}_"
                        f"{sel_iso}"
                    ),
                )

            else:

                st.plotly_chart(
                    empty_figure(
                        "버블을 클릭하거나 "
                        "사이드바에서 국가를 선택하세요."
                    ),
                    use_container_width=True,
                    key=(
                        "page2_empty_"
                        f"{metric}"
                    ),
                )

    st.caption(
        "TIV(Trend Indicator Value)는 SIPRI가 "
        "무기의 군사적 능력을 지수화한 값으로 "
        "실제 거래 금액이 아닙니다. "
        "분쟁위험도는 UN INFORM Human Hazard 지수이며 "
        f"{RISK_START}년부터 제공됩니다."
    )
