"""바뀌지 않는 설정값 (경로, 페이지 제목, 컬럼 이름 등)"""
from pathlib import Path


# app_copy.py가 있는 폴더 (CSV 대체 파일도 이 폴더 기준으로 찾음)
APP_DIR = Path(__file__).resolve().parents[2]
ASSETS_DIR = APP_DIR / "dashboard" / "assets"


DATA_PATH = "Integrate_new.csv"


TOP_PANEL_HEIGHT = 540
BOTTOM_PANEL_HEIGHT = 445


COUNTRY_NONE = "__none__"
COUNTRY_NONE_LABEL = "— 선택 안 함 —"

COUNTRY_DISPLAY_FIX = {
    "Korea, South": "South Korea",
    "Korea, North": "North Korea",
    "Congo, DR": "DR Congo",
    "Congo, Republic": "Republic of the Congo",
    "Gambia, The": "The Gambia",
}


# babel 한글 국가명이 없거나 어색한 경우 직접 지정 (ISO3 기준)
KOREAN_NAME_FIX = {
    "XKX": "코소보",
}


DASH_TITLE = "무기 수출 유망국 탐색 지원"
# 부제목은 원본 전투기 배너에만 표시하고 사이드바에는 출력하지 않습니다.
DASH_SUBTITLE = "GDP · 군사비 · 분쟁위험도 · 무기수입점유율을 기반으로"

# {country} 자리에는 현재 선택 국가(표시용 이름)가 들어갑니다.
PAGE_ORDER = ["page1", "page3", "page4"]

PAGE_TITLES = {
    "page1": "전 세계 지표별 분포",
    "page2": "{country} 핵심 지표별 시계열 추이",
    "page3": "지표간 상관분석을 통한 수출 대상국 탐색",
    "page4": "조건별 무기 수출 대상국 탐색",
}

PAGE_NAV_LABELS = {
    "page1": "🌍  전 세계 지표별 분포",
    "page2": "📈  국가별 추이",
    "page3": "🔎  상관분석",
    "page4": "🎯  조건별 대상국 탐색",
}

# 연도 선택을 사용하는 페이지
PAGE_USES_YEAR = {
    "page1": True,
    "page2": True,
    "page3": True,
    "page4": True,
}

# 사이드바를 표시하는 페이지 (1페이지는 화면 안에 연도 선택과 이동 버튼이 있음)
PAGE_SHOWS_SIDEBAR = {
    "page1": True,
    "page2": True,
    "page3": True,
    "page4": True,
}


RISK_START = 2017

X_COL = "share_gdp_pct"
SIZE_COL = "gdp_calculated"
MILEX_COL = "current_usd"


SIM_TOP_N = 5

CORR_VARS = [
    ("GDP", "gdp_calculated", True),
    ("군사비", "current_usd", True),
    ("군사비/GDP", X_COL, False),
    ("무기수입 점유율", "TIV_5Y_Share", True),
    ("분쟁 위험도", "human_hazard_score", False),
]
