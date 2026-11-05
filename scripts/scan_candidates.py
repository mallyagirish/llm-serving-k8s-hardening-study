#!/usr/bin/env python3
"""Conservative candidate scanner for LLM-serving Kubernetes YAML.

This tool emits review candidates, not ground-truth TP/FP labels. It deliberately
avoids asserting that a static YAML indicator proves exploitability or exposure.
Requires PyYAML: python -m pip install PyYAML
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Iterable

try:
    import yaml
except ImportError:
    raise SystemExit("Missing dependency: install PyYAML with 'python -m pip install PyYAML'")

LLM_HINT = re.compile(r"(vllm|text-generation|tgi|sglang|ollama|llm|inference|rayserve|litellm)", re.I)
IMAGE_LATEST = re.compile(r":latest$")
GPU_KEYS = ("nvidia.com/gpu", "amd.com/gpu", "habana.ai/gaudi", "gpu.intel.com/i915")


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def docs_in(path: Path) -> Iterable[dict[str, Any]]:
    try:
        with path.open("r", encoding="utf-8") as f:
            for obj in yaml.safe_load_all(f):
                if isinstance(obj, dict) and isinstance(obj.get("kind"), str):
                    yield obj
    except (yaml.YAMLError, UnicodeDecodeError) as exc:
        print(f"WARNING: cannot parse {path}: {exc}", file=sys.stderr)


def workload_parts(obj: dict[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]]]:
    kind = obj.get("kind", "")
    spec = obj.get("spec") or {}
    template = spec.get("template") or {}
    pod = template.get("spec") or (spec if kind == "Pod" else {})
    containers = list(pod.get("containers") or []) + list(pod.get("initContainers") or [])
    return kind, pod, [c for c in containers if isinstance(c, dict)]


def looks_like_llm(obj: dict[str, Any], containers: list[dict[str, Any]]) -> bool:
    names = [str(obj.get("metadata", {}).get("name", ""))]
    names += [str(c.get("name", "")) + " " + str(c.get("image", "")) for c in containers]
    return any(LLM_HINT.search(s) for s in names)


def emit(out: list[dict[str, Any]], rule: str, path: Path, digest: str,
         obj: dict[str, Any], evidence: str, caveat: str) -> None:
    meta = obj.get("metadata") or {}
    out.append({
        "rule_id": rule,
        "status": "candidate_for_human_review",
        "source_file": str(path),
        "source_sha256": digest,
        "kind": obj.get("kind"),
        "namespace": meta.get("namespace", "default"),
        "resource_name": meta.get("name"),
        "evidence": evidence,
        "interpretation_limit": caveat,
    })


def scan_file(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    digest = sha256(path)
    for obj in docs_in(path):
        kind, pod, containers = workload_parts(obj)
        if kind in {"Pod", "Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}:
            # CronJob has an additional jobTemplate nesting; skip rather than guess.
            if kind == "CronJob":
                continue
            if not looks_like_llm(obj, containers):
                continue
            pod_sc = pod.get("securityContext") or {}
            if pod.get("hostNetwork") is True:
                emit(findings, "LLM-NET-05", path, digest, obj, "spec.hostNetwork=true", "Host networking is a risk indicator; surrounding node/network controls are not evaluated.")
            if pod.get("hostPID") is True:
                emit(findings, "LLM-NET-05", path, digest, obj, "spec.hostPID=true", "Host PID sharing is a risk indicator; runtime impact is not evaluated.")
            for c in containers:
                name = str(c.get("name", "container"))
                image = str(c.get("image", ""))
                sc = c.get("securityContext") or {}
                prefix = f"container={name}: "
                if sc.get("privileged") is True:
                    emit(findings, "LLM-GPU-03", path, digest, obj, prefix + "securityContext.privileged=true", "Privileged mode is a static risk indicator; device requirements and compensating controls need review.")
                if sc.get("allowPrivilegeEscalation") is True:
                    emit(findings, "LLM-WL-03", path, digest, obj, prefix + "allowPrivilegeEscalation=true", "Explicit true is a candidate; admission defaults and runtime policy are not evaluated.")
                if sc.get("runAsNonRoot") is not True and pod_sc.get("runAsNonRoot") is not True:
                    emit(findings, "LLM-WL-01", path, digest, obj, prefix + "no explicit runAsNonRoot=true at container or pod level", "Absence is not proof the process runs as root; image USER and admission policy are not evaluated.")
                if sc.get("readOnlyRootFilesystem") is not True:
                    emit(findings, "LLM-WL-02", path, digest, obj, prefix + "no explicit readOnlyRootFilesystem=true", "Some serving engines require writable paths; this is a hardening candidate, not an unconditional defect.")
                if IMAGE_LATEST.search(image):
                    emit(findings, "LLM-WL-05", path, digest, obj, prefix + "image=" + image, "Mutable tag indicator; registry digest and deployment admission controls are not checked.")
                elif image and "@sha256:" not in image and ":" in image.rsplit("/", 1)[-1]:
                    emit(findings, "LLM-WL-05", path, digest, obj, prefix + "image has tag but no digest: " + image, "Tag mutability depends on registry policy; this is a reproducibility/supply-chain candidate.")
                resources = c.get("resources") or {}
                req = resources.get("requests") or {}
                lim = resources.get("limits") or {}
                missing = [k for k in ("cpu", "memory") if k not in req or k not in lim]
                if missing:
                    emit(findings, "LLM-RES-01", path, digest, obj, prefix + "CPU/memory requests or limits absent: " + ",".join(missing), "Workload sizing and namespace defaults are not evaluated.")
                if not c.get("readinessProbe") and not c.get("startupProbe"):
                    emit(findings, "LLM-RES-03", path, digest, obj, prefix + "no readinessProbe or startupProbe", "A probe may be defined externally; startup/readiness semantics require workload review.")
        elif kind == "Service":
            spec = obj.get("spec") or {}
            ports = spec.get("ports") or []
            port_text = " ".join(str(p.get("port", "")) + " " + str(p.get("targetPort", "")) + " " + str(p.get("name", "")) for p in ports if isinstance(p, dict))
            meta_name = str((obj.get("metadata") or {}).get("name", ""))
            if spec.get("type") in {"LoadBalancer", "NodePort"} and (LLM_HINT.search(meta_name) or re.search(r"(8000|8080|11434|inference|vllm|llm)", port_text, re.I)):
                emit(findings, "LLM-NET-01", path, digest, obj, "Service type=" + str(spec.get("type")) + "; ports=" + port_text, "This does not prove internet reachability, missing authentication, or an exploitable endpoint.")
    return findings


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="YAML files or directories containing YAML")
    parser.add_argument("--output", default="-", help="JSONL output path (default: stdout)")
    args = parser.parse_args()
    files: list[Path] = []
    for raw in args.paths:
        p = Path(raw)
        if p.is_dir():
            files.extend(sorted(x for x in p.rglob("*") if x.suffix.lower() in {".yaml", ".yml"}))
        elif p.is_file():
            files.append(p)
        else:
            print(f"WARNING: path not found: {p}", file=sys.stderr)
    rows: list[dict[str, Any]] = []
    for path in sorted(set(files)):
        rows.extend(scan_file(path))
    output = sys.stdout if args.output == "-" else open(args.output, "w", encoding="utf-8")
    try:
        for row in rows:
            output.write(json.dumps(row, sort_keys=True) + "\n")
    finally:
        if output is not sys.stdout:
            output.close()
    print(f"Scanned {len(files)} YAML files; emitted {len(rows)} review candidates.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
