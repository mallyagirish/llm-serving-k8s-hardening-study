#!/usr/bin/env python3
"""Conservative candidate scanner for LLM-serving Kubernetes YAML.

Outputs candidate observations for human review, not ground-truth TP/FP labels.
A candidate is not proof of exploitability, internet exposure, or a vulnerability.
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

import yaml

LLM_HINT = re.compile(
    r"(vllm|text-generation|text_generation|tgi|sglang|ollama|llm|"
    r"rayserve|ray-serve|litellm|deepseek|llama|qwen|mistral|gemma|bloom|falcon|mixtral|phi|granite)",
    re.I,
)
IMAGE_DIGEST = re.compile(r"@sha256:[0-9a-f]{64}$", re.I)
NON_SERVING_HINT = re.compile(r"(finetun|fine[-_ ]?tun|training|trainer)", re.I)
EXPLICIT_SERVING_ENGINE = re.compile(r"(vllm|text-generation|text_generation|tgi|sglang|ollama|litellm)", re.I)


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
    if kind == "CronJob":
        spec = ((spec.get("jobTemplate") or {}).get("spec") or {})
    template = spec.get("template") or {}
    pod = template.get("spec") or (spec if kind == "Pod" else {})
    containers = list(pod.get("containers") or []) + list(pod.get("initContainers") or [])
    return kind, pod, [c for c in containers if isinstance(c, dict)]


def identity_matches(text: str) -> bool:
    if NON_SERVING_HINT.search(text) and not EXPLICIT_SERVING_ENGINE.search(text):
        return False
    return bool(LLM_HINT.search(text))


def workload_has_llm_identity(obj: dict[str, Any], pod: dict[str, Any]) -> bool:
    meta = obj.get("metadata") or {}
    spec = obj.get("spec") or {}
    template = spec.get("template") or {}
    pod_meta = template.get("metadata") or {}
    # Deliberately exclude namespace and arbitrary args: e.g. namespace=llm-scan
    # must not make an unrelated operator look like an inference workload.
    identity = " ".join([
        str(meta.get("name", "")),
        str(meta.get("labels", "")),
        str(pod_meta.get("labels", "")),
        str(pod.get("labels", "")),
    ])
    return identity_matches(identity)


def container_has_llm_identity(container: dict[str, Any]) -> bool:
    identity = " ".join([
        str(container.get("name", "")),
        str(container.get("image", "")),
    ])
    return identity_matches(identity)


def emit(out: list[dict[str, Any]], rule: str, path: Path, digest: str,
         obj: dict[str, Any], evidence: str, caveat: str,
         container_name: str | None = None, document_index: int | None = None) -> None:
    meta = obj.get("metadata") or {}
    out.append({
        "rule_id": rule,
        "status": "candidate_for_human_review",
        "source_file": str(path),
        "source_sha256": digest,
        "document_index": document_index,
        "kind": obj.get("kind"),
        "namespace": meta.get("namespace", "default"),
        "resource_name": meta.get("name"),
        "container_name": container_name,
        "evidence": evidence,
        "interpretation_limit": caveat,
    })


def effective_pod_or_container_value(container_sc: dict[str, Any],
                                     pod_sc: dict[str, Any], key: str) -> Any:
    if key in container_sc:
        return container_sc[key]
    return pod_sc.get(key)


def scan_file(path: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    digest = sha256(path)
    for document_index, obj in enumerate(docs_in(path)):
        kind, pod, containers = workload_parts(obj)
        if kind in {"Pod", "Deployment", "StatefulSet", "DaemonSet", "Job", "CronJob"}:
            if not containers:
                continue
            workload_hint = workload_has_llm_identity(obj, pod)
            matched = [c for c in containers if container_has_llm_identity(c)]
            if not workload_hint and not matched:
                continue

            # Container-level checks target only containers with their own
            # serving-engine identity. If a workload is clearly LLM-serving
            # but has a single generic container, that sole container is the
            # target. Do not blindly flag sidecars in multi-container pods.
            if matched:
                target_containers = matched
            elif workload_hint and len(containers) == 1:
                target_containers = containers
            else:
                target_containers = []

            pod_sc = pod.get("securityContext") or {}
            if workload_hint or matched:
                if pod.get("hostNetwork") is True:
                    emit(findings, "LLM-NET-05", path, digest, obj, "spec.hostNetwork=true",
                         "Host networking is a risk indicator; node and network controls are not evaluated.",
                         document_index=document_index)
                if pod.get("hostPID") is True:
                    emit(findings, "LLM-NET-05", path, digest, obj, "spec.hostPID=true",
                         "Host PID sharing is a risk indicator; runtime impact is not evaluated.",
                         document_index=document_index)
                for volume in pod.get("volumes") or []:
                    host_path = ((volume.get("hostPath") or {}).get("path")) if isinstance(volume, dict) else None
                    if isinstance(host_path, str) and (host_path == "/dev" or host_path.startswith("/dev/")):
                        emit(findings, "LLM-GPU-03", path, digest, obj,
                             "Pod volume " + str(volume.get("name", "")) + " mounts hostPath " + host_path,
                             "Host device mounts may be required for GPU access; assess device scope and least privilege.",
                             document_index=document_index)

            for c in target_containers:
                name = str(c.get("name", "container"))
                image = str(c.get("image", ""))
                sc = c.get("securityContext") or {}
                prefix = f"container={name}: "
                common = {"container_name": name, "document_index": document_index}
                if sc.get("privileged") is True:
                    emit(findings, "LLM-GPU-03", path, digest, obj,
                         prefix + "securityContext.privileged=true",
                         "Privileged mode is a static risk indicator; device requirements and compensating controls need review.",
                         **common)
                added_caps = ((sc.get("capabilities") or {}).get("add") or [])
                dangerous_caps = sorted({
                    str(cap).upper() for cap in added_caps
                    if str(cap).upper() in {"ALL", "SYS_ADMIN", "SYS_PTRACE", "SYS_MODULE", "DAC_READ_SEARCH"}
                })
                if dangerous_caps:
                    emit(findings, "LLM-GPU-03", path, digest, obj,
                         prefix + "dangerous capabilities added: " + ",".join(dangerous_caps),
                         "Capability risk depends on runtime needs; review whether each capability is essential.",
                         **common)
                if sc.get("allowPrivilegeEscalation") is not False:
                    emit(findings, "LLM-WL-03", path, digest, obj,
                         prefix + "allowPrivilegeEscalation is not explicitly false",
                         "Runtime defaults and admission policies are not evaluated; this is an explicit-hardening candidate.",
                         **common)
                if effective_pod_or_container_value(sc, pod_sc, "runAsNonRoot") is not True:
                    emit(findings, "LLM-WL-01", path, digest, obj,
                         prefix + "effective runAsNonRoot is not explicitly true",
                         "Image USER, runtime identity, and admission policy are not evaluated.",
                         **common)
                if sc.get("readOnlyRootFilesystem") is not True:
                    emit(findings, "LLM-WL-02", path, digest, obj,
                         prefix + "readOnlyRootFilesystem is not explicitly true",
                         "Some serving engines require writable paths; this is a hardening candidate, not an unconditional defect.",
                         **common)
                if image and not IMAGE_DIGEST.search(image):
                    emit(findings, "LLM-WL-05", path, digest, obj,
                         prefix + "image reference has no sha256 digest: " + image,
                         "Tag mutability depends on registry policy; digest pinning is a reproducibility/supply-chain candidate.",
                         **common)
                resources = c.get("resources") or {}
                req = resources.get("requests") or {}
                lim = resources.get("limits") or {}
                missing = [key for key in ("cpu", "memory") if key not in req or key not in lim]
                if missing:
                    emit(findings, "LLM-RES-01", path, digest, obj,
                         prefix + "CPU/memory requests or limits absent: " + ",".join(missing),
                         "Namespace defaults, VPA, and workload sizing are not evaluated.",
                         **common)
                if not c.get("readinessProbe") and not c.get("startupProbe"):
                    emit(findings, "LLM-RES-03", path, digest, obj,
                         prefix + "no readinessProbe or startupProbe",
                         "A probe may be defined externally; startup/readiness semantics require workload review.",
                         **common)
        elif kind == "Service":
            spec = obj.get("spec") or {}
            ports = spec.get("ports") or []
            port_text = " ".join(
                str(p.get("port", "")) + " " + str(p.get("targetPort", "")) + " " + str(p.get("name", ""))
                for p in ports if isinstance(p, dict)
            )
            meta_name = str((obj.get("metadata") or {}).get("name", ""))
            if spec.get("type") in {"LoadBalancer", "NodePort"} and (
                LLM_HINT.search(meta_name) or re.search(r"(8000|8080|11434|inference|vllm|llm)", port_text, re.I)
            ):
                emit(findings, "LLM-NET-01", path, digest, obj,
                     "Service type=" + str(spec.get("type")) + "; ports=" + port_text,
                     "This does not prove internet reachability, missing authentication, or an exploitable endpoint.",
                     document_index=document_index)
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
