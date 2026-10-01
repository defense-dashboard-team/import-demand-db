import pandas as pd
from sqlalchemy import text

from db_connect import get_engine

# DB 접속 정보는 프로젝트 루트의 .env 에서 읽는다 (db_connect.py 참고)
engine = get_engine()


df_usd = pd.read_sql("SELECT * FROM current_usd", con=engine)
df_gdp = pd.read_sql("SELECT * FROM gdp_calculated", con=engine)
df_share = pd.read_sql("SELECT * FROM share_gdp", con=engine)

df_usd.columns = df_usd.columns.astype(str)
df_gdp.columns = df_gdp.columns.astype(str)
df_share.columns = df_gdp.columns.astype(str)


target_years = [str(y) for y in range(2000, 2026)]

# current_usd 데이터를 세로로 변환
df_usd_long = df_usd.melt(
    id_vars=['Iso3', 'Country'], 
    value_vars=target_years, 
    var_name='Year', 
    value_name='current_usd'
)

# gdp_calculated 데이터를 세로로 변환
df_gdp_long = df_gdp.melt(
    id_vars=['Iso3', 'Country'], 
    value_vars=target_years, 
    var_name='Year', 
    value_name='gdp_calculated'
)

# share_gdp 데이터를 세로로 변환
df_share_long = df_share.melt(
    id_vars=['Iso3', 'Country'], 
    value_vars=target_years, 
    var_name='Year', 
    value_name='share_gdp'
)

df_usd_long['Year'] = df_usd_long['Year'].astype(int)
df_gdp_long['Year'] = df_gdp_long['Year'].astype(int)
df_share_long['Year'] = df_share_long['Year'].astype(int)

df_usd_long.to_sql(name='temp_usd_long', con=engine, if_exists='replace', index=False)
df_gdp_long.to_sql(name='temp_gdp_long', con=engine, if_exists='replace', index=False)
df_share_long.to_sql(name='temp_share_long', con=engine, if_exists='replace', index=False)


query = """
SELECT 
    u.Iso3,
    u.Country,
    u.Year,
    u.current_usd,
    s.share_gdp,
    g.gdp_calculated,
    t.TIV_5Y_Sum,
    t.TIV_5Y_Share,
    h.IndicatorScore AS human_hazard_score
FROM temp_usd_long u

LEFT JOIN temp_gdp_long g 
    ON u.Iso3 = g.Iso3 AND u.Year = g.Year

LEFT JOIN temp_share_long s 
    ON u.Iso3 = s.Iso3 AND u.Year = s.Year
    
LEFT JOIN tiv_5y_share t 
    ON u.Iso3 = t.Country_Code AND u.Year = t.Year
    
LEFT JOIN human_hazard_trend h 
    ON u.Iso3 = h.Iso3 AND u.Year = h.INFORMYear
    
ORDER BY u.Iso3, u.Year;
"""

df_final = pd.read_sql(query, con=engine)
print("\n최종 통합 데이터 (2000~2025):")
print(df_final.head(15))


df_final.to_sql(name='integrate', con=engine, if_exists='replace', index=False)

with engine.connect() as conn:
    conn.execute(text("DROP TABLE IF EXISTS temp_usd_long;"))
    conn.execute(text("DROP TABLE IF EXISTS temp_gdp_long;"))
    conn.execute(text("DROP TABLE IF EXISTS temp_share_long;"))
    conn.commit()