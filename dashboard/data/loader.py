"""integrate 테이블을 DB(안 되면 CSV)에서 읽고 숫자형·단위를 정리함."""
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

from dashboard.config import DATA_PATH, ROOT_DIR


@st.cache_resource
def get_db_engine(db_url):
    return create_engine(db_url, pool_pre_ping=True)


# DB는 수동으로 갱신되므로 6시간 동안 저장해 두고 씁니다.
# (10분마다 다시 불러오면 그때마다 4초 정도 기다려야 합니다)
@st.cache_data(ttl=60 * 60 * 6, show_spinner="데이터를 불러오는 중...")
def load_integrate_raw():
    """
    공용 AWS DB(import_demand_db)의 integrate 테이블을 불러옵니다.
    .streamlit/secrets.toml 에 [mysql] db_url 이 없거나 DB 연결에 실패하면
    같은 내용의 Integrate_new.csv 를 대신 사용합니다.
    돌려주는 값 : (데이터, 출처 설명, DB 오류 메시지 또는 None)
    """
    try:
        db_url = st.secrets["mysql"]["db_url"]
    except Exception:
        db_url = None

    db_error = None

    if db_url:
        try:
            data = pd.read_sql(
                "SELECT * FROM integrate;",
                get_db_engine(db_url),
            )
            return data, "AWS DB (integrate)", None
        except Exception as error:
            db_error = str(error)

    # app.py 옆에 없으면 저장소의 00_files 폴더에서 찾습니다 (배포 환경용).
    base_dir = ROOT_DIR
    path = base_dir / DATA_PATH
    if not path.exists():
        path = base_dir / "00_files" / DATA_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"DB 설정이 없고 {DATA_PATH} 파일도 찾을 수 없습니다."
        )

    try:
        data = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        data = pd.read_csv(path, encoding="cp949")

    return data, f"CSV ({DATA_PATH})", db_error


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
