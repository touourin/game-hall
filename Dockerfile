FROM node:24-alpine AS web-builder

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN npm --prefix frontend ci --no-audit --no-fund
COPY frontend/ ./frontend/
COPY third_party_games/ ./third_party_games/
RUN npm --prefix frontend run build


FROM python:3.13-slim AS runtime

ARG PIP_INDEX_URL=https://pypi.org/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY backend/ ./backend/
RUN pip install --no-cache-dir --index-url "$PIP_INDEX_URL" ./backend
COPY third_party_games/ ./third_party_games/
COPY --from=web-builder /build/frontend/dist ./frontend/dist

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
