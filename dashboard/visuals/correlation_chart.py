"""지표 간 상관계수 히트맵"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from dashboard.common.config import CORR_VARS
from dashboard.visuals.theme import CHART_FONT, CORR_SCALE, empty_figure


try:
    from scipy import stats as scipy_stats
    HAS_SCIPY = True
except Exception:               # scipy 미설치 환경에서도 동작
    scipy_stats = None
    HAS_SCIPY = False


def make_corr_heatmap(
    data,
    year,
    method="spearman",
    height=430,
):
    d = data[data["Year"] == year]

    frame = {}
    labels = []

    for label, col, is_skewed in CORR_VARS:
        if col not in d.columns:
            continue

        s = pd.to_numeric(d[col], errors="coerce")

        if s.notna().sum() < 10:
            continue

        if method == "pearson" and is_skewed:
            s = np.log10(s.where(s > 0))
            label = f"{label} (로그)"

        frame[label] = s
        labels.append(label)

    if len(labels) < 2:
        return empty_figure(
            f"{year}년에는 상관분석에 쓸 지표가 부족합니다.",
            height=height,
        ), 0

    mat = pd.DataFrame(frame)
    n = int(mat.dropna().shape[0])

    size = len(labels)

    corr_values = np.full((size, size), np.nan)
    p_values = np.full((size, size), np.nan)
    n_values = np.zeros((size, size), dtype=int)

    # 지표마다 결측 구간이 달라 쌍(pair)별로 따로 계산합니다.
    for i in range(size):
        for j in range(size):

            a = mat[labels[i]]
            b = mat[labels[j]]

            ok = a.notna() & b.notna()
            pair_n = int(ok.sum())
            n_values[i, j] = pair_n

            if pair_n < 3:
                continue

            if HAS_SCIPY:
                if method == "spearman":
                    r, p = scipy_stats.spearmanr(a[ok], b[ok])
                else:
                    r, p = scipy_stats.pearsonr(a[ok], b[ok])
            else:
                r = a[ok].corr(b[ok], method=method)
                p = np.nan

            corr_values[i, j] = r
            p_values[i, j] = p

    def star_mark(p_value):
        if p_value is None or pd.isna(p_value):
            return ""
        if p_value < 0.001:
            return "***"
        if p_value < 0.01:
            return "**"
        if p_value < 0.05:
            return "*"
        return ""

    NBSP = " "

    cell_text = []
    custom = []

    for i in range(size):

        text_row = []
        custom_row = []

        for j in range(size):

            r = corr_values[i, j]

            # 모든 칸을 '빈 줄 / 숫자 / 별표' 3줄로 써서
            # 별표 유무와 상관없이 숫자가 칸 가운데에 오게 합니다.
            if pd.isna(r):
                text_row.append(f"{NBSP}<br>-<br>{NBSP}")
                custom_row.append(["-", str(n_values[i, j])])
                continue

            mark = "" if i == j else star_mark(p_values[i, j])
            text_row.append(
                f"{NBSP}<br>{r:.2f}<br>{mark or NBSP}"
            )

            p = p_values[i, j]

            custom_row.append([
                "-" if pd.isna(p) else (
                    "<0.001" if p < 0.001 else f"{p:.3f}"
                ),
                str(n_values[i, j]),
            ])

        cell_text.append(text_row)
        custom.append(custom_row)

    corr = pd.DataFrame(corr_values, index=labels, columns=labels)

    fig = go.Figure(
        go.Heatmap(
            z=corr_values,
            x=labels,
            y=labels,
            zmin=-1,
            zmax=1,
            zmid=0,
            colorscale=CORR_SCALE,
            text=cell_text,
            texttemplate="%{text}",
            textfont=dict(size=13),
            customdata=custom,
            hovertemplate=(
                "%{y} ↔ %{x}<br>"
                "상관계수 %{z:.2f}<br>"
                "p = %{customdata[0]}<br>"
                "n = %{customdata[1]}"
                "<extra></extra>"
            ),
            colorbar=dict(
                thickness=12,
                len=0.8,
                tickvals=[-1, -0.5, 0, 0.5, 1],
            ),
        )
    )

    fig.update_yaxes(
        autorange="reversed",
        fixedrange=True,
        automargin=True,
        tickfont=dict(size=11),
    )

    fig.update_xaxes(
        fixedrange=True,
        automargin=True,
        tickangle=-18,
        side="bottom",
        tickfont=dict(size=10),
    )

    # 제목은 패널 헤더(HTML)에서 한 번만 표시합니다.
    fig.update_layout(
        height=height,
        dragmode=False,
        margin=dict(l=62, r=48, t=16, b=62),
        template="dash_clean",
        font=dict(
            family=CHART_FONT,
            size=12,
        ),
        hovermode="closest",
    )

    return fig, n
