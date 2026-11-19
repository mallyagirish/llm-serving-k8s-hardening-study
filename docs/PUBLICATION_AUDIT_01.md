# Publication audit 01 — provenance and claim consistency (2026-11-18)

This audit checks committed documentation and file presence; it does **not** claim to have rerun numerical analyses or independently inspected all 2,940 CSV rows.

## Files verified on publication branch
| File | Git blob SHA (not SHA-256 of downloaded bytes) | Observation |
|---|---|---|
| `docs/MANUSCRIPT_DRAFT.md` | see repository history | Manuscript v0.1 contains frozen v2 results and pre-adjudication comparison |
| `results/labels/reference_labels_author_validated_v2.csv` | `2462d7ab3d4a380a3fd0f25904a75dd2dba27b28` | File exists; contents/counts not independently recomputed in this audit |
| `docs/REFERENCE_LABEL_VALIDATION.md` | `474fe53d2d1fb074bfb3bd6b42813df1aa0b5175` | Documents author report of full validation, identifies AI-assisted origin |
| `docs/EXTERNAL_REVIEW_PROVENANCE.md` | see repository history | Second-person review is author-reported; no independent annotation matrix or disagreement trail documented |
| `docs/RES02_RAY_SERVE_DECISION.md` | `d59c096662e6711a77084f44246146d8307b6600` | Documents post-freeze v2 RES-02 predicate amendment |

## Claims and cross-file discrepancies to fix
1. **Frozen-set path drift:** protocol §5B's reproduction example uses `results/labels/reviewer_AI1_full.csv` for the primary comparison and `reference_labels_author_validated_v1.csv` for post-adjudication sensitivity. Manuscript reports frozen **v2** counts. Confirm which pre-adjudication file and v2 file actually produced the manuscript's reported scores; update commands only after reproducing them. Never silently substitute label versions.
2. **Protocol chronology:** protocol header still calls itself v0.1 with 'no prevalence results' and includes earlier study questions. Preserve historical protocol as such or append a dated amendment pointing to current analysis; do not present it as the current results report.
3. **Reference independence:** source label filename `reviewer_AI1_full.csv` is misleading if interpreted as independent human ground truth. The author-validation record explains its history, but the manuscript must consistently describe this as AI-assisted and author-validated.
4. **Second review:** author-reported inspection of 2,940 labels is not independent double annotation. No agreement coefficient, zero-disagreement assertion, or independently validated ground-truth claim is warranted without contemporaneous reviewer records.
5. **Potential label leakage:** four scanner disagreements were resolved with scanner predictions visible. Primary evaluation must use pre-adjudication reference; perfect post-adjudication score only as sensitivity.
6. **Dependence and uncertainty:** 105 bundles derive from 10 upstream clusters. Any intervals must reflect clustering and be described as exploratory with few clusters; no claims about production deployment prevalence.
7. **Outcome semantics:** `PRESENT` means the rule's *finding/weakness* is present, not that a protective control is present. `ABSENT` means sufficient evidence of no finding under the rule predicate; `U` is insufficient static evidence; `NA` is inapplicability. Make this explicit in every figure/table legend.
8. **Scanner scope:** scanner implements 13/28 rules; binary confusion metrics exclude U and NA. High pooled agreement is not evidence of 28-rule automated coverage.

## Reproduction acceptance criteria (still open)
- Read exact frozen v2 CSV and confirm unique (bundle, rule) pairs, 105×28 completeness, allowed labels and counts (manuscript reports 647/738/697/858).
- Verify locked input SHA-256 values, project cluster mapping, label version and rule-guide version.
- Run documented evaluation on pre-adjudication reference and separately on v2; compare all counts, per-rule results and bootstrap settings to manuscript.
- Produce a machine-generated discrepancy table with commands, environment, input hashes, and output hashes.
- Do not treat this documentation-only audit as passing these gates.

## Reviewer evidence request (not a claim)
Obtain a dated statement or original log from the independent reviewer specifying source file version, whether all evidence was independently opened, what labels were challenged, whether any corrections were requested, and how disagreements were resolved. If unavailable, keep the narrow author-reported review wording.
