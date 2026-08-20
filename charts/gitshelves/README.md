# GitShelves chart

Use an immutable image coordinate:

```sh
helm lint charts/gitshelves --set image.tag=main-0123abcd
helm template gitshelves charts/gitshelves --set image.tag=main-0123abcd
helm install gitshelves charts/gitshelves --set image.tag=main-0123abcd
helm upgrade gitshelves charts/gitshelves --set image.tag=main-89abcdef
helm test gitshelves
helm rollback gitshelves 1
```

Ingress is disabled and hostless by default. Enable it with `ingress.enabled=true`, `ingress.className`, `ingress.host`, and `ingress.tls`. The chart contains no secrets or environment-specific hostname.
