# Publication audit 02 — frozen label lineage and scanner denominators

**Date:** 2026-11-18. **Scope:** Cross-check committed metadata, author adjudication history and scanner report. This is a documentary audit, not a byte-level CSV recount or execution of analysis scripts.

## Immutable lineage verified from committed sidecar and history

| Artifact | Role | Recorded counts | Evidence |
|---|---|---|---|
| `results/labels/reviewer_AI1_full.csv` | Original AI-assisted classifications, subsequently author-validated by author report | 2,940 rows | `docs/REFERENCE_LABEL_VALIDATION.md` |
| `results/labels/reference_labels_author_validated_v1.csv` | Four scanner-disagreement adjudications applied | P 646 / A 738 / U 697 / NA 859 | `docs/REFERENCE_LABEL_VALIDATION.md` |
| `results/labels/reference_labels_author_validated_v2.csv` | v1 plus one RES-02 guide amendment | P 647 / A 738 / U 697 / NA 858 | `results/labels/reference_labels_author_validated_v2.csv.meta.json` |

The v2 sidecar records source v1 SHA-256 `d8774402e20fd13f6796cf87981db4f228855403a84965b86889d36bdd41f3ef` and frozen v2 SHA-256 `c7eeb2ea5f62d3e01724137de30ea6cbe769ba66d936e4a437155def7410aebe`. These are **recorded hashes**, not hashes independently recomputed in this audit. Git blob SHA of v2 CSV: `2462d7ab3d4a380a3fd0f25904a75dd2dba27b28` (not a SHA-256 file digest).

## Five adjudication decisions in committed CSV

The `results/labels/author_adjudication_history.csv` has five data records:
1. KServe managed-DRA, WL-05: PRESENT → U (sidecar image tag, main image unspecified).
2. Same bundle, RES-01: PRESENT → ABSENT (main has CPU/memory requests and limits).
3. KServe smoke-test CPU sample, RES-03: PRESENT → ABSENT (main has readiness probe).
4. KServe PD-disaggregation, RES-03: ABSENT → PRESENT (decode pool lacks readiness/startup probe).
5. KubeRay Ray Serve, RES-02: NA → PRESENT (v0.5 amendment recognizes Serve autoscaling to four replicas without an included matching PDB).

**Important:** records 1–4 were selected after scanner disagreement and adjudicated with predictions visible. Record 5 is a post-v1 rule-predicate amendment, not a scanner disagreement. Do not combine these as five independent validation disagreements.

## Arithmetic checks of manuscript-reported aggregate numbers

- v2 total: 647 + 738 + 697 + 858 = **2,940**, equal to 105 × 28.
- U / all: 697 / 2,940 = **23.7075%**, rounds to 23.71%.
- U / non-NA: 697 / (2,940 − 858) = **33.4774%**, rounds to 33.48%.
- Pre-adjudication scanner assessable total: 487 + 1 + 3 + 498 = **989**.
- Pre-adjudication precision: 487 / 488 = **99.7951%**; recall: 487 / 490 = **99.3878%**; F1: 974 / 978 = **99.5910%**.
- Post-adjudication assessable total: 488 + 0 + 0 + 500 = **988**. The one-unit reduction is consistent with WL-05 PRESENT → U; the other three adjudications remain binary. **Do not describe the pre/post denominator as unchanged.**
- Scanner coverage: 13 / 28 = **46.43%** of rule definitions implemented, not 46.43% of all label units automatically assessable.

## Publication corrections required

1. **Denominator clarity:** report pre-adjudication scanner n=989 and post-adjudication n=988 separately. The v2 RES-02 change does not affect scanner results because RES-02 is not implemented.
2. **Reference lineage:** do not equate original AI-generated predictions with independently blinded human labels. Author-reported validation and reviewer-reported inspection must be distinguished from independently generated second annotations.
3. **Terminology:** PRESENT means a *rule-defined finding*, not a protective control present; ABSENT means evidence sufficient for no finding under that predicate.
4. **Evaluation caution:** the post-adjudication perfect score is a scanner-visible, disagreement-selected sensitivity analysis, not a valid held-out accuracy estimate.
5. **Statistical generalization:** project-cluster bootstrap intervals with 10 clusters are exploratory; the sampling frame is selected public artifacts, not live production deployments.
6. **Version drift:** the old protocol's commands reference `reviewer_AI1_full.csv` and v1. Add a dated amendment and pin exact commands used for the manuscript before submission.

## Still unverified

The connector's partial read of the large v2 CSV returned no rows in this session. Accordingly this audit **does not** independently establish 2,940 unique keys, per-rule frequencies, source hashes, or complete row evidence. Reproduce those checks by downloading the exact frozen file and executing the evaluation in a pinned environment. Preserve output logs and checksums in a subsequent audit. Do not mark reproducibility gate passed based on this document.

## Suggested reproducibility commands (run against checked-out frozen revision)

```bash
sha256sum results/labels/reference_labels_author_validated_v1.csv results/labels/reference_labels_author_validated_v2.csv
python - <<'PY'
import csv, collections
p='results/labels/reference_labels_author_validated_v2.csv'
with open(p, newline='') as f:
    rows=list(csv.DictReader(f))
print('columns:', list(rows[0]) if rows else [])
print('rows:', len(rows))
PY
python -m unittest discover -s tests -v
python scripts/validate_corpus.py
```

The CSV schema must be inspected before implementing unique-key and outcome checks; do not guess field names. Follow the repository's current evaluator and bootstrap CLI help, not the historical protocol examples.
