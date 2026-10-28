# Hardening LLM Inference on Kubernetes

Empirical study of security and reliability misconfigurations in production LLM serving stacks on Kubernetes (Helm charts and manifests).

**Author:** [Girish Mallya](https://github.com/mallyagirish)  
**Working paper title:** *Hardening LLM Inference on Kubernetes: An Empirical Study of Production Serving Stacks*

## What’s in this repo

- `docs/PHASE1_RULES_AND_CORPUS.md` — 28-rule catalog + corpus design
- `corpus/SOURCES.lock.json` — pinned sources and collection timestamp
- `corpus/rendered/` — `helm template` / manifest outputs used for analysis
- `corpus/manifests/` — raw public Kubernetes YAML samples
- `scripts/` — fetch + render reproducibility scripts
- `rules/` — rule definitions / probes (growing)

The large fetched chart clones under `corpus/charts/` are **not** committed (≈1.3 GB). Re-fetch with:

```bash
./scripts/fetch_and_render.sh
```

## Reproduce

Requires: `helm`, `git`, `curl`, `jq`.

```bash
./scripts/fetch_and_render.sh   # full fetch + render + lockfile
# or
./scripts/render_all.sh         # re-render charts already under corpus/charts/
```

## Status

- Phase 1 (rules + corpus plan): done
- Phase 2 (fetch + render): done locally — 202 rendered bundles from 27 pinned sources (2026-10-28, America/Los_Angeles)
- Phase 3 (scan probes + prevalence): next

## Ethics / scope

Public configurations only. Tutorial and default values are expected to be insecure in places; findings characterize defaults, not production private clusters.

## License

See `LICENSE` if present; otherwise contributions welcome under Apache-2.0 intent pending LICENSE file.
