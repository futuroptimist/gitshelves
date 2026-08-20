# GitShelves chart

Use immutable, lowercase image coordinates only:

```bash
helm lint charts/gitshelves --set image.tag=main-0123456
helm template gitshelves charts/gitshelves --set image.tag=main-0123456
helm install gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves --version 0.1.0 --set image.tag=main-0123456
helm upgrade gitshelves oci://ghcr.io/futuroptimist/charts/gitshelves --version 0.1.1 --set image.tag=main-89abcde
helm test gitshelves
helm rollback gitshelves 1
```

Ingress is off and environment-neutral by default. Supply `ingress.enabled`, `ingress.className`, `ingress.host`, and `ingress.tls` from the environment owner. The stateless container needs no writable volume or temporary filesystem.
