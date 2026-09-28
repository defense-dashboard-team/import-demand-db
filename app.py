import os
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title='수출 유망국 탐색 — 복합지표',
    layout='wide',                      # 좌우 2열 배치를 위해 넓은 레이아웃
)

# ─────────────────────────────────────────────────────────
# 2. 경로 — app.py 위치 기준이라 어느 폴더에서 실행해도 동일
# ─────────────────────────────────────────────────────────
from pathlib import Path

BASE_DIR = Path(__file__).parent          # streamlit/
DATA_DIR = BASE_DIR.parent / 'data'       # 1차프로젝트/data/

USE_DB = True                             # DB 접속되면 True로 바꾸기
CSV_PATH = DATA_DIR / 'Integrate_new.csv'

DB_URL = ('mysql+pymysql://admin:dhgkqwlwhf5@'
          'import-demand-server.cqr8wgqy24po.us-east-1.rds.amazonaws.com:3306/import_demand_db')
SSL_CA = str(BASE_DIR / 'global-bundle.pem')

# ─────────────────────────────────────────────────────────
# 2-2. 상수(METRIC 등) — 노트북 셀 4와 동일
# ─────────────────────────────────────────────────────────
YEAR_MIN, YEAR_MAX = 2004, 2025
RISK_START = 2017                         # INFORM 위험도 시작 연도

X_COL = 'share_gdp_pct'                   # 두 버블차트 공통 X축
SIZE_COL = 'gdp_calculated'               # 버블 크기 (GDP)
MILEX_COL = 'current_usd'                 # 선그래프 왼쪽 축 (군사비)

METRIC = {
    'risk': {
        'col':   'human_hazard_score',
        'label': '분쟁위험도',
        'color': '#C1663B',
        'scale': 'OrRd',
        'fmt':   '.1f',
        'log_y': False,
        'log_color': False,
        'yticks': None,
        'ytext':  None,
        # 'yrange': [0, 10],        # 절대 척도 — 고정
    },
    'tiv': {
        'col':   'TIV_5Y_Share',
        'label': 'TIV 5년 점유율 (%)',
        'color': '#2C7A5A',
        'scale': 'BuGn',
        'fmt':   '.3f',
        'log_y': True,
        'log_color': True,
        'yticks': [0.004, 0.01, 0.03, 0.1, 0.3, 1, 3, 10],
        'ytext':  ['0', '0.01', '0.03', '0.1', '0.3', '1', '3', '10'],
        # 'yrange': None,           # 1만 배 편차 — 자동 척도
    },
}

MILEX_COLOR = '#2E6F9E'
BUBBLE_MIN, BUBBLE_MAX = 6, 46

BASE_LAYOUT = dict(
    template='plotly_white',
    font=dict(family='Malgun Gothic, AppleGothic, NanumGothic, sans-serif', size=12),
    margin=dict(l=60, r=70, t=55, b=55),
    hovermode='closest',
)

# ─────────────────────────────────────────────────────────
# 3. 데이터 로드 — 노트북 셀 2·3을 함수 하나로 묶음
# ─────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def load_data():
    """integrate 테이블을 읽고 전처리해서 반환한다.
    @st.cache_data 덕분에 화면을 조작해도 1시간에 한 번만 실제로 읽는다."""

    # 1) 로드 — DB 실패 시 CSV로 대체
    if USE_DB:
        try:
            from sqlalchemy import create_engine
            engine = create_engine(DB_URL,
                                connect_args={'ssl': {'ca': SSL_CA}, 'connect_timeout': 5})
            df = pd.read_sql('SELECT * FROM integrate', con=engine)
        except Exception:
            df = pd.read_csv(CSV_PATH)
    else:
        df = pd.read_csv(CSV_PATH)

    df.columns = [c.strip('\ufeff').strip() for c in df.columns]   # BOM 제거

    # 2) 전처리 — 노트북 셀 3과 동일
    NUM_COLS = ['Year', 'current_usd', 'gdp_calculated',
                'share_gdp', 'TIV_5Y_Sum', 'TIV_5Y_Share', 'human_hazard_score']
    for c in NUM_COLS:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df = df[(df['Year'] >= YEAR_MIN) & (df['Year'] <= YEAR_MAX)].copy()

    IND_COLS = ['current_usd', 'gdp_calculated', 'share_gdp',
                'TIV_5Y_Share', 'human_hazard_score']
    df = df[~df[IND_COLS].isna().all(axis=1)].copy()

    df['share_gdp_pct'] = df['share_gdp'] * 100

    return df


# 로드 실패시 에러 메시지 띄우기
try:
    df = load_data()
except Exception as e:
    st.error(f'데이터를 불러오지 못했습니다: {type(e).__name__} — {e}')
    st.stop()

# ─────────────────────────────────────────────────────────
# 4. 차트 함수 — 노트북 셀 5·6·7과 동일 (수정 없음)
# bubble_size, empty_figure, make_bubble, make_line
# ─────────────────────────────────────────────────────────

def bubble_size(values):
    """버블 '면적'이 값에 비례하도록 지름을 제곱근에 비례시킴"""
    v = np.sqrt(np.clip(values.astype(float), 0, None))   # 음수 방어 후 제곱근 ->면적이 GDP에 비례하도록 지름 계산
                                                          # np.clip(값, 최솟값, 최댓값) 하한 0, 상한 None
    lo, hi = np.nanmin(v), np.nanmax(v)                   # 결측치 무시한 최대 최소
    if hi == lo:                                          # 정규화에서 분모가 0인 경우엔 26px로 통일
        return np.full(len(v), (BUBBLE_MIN + BUBBLE_MAX) / 2)
    return BUBBLE_MIN + (v - lo) / (hi - lo) * (BUBBLE_MAX - BUBBLE_MIN)    # 최대-최소 정규화 (6~46px)

def empty_figure(message):
    """데이터가 없을 때 안내 문구만 표시"""
    fig = go.Figure()
    fig.add_annotation(text=message, xref='paper', yref='paper',             # xref='paper: 좌표를 데이터 값이 아니라 화면 비율 0~1로 해석해라
                       x=0.5, y=0.5, showarrow=False,
                       font=dict(size=14, color='#7A8794'))
    fig.update_layout(xaxis=dict(visible=False), yaxis=dict(visible=False),  # visible=False 축 관련 옵션 끄기 (축선, 눈금, 숫자, 라벨)
                      height=460, **BASE_LAYOUT)
    return fig

def make_bubble(data, year, metric='risk', size_col=SIZE_COL, log_x=True, highlight=None):
    """metric='risk' → 버블차트1, metric='tiv' → 버블차트2."""    # size_col=SIZE_COL: 기본값이 GDP
    m = METRIC[metric]

    # 1) 2017년 이전에는 위험도 데이터가 없음
    if metric == 'risk' and year < RISK_START:
        return empty_figure(
            f'분쟁위험도(INFORM)는 {RISK_START}년부터 제공됩니다.<br>'    # <br>: plotly 주석 줄바꿈
            f'{RISK_START}년 이후를 선택하거나 TIV 차트를 이용하세요.')

    # 2) 해당 연도만 뽑고, 그릴 수 없는 행 제거 - 가로축(GDP대비 군사비), 세로축(위험도 or TIV), 버블크기(GDP) 중 하나라도 없는 행
    d = data[data['Year'] == year].dropna(subset=[X_COL, m['col'], size_col])
    d = d[(d[X_COL] > 0) & (d[size_col] > 0)]    # share_gdp_pct, gdp_calculated 0인 행 제거
    if d.empty:                                  # len(d) == 0 True / False
        return empty_figure(f'{year}년 데이터가 없습니다.')

    # 3) y축이 로그면 하한을 0.004로 위치만 옮김(0 다음 값이 0.006)
    y = d[m['col']].clip(lower=0.004) if m['log_y'] else d[m['col']]

    # 3-2) 색도 y축과 같은 스케일로 매핑
    #      TIV는 중앙값 0.055인데 최대 14.96이라 선형으로 칠하면 75%가 흰색
    if m['log_color']:
        cvals = np.log10(d[m['col']].clip(lower=0.004))       # 색 결정용 값만 로그로 (위치·호버는 원본 유지)
        _ticks = [0.004, 0.01, 0.1, 1, 10]                    # 색상 막대에 표시할 원래 값
        colorbar = dict(title=dict(text=m['label'], side='right'),
                        thickness=12, len=0.75,
                        tickvals=np.log10(_ticks),            # 눈금 위치는 로그 공간에
                        ticktext=['0', '0.01', '0.1', '1', '10'])  # 글자는 원래 값으로 (0.004는 인공 하한이라 '0')
    else:
        cvals = d[m['col']]                                   # 위험도는 0~10 고르게 퍼져 선형 그대로
        colorbar = dict(title=dict(text=m['label'], side='right'),
                        thickness=12, len=0.75)

    # 4) 차트 본체
    fig = go.Figure(go.Scatter(
        x=d[X_COL], y=y,
        mode='markers',
        customdata=np.stack([d['Country'], d['Iso3'], d[SIZE_COL],    # 국가명: 호버 제목, 국가코드: 클릭 시 식별용
                             d[MILEX_COL], d[m['col']]], axis=-1),    # GDP, 군사비, Y축 원본값: 표시되는 값
        # 호버 상자 모양
        hovertemplate=(
            '<b>%{customdata[0]}</b><br>'
            'GDP 대비 군사비 %{x:.2f}%<br>'
            + m['label'] + ' %{customdata[4]:' + m['fmt'] + '}<br>'
            'GDP %{customdata[2]:,.0f}<br>'
            '군사비 %{customdata[3]:,.0f}<extra></extra>'),
        # 마커
        marker=dict(
            size=bubble_size(d[size_col]), sizemode='diameter',       # bubble_size 값을 지름으로 해석
            color=cvals, colorscale=m['scale'], showscale=True,       # 색상 범례 막대 표시
            colorbar=colorbar,                                        # 3-2에서 만든 것 (로그면 눈금 재지정)
            opacity=(0.72 if highlight is None
                     else [0.95 if i == highlight else 0.25 for i in d['Iso3']]),
            line=dict(
                width=[2 if i == highlight else 0.5 for i in d['Iso3']],
                color=['#111111' if i == highlight else 'rgba(60,60,60,0.4)'
                       for i in d['Iso3']])),
        selected=dict(marker=dict(opacity=0.95)),
        unselected=dict(marker=dict(opacity=0.25)),
    ))

    # 5) 축, 제목
    fig.update_layout(
        title=dict(text=f'{year}년 · GDP 대비 군사비 × {m["label"]}  (n={len(d)})',    # y축 이름, 몇개국인지
                   font=dict(size=15)),
        xaxis=dict(
            title='GDP 대비 군사비 (%)',
            type='log' if log_x else 'linear',    # GDP 대비 군사비: 0.003~39.56%인데 중앙값 1.46%
            tickvals=[0.2, 0.5, 1, 2, 5, 10, 20, 40] if log_x else None,                   # 눈금 찍을 위치 (데이터 값 기준). 기본은 10단위라 너무 듬성
            ticktext=['0.2', '0.5', '1', '2', '5', '10', '20', '40'] if log_x else None),  # 그 자리에 표시할 글자. 읽기 편하라고 지정. log가 아니면 Plotly 기본으로
        yaxis=dict(title=m['label'],
                   type='log' if m['log_y'] else 'linear',     # 위험도는 선형, TIV는 log
                   tickvals=m['yticks'],                     
                   ticktext=m['ytext']),
        height=460, **BASE_LAYOUT)
    return fig

def make_line(data, iso, metric='risk'):
    """선택 국가의 연도별 추이. 왼쪽 축 군사비, 오른쪽 축 metric."""
    m = METRIC[metric]

    # 1) 해당 국가만 뽑기
    d = data[data['Iso3'] == iso].sort_values('Year')
    if d.empty:
        return empty_figure('국가를 선택하세요.')
    name = d['Country'].iloc[0]

    # 2) 2004~2025 전 구간 뼈대를 만들어 없는 해를 NaN으로 남김 (연도 행이 빠진 국가 대비, 현재 GNB 1개국)
    full = pd.DataFrame({'Year': range(YEAR_MIN, YEAR_MAX + 1)})
    d = full.merge(d, on='Year', how='left')

    # 3) 좌우 Y축을 가진 빈 차트
    fig = make_subplots(specs=[[{'secondary_y': True}]])

    # 4) 왼쪽 축 — 군사비
    fig.add_trace(go.Scatter(                       # add_trace: 차트에 선(또는 점 묶음)을 하나씩 추가하는 함수
        x=d['Year'], y=d[MILEX_COL], name='군사비',
        mode='lines+markers', connectgaps=False,    # 점, 선 둘 다 그리고, NaN 구간에서 선 안 이음
        line=dict(color=MILEX_COLOR, width=2), marker=dict(size=4),
        hovertemplate='%{x}년<br>군사비 %{y:,.0f}<extra></extra>',
    ), secondary_y=False)                           # 어느축에 붙일지 정함

    # 5) 오른쪽 축 — 위험도 또는 TIV
    fig.add_trace(go.Scatter(
        x=d['Year'], y=d[m['col']], name=m['label'],
        mode='lines+markers', connectgaps=False,
        line=dict(color=m['color'], width=2, dash='dot'), marker=dict(size=4),    # dash='dot' 오른쪽 축만 점선으로 표시
        hovertemplate='%{x}년<br>' + m['label'] + ' %{y:' + m['fmt'] + '}<extra></extra>',
    ), secondary_y=True)

    # 6) 위험도가 2017년부터라고 화면에 명시
    if metric == 'risk':
        fig.add_vrect(x0=YEAR_MIN - 0.5, x1=RISK_START - 0.5,    # add_vrect: 2003.5~2016.5 구간을 검정 5% 불투명도로 칠함
                      fillcolor='#000000', opacity=0.05, line_width=0)
        fig.add_annotation(x=(YEAR_MIN + RISK_START) / 2, y=1.0, yref='paper',
                           text=f'위험도 미제공 (~{RISK_START - 1})',
                           showarrow=False, font=dict(size=10, color='#7A8794'))

    # 7) 축 설정
    fig.update_xaxes(title_text='연도', dtick=2,                                   # 눈금 간격 2년
                     range=[YEAR_MIN - 0.5, YEAR_MAX + 0.5])                      # 양 끝 여백
    # fig.update_yaxes(title_text='군사비', color=MILEX_COLOR, secondary_y=False)    # 축 제목, 눈금 글자색을 선과 맞춤
    fig.update_yaxes(title_text='군사비', color=MILEX_COLOR, secondary_y=False,
                    rangemode='tozero')         # 항상 0부터
    
    fig.update_yaxes(title_text=m['label'], color=m['color'],
                    secondary_y=True, showgrid=False,                             # 오른쪽 축 격자만 끔
                    tickformat=m['fmt'],   )                                       # 지표별 자릿수 적용 (위험도 .1f, TIV .3f)
                    # range=m['yrange'])                                            # None이면 자동 <- 추가함
    fig.update_layout(
        title=dict(text=f'{name} · 연도별 추이', font=dict(size=15),
                   y=0.97, yanchor='top'),                    # 제목을 위로 붙임
        legend=dict(orientation='h', y=1.02, x=0,             # 범례는 그래프 바로 위
                    yanchor='bottom'),
        height=460, margin=dict(l=60, r=70, t=85, b=55),      # 위 여백 55 → 85
        template='plotly_white',
        font=dict(family='Malgun Gothic, AppleGothic, NanumGothic, sans-serif', size=12),
        hovermode='closest')
    return fig

# ─────────────────────────────────────────────────────────
# 5. 화면
# ─────────────────────────────────────────────────────────
st.title('수출 유망국 탐색 — 복합지표')
st.caption('GDP 대비 군사비를 기준으로 분쟁위험도와 무기 수입 실적을 함께 확인합니다. '
           '버블을 클릭하면 해당 국가의 연도별 추이가 오른쪽에 표시됩니다.')

# 국가명 ↔ ISO3 변환표
names = df[['Iso3', 'Country']].drop_duplicates().sort_values('Country')
ISO_TO_NAME = dict(zip(names['Iso3'], names['Country']))
NAME_TO_ISO = dict(zip(names['Country'], names['Iso3']))
NONE_LABEL = '(선택 안 함)'
options = [NONE_LABEL] + names['Country'].tolist()

# ── 페이지 전환 시 위젯 상태가 사라지지 않게 재할당 (멀티페이지 공용)
for k in ['sel_year', 'sel_country']:
    if k in st.session_state:
        st.session_state[k] = st.session_state[k]

# ── 위젯이 만들어지기 전에 버블 클릭을 먼저 반영
#    (사이드바보다 위에 있어야 드롭다운에 즉시 적용된다)
for _m in ['risk', 'tiv']:
    _ev = st.session_state.get(f'bubble_{_m}')
    if _ev:
        _pts = (_ev.get('selection') or {}).get('points', [])
        if _pts:
            _iso = _pts[0]['customdata'][1]
            st.session_state['sel_country'] = ISO_TO_NAME.get(_iso, NONE_LABEL)

# ── 사이드바
with st.sidebar:
    st.header('필터')

    year = st.slider('연도', YEAR_MIN, YEAR_MAX,
                     st.session_state.get('sel_year', YEAR_MAX), key='sel_year')

    st.selectbox('국가', options, key='sel_country')

    size_col = st.radio(
        '버블 크기',
        ['gdp_calculated', 'current_usd'],
        format_func=lambda x: {'gdp_calculated': 'GDP',
                               'current_usd': '군사비'}[x],
    )

    if year < RISK_START:
        st.info(f'분쟁위험도는 {RISK_START}년부터 제공됩니다. '
                '선택한 연도에서는 TIV 차트만 표시됩니다.')

# 두 차트가 공유하는 선택 국가
chosen_name = st.session_state.get('sel_country', NONE_LABEL)
sel_iso = None if chosen_name == NONE_LABEL else NAME_TO_ISO.get(chosen_name)

# 버블차트 + 선그래프를 좌우 2열로, 지표별 2행
for metric in ['risk', 'tiv']:
    left, right = st.columns(2)

    with left:
        st.plotly_chart(
            make_bubble(df, year, metric, size_col=size_col, highlight=sel_iso),
            use_container_width=True,
            on_select='rerun',
            selection_mode='points',
            key=f'bubble_{metric}',
        )

    with right:
        if sel_iso:
            st.plotly_chart(make_line(df, sel_iso, metric),
                            use_container_width=True, key=f'line_{metric}')
        else:
            st.plotly_chart(empty_figure('버블을 클릭하거나 사이드바에서 국가를 선택하세요.'),
                            use_container_width=True, key=f'empty_{metric}')

st.caption('TIV(Trend Indicator Value)는 SIPRI가 무기의 군사적 능력을 지수화한 값으로 '
           '실제 거래 금액이 아닙니다. 분쟁위험도는 UN INFORM Human Hazard 지수이며 '
           f'{RISK_START}년부터 제공됩니다.')
