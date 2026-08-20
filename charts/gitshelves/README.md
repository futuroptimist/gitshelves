# GitShelves chart

The chart is environment-neutral and requires an immutable branch-SHA image tag.

```bash
helm lint . --set image.tag=main-0123456
helm template gitshelves . --set image.tag=main-0123456
helm install gitshelves . --set image.tag=main-0123456
helm upgrade gitshelves . --set image.tag=main-89abcde
helm test gitshelves
helm rollback gitshelves 1
```

Enable ingress with `ingress.enabled=true`, plus an explicit class, host, and optional TLS list. Sugarkube owns environment overlays; this chart embeds no staging hostname or secret.
