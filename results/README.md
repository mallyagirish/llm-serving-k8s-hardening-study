# Phase 3 results

This directory is reserved for reproducible empirical outputs.

No prevalence findings are published yet. Do not populate summary tables with illustrative or manually estimated values.

Planned outputs:
- raw_candidate_findings.jsonl — conservative scanner candidates for human review; not adjudicated findings.
- corpus_inventory.jsonl and corpus_validation.json — pinned file hashes, parseability, and resource-kind inventory.
- resource_eligibility_review.csv — resource-level triage queue.
- bundle_eligibility_review.csv — bundle-level preliminary eligibility queue with human decision fields.
- summary.csv — counts and denominators by rule, stack, and source type.
- scanner_metrics.csv — comparison against independently adjudicated reference labels.
- figures/ — scripts-generated figures.
- run_metadata.json — commit, corpus lockfile hash, tool versions, run timestamp, and configuration.

Every result must be regenerable from a documented command and pinned input snapshot. Preserve raw machine outputs separately from human reference labels and adjudication records.
## CI-generated review queues

The Phase 3 workflow writes freshly generated, preliminary inventory and eligibility queues under `results/ci-generated/` and uploads them in the `phase3-ci-generated-review-queues` artifact. These are disposable triage outputs, not the frozen, AI-assisted eligibility decisions. The canonical frozen bundle decisions remain `results/bundle_eligibility_review.csv`; do not replace them with an artifact copy. The CI queue artifact is not a canonical source for reviewer-sheet generation.
