# Phase 3 — Scanner comparison and descriptive prevalence (exploratory)

**Evaluation commit:** \`2248fe4163a5a74c9bddcb5b0548cf4520fa22cb\`  
**Current branch head when this report was written:** \`7adb2d221944edbd44ffd68ae76f1f693354744e\`  
**CI:** [run 42402372928](https://github.com/mallyagirish/llm-serving-k8s-hardening-study/actions/runs/42402372928) — success  
**Scanner:** 2.0.0  
**Evaluator:** 1.1.0  
**Scanner SHA-256:** \`c5572a9db1a3690423f2b3b94358e0bc3c2a437a73bd33427de3d628cb4f644a\`

## Interpretation boundary

The 2,940 reference labels are AI-1 generated. They are scanner-blind, but they are not independent human ground truth. The metrics below are **exploratory agreement between scanner candidates and AI-1 reference classifications**, not human-validated precision/recall. A scanner candidate is not proof of exploitability, reachability, or a confirmed vulnerability.

The primary evaluation unit is one bundle × rule. Multiple resource-level scanner candidates within a bundle-rule pair are collapsed to one positive prediction. U and NA are excluded from binary confusion matrices and reported separately. Only the 13 implemented rules receive scanner metrics.

## Corpus and execution

- 105 primary bundles × 28 rules = 2,940 AI-1 reference labels.
- 202 parseable corpus bundles were scanned; evaluation was filtered to the frozen 105 primary bundles.
- 10 upstream project clusters.
- 740 resource-level scanner candidate records in total; 733 were in primary bundles and 7 were outside the primary set.
- 541 unique positive bundle-rule predictions in the primary set.
- 13/28 rules have scanner implementations (46.4%).
- Candidate output hashes were checked against the corpus inventory and frozen reference bundle hashes.
- CI tests, corpus validation, scanner execution, and evaluator all passed.

## Scanner comparison

Across the 989 assessable bundle-rule units for the 13 implemented rules:

| Metric | Result |
|---|---:|
| TP | 487 |
| FP | 1 |
| FN | 3 |
| TN | 498 |
| Precision | 99.80% |
| Recall | 99.39% |
| Specificity | 99.80% |
| F1 | 99.59% |
| Accuracy | 99.60% |

Macro-F1 is 99.53% across the 10 implemented rules that have both PRESENT and ABSENT reference examples. The other three implemented rules do not have both reference classes and are excluded from that macro average.

### Per-rule confusion counts

| Rule | TP | FP | FN | TN | Reference limitation |
|---|---:|---:|---:|---:|---|
| LLM-GPU-01 | 0 | 0 | 0 | 57 | No PRESENT examples; recall not estimable |
| LLM-GPU-03 | 2 | 0 | 0 | 88 | Only 2 PRESENT examples |
| LLM-NET-01 | 2 | 0 | 0 | 44 | Only 2 PRESENT examples |
| LLM-NET-03 | 0 | 0 | 0 | 1 | Only 1 ABSENT; no PRESENT examples |
| LLM-NET-05 | 2 | 0 | 0 | 90 | Only 2 PRESENT examples |
| LLM-RES-01 | 51 | 0 | 1 | 26 | — |
| LLM-RES-03 | 26 | 1 | 1 | 55 | One remaining disagreement requires adjudication |
| LLM-SEC-02 | 2 | 0 | 0 | 97 | Only 2 PRESENT examples |
| LLM-WL-01 | 77 | 0 | 0 | 13 | — |
| LLM-WL-02 | 88 | 0 | 0 | 2 | Only 2 ABSENT examples |
| LLM-WL-03 | 77 | 0 | 0 | 13 | — |
| LLM-WL-04 | 78 | 0 | 0 | 12 | — |
| LLM-WL-05 | 82 | 0 | 1 | 0 | No ABSENT examples; specificity not estimable |

Do not interpret the pooled score as evidence of general scanner accuracy. The evaluation is a development-stage comparison on one pinned corpus, and the reference labels are AI-generated.

### Scanner development comparison

An earlier scanner pass (core Kubernetes workload kinds only) produced 288 TP, 26 FP, 202 FN, and 473 TN on its assessable AI-1 reference units. The current 2.0.0 scanner adds selected KServe/Ray serving CRDs, excludes auxiliary test/migration/cache workloads from workload-hardening checks, recognizes remote GPU resource keys, and narrows credential detection.

The earlier and current results are **not a controlled benchmark comparison**: the scanner's supported resource surface and candidate scope changed. The change is useful evidence that resource-kind coverage and workload identity were major sources of the earlier false negatives, but the two scores must not be presented as a clean before/after performance experiment.

## Descriptive reference-label results

These are AI-1 reference-label counts for the pinned public configuration corpus, not prevalence in deployed production clusters.

| Rule | PRESENT | ABSENT | U | NA | Interpretation |
|---|---:|---:|---:|---:|---|
| LLM-AUTH-02 | 0 | 0 | 99 | 6 | Non-estimable from static artifacts |
| LLM-AUTH-03 | 0 | 0 | 99 | 6 | Non-estimable from static artifacts |
| LLM-AUTH-04 | 0 | 0 | 99 | 6 | Non-estimable from static artifacts |
| LLM-NET-02 | 80 | 0 | 0 | 25 | 80/80 applicable bundles have no included NetworkPolicy selecting their inference workload |
| LLM-RES-02 | 21 | 0 | 0 | 84 | 21/21 applicable scaled bundles have no matching PDB under the current predicate |
| LLM-SEC-01 | 0 | 105 | 0 | 0 | No in-scope secret-like literal finding in this reference pass |

Across all 2,940 rows, U is 696 (23.67%). Among non-NA rows, U is 696 / (648 + 737 + 696) = 33.45%. Always state which denominator is used.

The RES-02 result remains sensitive to the definition of scaling: a Ray Serve application-level autoscaling template is present in one KubeRay configuration even though the Kubernetes worker group is not autoscaled. The current guide's predicate and the application-level interpretation should be resolved before final publication.

## Four remaining scanner/reference disagreements

The current row-level disagreement artifact contains three FN and one FP. Raw manifests indicate that several are likely AI-1 labeling or scope errors rather than scanner defects. The original AI-1 CSV must remain immutable; these are author-review recommendations, not silently applied corrections.

1. **LLM-WL-05 — KServe managed-DRA multi-device:** AI-1 labels PRESENT using \`busybox:1.36\`, but that image belongs to the \`sidecar\`; the \`main\` inference container has no image field. Recommended disposition: U for image immutability unless another source supplies the main image.
2. **LLM-RES-01 — same managed-DRA bundle:** AI-1 labels PRESENT, but the \`main\` container has CPU and memory requests and limits. Recommended disposition: ABSENT, assuming the displayed main container is the in-scope inference container.
3. **LLM-RES-03 — KServe smoke-test-data CPU sample:** AI-1 labels PRESENT, but the main container has a \`readinessProbe\` as well as a liveness probe. Recommended disposition: ABSENT.
4. **LLM-RES-03 — KServe PD-disaggregation config:** AI-1 labels ABSENT because a role template has a readiness probe, but the top-level main template has liveness only and no readiness/startup probe. Under the protocol's bundle aggregation rule (PRESENT if any in-scope serving template meets the positive predicate), recommended disposition: PRESENT. Confirm that both templates are in-scope before changing the reference label.

These four cases should be reviewed and resolved in a separate author-adjudication artifact. Do not overwrite \`reviewer_AI1_full.csv\`.

## Remaining validity limits

- Only 10 project clusters; KServe and vLLM Production Stack account for 83/105 bundles (79%). Project-level results are required; do not treat bundles as independent projects.
- No cluster-bootstrap confidence intervals are produced in this first pass.
- Public charts, examples, and rendered configurations do not represent all private or production deployments.
- AUTH-02/03/04 are non-estimable from this static-artifact corpus; do not turn U into ABSENT or report zero prevalence.
- GPU-01 has no PRESENT reference examples, and NET-03 has only one ABSENT example. Their scanner sensitivity cannot be evaluated from this sample.

## Reproduction and artifacts

Run:

\`\`\`bash
python scripts/validate_corpus.py
python scripts/scan_candidates.py corpus/rendered --output results/raw_candidate_findings.jsonl
python scripts/build_workload_inventory.py --out-dir results/ci-generated
python scripts/evaluate_scanner.py \\
  --labels results/labels/reviewer_AI1_full.csv \\
  --candidates results/raw_candidate_findings.jsonl \\
  --inventory results/corpus_inventory.jsonl \\
  --output-dir results/ci-analysis
\`\`\`

The successful CI artifact for [run 42402372928](https://github.com/mallyagirish/llm-serving-k8s-hardening-study/actions/runs/42402372928) contains the raw candidate JSONL, per-rule scanner metrics, prevalence tables, project-stratified metrics, row-level disagreements, and evaluator summary. The evaluator summary records the scanner version and source SHA-256.
