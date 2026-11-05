# Manuscript Outline (Results Pending)

**Working title:** Security-Relevant Configurations in Public Kubernetes-Based LLM Inference Stacks: A Reproducible Empirical Study

**Status:** Outline only. No prevalence results or claims are populated.

## Abstract (complete after confirmatory analysis)

- Context: Kubernetes is increasingly used to deploy LLM inference engines, gateways, and supporting GPU infrastructure.
- Gap: existing studies measure general Kubernetes/Helm misconfiguration or runtime exposure of self-hosted LLM services; this study examines public Kubernetes deployment artifacts as a distinct evidence layer.
- Method: pinned corpus, human-reviewed bundle eligibility, rule-specific evidence predicates, blinded reference labeling, conservative static candidate extraction.
- Results: [insert only after frozen corpus, labels, and analysis pipeline]
- Contribution: [finalize after systematic related-work review and validated results]

## 1. Introduction

- Motivation: LLM-serving deployment surfaces include API authentication, gateway routing, model credentials, distributed control ports, GPU devices, model/cache storage, and readiness.
- Why generic Kubernetes checks are insufficient to characterize all serving-specific surfaces.
- Research gap and scope boundary: public deployment configuration artifacts, not live public endpoint scanning.
- Research questions.
- Contributions, limited to what the results substantiate.

## 2. Background and Related Work

- Kubernetes/Helm configuration and workload security.
- LLM inference architectures: vLLM, TGI, SGLang, Ollama, KServe LLMInferenceService, Ray Serve, gateways.
- Runtime exposure studies of self-hosted LLM services (including LENS).
- GPU multi-tenancy and data isolation.
- Related Kubernetes/Helm empirical studies and scanner limitations.
- Explicit novelty comparison and non-overlap statement.

## 3. Corpus Construction

- Source discovery and selection.
- Snapshot date, lockfile, commit pins, licensing.
- Chart default renders, values overlays, raw manifests.
- Parseability exclusions and corpus flow diagram.
- Human-reviewed eligibility and exclusion criteria.
- Duplicate/version/overlay relationships.
- Primary unit: locked configuration bundle; resources are evidence within bundles.

## 4. Rule Catalog and Operationalization

- Rule taxonomy and rationale.
- Static evidence predicates.
- Context-dependent rules and uncertainty conditions.
- Positive/negative fixtures.
- Rule versioning and review.
- Distinguish configuration indicators from confirmed exploitability.

## 5. Study Design

- RQ-specific outcomes and denominators.
- TP/FP/U/NA reference-label semantics.
- Human blinded sampling and adjudication.
- Scanner extraction and rule-specific coverage.
- Statistical analysis and clustering by source/project.
- Reproducibility and artifact execution.

## 6. Results

### 6.1 Corpus and eligibility flow
[Populate from frozen inventory and reviewed eligibility table.]

### 6.2 Overall rule-level observations
[Populate from independently adjudicated labels; report numerator, denominator, uncertainty, applicability, and confidence intervals.]

### 6.3 Differences by source type and serving stack
[Only if sample size and dependence structure support comparison.]

### 6.4 Context-dependent and unassessable rules
[Report U/NA rates and examples.]

### 6.5 Case studies
[Select representative, independently reviewed cases; include no secret values.]

## 7. Discussion

- Practical implications for chart maintainers and platform teams.
- Which controls are realistically observable from public manifests.
- Why static indicators do not prove public reachability or exploitability.
- Recommendations for safer LLM-serving chart defaults.
- Upstream hardening opportunities.

## 8. Threats to Validity

- Construct validity and static-analysis limits.
- Selection/publication bias.
- Tutorial/default versus production behavior.
- Version drift.
- Source dependence and duplicate renders.
- Labeler bias and inter-rater reliability.
- Rule coverage and tool limitations.

## 9. Ethics and Responsible Disclosure

- Public artifacts only.
- Secret redaction.
- Responsible reporting to maintainers.
- Avoid publishing exploitable details before coordinated disclosure.

## 10. Conclusion

- Summarize only validated observations.
- State limits and future work.

## Artifact Appendix

- Commit and release identifiers.
- Corpus lockfile SHA-256.
- Exact commands and tool versions.
- Rule catalog version.
- Labeling guide and anonymized adjudication data.
- Raw scanner candidates and human reference labels.
- Analysis scripts and figure regeneration.
