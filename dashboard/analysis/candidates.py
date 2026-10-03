"""지표 구간으로 후보국을 거르고 우선순위대로 정렬 (조건별 대상국 탐색 화면)."""
import pandas as pd

from dashboard.metrics import P4_INDICATORS
from dashboard.utils.formatting import money_format


def p4_pct_col(label):
    return f"pct_{P4_INDICATORS[label]['column']}"


def p4_value_text(label, value):
    """국가 카드·슬라이더 안내에 표시할 값 (원자료 GDP·군사비는 백만 USD)."""
    if value is None or pd.isna(value):
        return "자료 없음"
    kind = P4_INDICATORS[label]["kind"]
    if kind == "money":
        return money_format(float(value) * 1_000_000)
    if kind == "share":
        return f"{float(value):.2f}%"
    return f"{float(value):.1f}점"


def p4_candidate_pool(source, chosen_year):
    """선택 연도의 국가별 값과 지표별 백분위(0~100, 100 = 가장 큰 값)."""
    columns = [spec["column"] for spec in P4_INDICATORS.values()]
    data = source.loc[
        source["Year"] == int(chosen_year), ["Country", "Iso3"] + columns
    ].copy()
    data = data.dropna(subset=["Country", "Iso3"])
    data = data.drop_duplicates(subset=["Iso3"], keep="first")
    for label, spec in P4_INDICATORS.items():
        col = spec["column"]
        data[col] = pd.to_numeric(data[col], errors="coerce")
        data[p4_pct_col(label)] = data[col].rank(pct=True, method="average") * 100
    return data


def p4_sort_candidates(pool, priorities, directions, top_n=5):
    """조건을 통과한 국가를 우선순위 지표 값으로 차례 정렬해 상위 최대 N개를 돌려줍니다."""
    total = len(pool)
    if not priorities or pool.empty:
        return pool.iloc[:0].copy(), 0
    pool = pool.sort_values(
        [P4_INDICATORS[label]["column"] for label in priorities] + ["Country"],
        ascending=[directions[label] == "오름차순" for label in priorities] + [True],
        kind="mergesort",
    )
    return pool.head(top_n).reset_index(drop=True), total
