# syntax=docker/dockerfile:1.7
ARG OPENSCAD_IMAGE=openscad/openscad@sha256:147e48525bec392bcf628d7a6d5ea4ccac71b16251952328f86e1061cbf47c37
ARG NODE_IMAGE=node:22.19.0-alpine3.22@sha256:d2166de198f26e17e5a442f537754dd616ab069c47cc57b889310a717e0abbf9
ARG RUNTIME_IMAGE=python:3.13.7-alpine3.22@sha256:9ba6d8cbebf0fb6546ae71f2a1c14f6ffd2fdab83af7fa5669734ef30ad48844
FROM --platform=$BUILDPLATFORM ${OPENSCAD_IMAGE} AS models
USER root
RUN apt-get update && apt-get install -y --no-install-recommends git xvfb && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY openscad ./openscad
RUN rm -rf openscad/lib/gridfinity-rebuilt && git clone https://github.com/kennetek/gridfinity-rebuilt-openscad.git openscad/lib/gridfinity-rebuilt && cd openscad/lib/gridfinity-rebuilt && git checkout 910e22d8607fd7f5f51ad5e5cbc5287a76810bfd && rm -rf .git
RUN mkdir -p /models && xvfb-run -a openscad -o /models/baseplate_2x6.stl --export-format binstl openscad/baseplate_2x6.scad && xvfb-run -a openscad -o /models/contrib_cube.stl --export-format binstl openscad/contrib_cube.scad && test -s /models/baseplate_2x6.stl && test -s /models/contrib_cube.stl
FROM ${NODE_IMAGE} AS web
WORKDIR /src/web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web ./
COPY --from=models /models ./public/models
RUN npm run build
FROM ${RUNTIME_IMAGE} AS runtime
RUN addgroup -S -g 10001 gitshelves && adduser -S -D -H -u 10001 -G gitshelves gitshelves
WORKDIR /app
COPY --from=web --chown=10001:10001 /src/web/dist /app
COPY --chown=10001:10001 deploy/server.py /server.py
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["python","/server.py"]
