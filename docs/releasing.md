# Web release guide

GitShelves publishes the image at `ghcr.io/futuroptimist/gitshelves` and the chart at `oci://ghcr.io/futuroptimist/charts/gitshelves`. Image tags and chart versions are independent immutable coordinates.

## Validate and build

```bash
pip install -e . && black --check . && pytest -q
cd web && npm ci && npm run format:check && npm run lint && npm run typecheck && npm test
npm run prepare:models && npm run build
cd .. && docker build -t gitshelves:local .
helm lint charts/gitshelves --set image.tag=main-0123456
helm template gitshelves charts/gitshelves --set image.tag=main-0123456
```

The model preparation step needs OpenSCAD, Xvfb when headless, and the pinned Gridfinity checkout. The multi-stage Docker build provides these inputs. Runtime is an audited in-repo Python standard-library static server; Node/OpenSCAD are absent. It writes no files and needs no temporary mount, so a read-only root filesystem is supported.

## Publish and discover

The [image workflow](https://github.com/futuroptimist/gitshelves/actions/workflows/ci-image.yml) prints `main-<shortsha>` and its multi-architecture digest. Source links: [Dockerfile](https://github.com/futuroptimist/gitshelves/blob/main/Dockerfile), [chart](https://github.com/futuroptimist/gitshelves/tree/main/charts/gitshelves), [chart workflow](https://github.com/futuroptimist/gitshelves/actions/workflows/ci-helm.yml), [image package](https://github.com/futuroptimist/gitshelves/pkgs/container/gitshelves), [chart package](https://github.com/futuroptimist/gitshelves/pkgs/container/charts%2Fgitshelves), and [this guide](https://github.com/futuroptimist/gitshelves/blob/main/docs/releasing.md).

Every chart-content change increments the SemVer `version` in `Chart.yaml`; never overwrite a published version. `appVersion` is descriptive and does not select an image. The chart workflow checks GHCR before pushing and prints the immutable OCI reference.

## Helm operations and rollback

```bash
helm template gitshelves charts/gitshelves --set image.tag=main-0123456
helm install gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves --version 0.1.0 --set image.tag=main-0123456
helm upgrade gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves --version 0.1.1 --set image.tag=main-89abcde
helm test gitshelves
helm rollback gitshelves PREVIOUS_REVISION
```

Sugarkube later supplies staging overlays including `staging.gitshelves.com`, performs verification and rollback, and discovers observability. Cloudflare DNS/Tunnel configuration is external. Roll back with the previous known-good chart version and image tag; record both coordinates.
