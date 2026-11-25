# Publication readiness plan — 18 November 2026

## Scope and evidence boundary
This branch prepares the existing study for peer review. Do not alter frozen corpus or labels in publication-only edits. The working manuscript is `docs/MANUSCRIPT_DRAFT.md`; review provenance is `docs/EXTERNAL_REVIEW_PROVENANCE.md`.

## Current manuscript-reported results (not independently recomputed in this document)
- 202 collected bundles; 105 primary bundles from 10 upstream project clusters.
- 28 rules and 2,940 bundle-rule reference entries.
- Frozen v2 labels as reported in manuscript: PRESENT 647, ABSENT 738, U 697, NA 858 (sum 2,940).
- Pre-adjudication scanner comparison for 13 implemented rules: TP 487, FP 1, FN 3, TN 498 (989 assessable units).
- Four scanner disagreements were subsequently reviewed with scanner predictions visible. The post-adjudication perfect score is sensitivity analysis, **not** independent validation.
- External second-person review of all labels and methodology is author-reported, not documented as independent blind double annotation. Do not report Cohen's kappa or 100% reviewer agreement without evidence.

## Release gates

### Gate 1: provenance and reproducibility
- [ ] Capture precise frozen v2 label path, SHA-256, rule-guide version, source lockfile revision, and analysis script commit.
- [ ] Re-run corpus validation, reference label counts, scanner evaluation and project-cluster bootstrap on the frozen inputs. Save command log, versions, hashes and output checksums.
- [ ] Confirm the pre-adjudication comparator truly corresponds to author-validated labels, rather than an unreviewed AI draft; resolve any mismatch in protocol instructions.
- [ ] Record independent review date, reviewer expertise/independence, exactly what evidence was inspected, any challenged rows, and resolutions. Obtain reviewer-generated documentation where available. Do not invent missing records or backdate them.
- [ ] Preserve pre- and post-adjudication datasets separately.

### Gate 2: statistical integrity
- [ ] Verify all per-rule denominators and the distinction between PRESENT/ABSENT/U/NA.
- [ ] Report descriptive findings only for eligible, author-validated bundle-rule units; never derive prevalence from raw scanner candidates.
- [ ] Include rule-level uncertainty, applicability, source type and project-level heterogeneity; avoid treating correlated bundles as independent.
- [ ] Audit cluster bootstrap methodology, interval stability with only 10 clusters, and leave-one-project-out sensitivity.
- [ ] Report scanner metrics only for 13 implemented rules, including U/NA exclusions and per-rule failures.

### Gate 3: manuscript consistency
- [ ] Reconcile older `docs/PHASE3_EMPIRICAL_PROTOCOL.md` wording with frozen v2 outcomes and current manuscript, without rewriting history.
- [ ] Verify bibliography and all numerical claims against committed outputs and original sources.
- [ ] Add reproducible corpus selection flow, per-rule four-outcome figure, project heterogeneity figure, and scanner confusion/coverage table.
- [ ] State explicitly that public tutorials/defaults are not production deployments, and static policy absence does not prove exposure or exploitability.
- [ ] Complete literature search log (databases, dates, queries, screening decisions) and compare against closest work.

### Gate 4: release
- [ ] Select venue based on actual contribution and manuscript format; confirm current submission rules, open-access fees, data policy, and prior-preprint policy.
- [ ] Prepare anonymized manuscript if venue requires double-anonymous review; remove author identity from manuscript and supplemental metadata where required.
- [ ] Archive reproducibility package and immutable release; preserve licenses and avoid exposing secrets.
- [ ] Final technical, ethical, statistical and copyediting review before submission.

## Publication-ready claim wording
The reference set was initially AI-assisted and then validated by the study author. A second person reportedly reviewed the full matrix and methodology, but no independent blind second annotation matrix or quantified human inter-rater reliability is currently documented. Findings describe the sampled public configuration artifacts, not actual production deployments. Primary scanner agreement is measured against the original AI-assisted comparator, whose exact pre-adjudication human-validation status is undocumented; it must not be presented as independent proof of ground truth. The frozen author-validated reference set is used for descriptive findings, and scanner-visible adjudication is a separate sensitivity analysis.

## Immediate next deliverable
A versioned reproducibility audit recording exact file paths, hashes, commands and discrepancies, followed by manuscript revisions and figure generation. Do not mark a gate complete solely because CI passed.

## Progress ledger — 24 November 2026

- Fresh reproduction evidence: [run 45380849713](https://github.com/mallyagirish/llm-serving-k8s-hardening-study/actions/runs/45380849713), input commit `b3d346cabc780e09b5dc66a20d3c3a1bff800526`, artifact 14912794691. See `docs/PUBLICATION_TABLE_RECONCILIATION_2026-11-24.md`: all 28 rule rows, denominators and displayed prevalence match. This is numerical reconciliation, not validation of labels.
- Manuscript now distinguishes primary comparator agreement from author-reported validation of frozen labels. The provenance gate remains open; see `docs/EXTERNAL_REVIEW_PROVENANCE.md`.
