# syntax=docker/dockerfile:1.7
ARG OPENSCAD_IMAGE=openscad/openscad:bookworm.2026-01-19
FROM --platform=$BUILDPLATFORM ${OPENSCAD_IMAGE} AS models
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git xvfb python3 && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY openscad/ openscad/
COPY scripts/fetch_gridfinity.sh scripts/prepare_web_models.py scripts/
RUN scripts/fetch_gridfinity.sh && python3 scripts/prepare_web_models.py
FROM --platform=$BUILDPLATFORM node:22.18.0-bookworm-slim AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
COPY --from=models /src/web/public/models ./public/models
RUN npm run build
FROM python:3.12.11-alpine3.22
RUN addgroup -S -g 10001 app && adduser -S -D -H -u 10001 -G app app
WORKDIR /app
COPY --from=web --chown=app:app /src/web/dist/ ./
COPY --chown=app:app scripts/static_server.py /server.py
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["python3","/server.py"]
