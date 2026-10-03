"""지표별 설정 (컬럼, 라벨, 색, 축 눈금). 차트와 화면이 같이 씀."""
from dashboard.charts.theme import BLUE, BLUE_SCALE, ORANGE, PURPLE, PURPLE_SCALE
from dashboard.config import X_COL


# 11. 2페이지 설정
# =========================================================

PAGE2_METRIC = {
    "risk": {
        "col":
            "human_hazard_score",
        "label":
            "분쟁위험도",
        "color":
            PURPLE,
            # "#C1663B",
        "scale":
            PURPLE_SCALE,
            # "OrRd",
        "fmt":
            ".1f",
        "log_y":
            False,
        "log_color":
            False,
        "yticks":
            None,
        "ytext":
            None,
    },
    "tiv": {
        "col":
            "TIV_5Y_Share",
        "label":
            "무기수입 점유율 (5년, %)",
        "color":
            BLUE,
            # "#2C7A5A",
        "scale":
            BLUE_SCALE,
            # "BuGn",
        "fmt":
            ".3f",
        "log_y":
            True,
        "log_color":
            True,
        "yticks":
            [
                0.004,
                0.01,
                0.03,
                0.1,
                0.3,
                1,
                3,
                10,
            ],
        "ytext":
            [
                "0",
                "0.01",
                "0.03",
                "0.1",
                "0.3",
                "1",
                "3",
                "10",
            ],
    },
}

SIM_TOP_N = 5

CORR_VARS = [
    ("GDP", "gdp_calculated", True),
    ("군사비", "current_usd", True),
    ("군사비/GDP", X_COL, False),
    ("무기수입 점유율", "TIV_5Y_Share", True),
    ("분쟁 위험도", "human_hazard_score", False),
]


# =========================================================
# 11-B. 2페이지(국가별 지표 추이) 설정
# =========================================================

TREND_ORDER = ["milex", "gdp", "tiv", "risk"]

TREND_METRICS = {
    "milex": {
        "label": "군사비 · 군사비/GDP",
        "short": "군사비 · 군사비/GDP",
        "kind": "bar_line",
        "col": "current_usd",
        "sub_col": "share_gdp_pct",
        "color": "#4C74B5",  # 군사비 막대 : 너무 진하지 않은 남청색
        "accent": ORANGE,
        "y_title": "군사비 (백만 USD)",
        "y2_title": "군사비/GDP (%)",
        "note": "막대: 군사비 · 선: GDP 대비 군사비(%)",
    },
    "gdp": {
        "label": "GDP",
        "short": "GDP",
        "kind": "bar",
        "col": "gdp_calculated",
        "sub_col": None,
        "color": BLUE,
        "accent": None,
        "y_title": "GDP (백만 USD)",
        "y2_title": None,
        "note": "국가 경제 규모",
    },
    "tiv": {
        "label": "무기수입 점유율 (5년 누적)",
        "short": "무기수입 점유율",
        "kind": "line",
        "col": "TIV_5Y_Share",
        "sub_col": None,
        "color": "#2E7DD1",
        "accent": None,
        "y_title": "무기수입 점유율 (5년, %)",
        "y2_title": None,
        "note": "최근 5년 누적 무기 수입의 세계 대비 비중",
    },
    "risk": {
        "label": "분쟁위험도",
        "short": "분쟁위험도",
        "kind": "line",
        "col": "human_hazard_score",
        "sub_col": None,
        "color": PURPLE,
        "accent": None,
        "y_title": "분쟁위험도 (0~10)",
        "y2_title": None,
        "note": "INFORM 인적 위험 점수 (0~10)",
    },
}


# ============================================================
# 3번째 메뉴 · 조건별 무기 수출 대상국 탐색
# ============================================================
# 상단 연도는 공통 연도 선택기와 공유합니다.
# 가중치 점수는 만들지 않습니다.
#  1) 지표별 구간(백분위 또는 실제 값)으로 국가를 거르고
#  2) 우선순위 지표 값으로 1순위부터 차례로 정렬합니다.
P4_INDICATORS = {
    "무기 수입 점유율": {"column": "TIV_5Y_Share", "kind": "share"},
    "군사비": {"column": "current_usd", "kind": "money"},
    "GDP": {"column": "gdp_calculated", "kind": "money"},
    "분쟁위험도": {"column": "human_hazard_score", "kind": "score"},
}
P4_DEFAULT_PRIORITY = ["무기 수입 점유율", "군사비", "GDP", "분쟁위험도"]
P4_DIRECTIONS = ["내림차순", "오름차순"]
P4_RANGE_MODES = ["백분위", "실제 값"]
# 실제 값 입력 단위 (GDP·군사비 원자료는 백만 USD → 10억 USD로 입력)
P4_INPUT_UNITS = {"money": ("10억 USD", 1000.0), "share": ("%", 1.0), "score": ("점", 1.0)}
# 추출 국가 순서대로 고정 색을 줍니다. 국가 카드의 점 색과 같습니다.
P4_COUNTRY_COLORS = ["#2563EB", "#F59E0B", "#10B981", "#8B5CF6", "#64748B"]
