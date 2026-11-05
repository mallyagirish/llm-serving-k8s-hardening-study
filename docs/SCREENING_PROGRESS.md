# Phase 3 Corpus Screening Progress

**Snapshot:** 2026-10-28 lockfile; latest verified Phase 3 CI run #74 (2026-11-05 UTC).  
**Branch:** research/phase3-empirical-evaluation  
**Status:** Automated triage only; human eligibility decisions are pending.

## Verified corpus accounting

| Measure | Count | Interpretation |
|---|---:|---|
| Locked bundle entries | 202 | Corpus inventory units, not deployments |
| Upstream project clusters | 11 | Versioned charts and related repositories grouped by upstream project |
| Parseable standalone YAML bundles | 195 | Passed PyYAML parsing |
| Documented non-standalone/invalid inputs | 7 | Six Helm template fragments and one invalid non-LLM example |
| YAML documents in parseable bundles | 617 | Documents, not independent observations |
| Exact duplicate file hashes | 0 | Near-duplicate versions/overlays still require source-aware review |
| Resource-level review records | 263 | Workloads and serving-related custom resources; review aid only |

The latest run validated all 202 locked bundle paths, found no parser errors beyond the seven documented exclusions, and found no exact duplicate bundle-file hashes. Near-duplicate chart versions and overlays still require source-aware review. The seven parse exceptions are enumerated in corpus/parse_exceptions.json.

## Provisional bundle triage

| Provisional stratum | Bundles |
|---|---:|
| Primary LLM-serving candidate | 102 |
| Supporting platform/GPU infrastructure candidate | 86 |
| Non-LLM or unclear | 7 |
| Documented parse exclusion | 7 |
| **Total** | **202** |

These are heuristic review queues, **not final inclusion decisions**. A reviewer must inspect the actual bundle and its resources before setting final_decision. The latest conservative scan emitted 613 candidate observations across 49 bundles for human review; these are not adjudicated findings or prevalence estimates.

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

## Interpretation and known dependence

- HAMi contributes 67 bundles, but only three are currently classified as direct LLM-serving candidates; most are generic GPU-sharing examples. Keep those in a separate supporting analysis unless a reviewer finds an LLM-serving workload.
- KServe contributes 79 bundles, including direct LLMInferenceService/LLMInferenceServiceConfig examples, generic ML samples, platform resources, and six non-standalone fragments. Review exact resource purpose.
- vLLM Production Stack contributes 30 bundles, including chart versions and tutorial overlays. Treat versions/overlays as correlated observations and report their strata separately.
- The 11 project clusters, not the 27 lockfile source entries or 202 bundles, are the conservative top-level grouping for dependence-aware summaries.

## Next gates

1. Human-review all primary candidates, supporting candidates, and unclear bundles; do not use the preliminary stratum as a final decision.
2. Record final bundle decisions, in-scope resource identity, rationale, reviewer, and source evidence in the review CSV.
3. Define exact/near-duplicate and chart-version/overlay handling before computing prevalence.
4. Freeze the primary bundle set and rule predicates.
5. Generate identical scanner-blind labeling sheets for two independent human reviewers using the same seed and sample size, but separate output files and reviewer IDs. The sheets expose source paths because reviewers need to inspect the artifacts; they are not source-blinded.
6. Lock both reviewers' labels before adjudication; report agreement, uncertainty, and adjudication changes.
7. Run confirmatory analysis only after labels and the protocol are frozen.

## Reproducibility artifacts

- [Latest successful CI run #74](https://github.com/mallyagirish/llm-serving-k8s-hardening-study/actions/runs/41955908875)
- Artifact: `phase3-corpus-validation-and-candidates`, artifact ID `13383270891`, expires 2026-12-05.
- The artifact contains corpus inventory, validation report, raw scanner candidates, and bundle/resource eligibility queues. Generated queue rows are not final human decisions.
