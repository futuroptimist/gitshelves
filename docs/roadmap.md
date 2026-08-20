# GitShelves hosted-product roadmap

Checkboxes describe merged implementation only; plans and documents do not make future runtime work complete.

## 1. Opening web/release contract (this PR)
- [x] Product design and browser-only Three.js MVP with local imports and manifest.
- [x] Reproducible container contract, GHCR image workflow, environment-neutral Helm chart/workflow, and release guide.
- Dependencies: existing metadata/OpenSCAD and pinned Gridfinity input. Risk: physical interfaces remain unvalidated.
- Exit: web checks pass; canonical models build; static endpoints and chart render are verified.

## 2. Physical calibration
- [ ] Design coupons; test-print base/module interfaces across documented printer/material/layer profiles; measure fit, repeat cycles, wobble, shear, and stack stability; publish results.
- Dependency: agreed pass thresholds and hardware access. Risk: tolerance varies by printer/material.
- Exit: versioned evidence matrix identifies at least one repeatable profile and explicitly records failures.

## 3. Contribution API/authentication
- [ ] Versioned same-origin API and authenticated server-side GitHub retrieval; cache, quota/backoff, validation, and redacted telemetry.
- Dependency: authentication/privacy decisions and phase 1 schema. Risk: token leakage and GitHub quotas.
- Exit: integration tests prove tokens never enter browser storage/logs and responses reproduce canonical counts.

## 4. Isolated generation
- [ ] Bounded asynchronous queue, isolated OpenSCAD worker, validated manifest, expiring storage, and signed download bundles.
- Dependency: phase 3 API and worker limits. Risk: resource abuse and CAD nondeterminism.
- Exit: load/abuse tests prove concurrency, time, memory, path, size, expiry, and cleanup limits.

## 5. Sugarkube staging
- [ ] Deploy immutable coordinates at `staging.gitshelves.com`; add rate limits, observability discovery, deployment proof, and rollback proof.
- Dependency: phases 3–4 and external Cloudflare routing. Risk: ARM/k3s capacity.
- Exit: public health/user-flow checks, dashboards/alerts, and recorded rollback pass.

## 6. Production
- [ ] Launch `gitshelves.com` and external `www` redirect using staging-approved immutable artifacts.
- Dependency: security, accessibility, physical validation, operations approval. Risk: demand and support load.
- Exit: production smoke/monitoring, rollback coordinate, incident ownership, and DNS/Tunnel evidence recorded.

## 7. Later product work
- [ ] Daily 53×7 views, modular carriers, validated alternate connectors, palettes, saved projects, sharing, and optional metrics.
- Dependency: research and privacy decisions. Risk: complexity and physical footprint.
- Exit: each capability gets a focused design, measurable acceptance criteria, and its own reviewable PR.
