"""색상, 글꼴, plotly 기본 템플릿 (import 시 한 번 등록)"""
import plotly.graph_objects as go
import plotly.io as pio


NAVY_DEEP = "#0B2545"

# 차트 글꼴 (화면 글꼴 Pretendard와 통일, 없으면 맑은 고딕)
CHART_FONT = (
    "Pretendard Variable, Pretendard, "
    "Malgun Gothic, AppleGothic, NanumGothic, sans-serif"
)

# 전 차트 공통 템플릿 : 연한 격자 · 회색 축 글자 · 투명 배경 · 흰 툴팁
# (샘플 대시보드처럼 차트가 카드 위에 가볍게 얹혀 보이도록)
_clean = go.layout.Template(pio.templates["plotly_white"])

_clean.layout.update(
    font=dict(family=CHART_FONT, size=12, color="#475569"),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    hoverlabel=dict(
        bgcolor="white",
        bordercolor="#E2E8F0",
        font=dict(family=CHART_FONT, size=12, color="#0F172A"),
    ),
    legend=dict(
        font=dict(size=12, color="#334155"),
        bgcolor="rgba(0,0,0,0)",
    ),
)

for _axis in ["xaxis", "yaxis"]:
    _clean.layout[_axis].update(
        gridcolor="#EEF2F6",
        zerolinecolor="#E2E8F0",
        linecolor="#E2E8F0",
        tickfont=dict(color="#64748B"),
        title=dict(font=dict(size=12, color="#64748B")),
    )

pio.templates["dash_clean"] = _clean
pio.templates.default = "dash_clean"
NAVY = "#13315C"
BLUE = "#1F6FEB"
PURPLE = "#6C5CE7"
ORANGE = "#E07A3F"
RED = "#D64545"

SIM_EDGE = ORANGE
BLUE_SCALE = ["#DCEBFB", "#5B9BE8", BLUE, NAVY_DEEP]
PURPLE_SCALE = ["#EAE6FA", "#A99BEC", PURPLE, "#2E2472"]

CORR_SCALE = [
    [0.0, "#B3423A"],
    [0.5, "#F5F8FC"],
    [1.0, NAVY],
]

MILEX_COLOR = ORANGE
BUBBLE_MIN = 6
BUBBLE_MAX = 46

BASE_LAYOUT = dict(
    template="dash_clean",
    font=dict(
        family=CHART_FONT,
        size=12,
    ),
    margin=dict(l=60, r=70, t=55, b=55),
    hovermode="closest",
)


def empty_figure(message, height=368):
    fig = go.Figure()

    fig.add_annotation(
        text=message,
        xref="paper",
        yref="paper",
        x=0.5,
        y=0.5,
        showarrow=False,
        font=dict(
            size=14,
            color="#7A8794",
        ),
    )

    fig.update_layout(
        xaxis=dict(visible=False, fixedrange=True),
        yaxis=dict(visible=False, fixedrange=True),
        height=height,
        dragmode=False,
        autosize=True,
        **BASE_LAYOUT,
    )

    return fig
