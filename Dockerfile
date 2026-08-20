# syntax=docker/dockerfile:1.7
FROM --platform=$BUILDPLATFORM debian:bookworm-slim AS models
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git openscad xvfb python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY openscad ./openscad
COPY web/scripts ./web/scripts
RUN web/scripts/prepare-models.sh /models

FROM --platform=$BUILDPLATFORM node:22.18.0-bookworm-slim AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY --from=models /models ./public/models
RUN npm run build

FROM python:3.13.7-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 GITSHELVES_ROOT=/app
RUN groupadd --gid 10001 gitshelves && useradd --uid 10001 --gid 10001 --no-create-home --shell /usr/sbin/nologin gitshelves
WORKDIR /app
COPY --from=web --chown=10001:10001 /src/web/dist/ ./
COPY --chown=10001:10001 server/server.py /server.py
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["python3","/server.py"]
