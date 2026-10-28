# Hardening LLM Inference on Kubernetes

Empirical study of security and reliability misconfigurations in public Helm charts and Kubernetes manifests used to serve large language models (vLLM, TGI, SGLang, Ollama, KServe GenAI, Ray Serve LLM, and related gateways).

**Author:** [Girish Mallya](https://github.com/mallyagirish)  
**Working title:** *Hardening LLM Inference on Kubernetes: An Empirical Study of Production Serving Stacks*  
**License:** [Apache-2.0](LICENSE)

> Not legal advice. This repository is an independent research artifact; it does not constitute immigration, legal, or security advice.

## Problem

Organizations increasingly run LLM inference on Kubernetes: OpenAI-compatible HTTP APIs, GPU-backed Deployments, Ingress/Gateway frontends, shared model caches, and multi-tenant GPU nodes. Default and tutorial configurations for these stacks often omit controls that matter specifically for inference—API authentication on `/v1` and sibling routes, NetworkPolicy around GPU pods, TLS on Ingress, secret handling for Hugging Face tokens, GPU isolation, and trusted model-cache mounts.

Generic Kubernetes and Helm hardening surveys (CIS benchmarks, Pod Security Standards, broad chart audits) catch many workload-security gaps, but they do not systematically cover **LLM-serving-specific** surfaces such as:

- OpenAI-compatible endpoints with missing or partial API-key coverage
- Tokenizer, admin, and developer endpoints left enabled
- LoadBalancer/NodePort exposure of inference ports
- Ray / torch.distributed / KV-transfer control-plane ports
- GPU sharing and multi-tenant isolation (e.g. MIG / HAMi-style)
- Model weight and compile-cache volume trust assumptions

This study builds a rule catalog aimed at those gaps and a pinned, reproducible corpus of public serving charts and manifests against which the rules can be measured.

## What's novel here

| Aspect | This study | Typical Helm / K8s misconfig surveys |
| --- | --- | --- |
| Scope | LLM **inference serving** stacks on Kubernetes | Broad charts or CIS/PSS across arbitrary workloads |
| Rules | **28 rules** spanning Auth, Network, Secrets, GPU/Isolation, Workload Security, Storage/Model, Resources, Observability—many LLM-specific | Generic container/RBAC/network checks |
| Unit of analysis | `helm template` defaults + named values overlays + raw manifests | Often chart source only, or live cluster scans |
| Corpus | Pinned public sources in `SOURCES.lock.json` (27 sources, 202 rendered bundles as of 2026-10-28) | Ad hoc or unpinned samples |
| Goal | Prevalence measurement, case studies, and upstream hardening (Phase 3+) | One-off audits or tool benchmarks |

Full rule definitions, severity, detection notes, and corpus design: **[docs/PHASE1_RULES_AND_CORPUS.md](docs/PHASE1_RULES_AND_CORPUS.md)**.

## Rule catalog (28 rules)

Detection baseline: render with `helm template` (default and tutorial values) or copy raw manifests → flatten YAML → static probes (grep / policy-as-code / custom scripts). Runtime exploitation is out of scope for Phase 2.

| Category | Rule IDs (examples) | LLM-serving relevance |
| --- | --- | --- |
| Auth | LLM-AUTH-01 … 05 | API keys on OpenAI-compatible routes; sibling path bypass; tokenizer/dev endpoints; CORS; Ingress auth |
| Network | LLM-NET-01 … 05 | LoadBalancer/NodePort; NetworkPolicy; TLS; distributed/Ray ports; hostNetwork/hostPID |
| Secrets / RBAC | LLM-SEC-01 … 03 | Tokens in values/ConfigMaps; missing `secretKeyRef`; over-privileged ServiceAccounts |
| GPU / Isolation | LLM-GPU-01 … 03 | GPU requests/limits; multi-tenant sharing gaps; privileged GPU shortcuts |
| Workload Security | LLM-WL-01 … 05 | runAsNonRoot, readOnlyRootFilesystem, privilege escalation, seccomp, image digests |
| Storage / Model | LLM-STOR-01 … 03 | Shared/world-writable model PVCs; untrusted cache mounts; privileged download initContainers |
| Resources | LLM-RES-01 … 03 | CPU/memory limits; PodDisruptionBudget; readiness/startup probes |
| Observability | LLM-OBS-01 | Unauthenticated metrics / Ray dashboard exposure |

Primary LLM-engine security anchor used in Phase 1 design: [vLLM security documentation](https://github.com/vllm-project/vllm/blob/main/docs/usage/security.md).

## Corpus (Phase 2)

Pinned snapshot in [`corpus/SOURCES.lock.json`](corpus/SOURCES.lock.json):

| Metric | Value |
| --- | --- |
| Collection time | 2026-10-28, America/Los_Angeles |
| Sources | **27** (git clones, Helm repos, OCI charts, raw manifests) |
| Rendered bundles | **202** |
| Breakdown | ~20 Helm defaults, ~28 values overlays (incl. vLLM tutorials), ~154 manifests |
| Stacks represented | vLLM production-stack, KServe, KubeRay / Ray Serve LLM, TGI charts, Ollama, HAMi examples, SGLang, LiteLLM, and related community charts |

Large chart clones under `corpus/charts/` are **not** committed. Re-fetch and re-render from the lockfile with the scripts below. Phase 2 notes: [docs/PHASE2_FETCH_RENDER.md](docs/PHASE2_FETCH_RENDER.md).

## Repository layout

```text
docs/PHASE1_RULES_AND_CORPUS.md   # 28-rule catalog + corpus plan
docs/PHASE2_FETCH_RENDER.md       # fetch/render status
corpus/SOURCES.lock.json          # pinned sources + counts
corpus/rendered/                  # helm template / manifest outputs
corpus/manifests/                 # raw public Kubernetes YAML
scripts/                          # fetch + render reproducibility
rules/                            # rule probes (growing; Phase 3)
results/                          # prevalence outputs (Phase 3)
```

## Reproduce

Requires: `helm`, `git`, `curl`, `jq`.

```bash
git clone https://github.com/mallyagirish/llm-serving-k8s-hardening-study.git
cd llm-serving-k8s-hardening-study

./scripts/fetch_and_render.sh   # full fetch + render + lockfile refresh
# or, if charts are already under corpus/charts/:
./scripts/render_all.sh
```

Rendered outputs land under `corpus/rendered/`. Scanning probes and prevalence tables are **not** published yet (Phase 3).

## Status

| Phase | Content | Status |
| --- | --- | --- |
| 1 | Rule catalog (28) + corpus design | Done — [docs/PHASE1_RULES_AND_CORPUS.md](docs/PHASE1_RULES_AND_CORPUS.md) |
| 2 | Fetch + render pinned public corpus | Done — 27 sources, 202 rendered bundles (2026-10-28, America/Los_Angeles) |
| 3 | Scan probes + prevalence measurement | Next |
| 4+ | Case studies, upstream issues/PRs, preprint draft | Planned |

No prevalence results, CVE claims, or paper citations are asserted in this README beyond the Phase 1–2 artifacts in-tree.

## Ethics and scope

- **Public configurations only.** No employer-private or entitlement-gated cluster configs.
- Tutorial and default values are often intentionally insecure for demos; findings characterize **published defaults and examples**, not private production clusters.
- Prefer responsible disclosure and upstream pull requests before highlighting Critical findings in charts marketed for production use.
- This work is independent research. It is not affiliated with the upstream projects scanned, except as a consumer of their public repositories.

## Citation

Working paper title (preprint not yet posted):

> Girish Mallya. *Hardening LLM Inference on Kubernetes: An Empirical Study of Production Serving Stacks*. Work in progress.

When an arXiv ID or DOI exists, this section will be updated. Prefer citing a specific commit or release tag of this repository until then.

## License

Copyright and license terms are in [LICENSE](LICENSE) (Apache License 2.0).
