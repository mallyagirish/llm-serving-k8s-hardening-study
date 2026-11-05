# Phase 3 Corpus Screening Progress

**Snapshot:** 2026-10-28 lockfile; Phase 3 CI run #54 (2026-11-05).  
**Branch:** research/phase3-empirical-evaluation  
**Status:** Provisional automated triage only; human eligibility decisions are pending.

## Verified corpus accounting

| Measure | Count | Interpretation |
|---|---:|---|
| Locked bundle entries | 202 | Corpus inventory units, not deployments |
| Upstream project clusters | 11 | Versioned charts and related repositories grouped by upstream project |
| Parseable standalone YAML bundles | 195 | Passed PyYAML parsing |
| Documented non-standalone/invalid inputs | 7 | Six Helm template fragments and one invalid non-LLM example |
| YAML documents in parseable bundles | 617 | Documents, not independent observations |
| Resource-level review records | 263 | Workloads and serving-related custom resources; review aid only |

All 202 bundle paths are tracked and the lockfile accounting reconciles. The seven parse exceptions are enumerated in corpus/parse_exceptions.json.

## Provisional bundle triage

The current inventory extractor groups resource evidence within each locked bundle and proposes a bundle-level stratum:

| Provisional stratum | Bundles |
|---|---:|
| Primary LLM-serving candidate | 102 |
| Supporting platform/GPU infrastructure candidate | 86 |
| Non-LLM or unclear | 7 |
| Documented parse exclusion | 7 |
| **Total** | **202** |

These are heuristic review queues, **not final inclusion decisions**. A reviewer must inspect the actual bundle and its resources before setting final_decision.

## Bundle counts by upstream project

| Upstream project cluster | Bundles | Primary candidates | Supporting | Unclear | Parse exclusions |
|---|---:|---:|---:|---:|---:|
| KServe | 79 | 49 | 18 | 6 | 6 |
| Project HAMi | 67 | 3 | 63 | 1 | 0 |
| vLLM Production Stack | 30 | 30 | 0 | 0 | 0 |
| KubeRay | 9 | 4 | 5 | 0 | 0 |
| Ollama Helm | 6 | 6 | 0 | 0 | 0 |
| Infracloud charts | 4 | 4 | 0 | 0 | 0 |
| LiteLLM | 2 | 2 | 0 | 0 | 0 |
| SGLang | 2 | 2 | 0 | 0 | 0 |
| OPEA TGI | 1 | 1 | 0 | 0 | 0 |
| Shalb charts | 1 | 1 | 0 | 0 | 0 |
| Louis030195 TGI Helm | 1 | 0 | 0 | 0 | 1 |
| **Total** | **202** | **102** | **86** | **7** | **7** |

## Important interpretation

- HAMi contributes 67 bundles, but only three are currently classified as direct LLM-serving candidates; most are generic GPU-sharing examples. Keep those in a separate supporting analysis unless a reviewer finds an LLM-serving workload.
- KServe contributes 79 bundles, including direct LLMInferenceService/LLMInferenceServiceConfig examples, generic ML samples, platform resources, and six non-standalone fragments. Review the exact resource purpose and avoid counting every KServe artifact as an LLM workload.
- vLLM Production Stack contributes 30 bundles, including four chart versions and tutorial overlays. Treat versions/overlays as correlated observations and report the chart-version/tutorial strata separately.
- The 11 project clusters, not the 27 lockfile source entries or 202 bundles, are the conservative top-level grouping for dependence-aware summaries.

## Next gates

1. Human-review the 102 primary candidates and 86 supporting candidates; resolve the 7 unclear bundles.
2. Record final bundle decisions and evidence in the screening CSV. Keep the parse exceptions excluded from static YAML analysis.
3. Define exact/near-duplicate and chart-version/overlay handling before computing prevalence.
4. Freeze the primary bundle set and rule predicates.
5. Create a reproducible blinded labeling sample and have two human reviewers label it independently.
6. Run confirmatory analysis only after labels and the protocol are frozen.

CI artifact: [Run #54](https://github.com/mallyagirish/llm-serving-k8s-hardening-study/actions/runs/41955336887). The artifact contains the generated bundle/resource eligibility queues, raw scanner candidates, and validation inventory; it expires after 30 days.
