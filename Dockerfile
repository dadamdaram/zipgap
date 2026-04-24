# ═══════════════════════════════════════════════════════════════
#  집값추적기 v12 — Dockerfile (멀티스테이지 프로덕션 빌드)
#
#  빌드:  docker build -t jibgap .
#  실행:  docker run -p 8000:8000 -e MOLIT_KEY=발급키 jibgap
#  또는:  docker compose up
# ═══════════════════════════════════════════════════════════════

# ── Stage 1: 의존성 빌드 ──────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# 빌드 도구 최소화
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
  && rm -rf /var/lib/apt/lists/*

# 의존성만 먼저 복사 (레이어 캐시 활용)
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


# ── Stage 2: 런타임 이미지 ────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# 빌드 결과 복사
COPY --from=builder /install /usr/local

# 앱 소스 복사
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# 데이터 디렉토리 (SQLite 영구 저장용 볼륨 마운트 포인트)
RUN mkdir -p /app/data && \
    # 실행 권한
    adduser --disabled-password --no-create-home appuser && \
    chown -R appuser:appuser /app
USER appuser

# env.js: 빌드 시 MOLIT_KEY 주입 (ARG) 또는 런타임 환경변수로 대체
ARG MOLIT_KEY=""
RUN echo "window.__ENV__ = { MOLIT_KEY: \"${MOLIT_KEY}\", generated: \"$(date -u +%Y-%m-%dT%H:%M:%SZ)\" };" \
    > /app/frontend/env.js

EXPOSE 8000

# 헬스체크
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/status')" || exit 1

# 프로덕션 실행 (멀티워커)
ENV WORKERS=4
CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers ${WORKERS} --proxy-headers --forwarded-allow-ips='*' --log-level warning"]
