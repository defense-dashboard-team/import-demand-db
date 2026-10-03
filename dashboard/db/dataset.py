"""분석용 데이터 준비"""
import pandas as pd
import streamlit as st

from dashboard.context import ctx
from dashboard.db.connection import load_integrate_raw


@st.cache_data
def load_data():
    data = load_integrate_raw()[0].copy()

    def find_col(candidates):
        for candidate in candidates:
            if candidate in data.columns:
                return candidate
        raise KeyError(f"필요한 컬럼을 찾지 못했습니다: {candidates}")

    COL = {
        "country": find_col(["Country", "country", "Recipient"]),
        "iso3": find_col(["Iso3", "ISO3", "iso3", "Country_Code", "country_code"]),
        "year": find_col(["Year", "year", "Delivery year"]),
        "gdp": find_col(["gdp_calculated", "GDP", "NY.GDP.MKTP.CD"]),
        "military": find_col(["current_usd", "Military_Expenditure", "military_expenditure"]),
        "share_gdp": find_col(["share_gdp", "Share_GDP"]),
        "tiv": find_col(["TIV_5Y_Share", "tiv_5y_share"]),
        "risk": find_col(["human_hazard_score", "Indicator Score", "indicator_score"]),
    }

    numeric_cols = [
        COL["year"],
        COL["gdp"],
        COL["military"],
        COL["share_gdp"],
        COL["tiv"],
        COL["risk"],
    ]

    for col in numeric_cols:
        data[col] = (
            data[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("%", "", regex=False)
            .str.strip()
        )
        data[col] = pd.to_numeric(data[col], errors="coerce")

    data = data.dropna(
        subset=[COL["country"], COL["iso3"], COL["year"]]
    )

    data[COL["country"]] = data[COL["country"]].astype(str).str.strip()
    data[COL["iso3"]] = data[COL["iso3"]].astype(str).str.upper().str.strip()
    data[COL["year"]] = data[COL["year"]].astype(int)

    data = (
        data.groupby(
            [COL["country"], COL["iso3"], COL["year"]],
            as_index=False,
        )
        .agg({
            COL["gdp"]: "mean",
            COL["military"]: "mean",
            COL["share_gdp"]: "mean",
            COL["tiv"]: "mean",
            COL["risk"]: "mean",
        })
    )

    share_values = data[COL["share_gdp"]].dropna()
    if not share_values.empty and share_values.max() <= 1:
        data[COL["share_gdp"]] *= 100

    tiv_values = data[COL["tiv"]].dropna()
    if not tiv_values.empty and tiv_values.max() <= 1:
        data[COL["tiv"]] *= 100

    return data, COL


def load_dataset():
    """rerun마다 호출. 데이터와 거기서 파생되는 값들을 ctx에 다시 채운다."""
    try:
        ctx.df, ctx.COL = load_data()
        ctx.DATA_SOURCE, ctx.DB_ERROR = load_integrate_raw()[1:]
    except Exception as error:
        st.error(str(error))
        st.stop()

    if ctx.DB_ERROR:
        st.warning(
            "공용 DB에 연결하지 못해 CSV 파일로 표시합니다. "
            f"(오류: {ctx.DB_ERROR[:200]})"
        )

    ctx.countries = sorted(ctx.df[ctx.COL["country"]].dropna().unique().tolist())
    ctx.years = sorted(ctx.df[ctx.COL["year"]].dropna().astype(int).unique().tolist())

    ctx.country_iso_table = (
        ctx.df[[ctx.COL["country"], ctx.COL["iso3"]]]
        .drop_duplicates(subset=[ctx.COL["country"]])
    )

    ctx.country_to_iso3 = dict(
        zip(
            ctx.country_iso_table[ctx.COL["country"]],
            ctx.country_iso_table[ctx.COL["iso3"]],
        )
    )

    ctx.default_country = (
        "Korea, South" if "Korea, South" in ctx.countries else ctx.countries[0]
    )
    ctx.default_year = 2025 if 2025 in ctx.years else max(ctx.years)

    ctx.METRIC_CONFIG = {
        "군사비": {
            "column": ctx.COL["military"],
            "axis": "군사비 (USD)",
        },
        "GDP": {
            "column": ctx.COL["gdp"],
            "axis": "GDP (USD)",
        },
        "군사비/GDP": {
            "column": ctx.COL["share_gdp"],
            "axis": "군사비/GDP (%)",
        },
        "무기수입 점유율": {
            "column": ctx.COL["tiv"],
            "axis": "무기수입 점유율 (5년, %)",
        },
        "분쟁 위험도": {
            "column": ctx.COL["risk"],
            "axis": "분쟁 위험도",
        },
    }

    # 1페이지 loader가 지표 비율을 % 단위로 통일하므로
    # 2페이지도 동일한 값을 사용합니다.
    ctx.df["Country"] = ctx.df[ctx.COL["country"]]
    ctx.df["Iso3"] = ctx.df[ctx.COL["iso3"]]
    ctx.df["Year"] = ctx.df[ctx.COL["year"]]
    ctx.df["gdp_calculated"] = ctx.df[ctx.COL["gdp"]]
    ctx.df["current_usd"] = ctx.df[ctx.COL["military"]]
    ctx.df["share_gdp"] = ctx.df[ctx.COL["share_gdp"]]
    ctx.df["TIV_5Y_Share"] = ctx.df[ctx.COL["tiv"]]
    ctx.df["human_hazard_score"] = ctx.df[ctx.COL["risk"]]
    ctx.df["share_gdp_pct"] = ctx.df[ctx.COL["share_gdp"]]

    ctx.YEAR_MIN = max(2004, int(ctx.df["Year"].min()))
    ctx.YEAR_MAX = min(2025, int(ctx.df["Year"].max()))

    ctx.min_year = int(ctx.df[ctx.COL["year"]].min())
    ctx.max_year = int(ctx.df[ctx.COL["year"]].max())


def get_country_year(country, year):
    temp = ctx.df[
        (ctx.df[ctx.COL["country"]] == country)
        & (ctx.df[ctx.COL["year"]] == year)
    ]
    return None if temp.empty else temp.iloc[0]
