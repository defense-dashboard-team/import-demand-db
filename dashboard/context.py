"""rerun마다 다시 계산되는 값을 담아 두는 곳.

app.py 한 파일일 때는 df, 선택 국가 같은 값이 스크립트 전역 변수였고 rerun마다 새로 계산됐다.
모듈로 나누면 import된 모듈은 rerun 때 다시 실행되지 않아서, 이런 값을 모듈 전역에 두면
처음 값에 고정된다 (버블을 눌러도 다른 차트가 안 바뀌는 식으로 깨짐).

그래서 app_copy.py가 rerun마다 ctx에 값을 다시 채우고, 다른 모듈은 ctx.df, ctx.country 처럼 읽는다.
실제 값은 st.session_state에 들어가므로 접속한 사용자(세션)마다 따로 유지된다.

채우는 곳
  - dashboard.db.dataset.load_dataset()               : df, COL, countries, years, country_to_iso3 ...
  - dashboard.screens.state.update_current_selection() : country, selected_year, current, sel_iso ...
"""
import streamlit as st
from streamlit.runtime.scriptrunner import get_script_run_ctx

_STORE_KEY = "_run_context"


class _RunContext:
    # 스크립트 실행 중이 아닐 때(테스트 도구가 format_func를 따로 부르는 경우 등) 쓰는 마지막 값
    _last = {}

    def _store(self):
        if get_script_run_ctx(suppress_warning=True) is None:
            return _RunContext._last
        if _STORE_KEY not in st.session_state:
            st.session_state[_STORE_KEY] = {}
        store = st.session_state[_STORE_KEY]
        _RunContext._last = store
        return store

    def __getattr__(self, name):
        try:
            return self._store()[name]
        except KeyError:
            raise AttributeError(f"ctx.{name} 값이 아직 없음") from None

    def __setattr__(self, name, value):
        self._store()[name] = value


ctx = _RunContext()
