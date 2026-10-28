#!/usr/bin/env bash
# Re-render helm charts already under corpus/charts into corpus/rendered/.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
export PATH="/usr/local/bin:${PATH:-}"
CHARTS="$ROOT/corpus/charts"
RENDERED="$ROOT/corpus/rendered"
ok=0; fail=0

render_chart() {
  local name="$1" chart="$2"; shift 2
  local outdir="$RENDERED/$name"
  mkdir -p "$outdir"
  if helm template "scan-${name}" "$chart" --namespace llm-scan "$@" >"$outdir/default.yaml" 2>"$outdir/default.yaml.err"; then
    rm -f "$outdir/default.yaml.err"
    echo "OK $name"
    ok=$((ok+1))
  else
    echo "FAIL $name"; fail=$((fail+1))
  fi
}

# vLLM stack versions
for VER in 0.1.13 0.1.12 0.1.11 0.1.10; do
  c="$CHARTS/vllm-stack-$VER/vllm-stack"
  [[ -d "$c" ]] || continue
  render_chart "vllm-stack-$VER" "$c" \
    --set 'kube-prometheus-stack.enabled=false' \
    --set 'prometheus-adapter.enabled=false' \
    --set 'k8s-aibom.enabled=false'
done

# Tutorials
WORK="$CHARTS/vllm-stack-tut-work"
TUT="$CHARTS/production-stack-git/tutorials/assets"
if [[ -d "$WORK" && -d "$TUT" ]]; then
  OUT="$RENDERED/vllm-stack-0.1.13-tutorials"
  mkdir -p "$OUT"
  for vf in "$TUT"/values-*.yaml; do
    base=$(basename "$vf" .yaml)
    rel="scan-$(echo "$base" | sed 's/values-//' | tr 'A-Z' 'a-z' | cut -c1-40)"
    if helm template "$rel" "$WORK" -f "$vf" --namespace llm-scan \
      --set 'kube-prometheus-stack.enabled=false' \
      --set 'prometheus-adapter.enabled=false' \
      --set 'k8s-aibom.enabled=false' \
      >"$OUT/${base}.yaml" 2>"$OUT/${base}.yaml.err"; then
      rm -f "$OUT/${base}.yaml.err"; echo "OK tut $base"; ok=$((ok+1))
    else
      echo "FAIL tut $base"; fail=$((fail+1))
    fi
  done
fi

echo "render_all done ok=$ok fail=$fail"
