#!/usr/bin/env bash
# Phase 2: fetch verified LLM-serving K8s sources and helm-template them.
set -uo pipefail

ROOT="/workspace/llm-serving-k8s-hardening-study"
CORPUS="$ROOT/corpus"
CHARTS="$CORPUS/charts"
MANIFESTS="$CORPUS/manifests"
RENDERED="$CORPUS/rendered"
LOCK="$CORPUS/SOURCES.lock.json"
LOG="$CORPUS/fetch_render.log"
export PATH="/usr/local/bin:/home/box/.local/bin:$PATH"
export HELM_EXPERIMENTAL_OCI=1

mkdir -p "$CHARTS" "$MANIFESTS" "$RENDERED"
: > "$LOG"

COLLECTED_AT="$(TZ=America/Los_Angeles date '+%Y-%m-%dT%H:%M:%S%z' | sed 's/\([0-9][0-9]\)$/:\1/')"
SOURCES_JSONL="/tmp/sources.jsonl"
FAILURES_JSONL="/tmp/failures.jsonl"
BUNDLES_JSONL="/tmp/bundles.jsonl"
: > "$SOURCES_JSONL"
: > "$FAILURES_JSONL"
: > "$BUNDLES_JSONL"

record_source() {
  jq -nc --arg name "$1" --arg type "$2" --arg version "$3" --arg url "$4" \
    --arg pin "$5" --arg notes "$6" --arg status "$7" \
    '{name:$name,type:$type,version:$version,url:$url,pin:$pin,notes:$notes,status:$status}' \
    >> "$SOURCES_JSONL"
}
record_failure() {
  jq -nc --arg name "$1" --arg reason "$2" '{name:$name,reason:$reason}' >> "$FAILURES_JSONL"
  echo "FAIL: $1 — $2" | tee -a "$LOG"
}
record_bundle() {
  local rel="${1#$CORPUS/}"
  jq -nc --arg path "$rel" --arg source "$2" --arg kind "$3" \
    '{path:$path,source:$source,kind:$kind}' >> "$BUNDLES_JSONL"
  echo "BUNDLE: $rel" | tee -a "$LOG"
}

helm_tpl() {
  local out="$1"; shift
  mkdir -p "$(dirname "$out")"
  if helm template "$@" --namespace llm-scan >"$out" 2>"$out.err"; then
    [[ -s "$out" ]] || echo "# empty render" > "$out"
    rm -f "$out.err"
    return 0
  else
    echo "helm template failed: $*" | tee -a "$LOG"
    sed 's/^/  /' "$out.err" | tee -a "$LOG" || true
    rm -f "$out"
    return 1
  fi
}

echo "=== Phase 2 fetch+render @ $COLLECTED_AT ===" | tee -a "$LOG"

########################################
# 1) vLLM production-stack
########################################
echo "--- vLLM production-stack ---" | tee -a "$LOG"
VLLM_REPO="$CHARTS/production-stack-git"
rm -rf "$VLLM_REPO"
if git clone --depth 1 https://github.com/vllm-project/production-stack.git "$VLLM_REPO" >>"$LOG" 2>&1; then
  VLLM_SHA=$(git -C "$VLLM_REPO" rev-parse HEAD)
  record_source "vllm-project/production-stack" "git" "HEAD" \
    "https://github.com/vllm-project/production-stack" "$VLLM_SHA" "includes helm/ + tutorials/assets" "ok"

  # Also pull published chart versions
  helm repo add vllm https://vllm-project.github.io/production-stack >>"$LOG" 2>&1 || true
  helm repo update vllm >>"$LOG" 2>&1 || true

  for VER in 0.1.13 0.1.12 0.1.11 0.1.10; do
    DEST="$CHARTS/vllm-stack-$VER"
    rm -rf "$DEST"
    mkdir -p "$DEST"
    if helm pull vllm/vllm-stack --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
      record_source "vllm-stack" "helm" "$VER" \
        "https://vllm-project.github.io/production-stack" "helm-repo:$VER" "Artifact Hub / gh-pages" "ok"
      # default render (skip deps that need network pull if chart has optional deps — use --skip-tests)
      OUTDIR="$RENDERED/vllm-stack-$VER"
      mkdir -p "$OUTDIR"
      # Build deps may fail for optional OCI; try with --skip-crds and without dependency build first
      CHART_PATH="$DEST/vllm-stack"
      if [[ ! -d "$CHART_PATH" ]]; then
        # helm pull --untar may put chart at DEST root differently
        CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
      fi
      if helm_tpl "$OUTDIR/default.yaml" "scan-vllm-$VER" "$CHART_PATH" \
          --set 'kube-prometheus-stack.enabled=false' \
          --set 'prometheus-adapter.enabled=false' \
          --set 'k8s-aibom.enabled=false'; then
        record_bundle "$OUTDIR/default.yaml" "vllm-stack-$VER" "helm-default"
      else
        # try without dependency charts by removing Charts/ if present and clearing deps
        if [[ -f "$CHART_PATH/Chart.yaml" ]]; then
          cp "$CHART_PATH/Chart.yaml" "$CHART_PATH/Chart.yaml.bak"
          # strip dependencies block loosely via python
          python3 - <<PY
import re, pathlib
p = pathlib.Path("$CHART_PATH/Chart.yaml")
t = p.read_text()
t2 = re.sub(r"(?m)^dependencies:.*?(?=^\S|\Z)", "", t, flags=re.S)
p.write_text(t2)
PY
          rm -rf "$CHART_PATH/charts"
          if helm_tpl "$OUTDIR/default.yaml" "scan-vllm-$VER" "$CHART_PATH"; then
            record_bundle "$OUTDIR/default.yaml" "vllm-stack-$VER" "helm-default-nodeps"
          else
            record_failure "vllm-stack-$VER-default" "helm template failed"
          fi
          mv "$CHART_PATH/Chart.yaml.bak" "$CHART_PATH/Chart.yaml" 2>/dev/null || true
        else
          record_failure "vllm-stack-$VER-default" "chart path missing"
        fi
      fi
    else
      record_failure "vllm-stack-$VER" "helm pull failed"
    fi
  done

  # Tutorial values against latest chart (0.1.13 or git helm/)
  TUT_DIR="$VLLM_REPO/tutorials/assets"
  CHART_LATEST="$CHARTS/vllm-stack-0.1.13/vllm-stack"
  [[ -d "$CHART_LATEST" ]] || CHART_LATEST=$(find "$CHARTS/vllm-stack-0.1.13" -maxdepth 2 -name Chart.yaml 2>/dev/null | head -1 | xargs dirname)
  [[ -d "$CHART_LATEST" ]] || CHART_LATEST="$VLLM_REPO/helm"
  if [[ -d "$TUT_DIR" && -d "$CHART_LATEST" ]]; then
    # Prep chart without optional deps for tutorials
    WORK="$CHARTS/vllm-stack-tut-work"
    rm -rf "$WORK"
    cp -a "$CHART_LATEST" "$WORK"
    python3 - <<PY
import re, pathlib
p = pathlib.Path("$WORK/Chart.yaml")
if p.exists():
    t = p.read_text()
    t2 = re.sub(r"(?m)^dependencies:.*?(?=^\S|\Z)", "", t, flags=re.S)
    p.write_text(t2)
PY
    rm -rf "$WORK/charts"
    OUTDIR="$RENDERED/vllm-stack-0.1.13-tutorials"
    mkdir -p "$OUTDIR"
    shopt -s nullglob
    for vf in "$TUT_DIR"/values-*.yaml; do
      base=$(basename "$vf" .yaml)
      out="$OUTDIR/${base}.yaml"
      if helm_tpl "$out" "scan-tut-$base" "$WORK" -f "$vf"; then
        record_bundle "$out" "vllm-stack-tutorials:$base" "helm-values"
      else
        record_failure "tutorial-$base" "helm template failed"
      fi
    done
    # also copy raw tutorial values into manifests
    mkdir -p "$MANIFESTS/vllm-production-stack-tutorials"
    cp -a "$TUT_DIR"/values-*.yaml "$MANIFESTS/vllm-production-stack-tutorials/" 2>/dev/null || true
  fi
else
  record_failure "vllm-project/production-stack" "git clone failed"
fi

########################################
# 2) KServe
########################################
echo "--- KServe ---" | tee -a "$LOG"
# OCI chart
for VER in v0.15.0 v0.14.1 0.15.0 0.14.1; do
  DEST="$CHARTS/kserve-resources-${VER}"
  rm -rf "$DEST"
  mkdir -p "$DEST"
  if helm pull "oci://ghcr.io/kserve/charts/kserve-resources" --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "kserve-resources" "helm-oci" "$VER" \
      "oci://ghcr.io/kserve/charts/kserve-resources" "oci:$VER" "" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/kserve-resources-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-kserve" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "kserve-resources-$VER" "helm-default"
    else
      record_failure "kserve-resources-$VER" "helm template failed"
    fi
    break
  fi
done

# Also try kserve chart itself
for VER in v0.15.0 v0.14.1 0.15.0; do
  DEST="$CHARTS/kserve-${VER}"
  rm -rf "$DEST"
  mkdir -p "$DEST"
  if helm pull "oci://ghcr.io/kserve/charts/kserve" --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "kserve" "helm-oci" "$VER" \
      "oci://ghcr.io/kserve/charts/kserve" "oci:$VER" "" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/kserve-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-kserve-core" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "kserve-$VER" "helm-default"
    else
      record_failure "kserve-$VER" "helm template failed"
    fi
    break
  fi
done

# KServe git samples / GenAI docs YAML
KSERVE_GIT="$CHARTS/kserve-git"
rm -rf "$KSERVE_GIT"
if git clone --depth 1 https://github.com/kserve/kserve.git "$KSERVE_GIT" >>"$LOG" 2>&1; then
  KSHA=$(git -C "$KSERVE_GIT" rev-parse HEAD)
  record_source "kserve/kserve" "git" "HEAD" "https://github.com/kserve/kserve" "$KSHA" "samples" "ok"
  mkdir -p "$MANIFESTS/kserve-samples"
  # Copy LLM/HuggingFace/vLLM related samples
  find "$KSERVE_GIT" -type f \( -iname '*vllm*' -o -iname '*huggingface*' -o -iname '*llm*' -o -iname '*text-generation*' -o -iname '*openai*' -o -iname '*genai*' \) \
    \( -name '*.yaml' -o -name '*.yml' \) 2>/dev/null | head -80 | while read -r f; do
    rel=$(echo "$f" | sed "s|$KSERVE_GIT/||" | tr '/' '_')
    cp "$f" "$MANIFESTS/kserve-samples/$rel"
  done
  # Also docs/samples classic paths
  for d in docs/samples/v1beta1/huggingface docs/samples/v1beta1/torchserve \
           config/samples charts; do
    if [[ -d "$KSERVE_GIT/$d" ]]; then
      mkdir -p "$MANIFESTS/kserve-samples/$(basename $d)"
      find "$KSERVE_GIT/$d" -name '*.yaml' -o -name '*.yml' | head -40 | while read -r f; do
        cp "$f" "$MANIFESTS/kserve-samples/$(basename $d)/$(basename $f)" 2>/dev/null || true
      done
    fi
  done
  # Each sample YAML as a rendered bundle (manifest copy)
  n=0
  find "$MANIFESTS/kserve-samples" -type f \( -name '*.yaml' -o -name '*.yml' \) | while read -r f; do
    base=$(basename "$f" | sed 's/\.[^.]*$//')
    outdir="$RENDERED/kserve-manifest-$base"
    mkdir -p "$outdir"
    cp "$f" "$outdir/manifest.yaml"
    record_bundle "$outdir/manifest.yaml" "kserve-sample:$base" "manifest"
  done
else
  record_failure "kserve/kserve" "git clone failed"
fi

# Fetch GenAI first ISVC from website raw if possible
mkdir -p "$MANIFESTS/kserve-genai-docs"
# Common documented examples via raw github website repo
for url in \
  "https://raw.githubusercontent.com/kserve/website/main/docs/getting-started/assets/huggingface.yaml" \
  "https://raw.githubusercontent.com/kserve/website/main/static/files/huggingface.yaml"; do
  bn=$(basename "$url")
  if curl -fsSL "$url" -o "$MANIFESTS/kserve-genai-docs/$bn" 2>>"$LOG"; then
    outdir="$RENDERED/kserve-genai-$bn"
    mkdir -p "${outdir%.yaml}"
    # fix: outdir shouldn't include .yaml oddly
    outdir="$RENDERED/kserve-genai-${bn%.yaml}"
    mkdir -p "$outdir"
    cp "$MANIFESTS/kserve-genai-docs/$bn" "$outdir/manifest.yaml"
    record_bundle "$outdir/manifest.yaml" "kserve-website:$bn" "manifest"
    record_source "kserve-website-$bn" "raw-yaml" "main" "$url" "url" "" "ok"
  fi
done

########################################
# 3) KubeRay + Ray Serve LLM samples
########################################
echo "--- KubeRay ---" | tee -a "$LOG"
helm repo add kuberay https://ray-project.github.io/kuberay-helm/ >>"$LOG" 2>&1 || true
helm repo update kuberay >>"$LOG" 2>&1 || true

# Get available versions
KUBERAY_VERS=$(helm search repo kuberay/kuberay-operator -o json 2>/dev/null | jq -r '.[0].version // empty')
for VER in ${KUBERAY_VERS} 1.3.0 1.2.2 1.1.1; do
  [[ -z "$VER" ]] && continue
  DEST="$CHARTS/kuberay-operator-$VER"
  rm -rf "$DEST"; mkdir -p "$DEST"
  if helm pull kuberay/kuberay-operator --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "kuberay-operator" "helm" "$VER" \
      "https://ray-project.github.io/kuberay-helm/" "helm:$VER" "" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/kuberay-operator-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-kuberay" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "kuberay-operator-$VER" "helm-default"
    else
      record_failure "kuberay-operator-$VER" "helm template failed"
    fi
    break
  fi
done

# Also ray-cluster chart
for VER in ${KUBERAY_VERS} 1.3.0 1.2.2; do
  [[ -z "$VER" ]] && continue
  DEST="$CHARTS/ray-cluster-$VER"
  rm -rf "$DEST"; mkdir -p "$DEST"
  if helm pull kuberay/ray-cluster --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "ray-cluster" "helm" "$VER" \
      "https://ray-project.github.io/kuberay-helm/" "helm:$VER" "" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/ray-cluster-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-raycluster" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "ray-cluster-$VER" "helm-default"
    else
      record_failure "ray-cluster-$VER" "helm template failed"
    fi
    break
  fi
done

KUBERAY_GIT="$CHARTS/kuberay-git"
rm -rf "$KUBERAY_GIT"
if git clone --depth 1 https://github.com/ray-project/kuberay.git "$KUBERAY_GIT" >>"$LOG" 2>&1; then
  KSHA=$(git -C "$KUBERAY_GIT" rev-parse HEAD)
  record_source "ray-project/kuberay" "git" "HEAD" "https://github.com/ray-project/kuberay" "$KSHA" "LLM samples" "ok"
  mkdir -p "$MANIFESTS/kuberay-llm-samples"
  SAMPLE_DIR="$KUBERAY_GIT/ray-operator/config/samples"
  if [[ -d "$SAMPLE_DIR" ]]; then
    find "$SAMPLE_DIR" -type f \( -iname '*llm*' -o -iname '*deepseek*' -o -iname '*vllm*' -o -iname '*serve*' \) \
      \( -name '*.yaml' -o -name '*.yml' \) | while read -r f; do
      bn=$(basename "$f")
      cp "$f" "$MANIFESTS/kuberay-llm-samples/$bn"
      outdir="$RENDERED/kuberay-sample-${bn%.yaml}"
      mkdir -p "$outdir"
      cp "$f" "$outdir/manifest.yaml"
      record_bundle "$outdir/manifest.yaml" "kuberay-sample:$bn" "manifest"
    done
  fi
else
  record_failure "ray-project/kuberay" "git clone failed"
fi

########################################
# 4) TGI community charts
########################################
echo "--- TGI community ---" | tee -a "$LOG"

# shalb huggingface-model OCI
for VER in 0.1.4 0.1.3 0.1.2 0.1.1 0.1.0; do
  DEST="$CHARTS/shalb-huggingface-model-$VER"
  rm -rf "$DEST"; mkdir -p "$DEST"
  if helm pull "oci://registry-1.docker.io/shalb/huggingface-model" --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "shalb/huggingface-model" "helm-oci" "$VER" \
      "oci://registry-1.docker.io/shalb/huggingface-model" "oci:$VER" "TGI community" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/shalb-huggingface-model-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-shalb" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "shalb-huggingface-model-$VER" "helm-default"
    else
      record_failure "shalb-huggingface-model-$VER" "helm template failed"
    fi
    break
  fi
done

# Also clone shalb charts for values examples
SHALB_GIT="$CHARTS/shalb-charts-git"
rm -rf "$SHALB_GIT"
if git clone --depth 1 https://github.com/shalb/charts.git "$SHALB_GIT" >>"$LOG" 2>&1; then
  SHA=$(git -C "$SHALB_GIT" rev-parse HEAD)
  record_source "shalb/charts" "git" "HEAD" "https://github.com/shalb/charts" "$SHA" "huggingface-model" "ok"
  if [[ -d "$SHALB_GIT/huggingface-model" ]]; then
    DEST="$CHARTS/shalb-huggingface-model-git"
    rm -rf "$DEST"
    cp -a "$SHALB_GIT/huggingface-model" "$DEST"
    OUTDIR="$RENDERED/shalb-huggingface-model-git"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-shalb-git" "$DEST"; then
      record_bundle "$OUTDIR/default.yaml" "shalb-huggingface-model-git" "helm-default"
    fi
    # extra values if any
    shopt -s nullglob
    for vf in "$DEST"/values*.yaml "$DEST"/ci/*.yaml "$DEST"/examples/*.yaml; do
      [[ -f "$vf" ]] || continue
      base=$(basename "$vf" .yaml)
      [[ "$base" == "values" ]] && continue
      out="$OUTDIR/${base}.yaml"
      if helm_tpl "$out" "scan-shalb-$base" "$DEST" -f "$vf"; then
        record_bundle "$out" "shalb:$base" "helm-values"
      fi
    done
  fi
else
  record_failure "shalb/charts" "git clone failed"
fi

# OPEA TGI chart
for VER in 1.2.0 1.1.0 1.0.0 0.9.0 0.8.0; do
  DEST="$CHARTS/opea-tgi-$VER"
  rm -rf "$DEST"; mkdir -p "$DEST"
  if helm pull "oci://ghcr.io/opea-project/charts/tgi" --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "opea/tgi" "helm-oci" "$VER" \
      "oci://ghcr.io/opea-project/charts/tgi" "oci:$VER" "OPEA TGI" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/opea-tgi-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-opea-tgi" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "opea-tgi-$VER" "helm-default"
    else
      record_failure "opea-tgi-$VER" "helm template failed"
    fi
    break
  fi
done

# louis030195 TGI helm
LOUIS_GIT="$CHARTS/louis030195-tgi-helm-git"
rm -rf "$LOUIS_GIT"
if git clone --depth 1 https://github.com/louis030195/text-generation-inference-helm.git "$LOUIS_GIT" >>"$LOG" 2>&1; then
  SHA=$(git -C "$LOUIS_GIT" rev-parse HEAD)
  record_source "louis030195/text-generation-inference-helm" "git" "HEAD" \
    "https://github.com/louis030195/text-generation-inference-helm" "$SHA" "stale community TGI" "ok"
  # find chart root
  CHART_PATH=$(find "$LOUIS_GIT" -name Chart.yaml | head -1 | xargs dirname)
  if [[ -n "$CHART_PATH" ]]; then
    OUTDIR="$RENDERED/louis030195-tgi-helm"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-louis-tgi" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "louis030195-tgi" "helm-default"
    else
      record_failure "louis030195-tgi" "helm template failed"
    fi
  fi
else
  record_failure "louis030195/tgi-helm" "git clone failed"
fi

# Infracloud charts via Artifact Hub / known repos
echo "--- Infracloud ---" | tee -a "$LOG"
# Try common repo URLs
for REPO_URL in \
  "https://charts.infracloud.io" \
  "https://infracloudio.github.io/charts" \
  "https://helm.infracloud.io"; do
  if helm repo add infracloud "$REPO_URL" >>"$LOG" 2>&1; then
    helm repo update infracloud >>"$LOG" 2>&1 || true
    break
  fi
done

for CHART_NAME in vllm text-generation-inference; do
  VER=$(helm search repo "infracloud/$CHART_NAME" -o json 2>/dev/null | jq -r '.[0].version // empty')
  if [[ -n "$VER" ]]; then
    DEST="$CHARTS/infracloud-${CHART_NAME}-$VER"
    rm -rf "$DEST"; mkdir -p "$DEST"
    if helm pull "infracloud/$CHART_NAME" --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
      record_source "infracloud/$CHART_NAME" "helm" "$VER" "infracloud helm repo" "helm:$VER" "" "ok"
      CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
      OUTDIR="$RENDERED/infracloud-${CHART_NAME}-$VER"
      mkdir -p "$OUTDIR"
      if helm_tpl "$OUTDIR/default.yaml" "scan-infra-$CHART_NAME" "$CHART_PATH"; then
        record_bundle "$OUTDIR/default.yaml" "infracloud-$CHART_NAME-$VER" "helm-default"
      else
        record_failure "infracloud-$CHART_NAME-$VER" "helm template failed"
      fi
    fi
  else
    # Try OCI / Artifact Hub download API
    echo "infracloud/$CHART_NAME not in repo; trying AH package info" | tee -a "$LOG"
  fi
done

# Artifact Hub API for infracloud packages
for PKG in "infracloud-charts/vllm" "infracloud-charts/text-generation-inference" "litellm/litellm-helm"; do
  echo "AH lookup $PKG" | tee -a "$LOG"
  AH_JSON=$(curl -fsSL "https://artifacthub.io/api/v1/packages/helm/$PKG" 2>>"$LOG" || true)
  if [[ -n "$AH_JSON" ]]; then
    echo "$AH_JSON" | jq '{name:.name,version:.version,content_url:.content_url,repository:.repository.url,available:.available_versions[0:5]}' >>"$LOG" 2>&1 || true
    CONTENT_URL=$(echo "$AH_JSON" | jq -r '.content_url // empty')
    VER=$(echo "$AH_JSON" | jq -r '.version // empty')
    REPO_URL=$(echo "$AH_JSON" | jq -r '.repository.url // empty')
    PKG_NAME=$(echo "$AH_JSON" | jq -r '.name // empty')
    SAFE=$(echo "$PKG" | tr '/' '-')
    if [[ -n "$REPO_URL" && -n "$PKG_NAME" ]]; then
      helm repo add "ah-$SAFE" "$REPO_URL" >>"$LOG" 2>&1 || true
      helm repo update "ah-$SAFE" >>"$LOG" 2>&1 || true
      DEST="$CHARTS/${SAFE}-$VER"
      rm -rf "$DEST"; mkdir -p "$DEST"
      # try pull by chart name from that repo
      CHART_REF=$(helm search repo "$PKG_NAME" -o json 2>/dev/null | jq -r --arg n "$PKG_NAME" '[.[]|select(.name|endswith("/"+$n) or .name==$n)][0].name // empty')
      if [[ -z "$CHART_REF" ]]; then
        CHART_REF=$(helm search repo "$PKG_NAME" -o json 2>/dev/null | jq -r '.[0].name // empty')
      fi
      if [[ -n "$CHART_REF" ]] && helm pull "$CHART_REF" --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
        record_source "$PKG" "helm" "$VER" "$REPO_URL" "helm:$VER" "via Artifact Hub" "ok"
        CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
        OUTDIR="$RENDERED/${SAFE}-$VER"
        mkdir -p "$OUTDIR"
        if helm_tpl "$OUTDIR/default.yaml" "scan-$SAFE" "$CHART_PATH"; then
          record_bundle "$OUTDIR/default.yaml" "$SAFE-$VER" "helm-default"
        else
          # try stripping deps
          python3 - <<PY
import re, pathlib
p = pathlib.Path("$CHART_PATH/Chart.yaml")
t = p.read_text()
p.write_text(re.sub(r"(?m)^dependencies:.*?(?=^\S|\Z)", "", t, flags=re.S))
PY
          rm -rf "$CHART_PATH/charts"
          if helm_tpl "$OUTDIR/default.yaml" "scan-$SAFE" "$CHART_PATH"; then
            record_bundle "$OUTDIR/default.yaml" "$SAFE-$VER" "helm-default-nodeps"
          else
            record_failure "$SAFE-$VER" "helm template failed"
          fi
        fi
      elif [[ -n "$CONTENT_URL" ]]; then
        TGZ="$DEST/chart.tgz"
        if curl -fsSL "$CONTENT_URL" -o "$TGZ" 2>>"$LOG"; then
          tar -xzf "$TGZ" -C "$DEST" 2>>"$LOG" || true
          record_source "$PKG" "helm-tgz" "$VER" "$CONTENT_URL" "tgz:$VER" "AH content_url" "ok"
          CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
          OUTDIR="$RENDERED/${SAFE}-$VER"
          mkdir -p "$OUTDIR"
          if helm_tpl "$OUTDIR/default.yaml" "scan-$SAFE" "$CHART_PATH"; then
            record_bundle "$OUTDIR/default.yaml" "$SAFE-$VER" "helm-default"
          else
            record_failure "$SAFE-$VER" "helm template failed"
          fi
        else
          record_failure "$PKG" "content_url download failed"
        fi
      else
        record_failure "$PKG" "helm pull failed"
      fi
    fi
  else
    record_failure "$PKG" "Artifact Hub API miss"
  fi
done

########################################
# 5) Ollama otwld
########################################
echo "--- Ollama otwld ---" | tee -a "$LOG"
helm repo add otwld https://helm.otwld.com/ >>"$LOG" 2>&1 || true
helm repo update otwld >>"$LOG" 2>&1 || true
OLLAMA_VER=$(helm search repo otwld/ollama -o json 2>/dev/null | jq -r '.[0].version // empty')
for VER in $OLLAMA_VER 1.26.0 1.25.0 1.20.0 1.15.0; do
  [[ -z "$VER" ]] && continue
  DEST="$CHARTS/otwld-ollama-$VER"
  rm -rf "$DEST"; mkdir -p "$DEST"
  if helm pull otwld/ollama --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "otwld/ollama" "helm" "$VER" "https://helm.otwld.com/" "helm:$VER" "" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/otwld-ollama-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-ollama" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "otwld-ollama-$VER" "helm-default"
    else
      record_failure "otwld-ollama-$VER" "helm template failed"
    fi
    # Also pull 1–2 older versions for multi-version corpus
    break
  fi
done
# Older ollama versions
for VER in 1.18.0 1.11.0 1.8.0; do
  DEST="$CHARTS/otwld-ollama-$VER"
  [[ -d "$DEST/ollama" || -d "$DEST" ]] && [[ -f "$(find "$DEST" -name Chart.yaml | head -1)" ]] && continue
  rm -rf "$DEST"; mkdir -p "$DEST"
  if helm pull otwld/ollama --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "otwld/ollama" "helm" "$VER" "https://helm.otwld.com/" "helm:$VER" "older pin" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/otwld-ollama-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-ollama-$VER" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "otwld-ollama-$VER" "helm-default"
    fi
  fi
done

OLLAMA_GIT="$CHARTS/ollama-helm-git"
rm -rf "$OLLAMA_GIT"
if git clone --depth 1 https://github.com/otwld/ollama-helm.git "$OLLAMA_GIT" >>"$LOG" 2>&1; then
  SHA=$(git -C "$OLLAMA_GIT" rev-parse HEAD)
  record_source "otwld/ollama-helm" "git" "HEAD" "https://github.com/otwld/ollama-helm" "$SHA" "" "ok"
  # example values
  CHART_PATH=$(find "$OLLAMA_GIT" -name Chart.yaml | head -1 | xargs dirname)
  OUTDIR="$RENDERED/otwld-ollama-git-examples"
  mkdir -p "$OUTDIR"
  shopt -s nullglob
  for vf in "$OLLAMA_GIT"/examples/*.yaml "$OLLAMA_GIT"/ci/*.yaml; do
    [[ -f "$vf" ]] || continue
    base=$(basename "$vf" .yaml)
    out="$OUTDIR/${base}.yaml"
    if helm_tpl "$out" "scan-ollama-$base" "$CHART_PATH" -f "$vf"; then
      record_bundle "$out" "otwld-ollama:$base" "helm-values"
    fi
  done
fi

########################################
# 6) HAMi
########################################
echo "--- HAMi ---" | tee -a "$LOG"
helm repo add hami-charts https://project-hami.github.io/HAMi/ >>"$LOG" 2>&1 || true
helm repo update hami-charts >>"$LOG" 2>&1 || true
HAMI_VER=$(helm search repo hami-charts/hami -o json 2>/dev/null | jq -r '.[0].version // empty')
for VER in $HAMI_VER 2.5.1 2.4.1 2.3.0; do
  [[ -z "$VER" ]] && continue
  DEST="$CHARTS/hami-$VER"
  rm -rf "$DEST"; mkdir -p "$DEST"
  if helm pull hami-charts/hami --version "$VER" --untar -d "$DEST" >>"$LOG" 2>&1; then
    record_source "hami" "helm" "$VER" "https://project-hami.github.io/HAMi/" "helm:$VER" "" "ok"
    CHART_PATH=$(find "$DEST" -maxdepth 2 -name Chart.yaml | head -1 | xargs dirname)
    OUTDIR="$RENDERED/hami-$VER"
    mkdir -p "$OUTDIR"
    if helm_tpl "$OUTDIR/default.yaml" "scan-hami" "$CHART_PATH"; then
      record_bundle "$OUTDIR/default.yaml" "hami-$VER" "helm-default"
    else
      record_failure "hami-$VER" "helm template failed"
    fi
    break
  fi
done

HAMI_GIT="$CHARTS/HAMi-git"
rm -rf "$HAMI_GIT"
if git clone --depth 1 https://github.com/Project-HAMi/HAMi.git "$HAMI_GIT" >>"$LOG" 2>&1; then
  SHA=$(git -C "$HAMI_GIT" rev-parse HEAD)
  record_source "Project-HAMi/HAMi" "git" "HEAD" "https://github.com/Project-HAMi/HAMi" "$SHA" "vLLM examples" "ok"
  mkdir -p "$MANIFESTS/hami-examples"
  find "$HAMI_GIT/examples" -type f \( -name '*.yaml' -o -name '*.yml' \) 2>/dev/null | while read -r f; do
    rel=$(echo "$f" | sed "s|$HAMI_GIT/examples/||" | tr '/' '_')
    cp "$f" "$MANIFESTS/hami-examples/$rel"
    outdir="$RENDERED/hami-example-${rel%.yaml}"
    mkdir -p "$outdir"
    cp "$f" "$outdir/manifest.yaml"
    record_bundle "$outdir/manifest.yaml" "hami-example:$rel" "manifest"
  done
else
  record_failure "Project-HAMi/HAMi" "git clone failed"
fi

########################################
# 7) SGLang
########################################
echo "--- SGLang ---" | tee -a "$LOG"
mkdir -p "$MANIFESTS/sglang"
SGL_URL="https://raw.githubusercontent.com/sgl-project/sglang/master/docker/k8s-sglang-service.yaml"
if curl -fsSL "$SGL_URL" -o "$MANIFESTS/sglang/k8s-sglang-service.yaml" 2>>"$LOG"; then
  # get commit of default branch tip via API
  SGL_SHA=$(curl -fsSL https://api.github.com/repos/sgl-project/sglang/commits/master 2>>"$LOG" | jq -r '.sha // "master"')
  record_source "sgl-project/sglang k8s-sglang-service.yaml" "raw-yaml" "master" "$SGL_URL" "$SGL_SHA" "" "ok"
  outdir="$RENDERED/sglang-k8s-sglang-service"
  mkdir -p "$outdir"
  cp "$MANIFESTS/sglang/k8s-sglang-service.yaml" "$outdir/manifest.yaml"
  record_bundle "$outdir/manifest.yaml" "sglang" "manifest"
else
  record_failure "sglang-k8s-yaml" "download failed"
fi
# Also clone for more k8s yamls
SGL_GIT="$CHARTS/sglang-git"
rm -rf "$SGL_GIT"
if git clone --depth 1 https://github.com/sgl-project/sglang.git "$SGL_GIT" >>"$LOG" 2>&1; then
  SHA=$(git -C "$SGL_GIT" rev-parse HEAD)
  record_source "sgl-project/sglang" "git" "HEAD" "https://github.com/sgl-project/sglang" "$SHA" "k8s yamls" "ok"
  find "$SGL_GIT" -type f \( -path '*/k8s/*' -o -path '*/kubernetes/*' -o -name '*k8s*.yaml' \) \
    \( -name '*.yaml' -o -name '*.yml' \) 2>/dev/null | head -30 | while read -r f; do
    bn=$(basename "$f")
    cp "$f" "$MANIFESTS/sglang/$bn"
    outdir="$RENDERED/sglang-${bn%.yaml}"
    mkdir -p "$outdir"
    cp "$f" "$outdir/manifest.yaml"
    record_bundle "$outdir/manifest.yaml" "sglang:$bn" "manifest"
  done
fi

########################################
# 8) LiteLLM (may already be fetched via AH)
########################################
echo "--- LiteLLM extra ---" | tee -a "$LOG"
# Also try git
LITELLM_GIT="$CHARTS/litellm-git"
rm -rf "$LITELLM_GIT"
if git clone --depth 1 https://github.com/BerriAI/litellm.git "$LITELLM_GIT" >>"$LOG" 2>&1; then
  SHA=$(git -C "$LITELLM_GIT" rev-parse HEAD)
  record_source "BerriAI/litellm" "git" "HEAD" "https://github.com/BerriAI/litellm" "$SHA" "deploy/charts" "ok"
  CHART_PATH=$(find "$LITELLM_GIT" -path '*/helm*' -name Chart.yaml 2>/dev/null | head -1 | xargs dirname)
  [[ -z "$CHART_PATH" ]] && CHART_PATH=$(find "$LITELLM_GIT" -name Chart.yaml 2>/dev/null | head -1 | xargs dirname)
  if [[ -n "$CHART_PATH" ]]; then
    OUTDIR="$RENDERED/litellm-git"
    mkdir -p "$OUTDIR"
    # strip deps if needed
    if ! helm_tpl "$OUTDIR/default.yaml" "scan-litellm" "$CHART_PATH"; then
      python3 - <<PY
import re, pathlib
p = pathlib.Path("$CHART_PATH/Chart.yaml")
t = p.read_text()
p.write_text(re.sub(r"(?m)^dependencies:.*?(?=^\S|\Z)", "", t, flags=re.S))
PY
      rm -rf "$CHART_PATH/charts"
      if helm_tpl "$OUTDIR/default.yaml" "scan-litellm" "$CHART_PATH"; then
        record_bundle "$OUTDIR/default.yaml" "litellm-git" "helm-default-nodeps"
      else
        record_failure "litellm-git" "helm template failed"
      fi
    else
      record_bundle "$OUTDIR/default.yaml" "litellm-git" "helm-default"
    fi
  fi
fi

########################################
# Extra: open-webui only if pairs with ollama - skip as candidate unless quick
# Extra: more vLLM community / values overlays for bundle count
########################################
echo "--- Extra vLLM values overlays ---" | tee -a "$LOG"
# Re-render vllm-stack with common security-relevant value toggles as named overlays
CHART_WORK="$CHARTS/vllm-stack-tut-work"
if [[ -d "$CHART_WORK" ]]; then
  OUTDIR="$RENDERED/vllm-stack-0.1.13-overlays"
  mkdir -p "$OUTDIR"
  # Create small overlay values files (not inventing upstream sources — these are scan scenarios documented as overlays)
  mkdir -p "$CORPUS/overlays/vllm-stack"
  cat > "$CORPUS/overlays/vllm-stack/service-loadbalancer.yaml" <<'OV'
serviceType: LoadBalancer
OV
  cat > "$CORPUS/overlays/vllm-stack/NOTE.md" <<'OV'
Synthetic scan overlays for default chart — not upstream tutorials.
Counted separately; primary corpus remains upstream defaults + tutorials.
OV
fi

########################################
# Deduplicate bundles that are empty/dup by content hash? keep all for now
########################################

# Write lockfile
BUNDLE_COUNT=$(wc -l < "$BUNDLES_JSONL" | tr -d ' ')
FAIL_COUNT=$(wc -l < "$FAILURES_JSONL" | tr -d ' ')
SRC_COUNT=$(wc -l < "$SOURCES_JSONL" | tr -d ' ')

jq -n \
  --arg collected_at "$COLLECTED_AT" \
  --arg timezone "America/Los_Angeles" \
  --slurpfile sources <(jq -s '.' "$SOURCES_JSONL") \
  --slurpfile failures <(jq -s '.' "$FAILURES_JSONL") \
  --slurpfile bundles <(jq -s '.' "$BUNDLES_JSONL") \
  --argjson bundle_count "$BUNDLE_COUNT" \
  --argjson fail_count "$FAIL_COUNT" \
  --argjson source_count "$SRC_COUNT" \
  '{
    collected_at: $collected_at,
    timezone: $timezone,
    phase: "2-fetch-render",
    counts: {
      sources: $source_count,
      rendered_bundles: $bundle_count,
      failures: $fail_count
    },
    sources: $sources[0],
    failures: $failures[0],
    bundles: $bundles[0]
  }' > "$LOCK"

echo "=== DONE bundles=$BUNDLE_COUNT sources=$SRC_COUNT failures=$FAIL_COUNT ===" | tee -a "$LOG"
echo "Lock: $LOCK"
