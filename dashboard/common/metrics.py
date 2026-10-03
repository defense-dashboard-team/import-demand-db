"""차트별 지표 설정 (라벨, 색, 축 눈금)"""
from dashboard.visuals.theme import BLUE, BLUE_SCALE, ORANGE, PURPLE, PURPLE_SCALE


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


# 상단 연도는 기존 공통 연도 선택기와 공유합니다.
# 별도의 예측/임의 가중치 점수를 만들지 않습니다. 우선순위가 높은
# 지표부터 차례대로 정렬하고, 사용자가 설정한 구간을 모두 만족하는
# 국가 중 최대 5개를 표시합니다.
P4_INDICATORS = {
    "GDP": {"column": "gdp_calculated", "scale": 1000.0,
             "unit": "10억 USD", "precision": 1},
    "군사비": {"column": "current_usd", "scale": 1000.0,
               "unit": "10억 USD", "precision": 1},
    "분쟁위험도": {"column": "human_hazard_score", "scale": 1.0,
                  "unit": "점", "precision": 2},
    "무기 수입 점유율": {"column": "TIV_5Y_Share", "scale": 1.0,
                         "unit": "% (5년)", "precision": 3},
}
P4_DEFAULT_PRIORITY = ["GDP", "군사비", "무기 수입 점유율", "분쟁위험도"]
P4_MUTED_COLORS = ["#96A8BC", "#8FAFAD", "#B09EBC", "#BEAFA0", "#96A6AD"]
