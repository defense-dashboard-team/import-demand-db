# 무기 수출 유망국 선정 대시보드

거시경제 지표와 분쟁 위험도를 바탕으로 무기 수입 수요가 큰 국가(수출 유망국)를 찾는 대시보드 프로젝트입니다.
원자료 전처리, 탐색적 분석(EDA), 가설검정, Streamlit 대시보드로 구성됩니다.

## 폴더 구조

```
import-demand-db/
├── app.py                  대시보드
├── requirements.txt
├── 01_preprocessing/       원자료 → DB 적재 스크립트
└── 02_notebooks/           EDA, 가설검정 노트북
```

## 사용 지표

분석과 대시보드는 DB의 `integrate` 테이블(한 행 = 한 국가의 한 해)을 사용합니다.

| 표기 | 컬럼명 | 내용 | 출처 |
|---|---|---|---|
| 군사비 | `current_usd` | 군사비 지출액 (경상 달러) | SIPRI 군사비 자료 |
| GDP | `gdp_calculated` | 국내총생산. 군사비 ÷ 군사비/GDP 로 계산 | SIPRI 군사비 자료 |
| 군사비/GDP | `share_gdp` | GDP 대비 군사비 비중 (0~1 비율) | SIPRI 군사비 자료 |
| 수입점유율 | `TIV_5Y_Share` | 최근 5년 무기 수입량(TIV)의 세계 점유율 (%) | SIPRI 무기 이전 자료 |
| 분쟁위험도 | `human_hazard_score` | 분쟁 위험 점수 (0~10, 높을수록 위험) | INFORM |

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

대시보드는 DB의 `integrate` 테이블을 읽습니다. `secrets.toml`이 없거나 DB 연결에 실패하면 같은 폴더의 `Integrate_new.csv`를 대신 사용합니다.

### 노트북

`02_notebooks/` 안의 노트북을 순서대로 실행합니다. 노트북은 상위 폴더에서 `.env`를 찾아 읽으므로 따로 경로를 바꿀 필요가 없습니다.

| 순서 | 노트북 | 내용 |
|---|---|---|
| 1 | `02_EDA.ipynb` | 이상치, 정규성 검정, 상관분석, 다중공선성 |
| 2 | `03_stat_hypothesis.ipynb` | 버블차트 축 조합 검정, 버블 크기 검정, 추세 검정 |

그 밖에 `04_Visualization.ipynb`는 대시보드 차트 시안 작업용입니다.

### 전처리

원자료를 가공해 DB 테이블로 적재하는 스크립트입니다. `integrate` 테이블이 이미 DB에 있으므로 **분석이나 대시보드만 실행할 때는 돌릴 필요가 없습니다.**

```
python 01_preprocessing/01_gdp_df.py
```

| 순서 | 스크립트 | 입력 | 만드는 DB 테이블 |
|---|---|---|---|
| 1 | `01_gdp_df.py` | `data/SIPRI-Milex-data-1949-2025_v1.2.xlsx` | `current_usd`, `share_gdp`, `gdp_calculated` |
| 2 | `01_inform_df.py` | `data/INFORM2026_TREND_2017_2026_v72_ALL.xlsx` | `human_hazard_trend` |
| 3 | `01_tiv_merged.py` | `trade-register.csv` | `defense_demand_processed`, `tiv_5y_share` |
| 4 | `01_integrate_df.py` | 위 테이블들 | `integrate` |
| 5 | `01_integrate_new.py` | 위 테이블들 | `integrate` (국가코드 기준으로 다시 병합, 2000~2025년) |

- DB 연결은 `db_connect.py`가 맡습니다. 프로젝트 루트의 `.env`와 인증서를 읽어 연결하므로 스크립트에 접속 정보를 적지 않습니다.
- 입력 파일 경로는 프로젝트 루트 기준입니다. 원자료 파일은 저장소에 포함돼 있지 않습니다.
- 스크립트는 DB 테이블을 **덮어씁니다**(`if_exists='replace'`). 실행 전에 팀과 확인하세요.

## 분석 요약

자세한 내용은 `02_notebooks/`의 노트북을 참고하세요.

- 무기 수입점유율은 군사비·GDP와 강하게 연결돼 있습니다 (Spearman 0.85, 0.79).
- 군사비, GDP, 수입점유율은 분포가 크게 치우쳐 있어 로그 또는 순위 변환 후 사용해야 합니다.
- 분쟁위험도는 다른 지표와 유의한 상관이 없는 별개의 정보입니다.
- 군사비·GDP·군사비/GDP는 함께 쓰면 중복됩니다. 버블 크기로는 GDP가 적합합니다.
- 군사비는 상위 50개국 중 45개국에서 증가했지만, 군사비/GDP가 증가한 나라는 8개국입니다.

## 정리 예정

- `01_integrate_df.py`와 `01_integrate_new.py` 통합
