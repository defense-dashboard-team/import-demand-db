"""무기 수출 유망국 대시보드 실행 파일.

    streamlit run app_test.py

화면·차트·데이터 코드는 dashboard/ 패키지에 있고, 여기서는 순서대로 부르기만 함.

Streamlit은 위젯을 건드릴 때마다 이 파일을 처음부터 다시 실행(rerun)하지만 import된 모듈은 다시 실행하지 않음.
그래서 rerun마다 바뀌는 값은 모듈 전역에 두지 않고, 여기서 매번 새로 만들어 화면 함수에 넘겨줌.
  dataset : 데이터 (dashboard/data/dataset.py)
  sel     : 상단 필터에서 고른 연도·국가 (dashboard/state.py)
"""
import streamlit as st

from dashboard.data.dataset import load_dataset
from dashboard.layout.banner import render_banner
from dashboard.layout.navigation import render_sidebar
from dashboard.layout.top_filters import render_top_filters
from dashboard.pages.correlation import render_correlation_view
from dashboard.pages.explore import render_page4
from dashboard.pages.overview import render_overview
from dashboard.state import current_selection, init_session_state, validate_selection
from dashboard.styles import inject_global_css
from dashboard.utils.html import scroll_to_top_script


st.set_page_config(
    page_title="글로벌 방산시장 개요",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_global_css()

dataset = load_dataset()
init_session_state(dataset)

render_sidebar()

# 원본 제트기 배너 + 공통 상단 필터
# 연도/국가는 모든 화면에서 동일한 session_state를 사용합니다.
render_banner(st.session_state.app_page, dataset)
validate_selection(dataset)
render_top_filters(dataset)

# 위젯 변경은 rerun 후에 반영되므로 필터를 그린 다음에 현재 선택값을 계산함
sel = current_selection(dataset)


# ============================================================
# 최종 화면 선택
# 1페이지: [전세계] 지도 + Top10 / [국가별] 기존 2페이지
# 2번째 메뉴: 기존 3페이지 상관분석
# ============================================================
if st.session_state.pop("scroll_to_top", False):
    scroll_to_top_script()

if st.session_state.app_page == "page1":
    render_overview(dataset, sel)

elif st.session_state.app_page == "page3":
    render_correlation_view(dataset, sel)

elif st.session_state.app_page == "page4":
    render_page4(dataset, sel)
