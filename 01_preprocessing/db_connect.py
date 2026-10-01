"""DB 연결 공통 모듈.

접속 정보는 코드에 적지 않고 프로젝트 루트의 .env 파일(또는 환경변수)에서 읽는다.

.env 예시
    DB_USER=
    DB_PASSWORD=
    DB_HOST=
    DB_PORT=3306
    DB_NAME=import_demand_db
    DB_SSL_CA=./global-bundle.pem

사용법
    from db_connect import get_engine
    engine = get_engine()
"""
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# 프로젝트 루트: 이 파일의 위치에서 위로 올라가며 .env 가 있는 폴더를 찾는다.
# 찾지 못하면 이 파일의 상위 폴더(= 저장소 루트)로 본다.
_HERE = Path(__file__).resolve().parent
ROOT = next((p for p in [_HERE, *_HERE.parents] if (p / '.env').exists()), _HERE.parent)


def _load_env():
    """.env 파일을 읽어 환경변수로 등록한다. 이미 설정된 값은 덮어쓰지 않는다."""
    env_file = ROOT / '.env'
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def db_name():
    """.env 에 적힌 데이터베이스 이름."""
    _load_env()
    return os.environ.get('DB_NAME', 'import_demand_db')


def get_engine(database=True):
    """SQLAlchemy 엔진을 만든다.

    database=True : DB_NAME 데이터베이스에 연결 (기본)
    database=False: 데이터베이스를 지정하지 않고 서버에만 연결
                    (CREATE DATABASE 처럼 데이터베이스가 아직 없을 때 사용)
    """
    _load_env()

    missing = [k for k in ['DB_USER', 'DB_PASSWORD', 'DB_HOST'] if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f'환경변수 없음: {", ".join(missing)} ({ROOT / ".env"} 파일 확인)')

    # RDS는 SSL 접속이므로 AWS 인증서가 필요하다. 상대 경로는 프로젝트 루트 기준으로 해석한다.
    ssl_ca = Path(os.environ.get('DB_SSL_CA', './global-bundle.pem'))
    if not ssl_ca.is_absolute():
        ssl_ca = ROOT / ssl_ca
    if not ssl_ca.exists():
        raise FileNotFoundError(f'RDS 인증서 없음: {ssl_ca}')

    url = URL.create(
        'mysql+pymysql',
        username=os.environ['DB_USER'],
        password=os.environ['DB_PASSWORD'],
        host=os.environ['DB_HOST'],
        port=int(os.environ.get('DB_PORT', 3306)),
        database=db_name() if database else None,
        query={'charset': 'utf8mb4'},
    )
    return create_engine(url, connect_args={'ssl': {'ca': str(ssl_ca)}})
