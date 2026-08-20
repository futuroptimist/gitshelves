# GitShelves roadmap

Each phase depends on the prior phase unless stated. Checked items are completed by this PR only.

## 1. Browser and release-contract MVP
- [x] Product/engineering design and monthly browser preview.
- [x] Local metadata/STL ingestion, manifest, exact canonical downloads, and fallback.
- [x] Reproducible container contract, GHCR image workflow, Helm chart/workflow, and release guide.
- [x] Unit/browser/health/chart test coverage.

**Exit:** synthetic sample is immediately useful; canonical models are generated during production build; immutable image/chart contracts validate. **Risk:** physical behavior remains unvalidated.

## 2. Physical validation
- [ ] Design calibration coupons; test PLA/PETG, layer heights, and tolerance variants.
- [ ] Record real prints, dimensional results, repeated assembly, wobble, shear, and stack stability.

**Dependency:** canonical MVP geometry. **Exit:** reproducible evidence matrix and supported tolerances. **Risk:** redesign may invalidate geometry assumptions.

## 3. Authenticated contribution API
- [ ] Versioned same-origin API and GitHub App/OAuth retrieval.
- [ ] Server-only token lifecycle, caching, quotas, validation, and API contract tests.

**Dependency:** security review and limits. **Exit:** no token reaches browser/storage/logs; rate-limit behavior proven. **Risk:** GitHub quotas/auth complexity.

## 4. Isolated generation
- [ ] Bounded asynchronous queue and isolated OpenSCAD workers.
- [ ] Integrity manifests, storage, expiry, cleanup, signed download bundles.

**Dependency:** API and validated geometry. **Exit:** resource/abuse tests and deterministic bundle. **Risk:** CPU exhaustion and artifact retention.

## 5. Sugarkube staging
- [ ] Deploy immutable coordinates to `staging.gitshelves.com` via Sugarkube overlay.
- [ ] Prove rate limits, public/internal observability, verification, and rollback.

**Dependency:** published artifacts; external DNS/Tunnel. **Exit:** recorded deployment and rollback proof. **Risk:** ARM/k3s capacity and Cloudflare routing.

## 6. Production
- [ ] Launch `gitshelves.com`; configure external `www` redirect.
- [ ] Publish operating/incident expectations.

**Dependency:** staging acceptance. **Exit:** health, download, monitoring, rollback, and redirect proof. **Risk:** abuse/cost/support load.

## 7. Product expansion
- [ ] Research daily 53×7 view and modular carrier tiles.
- [ ] Add validated palettes/connectors, saved projects, sharing, and optional metrics.

**Dependency:** demand and physical evidence. **Exit:** separate reviewed designs and privacy policy. **Risk:** scope, accessibility, and physical fragmentation.
