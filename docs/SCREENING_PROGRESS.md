# Phase 3 Corpus Screening Progress

**Snapshot:** 2026-10-28 lockfile; latest verified Phase 3 CI run #74 (2026-11-05 UTC).  
**Branch:** research/phase3-empirical-evaluation  
**Status:** Eligibility decisions FROZEN 2026-11-05 (see below). The freeze is an AI-assisted review pass recorded in the CSV with reviewer `claude-ai-assist`; per `docs/LABELING_GUIDE.md` §5, AI-assisted review is not a human second review, so author confirmation of the borderline calls listed below remains the outstanding protocol gate before the dataset is described as human-reviewed.

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

## Frozen eligibility decisions (2026-11-05)

Every one of the 202 bundles was screened against its actual manifests (resource kinds, container images, model/engine signals) and assigned a `final_decision` in `corpus/eligibility_review.csv`, with a frozen copy at `results/bundle_eligibility_review.csv`. No bundle remains `uncertain`.

| Final decision | Bundles |
|---|---:|
| `include_primary` | 105 |
| `include_supporting` | 71 |
| `exclude_non_llm` | 19 |
| `exclude_unparseable` | 7 |
| **Total** | **202** |

Movement from the committed preliminary strata in the CSV (primary 100 / supporting 69 / unclear 26 / parse-pending 7 — note these CSV strata never matched the 102/86/7 figures in earlier revisions of this document, which grouped the queues differently):

- Of 100 primary candidates: 99 confirmed primary; 1 excluded (a standalone JSON Patch test fragment that configures no workload by itself).
- Of 69 supporting candidates: 68 confirmed supporting; 1 excluded (a comment-only instruction document containing no resources).
- Of 26 unclear: 6 promoted to primary (four KServe HuggingFace/vLLM-Omni serving-runtime definitions and two Ray-LLM services), 3 to supporting (KServe controller install, KServe storage-container platform resource, Ray Serve custom-service example), and 17 excluded — the KServe generic-ML sample set (TorchServe image-classifier InferenceServices ×8, MNIST variants, and the two BERT sequence-classification samples), five bare storage tutorial resources, one empty (0-byte) bundle, and one toy Ray Serve DAG sample.
- All 7 parse-pending bundles confirmed `exclude_unparseable`, matching `corpus/parse_exceptions.json` (six Helm template fragments / raw template concat and one invalid-YAML non-LLM example).

Frozen counts by upstream project cluster:

| Upstream project cluster | Bundles | Primary | Supporting | Exclude (non-LLM) | Exclude (unparseable) |
|---|---:|---:|---:|---:|---:|
| KServe | 79 | 53 | 3 | 17 | 6 |
| Project HAMi | 67 | 2 | 64 | 1 | 0 |
| vLLM Production Stack | 30 | 30 | 0 | 0 | 0 |
| KubeRay | 9 | 4 | 4 | 1 | 0 |
| Ollama Helm | 6 | 6 | 0 | 0 | 0 |
| Infracloud charts | 4 | 4 | 0 | 0 | 0 |
| LiteLLM | 2 | 2 | 0 | 0 | 0 |
| SGLang | 2 | 2 | 0 | 0 | 0 |
| OPEA TGI | 1 | 1 | 0 | 0 | 0 |
| Shalb charts | 1 | 1 | 0 | 0 | 0 |
| Louis030195 TGI Helm | 1 | 0 | 0 | 0 | 1 |
| **Total** | **202** | **105** | **71** | **19** | **7** |

Borderline calls recorded for author confirmation (deciding evidence is in each row's `review_notes`):

- The two BERT samples (`kserve-manifest-bert`, `kserve-manifest-bert_gpu`) were excluded as generic-ML sequence-classification demos. An encoder-LM reading could argue primary; the exclusion follows the screening guide's rule that unclear cases need positive LLM-serving evidence.
- The LiteLLM gateway charts are primary with no model server in the bundle, per the screening guide's inclusion of gateways in the primary stratum.
- `LLMInferenceServiceConfig`-only bundles (llm-d templates, scheduler/EPP configs) are primary: they are direct LLM inference serving configurations, though they are config fragments correlated with their sample families and must be clustered accordingly in analysis.
- HAMi GPU-allocation pods stay supporting even when the image is a serving image (e.g. the VastAI vLLM image runs `sleep infinity`); they allocate shared GPUs and serve nothing.

The latest conservative scan emitted 613 candidate observations across 49 bundles for human review; these are not adjudicated findings or prevalence estimates.

## Interpretation and known dependence

- HAMi contributes 67 bundles, but only three are currently classified as direct LLM-serving candidates; most are generic GPU-sharing examples. Keep those in a separate supporting analysis unless a reviewer finds an LLM-serving workload.
- KServe contributes 79 bundles, including direct LLMInferenceService/LLMInferenceServiceConfig examples, generic ML samples, platform resources, and six non-standalone fragments. Review exact resource purpose.
- vLLM Production Stack contributes 30 bundles, including chart versions and tutorial overlays. Treat versions/overlays as correlated observations and report their strata separately.
- The 11 project clusters, not the 27 lockfile source entries or 202 bundles, are the conservative top-level grouping for dependence-aware summaries.

## Next gates

1. ~~Human-review all primary candidates, supporting candidates, and unclear bundles~~ — done 2026-11-05 as an AI-assisted pass (frozen table above); the remaining human gate is author confirmation of the borderline calls listed above.
2. ~~Record final bundle decisions, in-scope resource identity, rationale, reviewer, and source evidence in the review CSV~~ — done: `final_decision`, rationale, and reviewer are recorded for all 202 rows in `corpus/eligibility_review.csv` (frozen copy: `results/bundle_eligibility_review.csv`).
3. Define exact/near-duplicate and chart-version/overlay handling before computing prevalence.
4. Freeze the primary bundle set and rule predicates.
5. Generate identical scanner-blind labeling sheets for two independent human reviewers using the same seed and sample size, but separate output files and reviewer IDs. The sheets expose source paths because reviewers need to inspect the artifacts; they are not source-blinded.
6. Lock both reviewers' labels before adjudication; report agreement, uncertainty, and adjudication changes.
7. Run confirmatory analysis only after labels and the protocol are frozen.

## Reproducibility artifacts

- [Latest successful CI run #74](https://github.com/mallyagirish/llm-serving-k8s-hardening-study/actions/runs/41955908875)
- Artifact: `phase3-corpus-validation-and-candidates`, artifact ID `13383270891`, expires 2026-12-05.
- The artifact contains corpus inventory, validation report, raw scanner candidates, and bundle/resource eligibility queues. Generated queue rows are not final human decisions.
