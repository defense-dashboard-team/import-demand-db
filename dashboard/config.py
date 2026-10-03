"""대시보드 전체에서 쓰는 고정 설정 (경로, 페이지 제목·메뉴, 컬럼 이름, 기준 연도)."""
from pathlib import Path


# 저장소 루트 (app.py가 있는 폴더)
ROOT_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = Path(__file__).resolve().parent / "assets"

# DB에 연결하지 못할 때 대신 읽는 CSV
DATA_PATH = "Integrate_new.csv"

TOP_PANEL_HEIGHT = 540
BOTTOM_PANEL_HEIGHT = 445


# 상단 국가 선택 상자의 '선택 안 함' 항목
COUNTRY_NONE = "__none__"
COUNTRY_NONE_LABEL = "— 선택 안 함 —"


# ============================================================
# 4-0. 대제목 / 페이지 제목
# ============================================================

DASH_TITLE = "무기 수출 유망국 탐색 지원"
# 부제목은 원본 전투기 배너에만 표시하고 사이드바에는 출력하지 않습니다.
DASH_SUBTITLE = "GDP · 군사비 · 분쟁위험도 · 무기수입점유율을 기반으로"

# {country} 자리에는 현재 선택 국가(표시용 이름)가 들어갑니다.
PAGE_ORDER = ["page1", "page3", "page4"]

PAGE_TITLES = {
    "page1": "전 세계 지표별 분포",
    "page2": "{country} 핵심 지표별 시계열 추이",
    "page3": "상관 지표별 국가 특성 및 유사도 분석",
    "page4": "조건별 무기 수출 대상국 탐색 지원",
}

PAGE_NAV_LABELS = {
    "page1": "🌍  전 세계 지표별 분포",
    "page2": "📈  국가별 추이",
    "page3": "🔎  국가 특성 및 유사 국가",
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


# 분쟁위험도(INFORM)가 제공되기 시작한 해
RISK_START = 2017

# 버블차트 가로축 / 버블 크기 / 군사비 컬럼

X_COL = "share_gdp_pct"
SIZE_COL = "gdp_calculated"
MILEX_COL = "current_usd"


# 1페이지 전세계 화면이 쓰는 integrate 원본 컬럼
COUNTRY_COL = "Country"
ISO_COL = "Iso3"
YEAR_COL = "Year"

MIL_COL = "current_usd"
GDP_COL = "gdp_calculated"

TIV_SHARE_COL = "TIV_5Y_Share"
TIV_SUM_COL = "TIV_5Y_Sum"

RISK_COL = "human_hazard_score"
SHARE_GDP_COL = "share_gdp"

HIGH_RISK_THRESHOLD = 7.0

# 현재 current_usd가 SIPRI의 million USD 단위인 경우 True
MILITARY_VALUES_ARE_MILLION_USD = True
