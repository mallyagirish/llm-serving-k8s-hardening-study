# Phase 3 — Scanner comparison and descriptive prevalence (exploratory)

**Evaluation commit:** \`2248fe4163a5a74c9bddcb5b0548cf4520fa22cb\`  
**Current branch head when this report was written:** \`7adb2d221944edbd44ffd68ae76f1f693354744e\`  
**Dual-evaluation CI:** [run 43089354140](https://github.com/mallyagirish/llm-serving-k8s-hardening-study/actions/runs/43089354140) — success; both pre- and post-adjudication evaluator passes completed  
**Scanner:** 2.0.0  
**Evaluator:** 1.1.0  
**Scanner SHA-256:** \`c5572a9db1a3690423f2b3b94358e0bc3c2a437a73bd33427de3d628cb4f644a\`

## Interpretation boundary

The 2,940 reference labels were initially generated with AI assistance and subsequently **human-validated by the study author across all 2,940 bundle-rule entries** (105 primary bundles × 28 rules). The dataset is therefore described as an **AI-assisted, author-validated reference-label set**; see [the validation record](REFERENCE_LABEL_VALIDATION.md). The metrics below compare scanner candidates against this author-validated reference set. This was single-author validation, not independent double annotation, and no human inter-rater reliability statistic is claimed. A scanner candidate is not proof of exploitability, reachability, or a confirmed vulnerability.

The primary evaluation unit is one bundle × rule. Multiple resource-level scanner candidates within a bundle-rule pair are collapsed to one positive prediction. U and NA are excluded from binary confusion matrices and reported separately. Only the 13 implemented rules receive scanner metrics.

## Corpus and execution

- 105 primary bundles × 28 rules = 2,940 AI-assisted, author-validated reference labels.
- 202 locked corpus bundle files were scanned; the corpus validator reports 195 parseable standalone YAML bundles and 7 documented non-standalone/invalid inputs. Evaluation was filtered to the frozen 105 primary bundles.
- 10 upstream project clusters.
- 740 resource-level scanner candidate records in total; 733 were in primary bundles and 7 were outside the primary set.
- 541 unique positive bundle-rule predictions in the primary set.
- 13/28 rules have scanner implementations (46.4%).
- Candidate output hashes were checked against the corpus inventory and frozen reference bundle hashes.
- CI tests, corpus validation, scanner execution, and evaluator all passed.

## Scanner comparison

Across the 989 assessable bundle-rule units for the 13 implemented rules, the **primary, pre-adjudication comparison** is against the author-validated labels as they stood before scanner-disagreement review. This avoids using scanner-visible disagreement decisions as the primary benchmark.

| Metric | Pre-adjudication (primary) | Post-adjudication (sensitivity only) |
|---|---:|---:|
| TP | 487 | 488 |
| FP | 1 | 0 |
| FN | 3 | 0 |
| TN | 498 | 500 |
| Precision | 99.80% | 100.00% |
| Recall | 99.39% | 100.00% |
| Specificity | 99.80% | 100.00% |
| F1 | 99.59% | 100.00% |
| Accuracy | 99.60% | 100.00% |

Pre-adjudication macro-F1 is 99.53% across the 10 implemented rules with both PRESENT and ABSENT reference examples. The other three implemented rules do not have both reference classes and are excluded from that macro average. The post-adjudication 100% result is a sensitivity analysis only: the four disputed rows were selected because they disagreed with scanner predictions, and those predictions were visible during author review. It is therefore not an independent estimate of scanner accuracy.

### Per-rule confusion counts (pre-adjudication primary comparison)

| Rule | TP | FP | FN | TN | Reference limitation |
|---|---:|---:|---:|---:|---|
| LLM-GPU-01 | 0 | 0 | 0 | 57 | No PRESENT examples; recall not estimable |
| LLM-GPU-03 | 2 | 0 | 0 | 88 | Only 2 PRESENT examples |
| LLM-NET-01 | 2 | 0 | 0 | 44 | Only 2 PRESENT examples |
| LLM-NET-03 | 0 | 0 | 0 | 1 | Only 1 ABSENT; no PRESENT examples |
| LLM-NET-05 | 2 | 0 | 0 | 90 | Only 2 PRESENT examples |
| LLM-RES-01 | 51 | 0 | 1 | 26 | — |
| LLM-RES-03 | 26 | 1 | 1 | 55 | — |
| LLM-SEC-02 | 2 | 0 | 0 | 97 | Only 2 PRESENT examples |
| LLM-WL-01 | 77 | 0 | 0 | 13 | — |
| LLM-WL-02 | 88 | 0 | 0 | 2 | Only 2 ABSENT examples |
| LLM-WL-03 | 77 | 0 | 0 | 13 | — |
| LLM-WL-04 | 78 | 0 | 0 | 12 | — |
| LLM-WL-05 | 82 | 0 | 1 | 0 | No ABSENT examples; specificity not estimable |

Do not interpret the pooled score as evidence of general scanner accuracy. The evaluation is a development-stage comparison on one pinned corpus, and the reference labels were initially AI-assisted and subsequently validated by one study author.

### Scanner development comparison

An earlier scanner pass (core Kubernetes workload kinds only) produced 288 TP, 26 FP, 202 FN, and 473 TN on the corresponding assessable reference units. The current 2.0.0 scanner adds selected KServe/Ray serving CRDs, excludes auxiliary test/migration/cache workloads from workload-hardening checks, recognizes remote GPU resource keys, and narrows credential detection.

The earlier and current results are **not a controlled benchmark comparison**: the scanner's supported resource surface and candidate scope changed. The change is useful evidence that resource-kind coverage and workload identity were major sources of the earlier false negatives, but the two scores must not be presented as a clean before/after performance experiment.

## Descriptive reference-label results

These are author-validated reference-label counts for the pinned public configuration corpus, not prevalence in deployed production clusters.

| Rule | PRESENT | ABSENT | U | NA | Interpretation |
|---|---:|---:|---:|---:|---|
| LLM-AUTH-02 | 0 | 0 | 99 | 6 | Non-estimable from static artifacts |
| LLM-AUTH-03 | 0 | 0 | 99 | 6 | Non-estimable from static artifacts |
| LLM-AUTH-04 | 0 | 0 | 99 | 6 | Non-estimable from static artifacts |
| LLM-NET-02 | 80 | 0 | 0 | 25 | 80/80 applicable bundles have no included NetworkPolicy selecting their inference workload |
| LLM-RES-02 | 21 | 0 | 0 | 84 | 21/21 applicable scaled bundles have no matching PDB under the current predicate |
| LLM-SEC-01 | 0 | 105 | 0 | 0 | No in-scope secret-like literal finding in this reference pass |

Across the frozen 2,940 rows, U is 697 (23.71%). Among non-NA rows, U is 697 / (646 + 738 + 697) = 33.49%. Always state which denominator is used.

The RES-02 result remains sensitive to the definition of scaling: a Ray Serve application-level autoscaling template is present in one KubeRay configuration even though the Kubernetes worker group is not autoscaled. The current guide's predicate and the application-level interpretation should be resolved before final publication.

## Scanner/reference disagreements — resolved 2026-11-11

The row-level scanner disagreement artifact contained three FN and one FP against the pre-adjudication author-validated labels. The author reviewed these four rows against raw manifests and the labeling guide, with scanner predictions visible in the review queue, and recorded all decisions in `results/labels/author_adjudication_history.csv`. The resulting frozen set is `results/labels/reference_labels_author_validated_v1.csv` (PRESENT 646 / ABSENT 738 / U 697 / NA 859; SHA-256 in `reference_labels_author_validated_v1.csv.meta.json`). The original AI-assisted source file `reviewer_AI1_full.csv` remains unmodified. Because the four rows were selected by disagreement and scanner predictions were visible during review, the post-adjudication 100% score is potentially optimistic and is reported only as sensitivity analysis. The pre-adjudication metrics above remain the primary scanner comparison. The four final decisions are evidence-backed author adjudications, but not blinded independent labels.

1. **LLM-WL-05 — KServe managed-DRA multi-device:** PRESENT → **U**. The `busybox:1.36` image belongs to the `sidecar`; the `main` inference container has no image field, so image immutability is undecidable for the in-scope container.
2. **LLM-RES-01 — same managed-DRA bundle:** PRESENT → **ABSENT**. The `main` container has CPU and memory requests and limits explicitly configured.
3. **LLM-RES-03 — KServe smoke-test-data CPU sample:** PRESENT → **ABSENT**. The main container has a `readinessProbe` as well as a liveness probe.
4. **LLM-RES-03 — KServe PD-disaggregation config:** ABSENT → **PRESENT**. The top-level template is the decode serving pool; its main container has liveness only and no readiness/startup probe. Under the protocol's bundle aggregation rule (PRESENT if any in-scope serving template meets the positive predicate), the prefill pool's readiness probe does not cure the decode pool.

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
  --output-dir results/ci-analysis/pre-adjudication

# Repeat against the frozen post-adjudication reference set for sensitivity analysis:
python scripts/evaluate_scanner.py \\
  --labels results/labels/reference_labels_author_validated_v1.csv \\
  --candidates results/raw_candidate_findings.jsonl \\
  --inventory results/corpus_inventory.jsonl \\
  --output-dir results/ci-analysis/post-adjudication
\`\`\`

The author-validation provenance is recorded in [REFERENCE_LABEL_VALIDATION.md](REFERENCE_LABEL_VALIDATION.md). The Phase 3 CI workflow now runs both comparisons and uploads separate `pre-adjudication/` and `post-adjudication/` outputs, preserving the primary and sensitivity analyses. The evaluator summary records the scanner version and source SHA-256.
