"""모든 화면이 같이 쓰는 데이터 묶음(Dataset).

app.py가 rerun마다 load_dataset()으로 새로 만들어 화면 함수에 넘겨줌.
(모듈 전역에 df를 두면 rerun 때 다시 계산되지 않아 값이 처음 상태로 굳음)
"""
from dataclasses import dataclass

import pandas as pd
import streamlit as st

from dashboard.data.loader import load_data, load_integrate_raw
from dashboard.utils.countries import country_english, country_korean


@dataclass
class Dataset:
    df: pd.DataFrame        # 국가-연도별 지표
    COL: dict               # 지표 이름 → df 컬럼명
    countries: list
    years: list
    country_to_iso3: dict
    default_country: str
    default_year: int
    year_min: int           # 시계열 x축 범위
    year_max: int

    def country_display(self, name):
        """
        화면 표시용 국가명 : 한글 (데이터 원본 값은 그대로 두고 표기만 바꿈).
        한글 이름을 찾지 못하면 영문 표기를 사용합니다.
        """
        korean = country_korean(self.country_to_iso3.get(name))
        return korean or country_english(name)

    def get_country_year(self, country, year):
        df, COL = self.df, self.COL
        temp = df[
            (df[COL["country"]] == country)
            & (df[COL["year"]] == year)
        ]
        return None if temp.empty else temp.iloc[0]


def load_dataset():
    """데이터를 읽어 Dataset으로 돌려줌. 읽기에 실패하면 오류를 띄우고 화면을 멈춤."""
    try:
        df, COL = load_data()
        DATA_SOURCE, DB_ERROR = load_integrate_raw()[1:]
    except Exception as error:
        st.error(str(error))
        st.stop()

    if DB_ERROR:
        st.warning(
            "공용 DB에 연결하지 못해 CSV 파일로 표시합니다. "
            f"(오류: {DB_ERROR[:200]})"
        )

    countries = sorted(df[COL["country"]].dropna().unique().tolist())
    years = sorted(df[COL["year"]].dropna().astype(int).unique().tolist())

    country_iso_table = (
        df[[COL["country"], COL["iso3"]]]
        .drop_duplicates(subset=[COL["country"]])
    )

    country_to_iso3 = dict(
        zip(
            country_iso_table[COL["country"]],
            country_iso_table[COL["iso3"]],
        )
    )

    default_country = (
        "Korea, South" if "Korea, South" in countries else countries[0]
    )
    default_year = 2025 if 2025 in years else max(years)

    # 1페이지 loader가 지표 비율을 % 단위로 통일하므로
    # 2페이지도 동일한 값을 사용합니다.
    df["Country"] = df[COL["country"]]
    df["Iso3"] = df[COL["iso3"]]
    df["Year"] = df[COL["year"]]
    df["gdp_calculated"] = df[COL["gdp"]]
    df["current_usd"] = df[COL["military"]]
    df["share_gdp"] = df[COL["share_gdp"]]
    df["TIV_5Y_Share"] = df[COL["tiv"]]
    df["human_hazard_score"] = df[COL["risk"]]
    df["share_gdp_pct"] = df[COL["share_gdp"]]

    YEAR_MIN = max(2004, int(df["Year"].min()))
    YEAR_MAX = min(2025, int(df["Year"].max()))

    return Dataset(
        df=df,
        COL=COL,
        countries=countries,
        years=years,
        country_to_iso3=country_to_iso3,
        default_country=default_country,
        default_year=default_year,
        year_min=YEAR_MIN,
        year_max=YEAR_MAX,
    )
