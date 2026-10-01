import pandas as pd
import numpy as np

from db_connect import get_engine

# ----------------------------------------------------------------------
# DB 연결
# ----------------------------------------------------------------------
# DB 접속 정보는 프로젝트 루트의 .env 에서 읽는다 (db_connect.py 참고)
engine = get_engine()

# ----------------------------------------------------------------------
# 원천 데이터 적재 (기존 CSV -> DB 테이블)
# ----------------------------------------------------------------------
mil = pd.read_sql("SELECT * FROM current_usd", con=engine)
gdp = pd.read_sql("SELECT * FROM gdp_calculated", con=engine)
hazard = pd.read_sql("SELECT * FROM human_hazard_trend", con=engine)
tiv = pd.read_sql("SELECT * FROM tiv_5y_share", con=engine)

mil.columns = mil.columns.astype(str)
gdp.columns = gdp.columns.astype(str)
hazard.columns = hazard.columns.astype(str)
tiv.columns = tiv.columns.astype(str)

years = [str(year) for year in range(2000, 2026)]

# ----------------------------------------------------------------------
# 군사비 / GDP long 변환
# ----------------------------------------------------------------------
mil_long = mil.melt(
    id_vars="Country",
    value_vars=years,
    var_name="Year",
    value_name="Military_Expenditure"
)

mil_long["Year"] = mil_long["Year"].astype(int)

gdp_long = gdp.melt(
    id_vars="Country",
    value_vars=years,
    var_name="Year",
    value_name="GDP"
)

gdp_long["Year"] = gdp_long["Year"].astype(int)

# ----------------------------------------------------------------------
# 국가코드 매핑
# ----------------------------------------------------------------------
country_code_map = (
    tiv[["Country", "Country_Code"]]
    .drop_duplicates()
    .set_index("Country")["Country_Code"]
    .to_dict()
)

manual_country_codes = {
    "Bosnia and Herzegovina": "BIH",
    "Cape Verde": "CPV",
    "Congo, DR": "COD",
    "Congo, Republic": "COG",
    "Eswatini": "SWZ",
    "Gambia, The": "GMB",
    "Guinea-Bissau": "GNB",
    "Korea, North": "PRK",
    "Korea, South": "KOR",
    "Kyrgyz Republic": "KGZ",
    "Panama": "PAN",
    "Timor Leste": "TLS",
    "Türkiye": "TUR",
    "United States of America": "USA",
    "Kosovo": "XKX",
    "Yemen": "YEM"
}

country_code_map.update(manual_country_codes)

mil_long["Iso3"] = mil_long["Country"].map(country_code_map)
gdp_long["Iso3"] = gdp_long["Country"].map(country_code_map)

# 국가코드가 없는 국가들
# (전부 ~1992년까지 존재했던 국가들이라 2000년부터 기간을 잡은 우리는 삭제해도 괜찮음)
print(
    mil_long.loc[
        mil_long["Iso3"].isna(),
        "Country"
    ].drop_duplicates().tolist()
)

# 위의 국가들 삭제
mil_long = mil_long.dropna(subset=["Iso3"]).copy()
gdp_long = gdp_long.dropna(subset=["Iso3"]).copy()

# ----------------------------------------------------------------------
# 분쟁위험도 / TIV 정리
# ----------------------------------------------------------------------
# 분쟁데이터 컬럼명 year로 변경, 정수화, 사용할 컬럼만 추출, year는 2016~2025
hazard_clean = hazard.rename(
    columns={"Data_reference_year": "Year"}
).copy()

hazard_clean["Year"] = hazard_clean["Year"].astype(int)

hazard_clean = hazard_clean[
    [
        "Iso3",
        "Year",
        "IndicatorScore"
    ]
]

# 컬럼명 국가코드를 Iso3로 변경
tiv_clean = tiv.rename(
    columns={"Country_Code": "Iso3"}
).copy()

tiv_clean["Year"] = tiv_clean["Year"].astype(int)

tiv_clean = tiv_clean[
    [
        "Iso3",
        "Country",
        "Year",
        "Window",
        "TIV_5Y_Sum",
        "World_TIV_5Y_Sum",
        "TIV_5Y_Share"
    ]
]

# ----------------------------------------------------------------------
# 병합
# ----------------------------------------------------------------------
# 군사비 + GDP를 ISO3 + Year로 merge
merged = pd.merge(
    mil_long[
        [
            "Country",
            "Iso3",
            "Year",
            "Military_Expenditure"
        ]
    ],
    gdp_long[
        [
            "Iso3",
            "Year",
            "GDP"
        ]
    ],
    on=["Iso3", "Year"],
    how="outer"
)

# TIV merge
merged = pd.merge(
    merged,
    tiv_clean,
    on=["Iso3", "Year"],
    how="outer",
    suffixes=("", "_tiv")
)

# 분쟁위험도 merge
merged = pd.merge(
    merged,
    hazard_clean,
    on=["Iso3", "Year"],
    how="outer"
)

# 2000~2025
merged = merged[
    (merged["Year"] >= 2000) &
    (merged["Year"] <= 2025)
].copy()

# TIV에 있는 Country_tiv때문에 국가명 컬럼이 중복될 수 있음
# 기존 국가명이 있으면 국가명을 쓰고, 없으면 TIV 국가명 사용
# 사용 후 Country_tiv 컬럼 삭제
merged["Country"] = merged["Country"].fillna(
    merged["Country_tiv"]
)

merged = merged.drop(
    columns=["Country_tiv"]
)

column_order = [
    "Country",
    "Iso3",
    "Year",
    "Military_Expenditure",
    "GDP",
    "IndicatorScore",
    "TIV_5Y_Share",
    "TIV_5Y_Sum",
    "World_TIV_5Y_Sum",
    "Window"
]

merged = merged[column_order]

merged = merged.sort_values(
    by=["Country", "Year"]
).reset_index(drop=True)

# ----------------------------------------------------------------------
# 검증
# ----------------------------------------------------------------------
duplicates = merged[
    merged.duplicated(
        subset=["Iso3", "Year"],
        keep=False
    )
]

print("중복 행 수:", len(duplicates))

print(
    merged[
        [
            "Military_Expenditure",
            "GDP",
            "IndicatorScore",
            "TIV_5Y_Share"
        ]
    ].isna().sum()
)

merged = merged.rename(
    columns={"Military_Expenditure": "current_usd"}
)

print(merged.shape)
print(merged["Iso3"].nunique())
print(merged["Year"].min())
print(merged["Year"].max())
print(merged.head(20))

merged = merged.drop(
    columns=["World_TIV_5Y_Sum", "Window"]
)

# ----------------------------------------------------------------------
# human_hazard_score / share_gdp 결합 (기존 integrate.csv -> integrate 테이블)
# ----------------------------------------------------------------------
hazard_score = pd.read_sql("SELECT * FROM integrate", con=engine)
hazard_score.columns = hazard_score.columns.astype(str)

# Kosovo 국가코드 수정
hazard_score.loc[
    hazard_score["Country"] == "Kosovo",
    "Iso3"
] = "XKX"

# 필요한 컬럼만 선택
hazard_score = hazard_score[
    ["Iso3", "Year", "human_hazard_score", "share_gdp"]
]

# 중복 제거
hazard_score = hazard_score.drop_duplicates(
    subset=["Iso3", "Year"]
)

# merged에 추가
merged = pd.merge(
    merged,
    hazard_score,
    on=["Iso3", "Year"],
    how="left"
)

merged = merged.drop(
    columns=["IndicatorScore"]
)

merged = merged.rename(
    columns={"GDP": "gdp_calculated"}
)

# ----------------------------------------------------------------------
# 저장
# ----------------------------------------------------------------------
merged.to_sql(name='integrate', con=engine, if_exists='replace', index=False)