# Releasing GitShelves

GitShelves publishes two separate immutable coordinates: image `ghcr.io/futuroptimist/gitshelves:main-<shortsha>` and chart `oci://ghcr.io/futuroptimist/charts/gitshelves:<chart-version>`. A chart version never selects an image tag automatically.

## Validate and build

```bash
pip install -e .
black --check . && pytest -q
cd web && npm ci && npm run format:check && npm run lint && npm run typecheck && npm test
npm run prepare:models && npm run build
cd ..
docker build -t gitshelves:local .
helm lint charts/gitshelves --set image.tag=main-0123456
helm template gitshelves charts/gitshelves --set image.tag=main-0123456
```

The Docker model stage fetches Gridfinity revision `55fc273ddce8a5ea4c0575d6005482baa82951a7`, renders both canonical models, checks the meshes, and lets Vite copy those exact bytes. Generated STLs and `dist/` are ignored.

## Publish and discover

The [image workflow](https://github.com/futuroptimist/gitshelves/actions/workflows/ci-image.yml) publishes only trusted `main` pushes/manual runs and prints the tag/digest. Inspect the [image package](https://github.com/futuroptimist/gitshelves/pkgs/container/gitshelves), select the successful `main-<shortsha>`, and retain its digest.

Every chart content change requires a SemVer bump in [`Chart.yaml`](../charts/gitshelves/Chart.yaml): patch for compatible template/default fixes, minor for additive operator features, major for incompatible values/resource behavior. Never overwrite a version. The [chart workflow](https://github.com/futuroptimist/gitshelves/actions/workflows/ci-helm.yml) rejects an existing version and prints the OCI coordinate; inspect [GHCR packages](https://github.com/orgs/futuroptimist/packages?repo_name=gitshelves).

Source anchors: [Dockerfile](../Dockerfile), [chart source](../charts/gitshelves/), and [this release guide](releasing.md).

## Staging and rollback

Sugarkube—not this chart—supplies `staging.gitshelves.com`, ingress/TLS overlays, deploy verification, observability discovery, and rollback. Cloudflare supplies DNS and Tunnel routing. Before promotion, record image tag **and digest**, chart version, rendered values, `/`, `/healthz`, `/livez`, and Helm smoke-test outcomes.

```bash
helm upgrade --install gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves \
  --version 0.1.0 --set image.tag=main-0123456 -f environment-owned-values.yaml
helm test gitshelves
helm history gitshelves
helm rollback gitshelves PREVIOUS_REVISION
```

For a bad application build with unchanged chart, redeploy the previous known-good `main-<shortsha>` tag. For a bad rendered release, roll back to the previous Helm revision, then verify both health routes. Never use `latest`, bare `main`, `staging`, or `production` as deployment coordinates.
