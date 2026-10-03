"""유사 국가, 추세 구간, 조건별 후보 추출 계산"""
import numpy as np
import pandas as pd

from dashboard.common.config import SIM_TOP_N, SIZE_COL, X_COL
from dashboard.common.metrics import P4_INDICATORS, PAGE2_METRIC, TREND_METRICS


def similarity_axes(d, metric):
    """버블차트 화면에 보이는 좌표(로그축 반영)를 그대로 거리 계산에 사용"""
    m = PAGE2_METRIC[metric]

    fx = np.log10(d[X_COL].clip(lower=0.01))

    if m["log_y"]:
        fy = np.log10(d[m["col"]].clip(lower=0.004))
    else:
        fy = d[m["col"]].astype(float)

    return fx, fy


def find_similar_countries(
    data,
    year,
    metric,
    iso,
    top_n=SIM_TOP_N,
):
    """
    유사도 정의
    ------------------------------------------------
    1) 비교 축 3개
       - log10(GDP 대비 군사비) : 버블차트 x축
       - 기준지표                : 버블차트 y축
                                  (TIV는 log10)
       - log10(GDP)             : 국가 체급
         * 버블 크기 라디오와 무관하게 GDP 고정
    2) 각 축을 그 해 전체 국가 기준 z-표준화
       -> 단위가 다른 축을 같은 저울에 올림
       -> 거리 1 = 표준편차 1개만큼 떨어짐
    3) 표준화 유클리드 거리 d 계산
    4) 축 개수로 정규화 : d / sqrt(축 개수)
       -> 축 하나당 평균 거리로 환산
       -> 축을 몇 개 쓰든 눈금이 같아짐
    5) 유사도 = 100 * exp(-정규화 거리)
       -> 거리 0이면 100, 멀수록 지수적으로 감쇠
       -> 절대 기준이라 국가·연도 간 비교 가능
       -> 지수 감쇠는 표시용 변환이며
          순위는 거리 d 그대로임
    """
    m = PAGE2_METRIC[metric]
    other = "tiv" if metric == "risk" else "risk"
    o = PAGE2_METRIC[other]

    need = [X_COL, m["col"], SIZE_COL]

    d = data[data["Year"] == year].dropna(
        subset=need
    )
    d = d[
        (d[X_COL] > 0)
        & (d[SIZE_COL] > 0)
    ].copy()

    if d.empty or iso not in set(d["Iso3"]):
        return None, other

    fx, fy = similarity_axes(d, metric)
    fz = np.log10(d[SIZE_COL])

    axes = []

    for f in (fx, fy, fz):
        sd = f.std(ddof=0) or 1.0
        axes.append((f - f.mean()) / sd)

    pos = d.index[d["Iso3"] == iso][0]
    base = [a.loc[pos] for a in axes]

    d["_dist"] = np.sqrt(
        sum(
            (a - b) ** 2
            for a, b in zip(axes, base)
        )
    )

    d["유사도"] = 100 * np.exp(
        -d["_dist"] / np.sqrt(len(axes))
    )

    out = (
        d[d["Iso3"] != iso]
        .nsmallest(top_n, "_dist")
        .copy()
    )

    out.insert(0, "순위", range(1, len(out) + 1))

    # 맨 위에 기준 국가(선택 국가) 행을 붙입니다. 순위 0 = 기준 행.
    self_row = d[d["Iso3"] == iso].copy()
    self_row["유사도"] = 100.0
    self_row.insert(0, "순위", 0)

    out = pd.concat([self_row, out], ignore_index=True)

    cols = [
        "순위",
        "Country",
        "Iso3",
        "유사도",
        "_dist",
        X_COL,
        m["col"],
        o["col"],
    ]

    return out[cols], other


def trend_slice(data, iso, metric):
    """
    선택 국가 · 선택 지표에서 값이 존재하는 구간만 잘라 돌려줍니다.
    지표마다 데이터 시작 연도가 달라 x축 범위를 각각 계산합니다.
    """
    setting = TREND_METRICS[metric]

    d = data[data["Iso3"] == iso].sort_values("Year")

    if d.empty:
        return None, None, None

    col = setting["col"]

    if col not in d.columns:
        return None, None, None

    valid = d[d[col].notna()]

    if valid.empty:
        return None, None, None

    y0 = int(valid["Year"].min())
    y1 = int(valid["Year"].max())

    d = d[(d["Year"] >= y0) & (d["Year"] <= y1)]

    return d, y0, y1


def trend_year_span(data, iso, metric):
    _, y0, y1 = trend_slice(data, iso, metric)

    if y0 is None:
        return ""

    return f"{y0}–{y1}"


def p4_candidate_pool(source, chosen_year):
    """선택 연도의 국가별 실제 값을 사용하고 비국가·중복 코드를 방지합니다."""
    current_data = source.loc[
        source["Year"] == int(chosen_year),
        ["Country", "Iso3"] + [v["column"] for v in P4_INDICATORS.values()],
    ].copy()
    for label, setting in P4_INDICATORS.items():
        col = setting["column"]
        current_data[col] = pd.to_numeric(current_data[col], errors="coerce")
    current_data = current_data.dropna(subset=["Country", "Iso3"])
    return current_data.drop_duplicates(subset=["Iso3"], keep="first")


def p4_filter_candidates(source_year, priorities, ranges, directions, top_n=5):
    """조건 교집합 필터 → 사용자 우선순위별 순차 정렬 → 상위 최대 N개."""
    if not priorities or source_year.empty:
        return source_year.iloc[:0].copy(), 0
    working = source_year.copy()
    for label in priorities:
        setting = P4_INDICATORS[label]
        col = setting["column"]
        scale = setting["scale"]
        low, high = ranges[label]
        working = working.loc[
            working[col].notna()
            & (working[col] / scale >= low - 1e-8)
            & (working[col] / scale <= high + 1e-8)
        ]
    total = len(working)
    if working.empty:
        return working, 0
    working = working.sort_values(
        by=[P4_INDICATORS[label]["column"] for label in priorities]
        + ["Country"],
        ascending=[directions[label] == "낮은 값 우선" for label in priorities]
        + [True],
        kind="mergesort",
    )
    return working.head(top_n).reset_index(drop=True), total
