#!/usr/bin/env python3
"""Build a resource-level inventory for human LLM-serving eligibility review.

This is a triage aid only. It does not determine security findings or final
eligibility. The final primary/secondary/exclusion decision remains a human
reviewed field in the generated CSV.
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
SERVING_CR_KINDS = {"LLMInferenceService", "LLMInferenceServiceConfig", "InferenceService", "RayService", "RayCluster", "ServingRuntime", "ClusterServingRuntime", "LocalModelCache", "LocalModelNodeGroup", "LoraAdapter"}
DIRECT_ENGINE_HINT = re.compile(
    r"(vllm|text-generation|text_generation|tgi|sglang|ollama|litellm|"
    r"deepseek|llama|qwen|mistral|gemma|bloom|falcon|mixtral|phi|granite|llm)",
    re.I,
)
NON_SERVING_HINT = re.compile(r"(finetun|fine[-_ ]?tun|training|trainer)", re.I)
SUPPORT_HINT = re.compile(r"(kserve|kuberay|ray|hami|gpu|device-plugin|scheduler|operator|vllm|tgi|sglang|ollama|litellm|text-generation)", re.I)


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
    if NON_SERVING_HINT.search(identity) and not re.search(
        r"(vllm|text-generation|tgi|sglang|ollama|litellm)", identity, re.I
    ):
        return "supporting_platform_candidate", "Training/fine-tuning identity; not an inference workload candidate."
    if kind in {"LLMInferenceService", "LLMInferenceServiceConfig"}:
        return "primary_candidate", "Kubernetes LLM inference custom resource/config; verify version and rule-specific applicability."
    if DIRECT_ENGINE_HINT.search(identity):
        return "primary_candidate", "Resource name, labels, or container identity directly suggests an LLM inference engine/model; verify actual purpose."
    context = " ".join([kind, source, path])
    if kind in SERVING_CR_KINDS or SUPPORT_HINT.search(context):
        return "supporting_platform_candidate", "Serving platform/operator/GPU infrastructure or generic ML serving resource; determine rule-specific applicability."
    return "non_llm_or_unclear", "No direct LLM-serving identity detected from resource metadata/container images."

