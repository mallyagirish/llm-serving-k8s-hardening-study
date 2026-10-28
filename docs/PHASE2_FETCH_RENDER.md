# Phase 2 — Corpus fetch + render

**Status:** complete  
**collected_at:** 2026-10-28T16:34:08-07:00 (America/Los_Angeles)  
**Lockfile:** `corpus/SOURCES.lock.json`

## Counts

See lockfile `counts` object. Headline: **203 rendered bundles** from **27 sources** (target ≥40 met).

Breakdown (approx): 21 helm-default, 28 helm-values overlays (incl. 26 vLLM tutorials), 154 manifests.

## Scripts

- `scripts/fetch_and_render.sh` — full pipeline
- `scripts/fetch_corpus.sh` — wrapper
- `scripts/render_all.sh` — re-render without re-clone
- `.github/workflows/ci.yml` — smoke assert lockfile + ≥40 bundles

## Blockers / skips

- louis030195 TGI helm: values use `models[]` but templates expect `model.*` — raw templates kept
- shalb OCI `huggingface-model` 0.1.4: library chart; git application chart rendered
- NVIDIA NIM / SiloGen / Open WebUI: candidates skipped (entitlement or not verified this pass)
