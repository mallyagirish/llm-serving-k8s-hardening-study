# Publication audit 06 — automated frozen-label integrity gate (2026-11-23)

## New reproducibility control

Added `.github/workflows/publication-frozen-label-integrity.yml` on the publication branch. The workflow runs the committed regression tests and `scripts/verify_frozen_labels.py` against the **actual checked-out** frozen v2 CSV and its metadata sidecar, using Python 3.11. The verifier computes the actual CSV SHA-256, compares it to the frozen sidecar, and checks the 2,940-row, 105×28, 10-project matrix and four outcome totals. The workflow saves its JSON output as an Actions artifact when generated.

The workflow can run manually via `workflow_dispatch`; it also triggers on relevant publication-branch changes and matching pull requests. It has read-only repository permissions. It does not alter any frozen data.

## Evidence status

The workflow **was committed**, but no successful workflow execution, job log, or artifact was inspected as part of this audit. Its existence does not constitute an executed reproducibility result. The preceding audit directly inspected all CSV rows but did not recompute the frozen CSV SHA-256.

To close this narrow gate, inspect the Actions run for this workflow, confirm both test and verifier steps succeeded, archive the exact run URL and verification artifact, and compare the recorded SHA-256 to `c7eeb2ea5f62d3e01724137de30ea6cbe769ba66d936e4a437155def7410aebe`.

## Remaining independent reproduction

Even a successful frozen-label workflow does **not** reproduce scanner candidate generation, pre-/post-adjudication confusion matrices, project-cluster bootstrap intervals, or the substantive correctness of source-evidence labels. Those remain separate publication gates. The external reviewer provenance also remains author-reported, not a quantified independent second annotation.

## Editorial boundary

Continue to describe findings as rule-defined properties of sampled public Kubernetes artifacts, not production security prevalence. The scanner-visible post-adjudication 100% score is sensitivity analysis only. Do not mark the paper submission-ready until the full empirical pipeline, provenance, and manuscript checks are complete.
