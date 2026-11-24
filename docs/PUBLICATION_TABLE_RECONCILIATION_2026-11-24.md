# Publication table reconciliation — 2026-11-24

Evidence: GitHub Actions run 45380849713, artifact 14912794691, input commit b3d346cabc780e09b5dc66a20d3c3a1bff800526. Compared current manuscript blob 192cd9760faefc71bc9c9bb477f96c18d2d558fa against ci-analysis/post-adjudication/rule_prevalence.csv in the downloaded archive.

All 28 manuscript rule rows match the reproduced PRESENT, ABSENT, U, NA, assessable denominator and displayed prevalence (one decimal percent; undefined for zero assessable units). Programmatic checks on the CSV confirmed each row sums to 105 and assessable equals PRESENT + ABSENT. Column totals: 647, 738, 697, 858 respectively; total 2940. NET-02 is 80/80 and RES-02 is 22/22 under the frozen predicates. This verifies numerical consistency, not correctness of the underlying labels.

## Outstanding metadata discrepancy
The fresh post-adjudication evaluation_summary.json names reference_labels_author_validated_v2.csv as its input but retains the generic interpretation 'Exploratory AI-reference comparison; not human-validated scanner accuracy or real-world deployment prevalence.' Its limitations also say author verification and independent human reference review remain pending. These strings conflict with the manuscript's author-reported validation history and should not be treated as evidence either for or against actual human review. The summary also says no bootstrap intervals are produced by this first pass; separate cluster-analysis outputs exist. Clarify these scope-specific metadata strings in a future publication-only change without changing statistical logic or frozen labels. Preserve the original run artifact.

The exact pre-adjudication comparator's human-validation status remains unresolved; do not upgrade the scanner accuracy claim until documented. External review provenance remains pending. No release gate is waived by this reconciliation.
