"""DB 연결과 원본 테이블 로드 (실패하면 CSV)"""
import pandas as pd
from sqlalchemy import create_engine
import streamlit as st

from dashboard.common.config import APP_DIR, DATA_PATH


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

    path = APP_DIR / DATA_PATH

    if not path.exists():
        raise FileNotFoundError(
            f"DB 설정이 없고 {DATA_PATH} 파일도 찾을 수 없습니다."
        )

    try:
        data = pd.read_csv(path, encoding="utf-8-sig")
    except UnicodeDecodeError:
        data = pd.read_csv(path, encoding="cp949")

    return data, f"CSV ({DATA_PATH})", db_error
