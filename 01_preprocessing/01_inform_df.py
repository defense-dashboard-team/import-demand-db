import pandas as pd
import numpy as np
from sqlalchemy import text

from db_connect import db_name, get_engine

# DB 접속 정보는 프로젝트 루트의 .env 에서 읽는다 (db_connect.py 참고)
# 먼저 데이터베이스를 지정하지 않고 RDS 서버에 연결하는 base_engine 생성
base_engine = get_engine(database=False)

# 엔진이 연결 됐으면 SQL QUERY문 실행: 데이터베이스가 없으면 만든다
with base_engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {db_name()};"))

# 위에서 만든 데이터베이스에 연결하는 engine 생성
engine = get_engine()


file_path = 'data/INFORM2026_TREND_2017_2026_v72_ALL.xlsx'

df = pd.read_excel(file_path, sheet_name='INFORM2026Trend')

df_hazard = df[df['IndicatorName'] == 'Human Hazard'].copy()

df_hazard.columns = df_hazard.columns.str.replace(' ', '_')

df_hazard.to_sql(
    name='human_hazard_trend',
    con=engine,
    if_exists='replace',
    index=False
)

print("분쟁 위험도 테이블(human_hazard_trend)이 DB에 성공적으로 생성되었습니다.")
