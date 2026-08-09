ARG DEBIAN_MIRROR=http://mirrors.aliyun.com/debian
ARG DEBIAN_SECURITY_MIRROR=http://mirrors.aliyun.com/debian-security
ARG GITHUB_DOWNLOAD_PREFIX=https://ghfast.top/

FROM node:24-alpine AS web-builder

WORKDIR /build
COPY frontend/package.json frontend/package-lock.json ./frontend/
RUN npm --prefix frontend ci --no-audit --no-fund
COPY frontend/ ./frontend/
COPY third_party_games/ ./third_party_games/
RUN npm --prefix frontend run build


FROM debian:bookworm-slim AS ai-builder-base

ARG DEBIAN_MIRROR
ARG DEBIAN_SECURITY_MIRROR
ARG GITHUB_DOWNLOAD_PREFIX

RUN sed -i \
      -e "s|http://deb.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
      -e "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g" \
      /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
      ca-certificates cmake curl g++ libeigen3-dev make p7zip-full zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*


FROM ai-builder-base AS pikafish-builder

ARG TARGETARCH
ARG PIKAFISH_VERSION=Pikafish-2026-01-02
ARG PIKAFISH_SOURCE_SHA256=d1482fb903c0b757f8c8cc09c5d057e27f0a8b17934715faf2c58797dd999493
ARG PIKAFISH_RELEASE_SHA256=84257063905615919fb4ee6a70273a94843bb6ec04c45e3ac706098838bc1a49
ARG PIKAFISH_NET_SHA256=c4026370d7516d9b0f668447f9ca1931241538bdc689cde6fec6a991ac4d5f77

WORKDIR /src
RUN download_verified() { \
      expected="$1"; target="$2"; url="$3"; \
      for candidate in "${GITHUB_DOWNLOAD_PREFIX}${url}" "$url"; do \
        if curl -fL --retry 5 --retry-all-errors --connect-timeout 15 \
             "$candidate" -o "$target" \
          && echo "${expected}  ${target}" | sha256sum -c -; then \
          return 0; \
        fi; \
      done; \
      return 1; \
    } \
    && download_verified \
      "$PIKAFISH_SOURCE_SHA256" "/tmp/pikafish-source.tar.gz" \
      "https://github.com/official-pikafish/Pikafish/archive/refs/tags/${PIKAFISH_VERSION}.tar.gz" \
    && tar -xzf /tmp/pikafish-source.tar.gz \
    && mv "Pikafish-${PIKAFISH_VERSION}" Pikafish \
    && download_verified \
      "$PIKAFISH_RELEASE_SHA256" "/tmp/pikafish-release.7z" \
      "https://github.com/official-pikafish/Pikafish/releases/download/${PIKAFISH_VERSION}/Pikafish.2026-01-02.7z" \
    && mkdir -p /tmp/pikafish-release \
    && 7z e -y -o/tmp/pikafish-release \
      /tmp/pikafish-release.7z pikafish.nnue >/dev/null \
    && cp /tmp/pikafish-release/pikafish.nnue Pikafish/src/pikafish.nnue \
    && echo "${PIKAFISH_NET_SHA256}  Pikafish/src/pikafish.nnue" | sha256sum -c - \
    && case "$TARGETARCH" in \
         amd64) pikafish_arch=x86-64 ;; \
         arm64) pikafish_arch=armv8 ;; \
         *) pikafish_arch=general-64 ;; \
       esac \
    && make -C Pikafish/src -j"$(nproc)" build ARCH="$pikafish_arch" \
    && mkdir -p /out \
    && cp Pikafish/src/pikafish Pikafish/src/pikafish.nnue /out/ \
    && curl -fsSL "https://raw.githubusercontent.com/official-pikafish/Networks/a238f8da2df269c28fec0e2bd2ca0ffd241f83fe/README.md" \
      -o /out/PIKAFISH-NNUE-LICENSE.md \
    && make -C Pikafish/src clean \
    && rm Pikafish/src/pikafish.nnue


FROM ai-builder-base AS katago-builder

ARG KATAGO_VERSION=1.17.2
ARG KATAGO_MODEL_VERSION=1.17.0
ARG KATAGO_SOURCE_SHA256=d4531e969df138e1d0bc91f02dfd737c88c08296c922e78e63289af443ec501e
ARG KATAGO_MODEL_SHA256=0ba27eced5180b3e3d0b898b280c541112989765e789d1eb6cd0d31b2b2c1229

WORKDIR /src
RUN download_verified() { \
      expected="$1"; target="$2"; url="$3"; \
      for candidate in "${GITHUB_DOWNLOAD_PREFIX}${url}" "$url"; do \
        if curl -fL --retry 5 --retry-all-errors --connect-timeout 15 \
             "$candidate" -o "$target" \
          && echo "${expected}  ${target}" | sha256sum -c -; then \
          return 0; \
        fi; \
      done; \
      return 1; \
    } \
    && download_verified \
      "$KATAGO_SOURCE_SHA256" "/tmp/katago-source.tar.gz" \
      "https://github.com/lightvector/KataGo/archive/refs/tags/v${KATAGO_VERSION}.tar.gz" \
    && tar -xzf /tmp/katago-source.tar.gz \
    && mv "KataGo-${KATAGO_VERSION}" KataGo \
    && cmake -S KataGo/cpp -B KataGo/build \
      -DUSE_BACKEND=EIGEN -DNO_GIT_REVISION=1 -DCMAKE_BUILD_TYPE=Release \
    && cmake --build KataGo/build --parallel "$(nproc)" \
    && download_verified \
      "$KATAGO_MODEL_SHA256" "/src/katago-model.bin.gz" \
      "https://github.com/lightvector/KataGo/releases/download/v${KATAGO_MODEL_VERSION}/b10c384h6nbttflrs.bin.gz"


FROM python:3.13-slim AS runtime

ARG DEBIAN_MIRROR
ARG DEBIAN_SECURITY_MIRROR
ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIKAFISH_PATH=/opt/game-hall/ai/pikafish \
    PIKAFISH_EVAL_FILE=/opt/game-hall/ai/pikafish.nnue \
    KATAGO_PATH=/opt/game-hall/ai/katago \
    KATAGO_MODEL_PATH=/opt/game-hall/ai/katago-model.bin.gz \
    KATAGO_CONFIG_PATH=/opt/game-hall/ai/katago-analysis.cfg

RUN sed -i \
      -e "s|http://deb.debian.org/debian-security|${DEBIAN_SECURITY_MIRROR}|g" \
      -e "s|http://deb.debian.org/debian|${DEBIAN_MIRROR}|g" \
      /etc/apt/sources.list.d/debian.sources \
    && apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 libstdc++6 zlib1g \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY backend/ ./backend/
RUN pip install --no-cache-dir --index-url "$PIP_INDEX_URL" ./backend
COPY third_party_games/ ./third_party_games/
COPY --from=web-builder /build/frontend/dist ./frontend/dist
COPY --from=pikafish-builder /out/pikafish /opt/game-hall/ai/pikafish
COPY --from=pikafish-builder /out/pikafish.nnue /opt/game-hall/ai/pikafish.nnue
COPY --from=pikafish-builder /src/Pikafish /usr/share/game-hall/source/pikafish
COPY --from=katago-builder /src/KataGo/build/katago /opt/game-hall/ai/katago
COPY --from=katago-builder /src/katago-model.bin.gz /opt/game-hall/ai/katago-model.bin.gz
COPY backend/app/ai/katago-analysis.cfg /opt/game-hall/ai/katago-analysis.cfg
COPY --from=pikafish-builder /src/Pikafish/Copying.txt /usr/share/game-hall/licenses/PIKAFISH-GPL-3.0.txt
COPY --from=pikafish-builder /out/PIKAFISH-NNUE-LICENSE.md /usr/share/game-hall/licenses/PIKAFISH-NNUE-LICENSE.md
COPY --from=katago-builder /src/KataGo/LICENSE /usr/share/game-hall/licenses/KATAGO.txt

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=2)"

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
