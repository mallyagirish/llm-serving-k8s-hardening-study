# Phase 3 results

This directory is reserved for reproducible empirical outputs.

No prevalence findings are published yet. Do not populate summary tables with illustrative or manually estimated values.

Planned outputs:
- raw_findings.jsonl — structured rule assessments with evidence and applicability labels.
- summary.csv — counts and denominators by rule, stack, and source type.
- scanner_metrics.csv — comparison against independently adjudicated reference labels.
- figures/ — scripts-generated figures.
- run_metadata.json — commit, corpus lockfile hash, tool versions, run timestamp, and configuration.

Every result must be regenerable from a documented command and pinned input snapshot. Preserve raw machine outputs separately from human reference labels and adjudication records.
