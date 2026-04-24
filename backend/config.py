"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  집값추적기 — 설정 파일
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

API 키 주입 방법 (우선순위 순):
  1. 환경변수:  export MOLIT_KEY="발급받은키"
  2. .env 파일: 프로젝트 루트에 .env 생성 후 MOLIT_KEY=발급받은키 작성
  3. 아래 fallback 문자열 직접 수정 (커밋 금지)

.env 발급 방법:
  1. https://www.data.go.kr 접속
  2. "국토교통부 아파트매매 실거래 상세 자료" 검색
  3. 활용신청 → 자동승인 → 마이페이지에서 일반 인증키 복사
  4. 프로젝트 루트에 .env 파일 생성:
       MOLIT_KEY=여기에붙여넣기
"""

import os
from pathlib import Path

# ── .env 파일 로드 (python-dotenv 없이 직접 파싱) ────────────────
def _load_env_file() -> None:
    env_path = Path(__file__).parent.parent / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip('"').strip("'")
        if key and key not in os.environ:          # 환경변수 우선
            os.environ[key] = val

_load_env_file()

# ── 국토부 실거래가 API 키 ─────────────────────────────────────
MOLIT_API_KEY: str = os.environ.get("MOLIT_KEY", "")

# ── 기본 수집 설정 ─────────────────────────────────────────────
DEFAULT_MONTHS: int = 3
DEFAULT_METROS: list[str] = ["서울", "경기", "인천"]

# ── 서버 설정 ──────────────────────────────────────────────────
HOST: str = "0.0.0.0"
PORT: int = 8000
