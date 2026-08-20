# Releasing the GitShelves web MVP

GitShelves owns immutable build artifacts; Sugarkube later owns environment overlays and deployment. Cloudflare DNS and Tunnel routing remain external.

## Validate and build

```bash
pip install -e .
black --check . && pytest -q
cd web && npm ci && npm run format && npm run lint && npm run typecheck && npm test
npm run models:prepare && npm run build
docker build -t gitshelves:local .
helm lint charts/gitshelves --set image.tag=main-0123456789ab
helm template gitshelves charts/gitshelves --set image.tag=main-0123456789ab
```

The multi-stage [Dockerfile](../Dockerfile) pins Node, Python, OpenSCAD, and the Gridfinity commit. OpenSCAD runs on the build platform so its generated STL bytes are architecture-independent inputs to both target images. The final Python standard-library server contains neither Node nor OpenSCAD, runs as UID 10001 on 8080, writes no state, and needs no temporary filesystem mount; it supports a read-only root filesystem.

## Immutable coordinates

The [image workflow](https://github.com/futuroptimist/gitshelves/actions/workflows/ci-image.yml) prints the multi-platform digest and lowercase `main-<shortsha>` tag. Images live in [GHCR](https://github.com/futuroptimist/gitshelves/pkgs/container/gitshelves). Never deploy `latest`, a bare branch, `staging`, or `production`.

The [chart workflow](https://github.com/futuroptimist/gitshelves/actions/workflows/ci-helm.yml) publishes `oci://ghcr.io/futuroptimist/charts/gitshelves`. Every chart content change requires a SemVer bump in [Chart.yaml](../charts/gitshelves/Chart.yaml); an existing version is never overwritten. Image tag and chart version are independent: changing application bytes does not silently mutate a chart, and changing templates requires a new chart version.

Source links: [Dockerfile](https://github.com/futuroptimist/gitshelves/blob/main/Dockerfile), [chart](https://github.com/futuroptimist/gitshelves/tree/main/charts/gitshelves), [this guide](https://github.com/futuroptimist/gitshelves/blob/main/docs/releasing.md), [image packages](https://github.com/futuroptimist/gitshelves/pkgs/container/gitshelves), and [package index](https://github.com/orgs/futuroptimist/packages).

## Install, upgrade, test, rollback

```bash
helm template gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves \
  --version 0.1.0 --set image.tag=main-REPLACE_SHORTSHA
helm install gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves \
  --version 0.1.0 --set image.tag=main-REPLACE_SHORTSHA
helm upgrade gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves \
  --version 0.1.1 --set image.tag=main-REPLACE_SHORTSHA
helm test gitshelves
helm rollback gitshelves PREVIOUS_REVISION
```

Prefer rollback by redeploying the previous known-good immutable chart version and image tag; record both. Before staging, Sugarkube must provide its own `staging.gitshelves.com` ingress/TLS overlay, verify `/`, `/healthz`, and `/livez`, discover observability, capture deployment proof, and prove rollback. This repository intentionally contains no environment overlay or Cloudflare resource.
