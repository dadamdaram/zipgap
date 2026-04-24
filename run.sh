#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  집값추적기 v12 — 실행 스크립트
#  ./run.sh            개발 모드 (hot-reload, localhost:8000)
#  ./run.sh --prod     프로덕션 (멀티워커, 0.0.0.0:8000)
#  ./run.sh --port N   포트 지정
# ═══════════════════════════════════════════════════════════════
set -e
cd "$(dirname "$0")"

# ── 인자 파싱 ──────────────────────────────────────────────────
MODE="dev"
PORT=8000
while [[ $# -gt 0 ]]; do
  case $1 in
    --prod)   MODE="prod"; shift ;;
    --port)   PORT="$2"; shift 2 ;;
    --help|-h) echo "사용법: ./run.sh [--prod] [--port 포트]"; exit 0 ;;
    *) shift ;;
  esac
done

# ── .env 로드 ──────────────────────────────────────────────────
if [ -f ".env" ]; then
  while IFS='=' read -r key val; do
    [[ "$key" =~ ^#.*$ || -z "$key" ]] && continue
    val="${val%%#*}"
    val="${val%"${val##*[![:space:]]}"}"
    export "$key"="$val"
  done < <(grep -v '^#' .env | grep '=')
  echo "✅ .env 로드됨"
fi

# ── Python 경로 결정 ───────────────────────────────────────────
PY="${PYTHON:-}"
if [ -z "$PY" ]; then
  for c in python3.12 python3.11 python3.10 python3 python; do
    command -v "$c" &>/dev/null && { PY="$c"; break; }
  done
fi
[ -z "$PY" ] && { echo "❌ Python3 없음"; exit 1; }
echo "🐍 $($PY --version)"

# ── 가상환경 생성 및 복구 ──────────────────────────────────────
VENV_PY=".venv/bin/python"

# 가상환경 자체가 없거나 Python 바이너리가 깨진 경우 재생성
if [ ! -d ".venv" ] || [ ! -f "$VENV_PY" ]; then
  echo "📦 가상환경 생성 중..."
  rm -rf .venv
  $PY -m venv .venv
  if [ ! -f "$VENV_PY" ]; then
    echo "❌ 가상환경 생성 실패. Python venv 모듈 확인 필요."
    echo "   시도: $PY -m pip install virtualenv && $PY -m virtualenv .venv"
    exit 1
  fi
  echo "✅ 가상환경 준비됨"
fi

PY="$VENV_PY"

# 의존성 변경 시에만 재설치
HASH_FILE=".venv/.req_hash"
REQ_HASH=$(shasum -a 256 requirements.txt 2>/dev/null | awk '{print $1}' \
        || sha256sum requirements.txt 2>/dev/null | awk '{print $1}' \
        || md5 -q requirements.txt 2>/dev/null \
        || echo "")
STORED=$(cat "$HASH_FILE" 2>/dev/null || echo "")
if [ "$REQ_HASH" != "$STORED" ]; then
  echo "📥 의존성 설치 중..."
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
  echo "$REQ_HASH" > "$HASH_FILE"
  echo "✅ 설치 완료"
fi

# ── frontend/env.js 생성 ───────────────────────────────────────
MOLIT_VAL="${MOLIT_KEY:-}"
cat > frontend/env.js <<ENVEOF
// ⚠ run.sh 자동 생성 — 수정 금지 (.gitignore 포함)
window.__ENV__ = {
  MOLIT_KEY: "${MOLIT_VAL}",
  MODE: "${MODE}",
  generated: "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
};
ENVEOF

# ── 실행 정보 ──────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🏠  집값추적기 v20"
if [ -z "$MOLIT_VAL" ]; then
  echo "  ⚠   API 키 없음 → 샘플 데이터 모드"
  echo "      실거래 전환: cp .env.example .env"
else
  echo "  🔑  API 키: ${MOLIT_VAL:0:8}…"
fi
echo "  🌐  모드: $MODE  |  포트: $PORT"
echo "  📡  http://localhost:$PORT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# ── 서버 실행 ──────────────────────────────────────────────────
if [ "$MODE" = "prod" ]; then
  WORKERS="${WORKERS:-4}"
  exec "$PY" -m uvicorn backend.main:app \
    --host 0.0.0.0 --port "$PORT" \
    --workers "$WORKERS" \
    --proxy-headers --forwarded-allow-ips='*' \
    --log-level warning
else
  exec "$PY" -m uvicorn backend.main:app \
    --reload --host 127.0.0.1 --port "$PORT" \
    --log-level info
fi
