# Site artifact and owner handoff

The optional `site-export` Docker target reuses the existing models and web-build
stages. Docker, Helm and the default production image retain their current entry
points. No Site is registered or deployed by this repository or its CI.

```sh
docker buildx build --target site-export --output type=local,dest=site-artifact .
node scripts/validate-site.mjs site-artifact
```

The output contains `dist/index.html`, Vite assets, both canonical binary models
(`models/baseplate_2x6.stl` and `models/contrib_cube.stl`) and MIT notices for
Gitshelves, Gridfinity and Three.js. Validation refuses an incomplete model pair
and writes `SHA256SUMS` next to `dist`. Generated files must not be committed.
The PR-only Site artifact workflow uploads the same validated directory, named
with the PR head SHA. Check out that SHA when reproducing it.

The browser starts with synthetic contribution data. Metadata/STL imports and
downloads remain local to the browser; there is no live GitHub access, token flow,
server CAD generation or backend. Proxy geometry is explicitly non-printable.

## Owner-only deployment

After review, final-head CI and owner approval, use a separate private Sites
checkout, copy the validated `dist/`, and follow the current Sites workflow.
Its hosting manifest uses `static: {"directory": "dist"}` and the Site identity
returned by owner registration. Never put a real project ID or credentials in
this public repository. Registration, source synchronization and publication
are separate owner actions; the artifact alone is not a published Site.

Static hosting does not execute `web/server.py`: the container's `/healthz`,
`/livez` and Python cache-header behavior remain container features. Verify the
chosen static host's response headers during owner deployment. No Worker is
needed for the browser MVP. Smoke-test `/`, both model URLs, orbit/explode
controls, local imports and both STL downloads before sharing the Site URL.
