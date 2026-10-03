"""HTML 출력과 화면 스크롤 스크립트."""
import base64
from pathlib import Path
from textwrap import dedent

import streamlit as st
import streamlit.components.v1 as components


def render_html(code):
    st.html(code)


def p1_html(code):
    code = dedent(code).strip()

    if hasattr(st, "html"):
        st.html(code)
    else:
        st.markdown(code, unsafe_allow_html=True)


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


def scroll_to_bottom_script():
    """펼친 내용이 바로 보이도록 화면을 맨 아래로 내립니다 (차트가 늦게 그려져 몇 번 반복)."""
    components.html(
        """
        <script>
        const doc = window.parent.document;
        const scrollBottom = () => {
            const targets = [
                doc.querySelector('section.stMain'),
                doc.querySelector('[data-testid="stMain"]'),
                doc.querySelector('[data-testid="stAppViewContainer"]'),
                doc.scrollingElement,
            ];
            for (const t of targets) {
                if (!t) continue;
                try { t.scrollTo({ top: t.scrollHeight, behavior: 'smooth' }); }
                catch (e) { t.scrollTop = t.scrollHeight; }
            }
        };
        setTimeout(scrollBottom, 150);
        setTimeout(scrollBottom, 600);
        setTimeout(scrollBottom, 1200);
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
