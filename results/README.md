# Phase 3 results

This directory contains reproducible empirical outputs and intermediate review artifacts.

## Canonical inputs

- \`results/labels/reviewer_AI1_full.csv\` — frozen 105-bundle × 28-rule AI-1 reference classifications. These are AI-generated labels, not independent human ground truth.
- \`corpus/SOURCES.lock.json\` — pinned public source/bundle snapshot.
- \`rules/catalog.json\` and \`docs/LABELING_GUIDE.md\` — rule definitions and label semantics.

## Generated outputs

The Phase 3 CI workflow produces a downloadable artifact named \`phase3-scanner-evaluation-and-review-queues\` containing:

- \`raw_candidate_findings.jsonl\` — conservative scanner candidates; multiple resource-level candidates may occur within one bundle-rule unit.
- \`corpus_inventory.jsonl\` and \`corpus_validation.json\` — pinned file hashes, parseability, and resource-kind inventory.
- \`scanner_metrics.csv\` — bundle-rule confusion matrices for the 13 implemented scanner rules, comparing candidates with AI-1 reference labels.
- \`rule_prevalence.csv\` — descriptive PRESENT/(PRESENT+ABSENT), U, and NA rates for all 28 rules in this pinned corpus.
- \`project_rule_prevalence.csv\` — the same descriptive counts stratified by upstream project.
- \`evaluation_summary.json\` — run provenance, aggregate counts, pooled exploratory metrics, and limitations.
- \`ci-generated/*\` — disposable preliminary inventory and eligibility review queues.

Reproduce locally after installing \`requirements.txt\`:

\`\`\`bash
python scripts/validate_corpus.py
python scripts/scan_candidates.py corpus/rendered --output results/raw_candidate_findings.jsonl
python scripts/build_workload_inventory.py --out-dir results/ci-generated
python scripts/evaluate_scanner.py \\
  --labels results/labels/reviewer_AI1_full.csv \\
  --candidates results/raw_candidate_findings.jsonl \\
  --inventory results/corpus_inventory.jsonl \\
  --output-dir results/ci-analysis
\`\`\`

## Interpretation guardrails

- A scanner candidate is not proof of exploitability, reachability, or a confirmed vulnerability.
- Scanner predictions are aggregated to one positive/negative prediction per bundle-rule pair; repeated resource candidates do not inflate the evaluation unit.
- U and NA are excluded from binary confusion matrices and reported separately.
- The current reference labels are AI-generated. Scanner metrics are exploratory AI-reference agreement, not human-validated precision/recall.
- Rules not implemented by the scanner receive no scanner performance metrics.
- Prevalence estimates describe only the pinned public configuration corpus, not live clusters, production deployments, or the universe of LLM-serving systems.
- The corpus has only a small number of upstream project clusters and is concentrated in a few projects. Initial outputs are descriptive point estimates; no cluster-bootstrap confidence intervals are claimed.
- Do not replace the canonical label CSV with CI artifacts or overwrite the original AI-1 reference labels during adjudication.

The workflow writes freshly generated preliminary eligibility queues under \`results/ci-generated/\`. These are disposable triage outputs, not the frozen eligibility decisions. The canonical bundle decisions remain \`results/bundle_eligibility_review.csv\`.
