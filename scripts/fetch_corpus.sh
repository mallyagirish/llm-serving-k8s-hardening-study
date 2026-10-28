#!/usr/bin/env bash
# Fetch verified LLM-serving K8s sources into corpus/charts and corpus/manifests.
# Prefer scripts/fetch_and_render.sh for the full Phase 2 pipeline.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$ROOT/scripts/fetch_and_render.sh"
