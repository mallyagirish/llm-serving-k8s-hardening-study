# Related Work and Novelty Positioning

**Status:** Preliminary literature scan, not a systematic review. Update before manuscript submission.

## Closest related work

1. **Minna, Massacci, and Tuma (2025), “Analyzing and mitigating (with LLMs) the security misconfigurations of Helm charts from Artifact Hub,” Empirical Software Engineering 30(5), 132.** This is the closest broad empirical predecessor. It analyzed 4,961 chart templates with seven tools and evaluated LLM-generated mitigations, including manual review. It also reports that context matters and that generated changes can remove unrelated configuration and break applications. DOI: https://doi.org/10.1007/s10664-025-10688-0

2. **Shamim, Hu, and Rahman (ICSE 2025), “On Prescription or Off Prescription?: An Empirical Study of Community-prescribed Security Configurations for Kubernetes.”** This study examines 544 configuration files, 53 CIS recommendations, practitioner awareness, and five static analysis tools. It is relevant to configuration-level security measurement and scanner limitations. https://akondrahman.github.io/publication/icse25

3. **Ghorab, Abdel Latif, and Saied (2026), “Kubernetes Misconfigurations in the Wild: Taxonomy, Evolution, and Automated Repair with Large Language Models.”** This recent work analyzes 2,662 Stack Overflow issues and evaluates LLM remediation with schema-guided validation. It is directly relevant to broad Kubernetes misconfiguration taxonomy and automated repair. DOI: https://doi.org/10.1145/3805760.3814908 ; preprint: https://arxiv.org/abs/2609.27030

## Proposed differentiation

This project must not claim novelty for:
- being the first empirical study of Kubernetes/Helm misconfigurations;
- being the first to compare Kubernetes security scanners;
- being the first to use LLMs to propose Kubernetes fixes;
- generic schema-guided YAML repair.

The defensible candidate contribution is narrower:
- a corpus specifically focused on Kubernetes-based LLM inference serving stacks (vLLM, TGI, SGLang, Ollama, KServe GenAI, Ray Serve LLM, gateways and GPU-sharing examples);
- a domain-specific taxonomy for inference endpoint authentication/route coverage, distributed serving ports, GPU/device isolation, model-cache trust, and serving-specific operational surfaces;
- measurement that separates chart defaults, tutorial overlays, raw manifests, and synthetic scenarios;
- rule-level evidence and uncertainty reporting that distinguishes static indicators from verified exposure or exploitability;
- reproducible public corpus and upstream hardening artifacts.

These are hypotheses about the contribution, not proof of novelty. The systematic review must search ACM DL, IEEE Xplore, SpringerLink, USENIX, arXiv, and relevant cloud-native security venues for LLM-serving/Kubernetes security studies published before submission.

## Important methodological correction

The current catalog has 28 proposed rules, but not all are directly measurable from static YAML. The Phase 3 scanner currently emits conservative candidates for a subset; it does not establish ground truth. The manuscript must:
- label static evidence as configuration indicators, not confirmed vulnerabilities;
- distinguish public tutorial examples from production-oriented defaults;
- use workload/source-level denominators and address repeated chart versions/overlays;
- independently validate a sample of positive and negative cases;
- publish uncertainty and applicability counts;
- avoid claiming scanner precision/recall until an independent reference set exists.

## Positioning statement (draft)

“We present a domain-specific empirical characterization of security-relevant configuration patterns in public Kubernetes-based LLM inference serving artifacts. Unlike broad Helm/Kubernetes surveys, our focus is the serving stack’s endpoint, distributed-control, GPU, model-cache, and model-credential surfaces. We provide a pinned corpus and a rule-level evidence framework that explicitly separates observable manifest indicators from deployment-context-dependent security claims.”

Do not use “first” or “novel” in the abstract until the systematic review supports it.
