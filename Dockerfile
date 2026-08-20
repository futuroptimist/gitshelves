# syntax=docker/dockerfile:1.7
FROM --platform=$BUILDPLATFORM debian:bookworm-slim@sha256:abd67ffcfa541b485a3dff59865ab629aa048a6c613e639d36e7456b0b229241 AS models
ARG GRIDFINITY_COMMIT=910e22d8607fd7f5f51ad5e5cbc5287a76810bfd
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates git openscad=2021.01-6 python3 xauth xvfb && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY openscad ./openscad
COPY web/scripts/validate-stl.py ./validate-stl.py
RUN rm -rf openscad/lib/gridfinity-rebuilt && git clone https://github.com/kennetek/gridfinity-rebuilt-openscad.git openscad/lib/gridfinity-rebuilt && git -C openscad/lib/gridfinity-rebuilt checkout --detach "$GRIDFINITY_COMMIT" && \
    mkdir -p /models && xvfb-run -a openscad -o /models/baseplate_2x6.stl --export-format binstl openscad/baseplate_2x6.scad && \
    xvfb-run -a openscad -o /models/contrib_cube.stl --export-format binstl openscad/contrib_cube.scad && python3 ./validate-stl.py /models/baseplate_2x6.stl /models/contrib_cube.stl

FROM --platform=$BUILDPLATFORM node:22.19.0-alpine3.22@sha256:d2166de198f26e17e5a442f537754dd616ab069c47cc57b889310a717e0abbf9 AS web-build
WORKDIR /app
COPY web/package.json web/package-lock.json ./
RUN npm ci --ignore-scripts
COPY web/ ./
COPY --from=models /models/ ./public/models/
RUN npm run build

FROM python:3.12.10-alpine3.21
WORKDIR /app
COPY --from=web-build --chown=10001:10001 /app/dist ./dist
COPY --chown=10001:10001 web/server.py ./server.py
USER 10001:10001
EXPOSE 8080
ENTRYPOINT ["python3", "/app/server.py"]
