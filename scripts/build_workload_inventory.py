#!/usr/bin/env python3
"""Build a resource-level inventory for human LLM-serving eligibility review.

This is a triage aid only. It does not determine security findings or final
eligibility. The final primary/secondary/exclusion decision remains human
reviewed. The primary prevalence unit remains the configuration bundle.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

POD_WORKLOAD_KINDS = {"Pod", "Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}
SERVING_CR_KINDS = {
    "LLMInferenceService", "LLMInferenceServiceConfig", "InferenceService",
    "RayService", "RayCluster", "ServingRuntime", "ClusterServingRuntime",
    "LocalModelCache", "LocalModelNodeGroup", "LoraAdapter",
}
DIRECT_ENGINE_HINT = re.compile(
    r"(vllm|text-generation|text_generation|tgi|sglang|ollama|litellm|"
    r"deepseek|llama|qwen|mistral|gemma|bloom|falcon|mixtral|phi|granite|llm[-_ ]?(inference|serve|serving|server|api|gateway)|llmisvc)",
    re.I,
)
NON_SERVING_HINT = re.compile(r"(finetun|fine[-_ ]?tun|training|trainer)", re.I)
EXPLICIT_SERVING_ENGINE = re.compile(
    r"(vllm|text-generation|tgi|sglang|ollama|litellm)", re.I
)
SUPPORT_HINT = re.compile(
    r"(kserve|kuberay|ray|hami|gpu|device-plugin|scheduler|operator|"
    r"vllm|tgi|sglang|ollama|litellm|text-generation)", re.I
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def get_pod_spec(obj: dict[str, Any]) -> dict[str, Any]:
    kind = obj.get("kind")
    spec = obj.get("spec") or {}
    if kind == "CronJob":
        spec = ((spec.get("jobTemplate") or {}).get("spec") or {})
    template = spec.get("template") or {}
    if kind == "Pod":
        return spec
    return template.get("spec") or {}


def collect_containers(pod_spec: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for key in ("initContainers", "containers", "ephemeralContainers"):
        for c in pod_spec.get(key) or []:
            if isinstance(c, dict):
                item = dict(c)
                item["_container_type"] = key
                result.append(item)
    return result


def propose_stratum(kind: str, identity: str, source: str, path: str) -> tuple[str, str]:
    # Decide primary eligibility from the resource itself, not the bundle path.
    # A vLLM chart can also contain generic controllers, sidecars, and jobs.
    if NON_SERVING_HINT.search(identity) and not EXPLICIT_SERVING_ENGINE.search(identity):
        return "supporting_platform_candidate", "Training/fine-tuning identity; not an inference workload candidate."
    if kind in {"LLMInferenceService", "LLMInferenceServiceConfig"}:
        return "primary_candidate", "Kubernetes LLM inference custom resource/config; verify version and rule-specific applicability."
    if DIRECT_ENGINE_HINT.search(identity):
        return "primary_candidate", "Resource name, labels, or container identity directly suggests an LLM inference engine/model; verify actual purpose."
    context = " ".join([kind, source, path])
    if kind in SERVING_CR_KINDS or SUPPORT_HINT.search(context):
        return "supporting_platform_candidate", "Serving platform/operator/GPU infrastructure or generic ML serving resource; determine rule-specific applicability."
    return "non_llm_or_unclear", "No direct LLM-serving identity detected from resource metadata/container images."


def build_inventory(root: Path, lock_path: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    lock = json.loads(lock_path.read_text(encoding="utf-8"))
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    for bundle in lock.get("bundles", []):
        rel = str(bundle.get("path", ""))
        path = (root / "corpus" / rel).resolve()
        if not path.is_file():
            errors.append(f"missing bundle: corpus/{rel}")
            continue
        try:
            with path.open("r", encoding="utf-8") as f:
                documents = list(yaml.safe_load_all(f))
        except (yaml.YAMLError, UnicodeDecodeError):
            # Non-standalone inputs are documented in corpus/parse_exceptions.json.
            continue

        for doc_index, obj in enumerate(documents):
            if not isinstance(obj, dict) or not isinstance(obj.get("kind"), str):
                continue
            kind = obj["kind"]
            if kind not in POD_WORKLOAD_KINDS | SERVING_CR_KINDS:
                continue

            meta = obj.get("metadata") or {}
            pod_spec = get_pod_spec(obj) if kind in POD_WORKLOAD_KINDS else {}
            containers = collect_containers(pod_spec)
            names = [str(c.get("name", "")) for c in containers]
            images = [str(c.get("image", "")) for c in containers]
            labels = meta.get("labels") or {}
            identity_parts = [
                str(meta.get("name", "")),
                json.dumps(labels, sort_keys=True),
                " ".join(names),
                " ".join(images),
            ]
            # Inspect only serving-specific fields for custom resources. Avoid
            # arbitrary spec/args/namespace text (e.g. "llm-scan") as identity.
            spec = obj.get("spec") or {}
            if kind in {"RayService", "RayCluster"}:
                identity_parts.append(str(spec.get("serveConfigV2", "")))
            if kind == "InferenceService":
                predictor = spec.get("predictor") or {}
                model = predictor.get("model") or {}
                identity_parts.extend([
                    str((model.get("modelFormat") or {}).get("name", "")),
                    str(model.get("runtime", "")),
                    str(model.get("name", "")),
                ])
            identity = " ".join(identity_parts)
            stratum, reason = propose_stratum(
                kind, identity, str(bundle.get("source", "")), rel
            )
            rows.append({
                "bundle_path": rel,
                "source": bundle.get("source", ""),
                "bundle_kind": bundle.get("kind", ""),
                "document_index": doc_index,
                "api_version": obj.get("apiVersion", ""),
                "resource_kind": kind,
                "resource_name": meta.get("name", ""),
                "namespace": meta.get("namespace", "default"),
                "container_count": len(containers),
                "container_names": ";".join(names),
                "container_images": ";".join(images),
                "proposed_stratum": stratum,
                "proposed_reason": reason,
                "final_decision": "",
                "reviewer": "",
                "review_status": "pending",
                "review_notes": "",
                "source_sha256": sha256(path),
            })

    summary = {
        "locked_bundles": len(lock.get("bundles", [])),
        "resource_records": len(rows),
        "resource_kind_counts": dict(sorted(Counter(r["resource_kind"] for r in rows).items())),
        "proposed_strata": dict(sorted(Counter(r["proposed_stratum"] for r in rows).items())),
        "errors": errors,
        "final_eligibility_status": "not_reviewed",
        "note": "Resource rows are review aids, not independent prevalence observations; bundle is the primary analysis unit.",
    }
    return rows, summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--lockfile", default="corpus/SOURCES.lock.json")
    parser.add_argument("--out-dir", default="results")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    rows, summary = build_inventory(root, root / args.lockfile)
    out_dir = root / args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with (out_dir / "resource_eligibility_review.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        if fields:
            writer.writeheader()
            writer.writerows(rows)
    (out_dir / "workload_inventory_summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 1 if summary["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
