# GitShelves product roadmap

Checkboxes mean repository work is present and verified in the named phase; future intent remains unchecked. Dependencies, risks, and measurable exit criteria prevent aspirational features from looking shipped.

## 1. Opening web and release contract (this PR)

- [x] Product/physical/hosted engineering design and browser-only architecture.
- [x] Strict TypeScript Vite/Three.js MVP with synthetic sample, local import, text plan, manifest, and proxy/exact distinction.
- [x] Reproducible model-preparation path, production container contract, GHCR workflow, app-owned Helm chart/workflow, and release guide.
- [x] Unit, browser-smoke, server, and chart validation coverage added.

**Dependencies:** existing Python metadata/OpenSCAD sources and pinned Gridfinity revision. **Risks:** CI and local tool availability; no fit evidence. **Exit:** required sources exist, generated assets remain ignored, immutable coordinates are enforced, and applicable checks pass or are reported precisely.

## 2. Physical calibration

- [ ] Parameterized base/module coupons and documented measurement protocol.
- [ ] Real PLA and PETG test prints on at least two printers/layer profiles.
- [ ] Recorded dimensions, repeated assembly, wobble, shear, stability, wear, photos, and failures.
- [ ] Fit claims updated only from evidence.

**Depends on:** phase 1 geometry pin. **Risk:** printer/material variation. **Exit:** reviewable result dataset and a supported tolerance envelope.

## 3. Authenticated contribution API

- [ ] Versioned same-origin API and schemas.
- [ ] GitHub App/OAuth server boundary, conditional cache, quotas, rate limiting, and redaction tests.

**Depends on:** threat-model decisions and secret operations. **Risk:** token/quota leakage. **Exit:** no browser token, contract tests, audit logs without identity secrets, and bounded retrieval.

## 4. Isolated generation

- [ ] Bounded asynchronous queue and isolated OpenSCAD workers.
- [ ] CPU/memory/time/output limits, mesh checks, manifest hashes, storage, expiry, cleanup, and signed bundles.

**Depends on:** phases 2–3 and pinned CAD image. **Risk:** compute abuse and nondeterminism. **Exit:** load/failure tests prove limits, cleanup, and reproducible artifact manifests.

## 5. Sugarkube staging

- [ ] Deploy immutable image/chart coordinates at `staging.gitshelves.com` via external overlays.
- [ ] Rate limits, blackbox/optional metrics discovery, deployment proof, and rollback proof.

**Depends on:** publishable phases 3–4 plus Cloudflare/Sugarkube ownership. **Risk:** ARM/k3s capacity and routing. **Exit:** recorded deploy, `/healthz`/`/livez`, representative generation, observability, and rollback evidence.

## 6. Production

- [ ] Launch `gitshelves.com`; configure external `www` redirect.
- [ ] Operational SLOs, incident/backup/abuse runbooks, accessibility and physical-product sign-off.

**Depends on:** staging evidence. **Risk:** scale, support, safety claims. **Exit:** monitored production journey and tested rollback with immutable coordinates.

## 7. Later product work

- [ ] Daily 53×7 view and physically validated modular carrier tiles.
- [ ] Palettes, saved projects, sharing, and optional privacy-safe metrics.

**Depends on:** research and user evidence. **Risk:** part count, privacy, persistence complexity. **Exit:** separate approved designs and scoped implementation PRs.
