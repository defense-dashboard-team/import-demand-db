"""integrate_df의 원본-전처리-LEFT JOIN 순서를 유지해 Integrate_new를 1회 생성.

원본 DB: current_usd, gdp_calculated, share_gdp, tiv_5y_share,
         human_hazard_trend (기존 integrate 테이블은 읽지 않음)
전처리 (모든 원본에 병합 전 적용):
  - Kosovo: 잘못 지정된 SRB 국가코드를 XKX로 정규화
  - Yemen, North: 2000년 이후 분석 범위에서 제외
  - Iso3 / Year 통일, 국가·연도별 키 중복 및 값 충돌 검사
  - GDP는 gdp_calculated, 군사비/GDP는 share_gdp 원본에서 각각 추출
결합: integrate_df의 군사비 기준 SQL LEFT JOIN (Iso3 + Year)
결과: DB Integrate_new 테이블 + Integrate_new.csv, 기존 integrate 미변경

실행: db_connect.py 및 .env와 같은 폴더에서 python 01_Integrate_new.py
주의: 같은 이름의 DB 테이블은 교체됩니다. 실제 DB 원본 데이터는 별도로 확인하세요.
"""

from pathlib import Path
import re
import uuid
import warnings

import pandas as pd
from sqlalchemy import inspect, text


START_YEAR = 2000
END_YEAR = 2025
OUTPUT_TABLE = "Integrate_new"
OUTPUT_CSV = Path(__file__).resolve().parent / "Integrate_new.csv"
KEY = ["Iso3", "Year"]

# IndicatorScore와 human_hazard_score의 정의가 같은지 원본 자료에서 확인할 것.
# human_hazard_trend에 human_hazard_score가 없으면 integrate_df의 방식대로
# IndicatorScore를 human_hazard_score라는 출력 컬럼에 넣는다.
ALLOW_INDICATOR_FALLBACK = True

# 실제 파일에서 두 연도 컬럼이 동시에 발견되면 명시적으로 설정 가능
# 예: "Data_reference_year" 또는 "INFORMYear"
HAZARD_YEAR_COLUMN = None

MANUAL_ISO3 = {
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
    "Yemen": "YEM",
}

# 첫 번째 코드(integrate_new)의 최종 컬럼 구성과 순서
FINAL_COLUMNS = [
    "Country", "Iso3", "Year", "current_usd", "gdp_calculated",
    "TIV_5Y_Share", "TIV_5Y_Sum", "human_hazard_score", "share_gdp",
]


def standardize(raw):
    """컬럼명과 국가명/국가코드 표현 통일."""
    df = raw.copy()
    # 원본별 실제 컬럼 이름을 유지한다. (기존 df_share.columns = df_gdp.columns 오류 방지)
    df.columns = df.columns.map(lambda value: str(value).strip())
    if "Country" in df:
        df["Country"] = df["Country"].astype("string").str.strip()
        # 병합 전에 역사적 국가의 2000년 이후 불필요한 행을 제거한다.
        normalized = df["Country"].fillna("").map(
            lambda name: re.sub(r"[\s,._()\-]+", " ", str(name).casefold()).strip()
        )
        north_yemen = normalized.isin({"yemen north", "north yemen"})
        if north_yemen.any():
            print(f"[국가 정제] Yemen, North {int(north_yemen.sum())}행 제거")
            df = df.loc[~north_yemen].copy()
    for code_col in ("Iso3", "Country_Code"):
        if code_col in df:
            df[code_col] = df[code_col].astype("string").str.strip().str.upper()
            df[code_col] = df[code_col].replace({"": pd.NA, "NAN": pd.NA, "NONE": pd.NA})
            if "Country" in df:
                df.loc[df["Country"].str.casefold().eq("kosovo").fillna(False), code_col] = "XKX"
    return df


def make_country_map(*frames):
    """원본의 국가코드 및 integrate_new의 수동 매핑을 병합."""
    mapping = {}
    for df in frames:
        if df is None or "Country" not in df:
            continue
        col = "Iso3" if "Iso3" in df else "Country_Code" if "Country_Code" in df else None
        if col:
            for country, iso in df[["Country", col]].dropna().drop_duplicates().itertuples(index=False, name=None):
                country, iso = str(country).strip(), str(iso).strip().upper()
                if country in mapping and mapping[country] != iso:
                    warnings.warn(f"[국가코드] {country}: {mapping[country]}/{iso} 불일치. 최초 코드 사용")
                    continue
                mapping[country] = iso
    mapping.update(MANUAL_ISO3)
    return mapping


def ensure_iso3(df, mapping, source):
    df = standardize(df)
    if "Iso3" not in df:
        if "Country_Code" in df:
            df = df.rename(columns={"Country_Code": "Iso3"})
        else:
            df["Iso3"] = pd.Series(pd.NA, index=df.index, dtype="string")
    if "Country" in df:
        df["Iso3"] = df["Iso3"].fillna(df["Country"].map(mapping))
        df.loc[df["Country"].str.casefold().eq("kosovo").fillna(False), "Iso3"] = "XKX"
    # 빈 코드 및 알려진 비국가 행은 결측 키로 남겨 병합 대상에서 제외
    missing = df["Iso3"].isna()
    if missing.any():
        country_list = df.loc[missing, "Country"].dropna().unique().tolist() if "Country" in df else []
        warnings.warn(f"[{source}] Iso3 없는 {missing.sum()}행 제외: {country_list[:12]}")
    return df.loc[~missing].copy()


def ensure_year(df, column, source):
    if column not in df:
        raise ValueError(f"[{source}] 연도 컬럼 '{column}'이 없습니다.")
    df = df.copy()
    year = pd.to_numeric(df[column], errors="coerce")
    in_range = year.between(START_YEAR, END_YEAR) & year.mod(1).eq(0)
    skipped = int((~in_range).sum())
    if skipped:
        print(f"[{source}] 기간 밖이거나 연도가 잘못된 행 {skipped}개 제외")
    df = df.loc[in_range].copy()
    df["Year"] = year.loc[in_range].astype(int)
    return df


def numeric_values(df, columns):
    for col in columns:
        df[col] = pd.to_numeric(
            df[col].astype("string").str.replace(",", "", regex=False), errors="coerce"
        )
    return df


def require_unique(df, name, measure_columns):
    """완전 중복은 정리하되, 서로 다른 실제 측정값을 가진 키는 오류로 표시."""
    if df.empty:
        raise ValueError(f"[{name}] 유효한 데이터가 없습니다.")
    duplicate = df.duplicated(KEY, keep=False)
    if not duplicate.any():
        return df
    for col in measure_columns:
        conflicting = df.groupby(KEY, dropna=False)[col].nunique(dropna=True)
        keys = conflicting[conflicting > 1]
        if not keys.empty:
            raise ValueError(
                f"[{name}] 같은 Iso3·Year에 서로 다른 {col} 값이 있습니다: "
                f"{list(keys.index[:8])}"
            )
    def first_non_null(s):
        s = s.dropna()
        return s.iloc[0] if not s.empty else None
    result = df.groupby(KEY, as_index=False).agg(
        {col: first_non_null for col in df.columns if col not in KEY}
    )
    print(f"[{name}] 동일 키 중복 {duplicate.sum()}행 → {len(result)}행 정리")
    return result


def reshape_wide(raw, value_name, mapping, source):
    """integrate_df의 melt 형식을 유지하며 국가코드가 없는 원본도 지원."""
    df = standardize(raw)
    if "Year" in df and value_name in df:
        long_df = df.copy()  # 이미 세로형인 원본
    else:
        target_years = [str(y) for y in range(START_YEAR, END_YEAR + 1)]
        available = [y for y in target_years if y in df]
        if not available:
            raise ValueError(f"[{source}] {START_YEAR}~{END_YEAR} 연도 컬럼이 없습니다.")
        if len(available) < len(target_years):
            warnings.warn(f"[{source}] 없는 연도 컬럼: {sorted(set(target_years) - set(available))}")
        ids = [col for col in ("Iso3", "Country", "Country_Code") if col in df]
        if not ids:
            raise ValueError(f"[{source}] 국가명·국가코드 컬럼이 없습니다.")
        long_df = df.melt(id_vars=ids, value_vars=available,
                          var_name="Year", value_name=value_name)
    long_df = ensure_iso3(long_df, mapping, source)
    long_df = ensure_year(long_df, "Year", source)
    long_df = numeric_values(long_df, [value_name])
    # GDP와 share_gdp는 각 원본 테이블에서 별도 추출: 위치 기반 컬럼 대입 금지.
    if value_name == "share_gdp" and long_df[value_name].gt(100).any():
        offenders = long_df.loc[long_df[value_name].gt(100), KEY + [value_name]].head(5)
        raise ValueError(
            "[share_gdp] 100%를 초과한 값이 존재합니다. GDP와 열이 바뀌었는지 "
            f"원본 테이블을 확인하세요:\n{offenders.to_string(index=False)}"
        )
    if value_name == "gdp_calculated" and long_df[value_name].lt(0).any():
        raise ValueError("[gdp_calculated] 음수 GDP를 발견했습니다. 원본을 확인하세요.")
    columns = KEY + (["Country"] if "Country" in long_df else []) + [value_name]
    return require_unique(long_df[columns], source, [value_name])


def prepare_tiv(raw, mapping):
    df = ensure_iso3(raw, mapping, "TIV")
    expected = ["Year", "TIV_5Y_Sum", "TIV_5Y_Share"]
    missing = [col for col in expected if col not in df]
    if missing:
        raise ValueError(f"[TIV] 컬럼 누락: {missing}")
    df = ensure_year(df, "Year", "TIV")
    df = numeric_values(df, ["TIV_5Y_Sum", "TIV_5Y_Share"])
    fields = KEY + ["TIV_5Y_Sum", "TIV_5Y_Share"]
    return require_unique(df[fields], "TIV", fields[2:])


def prepare_hazard(raw, mapping):
    df = ensure_iso3(raw, mapping, "분쟁위험도")
    candidates = [c for c in ("Data_reference_year", "INFORMYear", "Year") if c in df]
    if HAZARD_YEAR_COLUMN:
        if HAZARD_YEAR_COLUMN not in candidates:
            raise ValueError(f"[분쟁위험도] 지정한 연도 컬럼이 없습니다: {HAZARD_YEAR_COLUMN}")
        year_col = HAZARD_YEAR_COLUMN
    elif not candidates:
        raise ValueError("[분쟁위험도] Data_reference_year / INFORMYear / Year가 없습니다.")
    else:
        year_col = candidates[0]
        if len(candidates) > 1:
            other = candidates[1]
            different = (
                pd.to_numeric(df[year_col], errors="coerce")
                != pd.to_numeric(df[other], errors="coerce")
            ) & df[year_col].notna() & df[other].notna()
            if different.any():
                warnings.warn(f"[분쟁위험도] {year_col}와 {other}가 다른 "
                              f"{int(different.sum())}행 발견. {year_col} 사용")
    df = ensure_year(df, year_col, "분쟁위험도")
    if "human_hazard_score" in df:
        score_col = "human_hazard_score"
    elif "IndicatorScore" in df and ALLOW_INDICATOR_FALLBACK:
        score_col = "IndicatorScore"
        warnings.warn(
            "[분쟁위험도] IndicatorScore를 human_hazard_score 컬럼으로 저장합니다. "
            "두 지표의 정의가 같은지 원본 데이터를 확인하세요."
        )
    else:
        raise ValueError("[분쟁위험도] human_hazard_score가 없습니다. "
                         "IndicatorScore 대체 허용 여부를 확인하세요.")
    df = numeric_values(df, [score_col])
    df = df[KEY + [score_col]].rename(columns={score_col: "human_hazard_score"})
    print(f"[분쟁위험도] 사용 연도: {year_col}; 사용 지표: {score_col}")
    return require_unique(df, "분쟁위험도", ["human_hazard_score"])


def prepare_sources(usd, gdp, tiv, hazard, share=None):
    """다섯 개 원본을 정규화하되 병합 결과는 별도 저장하지 않는다."""
    raw_list = [standardize(x) for x in (usd, gdp, tiv, hazard)]
    raw_share = standardize(share) if share is not None else None
    mapping = make_country_map(*raw_list, raw_share)
    usd_long = reshape_wide(usd, "current_usd", mapping, "군사비")
    gdp_long = reshape_wide(gdp, "gdp_calculated", mapping, "GDP")
    tiv_clean = prepare_tiv(tiv, mapping)
    hazard_clean = prepare_hazard(hazard, mapping)
    if share is None:
        raise ValueError("[share_gdp] 필수 테이블이 없습니다. GDP 대비 군사비를 누락하지 않습니다.")
    share_long = reshape_wide(share, "share_gdp", mapping, "군사비/GDP")
    # SQL JOIN을 위한 임시 테이블에는 중복 이름 컬럼 Country를 넣지 않음
    if "Country" not in usd_long:
        raise ValueError("[current_usd] 기준 테이블에 국가명 Country 컬럼이 없습니다.")
    gdp_long = gdp_long[KEY + ["gdp_calculated"]]
    share_long = share_long[KEY + ["share_gdp"]]
    return usd_long, gdp_long, share_long, tiv_clean, hazard_clean


def validate_integrate_new(df):
    if df.empty:
        raise ValueError("[최종 검증] 최종 데이터에 행이 없습니다.")
    if df.duplicated(KEY).any():
        raise ValueError("[최종 검증] Iso3·Year 중복이 발생했습니다.")
    if not df["Year"].between(START_YEAR, END_YEAR).all():
        raise ValueError("[최종 검증] 2000~2025 외 연도가 포함됐습니다.")
    print("\n[최종 결과]")
    print("행/열:", df.shape, "| 국가 수:", df["Iso3"].nunique(),
          "| 연도:", df["Year"].min(), "~", df["Year"].max())
    print("Iso3·Year 중복:", int(df.duplicated(KEY).sum()))
    if df.loc[df["Country"].str.casefold().eq("kosovo").fillna(False), "Iso3"].ne("XKX").any():
        raise ValueError("[최종 검증] Kosovo 국가코드가 XKX가 아닙니다.")
    excluded = df["Country"].fillna("").map(
        lambda v: re.sub(r"[\s,._()\-]+", " ", str(v).casefold()).strip()
    ).isin({"yemen north", "north yemen"})
    if excluded.any():
        raise ValueError("[최종 검증] Yemen, North 행이 남아 있습니다.")
    print("\n[주요 지표 결측치]\n" + df[FINAL_COLUMNS[3:]].isna().sum().to_string())
    print("\n[미리보기]\n", df.head(10).to_string(index=False))


def execute_df_flow(engine, usd, gdp, tiv, hazard, share=None, save=True):
    """integrate_df와 동일하게 임시 테이블 + SQL LEFT JOIN으로 결합."""
    usd_long, gdp_long, share_long, tiv_clean, hazard_clean = prepare_sources(
        usd, gdp, tiv, hazard, share
    )
    suffix = uuid.uuid4().hex[:10]
    temp_names = {
        "u": f"tmp_integrate_usd_{suffix}",
        "g": f"tmp_integrate_gdp_{suffix}",
        "s": f"tmp_integrate_share_{suffix}",
        "t": f"tmp_integrate_tiv_{suffix}",
        "h": f"tmp_integrate_hazard_{suffix}",
    }
    created = []
    try:
        for key, data in zip(("u", "g", "s", "t", "h"),
                             (usd_long, gdp_long, share_long, tiv_clean, hazard_clean)):
            data.to_sql(temp_names[key], con=engine, if_exists="fail", index=False,
                        chunksize=2000)
            created.append(temp_names[key])
        # 국가코드·Yemen 정제 및 지표 이름 고정 후 SQL LEFT JOIN (integrate_df의 본류)
        sql = f"""
            SELECT
                u.Country, u.Iso3, u.Year, u.current_usd,
                g.gdp_calculated, t.TIV_5Y_Share, t.TIV_5Y_Sum,
                h.human_hazard_score, s.share_gdp
            FROM `{temp_names['u']}` u
            LEFT JOIN `{temp_names['g']}` g
                ON u.Iso3 = g.Iso3 AND u.Year = g.Year
            LEFT JOIN `{temp_names['s']}` s
                ON u.Iso3 = s.Iso3 AND u.Year = s.Year
            LEFT JOIN `{temp_names['t']}` t
                ON u.Iso3 = t.Iso3 AND u.Year = t.Year
            LEFT JOIN `{temp_names['h']}` h
                ON u.Iso3 = h.Iso3 AND u.Year = h.Year
            ORDER BY u.Country, u.Year, u.Iso3
        """
        with engine.connect() as conn:
            integrate_new = pd.read_sql(text(sql), con=conn)
    finally:
        # 실패 시에도 자기 실행에서 생성한 임시 테이블만 삭제
        with engine.begin() as conn:
            for table_name in created:
                conn.execute(text(f"DROP TABLE IF EXISTS `{table_name}`"))

    integrate_new = integrate_new[FINAL_COLUMNS]
    validate_integrate_new(integrate_new)
    if save:
        # 원본 integrate는 사용하거나 덮어쓰지 않고 최종 Integrate_new만 저장.
        integrate_new.to_sql(OUTPUT_TABLE, con=engine, if_exists="replace", index=False,
                             chunksize=2000, method="multi")
        integrate_new.to_csv(OUTPUT_CSV, index=False, encoding="utf-8-sig")
        print(f"\n[저장 완료] DB: {OUTPUT_TABLE} / CSV: {OUTPUT_CSV}")
    return integrate_new


def main():
    from db_connect import get_engine
    engine = get_engine()
    required = ["current_usd", "gdp_calculated", "share_gdp", "tiv_5y_share", "human_hazard_trend"]
    existing = set(inspect(engine).get_table_names())
    missing = sorted(set(required) - existing)
    if missing:
        raise RuntimeError(f"DB에 필요한 테이블이 없습니다: {missing}")
    with engine.connect() as conn:
        sources = {name: pd.read_sql(text(f"SELECT * FROM `{name}`"), con=conn)
                   for name in required}
        share = sources["share_gdp"]
    execute_df_flow(
        engine,
        usd=sources["current_usd"],
        gdp=sources["gdp_calculated"],
        tiv=sources["tiv_5y_share"],
        hazard=sources["human_hazard_trend"],
        share=share,
    )


if __name__ == "__main__":
    main()
