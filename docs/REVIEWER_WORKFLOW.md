# Two-reviewer labeling workflow

## What is and is not blinded

The current process is **scanner-blind**, not source-blind. Reviewers need the bundle path, project, and resource identity to inspect the configuration. They must not see raw scanner candidate output, AI-generated labels, or each other's labels during the independent pass. Do not describe this as double-blind or source-blind.

## Preconditions

- Complete and freeze bundle eligibility decisions in the generated `bundle_eligibility_review.csv`.
- Resolve all `uncertain` and `non_llm_or_unclear` cases or explicitly exclude them from the primary set.
- Confirm duplicate/version/overlay grouping and freeze the rule catalog version.
- Store the generated eligibility CSV at `results/bundle_eligibility_review.csv`; do not overwrite the generated artifact without retaining provenance.

## Generate separate sheets

Run twice with the **same eligibility CSV, rule catalog, seed, and sample size**. Use separate output files and reviewer IDs. The script does not read scanner findings.

```bash
python scripts/create_blinded_labeling_sample.py \
  --eligibility-csv results/bundle_eligibility_review.csv \
  --seed 20261105 --sample-size 30 --reviewer-id R1 \
  --output results/labels/reviewer_R1.csv

python scripts/create_blinded_labeling_sample.py \
  --eligibility-csv results/bundle_eligibility_review.csv \
  --seed 20261105 --sample-size 30 --reviewer-id R2 \
  --output results/labels/reviewer_R2.csv
```

The sample size of 30 above is a **pilot only**, not a final statistically powered sample. Confirm the pilot size and sampling strata before running it. Do not generate a confirmatory sample until eligibility and protocol are frozen. If all eligible bundles are intended for review, omit `--sample-size` in both commands.

The generator (v2) validates the frozen nine-column eligibility schema and fails loudly — it never silently defaults: upstream project is derived from the pinned corpus mapping (`upstream_project_for_bundle` in `scripts/build_workload_inventory.py`), each selected bundle's SHA-256 is computed from the file on disk, and missing files, duplicate bundle paths, pending/unrecognized `final_decision` values, or unmapped projects abort the run. Each run also writes a provenance sidecar next to the sheet (`<output>.meta.json`) recording the eligibility CSV and rule-catalog hashes, the seed, the reviewer ID, and the exact selected bundle list with projects and hashes. Before distributing the sheets, check that the R1 and R2 sidecars agree on input hashes, seed, sample size, and selected bundles, differing only in `reviewer_id`.

## Independent review

1. Give each reviewer only their own CSV and read-only access to the pinned corpus and labeling guide.
2. Do not share scanner output, the other reviewer's sheet, or interim labels.
3. For each bundle × rule row, enter one of `PRESENT`, `ABSENT`, `U`, or `NA`, plus evidence path and concise rationale. These are reference classifications of the rule condition — reviewers never see scanner predictions, so do not think of them as scanner true/false positives (see `docs/LABELING_GUIDE.md` §1).
4. Use `U` when static artifacts do not establish the required context; do not force a binary decision.
5. Do not record credential values. Record key names and locations only.
6. Lock and timestamp both sheets before any discussion.

## Agreement and adjudication

After both sheets are locked, calculate raw agreement and a chance-corrected statistic appropriate to the label distribution (for four nominal categories, report Cohen's kappa and class counts; consider prevalence effects and confidence intervals). Report U and NA frequencies. Resolve disagreements in a third adjudication column; preserve both original labels and the reason for each change. Do not overwrite either independent sheet.

## Sampling and reporting cautions

- The 30-bundle example is a workflow smoke test, not a publication-ready sample-size justification.
- A bundle × 28-rule matrix can contain many NA rows. Report per-rule applicable denominators and do not treat every matrix cell as an independent sample.
- If the sample is stratified or disproportionate, preserve inclusion probabilities and apply appropriate weights for population estimates.
- Cluster uncertainty estimates by upstream project/source; only 11 project clusters are currently represented.
- AI-generated or scanner-generated candidates can be examined after independent labels are locked, for comparison only.
