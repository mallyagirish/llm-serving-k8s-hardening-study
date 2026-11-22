# Publication audit 05 — direct inspection of frozen v2 CSV (2026-11-22)

## Scope and acquisition

Retrieved the complete GitHub blob for `results/labels/reference_labels_author_validated_v2.csv` through the connected GitHub blob API, blob SHA `2462d7ab3d4a380a3fd0f25904a75dd2dba27b28`. The returned UTF-8 content had **1,686,331 JavaScript string characters**. Parsed the returned CSV with an RFC-style quoted-field parser (including escaped quotes and quoted line breaks), using the header fields rather than assuming positional columns. This is a direct content inspection, not a checkout-based invocation of `scripts/verify_frozen_labels.py`.

## Checks performed against retrieved rows

| Check | Observed | Result |
|---|---:|---|
| Data rows | 2,940 | PASS |
| Distinct bundle paths | 105 | PASS |
| Distinct rule IDs | 28 | PASS |
| Distinct upstream projects | 10 | PASS |
| Unique bundle × rule keys | 2,940 | PASS |
| Missing or duplicate bundle × rule keys | 0 (2,940 = 105 × 28) | PASS |
| Conflicting bundle SHA values per bundle path | 0 | PASS |
| Conflicting project assignments per bundle path | 0 | PASS |
| PRESENT | 647 | PASS vs v2 sidecar |
| ABSENT | 738 | PASS vs v2 sidecar |
| U | 697 | PASS vs v2 sidecar |
| NA | 858 | PASS vs v2 sidecar |

### Rule-level spot checks

| Rule | PRESENT | ABSENT | U | NA |
|---|---:|---:|---:|---:|
| LLM-AUTH-02 | 0 | 0 | 99 | 6 |
| LLM-NET-02 | 80 | 0 | 0 | 25 |
| LLM-RES-02 | 22 | 0 | 0 | 83 |

These values agree with `docs/SCANNER_EVALUATION_REPORT.md`. In particular, RES-02 uses the v2 predicate after the Ray Serve amendment.

The 10 observed upstream-project identifiers are `BerriAI/litellm`, `Project-HAMi/HAMi`, `infracloud/charts`, `kserve/kserve`, `opea-project/charts/tgi`, `otwld/ollama-helm`, `ray-project/kuberay`, `sgl-project/sglang`, `shalb/charts`, and `vllm-project/production-stack`.

## Limits of this verification

- This direct blob-content check resolves the prior inability to inspect actual frozen CSV **rows** and supports matrix completeness, outcome totals and project consistency.
- It does **not** independently recompute the SHA-256 digest `c7eeb2ea5f62d3e01724137de30ea6cbe769ba66d936e4a437155def7410aebe` recorded in the sidecar; the Git blob SHA is a different hash.
- It does not independently inspect all source YAML evidence, establish substantive correctness of labels, run scanner/evaluator/cluster bootstrap, or validate the external review provenance.
- Therefore **the full reproducibility gate remains open**. Next run should acquire executable checkout or complete required analysis inputs and reproduce scanner confusion matrices, bootstrap intervals, and output checksums.

## Claim discipline

These are reference-label outcomes in a selected public artifact corpus. PRESENT denotes a rule-defined finding, not a protective control. The 80/80 NET-02 and 22/22 RES-02 observations are conditional on rule applicability and do not estimate operational production-cluster exposure. The label matrix was AI-assisted then author-validated; this check is computational structural validation, not independent human labeling.
