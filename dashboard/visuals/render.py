"""HTML/CSS/스크립트 출력 보조"""
import base64
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from dashboard.common.config import ASSETS_DIR


def render_html(code):
    st.html(code)


def read_asset(name):
    """dashboard/assets 안의 텍스트 파일 읽기 (CSS 등)"""
    return (ASSETS_DIR / name).read_text(encoding="utf-8")


def style_block(css):
    return f"\n<style>\n{css}</style>\n"


def scroll_to_top_script():
    """
    Streamlit은 rerun 후에도 스크롤 위치를 유지하므로
    페이지 이동 직후에만 맨 위로 올려 줍니다.
    components.html은 iframe 안에서 실행되어 parent 문서를 조작합니다.
    """
    components.html(
        """
        <script>
        const doc = window.parent.document;

        const scrollTop = () => {
            const targets = [
                doc.querySelector('section.stMain'),
                doc.querySelector('[data-testid="stMain"]'),
                doc.querySelector('section.main'),
                doc.querySelector('[data-testid="stAppViewContainer"]'),
                doc.scrollingElement,
                doc.documentElement,
                doc.body,
            ];
            for (const t of targets) {
                if (!t) continue;
                try { t.scrollTo({ top: 0, behavior: 'auto' }); }
                catch (e) { t.scrollTop = 0; }
            }
        };

        scrollTop();
        requestAnimationFrame(scrollTop);
        setTimeout(scrollTop, 60);
        setTimeout(scrollTop, 200);
        </script>
        """,
        height=0,
    )


def image_to_data_uri(path):
    path = Path(path)
    if not path.exists():
        return ""
    suffix = path.suffix.lower().replace(".", "")
    if suffix == "jpg":
        suffix = "jpeg"
    encoded = base64.b64encode(path.read_bytes()).decode("utf-8")
    return f"data:image/{suffix};base64,{encoded}"
