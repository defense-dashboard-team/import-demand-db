"""CSS 파일을 읽어 화면에 넣음.

import된 모듈은 rerun 때 다시 실행되지 않으므로 CSS 출력은 함수로 두고 app.py가 rerun마다 부름.
"""
from pathlib import Path

import streamlit as st


STYLES_DIR = Path(__file__).resolve().parent

# 뒤에 오는 파일이 앞 파일을 덮어쓰므로 순서를 바꾸면 안 됨
GLOBAL_CSS = [
    "base.css",            # 기본 배경, 카드, KPI, 배너 등
    "overview_frame.css",  # 1페이지 전세계 / 국가별 공통 패널과 책갈피형 탭
    "theme.css",           # 디자인 정리 레이어 (Pretendard 글꼴, 카드·제목 모양 통일)
    "top_filters.css",     # 배너 아래 연도·국가 선택 상자
]


def read_css(filename):
    return (STYLES_DIR / filename).read_text(encoding="utf-8")


def inject_global_css():
    """모든 화면 공통 CSS"""
    for filename in GLOBAL_CSS:
        st.html(f"\n<style>\n{read_css(filename)}</style>\n")


def inject_page1_css():
    """1페이지 전세계 화면에서만 넣는 CSS"""
    st.html(f"<style>\n{read_css('page1_world.css')}</style>")
