# Independent second-annotator packet

**Prepared:** 2026-11-11 · **Status: will not be fielded** — author decision
2026-11-11: no independent second annotator for this submission. This packet
is retained as an unused prepared instrument; no second annotator has labeled
anything, and nothing in this folder is evidence.

## Why this exists

The frozen reference set (`results/labels/reference_labels_author_validated_v2.csv`,
2,940 cells) is **AI-assisted, author-validated**: one author validated
every cell. That is single-author validation, not independent double
annotation, and it supports no human inter-rater reliability claim (see
`docs/REFERENCE_LABEL_VALIDATION.md`). This packet is the turnkey
instrument for closing that gap honestly: an independent annotator labels
a stratified sample **from the manifests and the guide alone**, and
agreement with the frozen labels is computed mechanically.

## Sample design

- 15 of the 105 primary bundles, stratified by upstream project: one per
  project (10 projects), plus 3 extra KServe and 2 extra
  production-stack bundles (the two dominant projects). Fixed seed
  20261111; the draw is recorded in `sample_manifest.csv` with SHA-256
  per bundle.
- All 28 rules per bundle → **420 cells**. At bundle granularity, so the
  annotator always sees full bundle context, never isolated rows.
- If 420 cells is too much for the annotator available, whole bundles can
  be dropped from the end of the sheet — agreement statistics remain
  valid for completed bundles; say which bundles were done.

## Contents

- `annotation_sheet.csv` — the sheet to complete (420 rows; `label`,
  `evidence_path`, `rationale` start blank). Column schema matches the
  study's other label files so the join is mechanical.
- `manifests/` — the 15 sampled bundles, copied verbatim (filenames are
  the bundle paths with `/` → `__`). **The packet is self-contained:** the
  annotator never needs the repository.
- `LABELING_GUIDE.md` — labeling guide v0.4, verbatim copy. This is the
  only definition source the annotator should use.
- `sample_manifest.csv` — bundle list with hashes (provenance, not labels).
- `analyze_agreement.py` — stdlib-only agreement analysis (see below).

## Instructions for the annotator (also in ANNOTATOR_INSTRUCTIONS.md)

Label every cell PRESENT / ABSENT / U / NA per the guide, citing the
manifest evidence, **without** looking at any existing labels — do not
open the study repository's `results/labels/` folder or the frozen
reference file if you have repo access; work only from this packet.

## Running the analysis (after a completed sheet returns)

```
python3 analyze_agreement.py /path/to/completed_sheet.csv \
    --reference ../../results/labels/reference_labels_author_validated_v1.csv \
    --out-prefix agreement_v1
```

Reports overall and per-rule percent agreement and Cohen's κ
(4-category), κ on decided cells (PRESENT/ABSENT on both sides), the
decided/undecided boundary-crossing count, a confusion matrix, and a
`agreement_v1_disagreements.csv` for adjudication review. Blank
annotator cells are reported as incomplete, never scored.

## What a completed round would — and would not — establish

- **Would:** a genuine human-vs-reference Cohen's κ on a stratified
  420-cell sample; a disagreement list the author can adjudicate through
  the normal artifact (`author_adjudication_history.csv`), issuing a v2
  frozen set if any labels change.
- **Would not:** retroactively make the full 2,940-cell set independently
  labeled — the manuscript claim stays "author-validated full set;
  independent double annotation on a stratified 420-cell sample (κ = …)".
  Disagreements are adjudicated by the author, and that role asymmetry
  is stated in the methods text.

## Manuscript wording (draft, for the author to adopt or edit)

> Reference labels were produced with AI assistance and validated in full
> by the author (2,940 cells). To test the reliability of the labeling
> protocol independently, a second annotator, blinded to the reference
> labels and working only from the manifests and the labeling guide,
> labeled a stratified sample of 15 bundles (420 cells, one or more per
> upstream project). Agreement between the independent labels and the
> reference labels was κ = [VALUE] overall ([VALUE] on cells both sides
> decided PRESENT/ABSENT); all disagreements were adjudicated by the
> author and are recorded in the replication package. The full-set labels
> remain single-author validated; the sample result bounds, but does not
> eliminate, the risk of systematic author labeling bias.
