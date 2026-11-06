# Phase 3 — Empirical Evaluation Protocol

**Version:** 0.1 draft  
**Status:** Protocol design; no prevalence results have been generated.  
**Parent artifact:** Phase 1 rule catalog and Phase 2 pinned public corpus.

## 1. Objective

Measure how often the 28 proposed LLM-serving Kubernetes security rules are applicable and satisfied in the pinned public configuration corpus. Distinguish an evidenced weakness from a missing field, unsupported inference, or control that cannot be assessed from static YAML.

The primary unit of analysis is the **configuration bundle** recorded in the corpus lockfile (one rendered chart/version/values overlay or one raw manifest bundle). A bundle may contain multiple Kubernetes resources and workloads; those resources are evidence within the bundle, not automatically independent observations. The resource-level inventory is a review aid for identifying the actual LLM-serving workload and its related Services, Ingresses, policies, and RBAC objects. Do not count its 263 resource rows as independent deployments. Chart versions and tutorial overlays from one upstream project are correlated and must be clustered or summarized separately.

## 2. Research questions

- **RQ1 — Exposure:** What proportion of eligible LLM-serving configuration bundles expose each in-scope security weakness?
- **RQ2 — Category profile:** How does posture vary across authentication, network, secrets/RBAC, GPU/isolation, workload security, storage/model, resources, and observability?
- **RQ3 — Stack differences:** How do results differ by serving stack and source type (official chart, community chart, tutorial/example, raw manifest)?
- **RQ4 — Evidence quality:** Which rules can be assessed reliably from static configuration, and which require runtime, deployment, or application context?
- **RQ5 — Remediation opportunities:** Which high-confidence findings have actionable, narrowly scoped upstream fixes?

## 3. Corpus accounting and inclusion

Use the committed corpus/SOURCES.lock.json as the immutable Phase 2 snapshot. The lockfile records 27 sources and 202 rendered bundles. The Phase 2 narrative document currently says 203 in one place; resolve this discrepancy from the lockfile before analysis and use the verified count consistently.

Before scanning:
1. Validate every lockfile bundle path exists in the reproduced corpus.
2. Compute SHA-256 for every input file.
3. Parse each YAML stream and record document count, API kind, namespace, workload identity, and source metadata.
4. Classify provenance as chart default, named upstream values overlay, raw upstream manifest, or synthetic researcher-created overlay.
5. Identify exact and near-duplicates. Preserve raw data, but define a primary analysis set that prevents repeated chart versions/overlays from silently inflating prevalence.
6. Publish inclusion/exclusion decisions and a corpus flow diagram.

Do not mix researcher-created overlays into primary upstream-default prevalence. Analyze them separately as controlled scenarios.

## 4. Rule applicability and outcome labels

Each rule × eligible configuration bundle receives one of four labels. A bundle is eligible for a rule only when it contains at least one workload/resource to which that rule applies:

- **PRESENT (finding present):** all predeclared evidence conditions for the rule are met.
- **ABSENT (no finding):** the rule is applicable and the configuration provides sufficient evidence that the weakness is absent.
- **U (uncertain):** static artifacts do not provide enough context to decide reliably.
- **NA (not applicable):** the rule does not apply to this resource/workload/source type.

These labels describe a rule's assessment of a configuration, not scanner performance against independent ground truth. Do not call a scanner finding a true positive unless an independently adjudicated reference label supports it.

For scanner evaluation, compare automated output to independent reference labels and report TP/FP/FN/TN using conventional classifier definitions: a scanner candidate on a PRESENT unit is a TP, a candidate on an ABSENT unit is an FP, no candidate on a PRESENT unit is an FN, and no candidate on an ABSENT unit is a TN. Keep U and NA out of the binary confusion matrix, report their counts, and run sensitivity bounds where appropriate.

## 5. Rule-specific evidence requirements

Every rule needs a machine-readable specification containing:
- rule ID, title, category, severity, and rationale;
- eligible resource kinds and source types;
- positive and negative evidence predicates;
- explicit uncertainty and NA conditions;
- known limitations and required context;
- at least one positive and one negative fixture;
- rule owner/reviewer and version.

Important guardrails:
- Missing NetworkPolicy in a chart does not prove cluster-wide reachability or exposure; describe absence of a policy in the sampled artifact, not proof of exploitability.
- LoadBalancer or NodePort is an exposure indicator, not proof that the endpoint is internet-accessible or unauthenticated.
- Static YAML cannot establish that an API key is valid or enforced on every route unless relevant gateway/application configuration is present and verifiable.
- Sibling-route auth coverage (AUTH-02) and CORS/middleware behavior (AUTH-04) require included route or application configuration for a determinate decision; do not infer either from missing manifest fields (guide v0.3).
- Absence of an endpoint enable flag (AUTH-03) does not establish the endpoint is disabled; determinate decisions need an explicit flag, a documented version-specific default, or configuration that definitively establishes the endpoint surface.
- SEC-03 claims are limited to **in-bundle RBAC evidence**: whether the bundle itself binds a workload ServiceAccount to broad permissions. A ServiceAccount's effective cluster permissions cannot be established from a bundle and are outside the study's claims.
- A declared Service port (NET-04), including on a ClusterIP Service, does not by itself establish exposure of distributed/KV-transfer control ports beyond the serving system's own trust boundary (its router/engine/KV peers within the deployment); PRESENT requires included evidence of reachability beyond that boundary, ABSENT requires the ports to be demonstrably absent or explicitly isolated.
- GPU co-tenancy and isolation (GPU-02) cannot be inferred from static YAML in either direction; determinate labels require runtime/node evidence.
- **RES-02 decided (2026-11-06, author decision, recorded before the full 105-bundle review):** the production-intent test is replaced by a predeclared observable predicate (guide v0.4). A bundle is in scope when an inference workload is configured with replicas > 1 or with autoscaling (an included HPA; controller autoscaling fields permitting more than one replica, e.g. `minReplicas` < `maxReplicas` or `enableInTreeAutoscaling: true`; or a Knative Service, autoscaled by construction). PRESENT = an in-scope workload with no matching PodDisruptionBudget in the bundle; ABSENT = an included PDB whose selector matches the workload's pods; NA = no in-scope workload (all workloads single static replicas, or no workload in the bundle, e.g. config/template fragments); U = the workload's scaling configuration cannot be determined from the bundle. The construct changes accordingly — scaled workloads lacking a PDB, not production intent — and must be reported in those terms.
- Missing GPU resource declarations do not prove CPU fallback, GPU theft, or scheduler overcommit.
- Lack of MIG/HAMi declarations does not prove multi-tenant co-location or absence of hardware isolation.
- Missing PDB/probes/securityContext fields are configuration observations; operational impact requires runtime or workload-specific evidence.
- Do not infer a plaintext secret from placeholder strings. Never publish actual secret-like values.
- A latest tag and a tag without digest are separate policy decisions; document the exact predicate.
- Account for pod-level and container-level securityContext inheritance and precedence.

If a rule's intended claim cannot be tested from available artifacts, downgrade it to an explicitly static proxy or move it to runtime/future work. Do not overstate what the scanner establishes.

## 5A. Current scanner coverage (implementation status)

The current conservative candidate scanner emits candidates for 13 rule IDs: LLM-NET-01, LLM-NET-03, LLM-NET-05, LLM-SEC-02, LLM-GPU-01, LLM-GPU-03, LLM-WL-01, LLM-WL-02, LLM-WL-03, LLM-WL-04, LLM-WL-05, LLM-RES-01, and LLM-RES-03. The remaining 15 rules are not yet automatically assessed by this script and require rule-specific manual evidence review or future tested extractors.

The scanner intentionally emits candidates rather than TP/FP labels. It uses container/resource identity heuristics and can still miss or misclassify workloads. Candidate counts must not be presented as rule prevalence, scanner precision, or recall. The rule catalog's automation field is the authoritative coverage declaration for each rule version.

## 6. Human reference labeling

Create a written labeling guide with rule-specific examples. Sample independently at workload/bundle level using a reproducible random seed and stratification across rule categories and source types.

- Two human reviewers independently label the same blinded sample before discussion.
- Reviewers must not see scanner output or AI-generated pre-labels during the independent pass.
- Record evidence paths and concise rationale for each label.
- Adjudicate disagreements only after independent labels are locked.
- Report raw agreement, class-wise agreement, and an appropriate chance-corrected statistic with confidence intervals.
- Do not treat author adjudication of AI pre-labels as independent second-rater validation.
- Keep an audit trail of label changes and reasons.

If feasible, independently label all high-severity candidate findings and a representative sample of non-findings. Publish sampling weights and use them in population estimates.

## 7. Outcomes and denominators

Report:
- eligible units per rule;
- PRESENT, ABSENT, U, and NA counts;
- finding prevalence among assessable applicable units: PRESENT / (PRESENT + ABSENT);
- uncertainty rate: U / (PRESENT + ABSENT + U);
- applicability rate: (PRESENT + ABSENT + U) / all sampled units;
- source-weighted and unweighted estimates, clearly distinguished;
- per-stack and per-source-type estimates;
- confidence intervals accounting for clustering by upstream source/project.

Do not use total YAML documents or the resource-level review inventory as denominators for bundle-level prevalence. Within a bundle, aggregate a rule as present if at least one in-scope workload/resource has the predeclared positive evidence; label U when the bundle does not provide enough context to assess the rule across its relevant workload surface. Record resource-level evidence paths and workload identities so readers can inspect the aggregation. Avoid counting multiple resources from one bundle as independent samples. Explain how multiple workloads in one rendered bundle are identified.

For scanner benchmarking, report precision, recall, specificity, F1, and coverage only where reference labels and denominator support them. Include confidence intervals and per-rule results; pooled scores must not conceal poor performance on individual rules.

## 8. Statistical plan

This is a descriptive empirical study. Predefine primary unit, eligibility rules, deduplication strategy, sampling design, and primary outcomes before final prevalence inspection.

Use cluster-aware bootstrap resampling at upstream project/source level when estimating uncertainty. If independent clusters are few, report that limitation and avoid overconfident intervals. For stratified human-label samples, apply sampling weights when estimating population metrics.

Separate exploratory comparisons from confirmatory claims. Report effect sizes and intervals, not only p-values. Do not claim causality from cross-sectional public configuration samples.

## 9. Validity threats

- **Selection bias:** public charts and tutorials do not represent all private production deployments.
- **Tutorial bias:** intentionally permissive examples must not be described as production defaults.
- **Version bias:** pinned snapshots age; report collection date and avoid current-default claims without refresh.
- **Static-analysis limits:** YAML does not reveal all gateway, cloud firewall, runtime, admission, or application controls.
- **Dependence:** versions, overlays, and resources from one project are correlated.
- **Construct validity:** several rules are risk proxies rather than proof of exploitability.
- **Label validity:** ambiguous rules require uncertainty labels and independent review.
- **Researcher bias:** authors designed the rule catalog; independent review and preregistered decision rules reduce but do not eliminate it.

## 10. Release gates

Do not publish prevalence claims until:
- [ ] lockfile and bundle count reconcile;
- [ ] all included bundles are reproducibly parsed;
- [ ] rule predicates and fixtures are versioned;
- [ ] static proxies are distinguished from security guarantees;
- [ ] a blinded independent reference-label sample is completed;
- [ ] agreement and adjudication are reported transparently;
- [ ] denominators, weights, and clustering are documented;
- [ ] primary results regenerate from scripts;
- [ ] limitations and deviations are included in the manuscript.

## 11. Planned outputs

- rules/catalog.yaml: machine-readable rule definitions.
- rules/fixtures/: positive, negative, and uncertainty fixtures.
- scripts/scan.py: deterministic scanner with structured evidence.
- results/raw_findings.jsonl: one record per rule × unit assessment.
- results/summary.csv: aggregated counts and denominators.
- results/figures/: reproducible plots.
- docs/labeling-guide.md: human reference-label protocol.
- docs/deviations.md: timestamped protocol changes.

No numerical findings should be added until generated from the frozen pipeline.
