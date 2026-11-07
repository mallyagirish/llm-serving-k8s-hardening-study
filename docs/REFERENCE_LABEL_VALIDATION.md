# Reference-label validation record

**Recorded:** 2026-11-07  
**Dataset:** `results/labels/reviewer_AI1_full.csv`  
**Scope:** 105 primary bundles × 28 rules = 2,940 bundle-rule labels  
**Validation status:** Author reports that all 2,940 entries were human-validated.

## Provenance

The labels were initially generated with AI assistance. The study author subsequently states that every entry in the full 2,940-row label matrix was human-validated. Accordingly, the dataset should be described as an **AI-assisted, author-validated reference-label dataset**.

This description distinguishes the origin of the initial classifications from responsibility for the final reference labels. It does not imply that a second independent human annotator labeled the same rows, that the author was blinded to AI suggestions, or that inter-rater reliability was measured.

## What this record establishes

- Validation scope covers all 2,940 bundle-rule entries, not merely a spot-check sample.
- The four labels retain their protocol meanings: PRESENT, ABSENT, U, and NA.
- The source AI-assisted label file remains the preserved input artifact; this record does not overwrite or silently alter its rows.
- Scanner confusion-matrix results may be described as agreement/performance against the **author-validated reference labels**, with the AI-assisted initial-labeling workflow disclosed.
- The validation is single-author validation. It is not independent double annotation and does not support a human-versus-human Cohen's kappa or other inter-rater reliability claim.

## Remaining audit trail

The following details should be added if available before submission: the dates or period over which validation was performed; whether every row's cited source path and evidence field was re-opened during validation; the number and identities of changed labels; and a machine-readable change log linking each changed row to its prior label, final label, reason, and evidence. Do not invent these details retrospectively.

The scanner disagreement queue remains a separate audit aid. Its proposed dispositions are not applied by this record. Any subsequent change to a reference label must be recorded in a separate author-adjudication artifact while preserving the original AI-assisted file.

## Recommended manuscript wording

> Initial bundle-rule classifications were generated with AI assistance. The study author then human-validated all 2,940 entries (105 primary configuration bundles × 28 rules) against the source artifacts and the labeling guide. We therefore use the term *AI-assisted, author-validated reference labels* for the final reference set. This was a single-author validation process, not independent double annotation; no human inter-rater reliability statistic is claimed.
