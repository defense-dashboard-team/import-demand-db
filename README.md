# 무기 수출 유망국 선정 대시보드

거시경제 지표와 분쟁 위험도를 바탕으로 무기 수입 수요가 큰 국가(수출 유망국)를 찾는 대시보드 프로젝트입니다.
원자료 전처리, 탐색적 분석(EDA), 가설검정, Streamlit 대시보드로 구성됩니다.

## 폴더 구조

```
import-demand-db/
├── app.py                  대시보드 실행 파일 (실제 코드는 dashboard/에 있음)
├── dashboard/              대시보드 코드
├── requirements.txt
├── .streamlit/config.toml  Streamlit 테마 (슬라이더·라디오 등의 기본 색)
├── 00_files/               원자료와 DB 테이블 CSV 사본
├── 01_preprocessing/       원자료 → DB 적재 스크립트
└── 02_notebooks/           EDA, 가설검정 노트북
```

### 데이터 파일 (`00_files/`)

| 파일 | 내용 |
|---|---|
| `SIPRI-Milex-data-1949-2025_v1.2.xlsx` | SIPRI 군사비 원자료 |
| `INFORM2026_TREND_2017_2026_v72_ALL.xlsx` | INFORM 위험도 원자료 |
| `trade-register.csv` | SIPRI 무기 이전(TIV) 원자료 |
| `current_usd.csv`, `gdp_calculated.csv`, `human_hazard_trend.csv`, `tiv_5y_share.csv` | 같은 이름의 DB 테이블 사본 |
| `Integrate_new.csv` | 통합 테이블 사본. 대시보드가 DB에 연결하지 못할 때 대신 읽음 |

### 대시보드 코드 (`dashboard/`)

```
dashboard/
├── config.py               고정 설정 (경로, 페이지 제목·메뉴, 컬럼 이름, 기준 연도)
├── metrics.py              지표별 설정 (컬럼, 라벨, 색, 축 눈금)
├── state.py                화면끼리 공유하는 선택 상태 (연도, 국가, 현재 페이지)
├── data/                   데이터 읽기
│   ├── loader.py             DB(안 되면 CSV)에서 integrate 읽기
│   ├── dataset.py            모든 화면이 같이 쓰는 데이터 묶음
│   ├── world.py              1페이지 전세계 화면용 집계
│   └── world_geojson.py      세계지도 국경선
├── analysis/               차트에 넣기 전 계산
│   ├── similarity.py         유사 국가 찾기
│   └── candidates.py         조건별 후보국 거르기·정렬
├── charts/                 plotly 그림 만들기 (차트 하나에 파일 하나)
│   ├── theme.py              차트 공통 색·글꼴·템플릿, 빈 차트
│   ├── events.py             차트 클릭(선택) 이벤트 읽기
│   ├── world_map.py          1페이지 세계지도
│   ├── trend.py              국가별 탭 지표 추이
│   ├── bubble.py             상관분석 버블차트
│   ├── corr_heatmap.py       상관계수 히트맵
│   ├── country_line.py       상관분석 선택 국가 시계열
│   └── candidate_trend.py    조건별 탐색 추출 국가 비교 시계열
├── layout/                 모든 페이지 공통 화면
│   ├── banner.py             맨 위 전투기 배너
│   ├── navigation.py         사이드바 메뉴
│   ├── top_filters.py        배너 아래 연도·국가 선택 상자
│   └── page_strip.py         현재 선택 국가 칩
├── pages/                  페이지별 화면
│   ├── overview.py           1페이지 틀 (전세계 / 국가별 탭)
│   ├── overview_world/       1페이지 전세계 탭 (KPI, 세계지도, 범례, Top10)
│   ├── overview_country.py   1페이지 국가별 탭
│   ├── correlation.py        상관분석
│   └── explore.py            조건별 대상국 탐색
├── utils/                  보조 함수 (국가명·국기, 숫자 표시, HTML 출력)
├── styles/                 CSS
└── assets/                 배너 이미지, 세계지도 국경선 파일
```

`app.py`는 위젯을 건드릴 때마다 처음부터 다시 실행되지만 `dashboard/` 안의 모듈은 다시 실행되지 않습니다.
그래서 매번 바뀌는 값(데이터 `dataset`, 현재 선택 `sel`)은 `app.py`에서 새로 만들어 각 화면 함수에 넘겨줍니다.
모듈 맨 위(전역)에 이런 값을 두면 지도나 버블을 클릭해도 다른 차트가 바뀌지 않으니 주의하세요.

### 대시보드 화면

상단의 연도·국가 선택은 모든 화면이 같이 씁니다. 지도나 버블에서 국가를 클릭해도 같은 선택이 바뀝니다.

| 메뉴 | 화면 | 내용 |
|---|---|---|
| 전 세계 지표별 분포 | 전세계 탭 | KPI 4개, 지표별 세계지도와 범례, 상위 10개국 |
| | 국가별 탭 | 선택 국가의 핵심 지표별 시계열 추이 |
| 국가 특성 및 유사 국가 | | 버블차트, 상관계수 히트맵, 유사 국가, 선택 국가 시계열 |
| 조건별 대상국 탐색 | | 조건으로 후보국을 거르고 추출 국가의 추이를 비교 (연도만 선택) |

## 사용 지표

분석과 대시보드는 DB의 `integrate` 테이블(한 행 = 한 국가의 한 해)을 사용합니다.

| 표기 | 컬럼명 | 내용 | 출처 |
|---|---|---|---|
| 군사비 | `current_usd` | 군사비 지출액 (경상 달러, 백만 달러 단위) | SIPRI 군사비 자료 |
| GDP | `gdp_calculated` | 국내총생산. 군사비 ÷ 군사비/GDP 로 계산 | SIPRI 군사비 자료 |
| 군사비/GDP | `share_gdp` | GDP 대비 군사비 비중 (0~1 비율) | SIPRI 군사비 자료 |
| 수입점유율 | `TIV_5Y_Share` | 최근 5년 무기 수입량(TIV)의 세계 점유율 (%) | SIPRI 무기 이전 자료 |
| 분쟁위험도 | `human_hazard_score` | 분쟁 위험 점수 (0~10, 높을수록 위험). 2017년부터 있음 | INFORM |

이 밖에 `Country`, `Iso3`, `Year`, `TIV_5Y_Sum`(최근 5년 TIV 합계) 컬럼이 있습니다.

## 환경 설정

### 1. 패키지 설치

```
pip install -r requirements.txt
```

### 2. DB 인증서

AWS RDS 인증서 번들 `global-bundle.pem`을 프로젝트 루트에 둡니다.
AWS 문서의 "SSL/TLS를 사용하여 DB 인스턴스 연결 암호화" 페이지에서 내려받을 수 있습니다.

### 3. DB 접속 정보

접속 정보는 코드에 적지 않고 아래 두 파일에서 읽습니다. **두 파일 모두 커밋하지 않습니다.**
실제 값은 팀 내부에서 공유받으세요.

노트북·전처리용 — 프로젝트 루트에 `.env`

```
DB_USER=
DB_PASSWORD=
DB_HOST=
DB_PORT=3306
DB_NAME=import_demand_db
DB_SSL_CA=./global-bundle.pem
```

대시보드용 — `.streamlit/secrets.toml`

```
[mysql]
db_url = "mysql+pymysql://사용자:비밀번호@호스트:3306/import_demand_db?ssl_ca=./global-bundle.pem"
```

## 실행 방법

모든 명령은 **프로젝트 루트에서** 실행합니다.

### 대시보드

```
streamlit run app.py
```

`streamlit` 명령을 찾지 못하면 `python -m streamlit run app.py`로 실행합니다.

대시보드는 DB의 `integrate` 테이블을 읽습니다. `secrets.toml`이 없거나 DB 연결에 실패하면 `Integrate_new.csv`를 대신 사용합니다.
CSV는 프로젝트 루트에서 먼저 찾고, 없으면 `00_files/`에서 찾습니다.
한 번 읽은 데이터는 6시간 동안 저장해 두고 쓰므로, DB를 갱신한 직후에는 대시보드를 다시 시작해야 반영됩니다.

### 노트북

`02_notebooks/` 안의 노트북을 순서대로 실행합니다. 노트북은 상위 폴더에서 `.env`를 찾아 읽으므로 따로 경로를 바꿀 필요가 없습니다.

| 순서 | 노트북 | 내용 |
|---|---|---|
| 1 | `02_EDA.ipynb` | 이상치, 정규성 검정, 상관분석, 산점도, 다중공선성 |
| 2 | `03_stat_hypothesis.ipynb` | 버블차트 축 조합 검정, 버블 크기 검정, 추세 검정 |

그 밖에 `04_Visualization.ipynb`는 대시보드 차트 시안 작업용입니다. DB가 아니라 작성자 PC의 CSV 경로를 읽으므로, 실행하려면 경로를 바꿔야 합니다.

### 전처리

원자료를 가공해 DB 테이블로 적재하는 스크립트입니다. `integrate` 테이블이 이미 DB에 있으므로 **분석이나 대시보드만 실행할 때는 돌릴 필요가 없습니다.**

```
python 01_preprocessing/01_gdp_df.py
```

| 순서 | 스크립트 | 입력 | 만드는 DB 테이블 |
|---|---|---|---|
| 1 | `01_gdp_df.py` | `SIPRI-Milex-data-1949-2025_v1.2.xlsx` | `current_usd`, `share_gdp`, `gdp_calculated` |
| 2 | `01_inform_df.py` | `INFORM2026_TREND_2017_2026_v72_ALL.xlsx` | `human_hazard_trend` |
| 3 | `01_tiv_merged.py` | `trade-register.csv` | `defense_demand_processed`, `tiv_5y_share` |
| 4 | `01_Integrate_new.py` | 위 테이블들 | `Integrate_new` (국가코드 + 연도 기준 병합, 2000~2025년) |

- DB 연결은 `db_connect.py`가 맡습니다. 프로젝트 루트의 `.env`와 인증서를 읽어 연결하므로 스크립트에 접속 정보를 적지 않습니다.
- `01_Integrate_new.py`는 기존 `integrate` 테이블을 읽거나 바꾸지 않고, `Integrate_new` 테이블과 `01_preprocessing/Integrate_new.csv`를 새로 만듭니다.
- `01_tiv_merged.py`는 실행한 폴더에 중간 파일(`arms_year.csv`, `df2.csv`, `merged.csv`)을 남깁니다.
- 스크립트는 DB 테이블을 **덮어씁니다**(`if_exists='replace'`). 실행 전에 팀과 확인하세요.

## 분석 요약

2023년 기준 다섯 지표가 모두 있는 147개국을 분석했습니다. 자세한 내용은 노트북을 참고하세요.

- 무기 수입점유율은 군사비·GDP와 강하게 연결돼 있습니다 (Spearman 0.85, 0.79).
- 군사비, GDP, 수입점유율은 분포가 크게 치우쳐 있어 로그 또는 순위 변환 후 사용해야 합니다.
- 분쟁위험도는 다른 지표와 유의한 상관이 없는 별개의 정보입니다.
- 군사비·GDP·군사비/GDP는 함께 쓰면 중복됩니다. 버블 크기로는 GDP가 적합합니다.
- 두 버블차트의 y축인 분쟁위험도와 수입점유율은 서로 무관해서, 나란히 두어도 같은 내용을 반복하지 않습니다.
- 군사비는 상위 50개국 중 45개국에서 증가했지만, 군사비/GDP가 증가한 나라는 8개국입니다.

## 정리 예정

- 전처리 스크립트의 입력 경로를 `00_files/`로 수정. 지금은 `data/...`와 실행 폴더의 `trade-register.csv`로 적혀 있어 그대로는 파일을 찾지 못함
- `01_Integrate_new.py`가 만드는 `Integrate_new` 테이블과 대시보드·노트북이 읽는 `integrate` 테이블 이름 통일
