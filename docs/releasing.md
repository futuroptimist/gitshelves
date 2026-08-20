# Releasing the GitShelves web application

## Validate and build

```sh
pip install -e . && black --check . && pytest -q
cd web && npm ci && npm run format && npm run lint && npm run typecheck && npm test
cd .. && scripts/fetch_gridfinity.sh && python scripts/prepare_web_models.py
cd web && npm run build
cd .. && docker build -t gitshelves:verify .
helm lint charts/gitshelves --set image.tag=main-0123abcd
```

The multi-stage [Dockerfile](../Dockerfile) generates the pinned Gridfinity/OpenSCAD base and module, builds Vite from the lockfile, then copies only static output and a Python standard-library server. Node/OpenSCAD are absent at runtime; UID 10001 listens on 8080 and needs no writable temporary mount, so read-only root works.

## Immutable coordinates

The [image workflow](../.github/workflows/ci-image.yml) validates pull requests and publishes main/manual builds to `ghcr.io/futuroptimist/gitshelves:main-<shortsha>`. Discover the exact tag and digest in its summary/log: <https://github.com/futuroptimist/gitshelves/actions/workflows/ci-image.yml>. Package: <https://github.com/futuroptimist/gitshelves/pkgs/container/gitshelves>.

The [chart source](../charts/gitshelves/) and [chart workflow](../.github/workflows/ci-helm.yml) publish `oci://ghcr.io/futuroptimist/charts/gitshelves:<chart-version>`; see <https://github.com/futuroptimist/gitshelves/actions/workflows/ci-helm.yml> and <https://github.com/orgs/futuroptimist/packages?repo_name=gitshelves>. Every chart-content change requires a SemVer `Chart.yaml` version bump: patch for compatible templates/default fixes, minor for compatible features, major for breaking values/templates. Publishing refuses an existing version.

Image tag and chart version are independent immutable coordinates. A chart may deploy many image releases; never substitute `latest`, branch-only, `staging`, or `production`.

## Staging and rollback

GitShelves publishes artifacts only. Sugarkube later supplies the `staging.gitshelves.com` overlay, deploys, verifies `/healthz` and `/livez`, discovers observability, and proves rollback. Cloudflare supplies DNS/Tunnel routing externally.

```sh
helm upgrade --install gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves \
  --version 0.1.0 --set image.tag=main-0123abcd
helm test gitshelves
helm rollback gitshelves PREVIOUS_REVISION
```

Prefer rollback to both the previous chart version and previously verified `main-<shortsha>` where template and image changed. This guide lives at <https://github.com/futuroptimist/gitshelves/blob/main/docs/releasing.md>.
