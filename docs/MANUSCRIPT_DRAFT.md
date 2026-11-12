# Security-Relevant Configuration Patterns in Public Kubernetes-Based LLM Inference Stacks: A Reproducible Empirical Study

**Manuscript status:** Working draft v0.1 — 11 November 2026  
**Target genre:** Empirical software engineering / systems security  
**Study repository:** https://github.com/mallyagirish/llm-serving-k8s-hardening-study  
**Analysis branch:** `research/phase3-empirical-evaluation`

> **Drafting and evidence note.** This manuscript is a first full-text draft assembled from the current repository artifacts. It is not submission-ready. Bracketed notes marked **[AUTHOR ACTION]** identify decisions or evidence that must be completed or independently checked before submission. Numerical results below are tied to the current frozen artifacts and CI analysis. Do not silently update them if the corpus, labels, or scanner changes.

## Abstract

Kubernetes has become a common deployment substrate for large language model (LLM) inference, where serving systems combine model-serving containers with gateways, distributed execution components, GPU resources, model caches, and supporting Kubernetes resources. Security guidance for these systems spans both generic workload hardening and inference-specific concerns, but the extent to which such controls are represented in publicly published deployment configurations is not well characterized. We present a reproducible empirical study of security-relevant configuration patterns in public Kubernetes-based LLM inference artifacts.

We assembled a pinned corpus of 202 rendered or collected configuration bundles from 27 source entries and identified 105 primary bundles containing in-scope LLM inference workloads. These bundles represent 10 upstream project clusters. We defined 28 rules across authentication, networking, secrets and RBAC, GPU isolation, workload hardening, model storage, resource management, and observability. Each primary bundle was assessed against each rule, yielding 2,940 bundle–rule labels with four outcomes: PRESENT, ABSENT, uncertain (U), and not applicable (NA). Initial classifications were AI-assisted; the study author subsequently human-validated all entries. We therefore describe the labels as an AI-assisted, author-validated reference set, not as independently double-annotated ground truth.

The frozen reference set contains 647 PRESENT, 738 ABSENT, 697 U, and 858 NA labels. Uncertainty is 23.71% of all labels and 33.48% of non-NA labels. Three authentication rules were non-estimable from static artifacts for nearly all bundles. For example, all 80 assessable bundles for the NetworkPolicy rule lacked an included policy selecting the inference workload, while all 22 assessable scaled bundles for the PodDisruptionBudget rule lacked a matching PDB under the study predicate. These observations describe the sampled public artifacts, not deployed production clusters.

A conservative scanner implemented 13 of the 28 rules. Against the pre-adjudication author-validated labels, it produced 487 true positives, one false positive, three false negatives, and 498 true negatives across 989 assessable bundle–rule units (precision 99.80%, recall 99.39%, and F1 99.59%). A project-cluster bootstrap yielded exploratory 95% percentile intervals of 99.54–100.00% for precision, 98.63–100.00% for recall, and 99.09–100.00% for F1. All four disagreements were concentrated in one project cluster, and only 10 clusters were available. A post-adjudication 100% score is reported only as a sensitivity analysis because the four disputed rows were selected by scanner disagreement and reviewed with scanner predictions visible.

The study contributes a pinned LLM-inference configuration corpus, an evidence-oriented 28-rule assessment framework, and a reproducible characterization that makes applicability and uncertainty explicit. The results should be interpreted as properties of a selected public configuration corpus, not as estimates of production deployment security or proof of exploitability.

**Keywords:** Kubernetes; LLM inference; configuration security; Helm; empirical study; static analysis; GPU serving; security misconfiguration

---

## 1. Introduction

Large language models are increasingly served through self-hosted inference systems deployed on Kubernetes. A typical deployment is not a single container: it may include an inference engine, an API gateway, a scheduler or router, distributed execution components, model-download jobs, persistent model caches, GPU device plugins, Services, Ingress resources, and policy objects. Security therefore depends on the composition of application-level behavior and infrastructure configuration. An inference API may have authentication enabled on one route but not another; a GPU-serving pod may be reachable through a Service whose exposure is determined elsewhere; and a writable model cache may introduce trust assumptions that are not visible from the inference container alone.

Prior research has established that security risks exist across the LLM software and deployment stack. LENS measures and probes publicly reachable self-hosted LLM services, focusing on deployed endpoints and exploit chains [1]. A second internet-scale measurement catalogs 320,102 public-facing LLM services across 15 frameworks and likewise documents widespread unauthenticated access at deployed endpoints [10]. Other studies analyze vulnerabilities in LLM-powered applications and local inference frameworks [2], as well as cross-layer weaknesses in inference frameworks that process untrusted model artifacts [3]. Work on GPU information-flow tracking further demonstrates that user-data isolation in LLM serving is a distinct systems problem [4]. The vLLM security guidance also documents path-specific API-key coverage, internal distributed-communication trust boundaries, cache-directory assumptions, and the Ray cluster trust model [9]. These studies motivate careful analysis of inference infrastructure, but they do not answer a narrower configuration question: what security-relevant controls and potentially weak patterns are visible in the public Kubernetes artifacts used to describe LLM inference deployments?

General Kubernetes and Helm configuration studies provide a second foundation. The canonical manifest study, Rahman et al., characterizes security misconfigurations across 2,039 open-source Kubernetes manifests [11], and Zhang et al. find that eight widely used static analyzers reach average precision and recall at or below 0.28 against human-labeled Kubernetes configuration defects [12]. Shamim et al. examine community-prescribed Kubernetes security configurations and the behavior of static analysis tools [5]. Minna et al. analyze security misconfigurations in Helm charts and evaluate LLM-generated remediation, finding that fixes may be incomplete or may break unrelated configuration [6]. Recent work also studies Kubernetes misconfiguration taxonomies and LLM-assisted repair [7], while LLMSecConfig explores context-grounded repair of container-orchestrator configurations [8]. This literature means that neither generic Kubernetes hardening surveys nor generic Helm misconfiguration detection can serve as the novelty claim for the present work.

We instead study a domain-specific layer: public Kubernetes and Helm artifacts associated with LLM inference serving. The distinction matters. A manifest can reveal a declared Service type, pod security context, container image reference, resource request, or NetworkPolicy selector. It generally cannot establish whether an API route is actually protected by application middleware, whether an external gateway supplies authentication, whether a cloud firewall blocks traffic, whether GPU tenants are co-located, or whether a model cache is writable by an attacker at runtime. We therefore separate directly evidenced configuration properties from claims that require deployment, runtime, or application context.

This paper reports a reproducible empirical study of a pinned public corpus. We define 28 rules across eight categories, select primary bundles that contain in-scope inference workloads, and assess each bundle–rule pair using four outcomes: PRESENT, ABSENT, U, and NA. The four-valued scheme is intentional. Treating every missing field as a confirmed weakness would conflate absence of evidence with evidence of absence, and would turn static configuration analysis into unsupported claims about operational security.

We also implement a conservative scanner for 13 rules and compare its bundle-level predictions against the author-validated reference labels. Because the labels were initially generated with AI assistance and then validated by one author, the evaluation is explicitly a comparison against an **AI-assisted, author-validated reference set**. It is not a comparison against independent double annotation. Four scanner disagreements were subsequently adjudicated with scanner predictions visible; those decisions are retained as a separate sensitivity analysis rather than used to improve the primary scanner score.

The study addresses the following research questions:

- **RQ1 — Configuration patterns:** What security-relevant configuration patterns are observed across public Kubernetes-based LLM inference bundles, when PRESENT, ABSENT, U, and NA are distinguished?
- **RQ2 — Assessability:** Which classes of LLM-serving security properties can be assessed from static deployment artifacts, and which remain uncertain or not applicable?
- **RQ3 — Project heterogeneity:** How do observed patterns vary across upstream project clusters, and how sensitive are aggregate estimates to project-level concentration?
- **RQ4 — Scanner agreement:** How closely does a conservative static scanner agree with the author-validated reference labels for the subset of rules it implements?

The contributions are:

1. **A pinned public-artifact corpus and explicit inclusion boundary** for Kubernetes-based LLM inference configurations, separating primary inference bundles from supporting platform examples and out-of-scope material.
2. **A 28-rule evidence framework** that records applicability and uncertainty rather than treating every absent YAML field as a confirmed vulnerability.
3. **An empirical characterization** of 2,940 bundle–rule assessments across 105 primary bundles and 10 upstream project clusters.
4. **A reproducible scanner comparison and project-aware sensitivity analysis**, including per-rule confusion counts, cluster-bootstrap intervals, and leave-one-project-out results.
5. **An auditable reference-label provenance record** that discloses AI-assisted initial classifications, author validation of all entries, and the separate scanner-visible adjudication of four disagreements.

We do not claim to measure the security of live clusters, public endpoint exposure, production prevalence, exploitability, or the effectiveness of runtime controls.

## 2. Related Work

### 2.1 Security of self-hosted LLM services and inference frameworks

Liu et al. introduce LENS, a framework for discovering and assessing publicly reachable self-hosted LLM services. Their measurement spans 16 platforms, 71,249 discovered targets, and 307 API endpoints [1]. LENS operates on deployed services and probes endpoint behavior. Our study is complementary: it examines public deployment artifacts before or apart from deployment. A Kubernetes Service declared as LoadBalancer, for example, is a configuration property; it does not by itself prove internet reachability or the absence of upstream network controls. Conversely, a manifest that does not include an authentication configuration cannot establish that application-level authentication is absent.

Gomez-Rangel et al. analyze reported vulnerabilities across LLM-powered applications and local inference frameworks [2]. Sen et al.'s LIMA study focuses on cross-layer vulnerabilities triggered by untrusted model artifacts in local inference frameworks, including model-loading attack surfaces [3]. Shi et al. study GPU information-flow tracking for data isolation in LLM serving [4]. These works establish that inference security spans application, framework, model-artifact, and GPU layers. Our rule catalog focuses on the subset of security-relevant properties that can be assessed, or explicitly marked unassessable, from public Kubernetes configuration artifacts.

Two further results bound what static configuration analysis can claim. Hou et al. provide a second runtime measurement of deployed LLM services — 320,102 public-facing services across 15 frameworks — reinforcing, with LENS, that endpoint exposure is a runtime property our artifact labels do not measure [10]. And runtime work on the serving layer itself shows failure modes no manifest can reveal: fuzzing of vLLM and SGLang surfaces KV-cache isolation failures under concurrency [13], and a page-fault side channel defeats even correctly configured MIG partitioning [14]. Our GPU and cache rules are therefore static indicators, not isolation evidence.

### 2.2 Kubernetes and Helm configuration security

Shamim et al. study community-prescribed Kubernetes security configurations, examining configuration files and static analysis tools [5]. Their work provides a general Kubernetes baseline and highlights limitations in the coverage and accuracy of existing tools. Minna et al. examine 4,961 Helm chart templates using security analyzers and evaluate LLM-generated fixes [6]. They report that remediation quality depends on context and that generated changes can break unrelated configuration. Ghorab et al. study developer-reported Kubernetes misconfigurations and LLM-assisted remediation [7]. Ye et al. introduce LLMSecConfig, combining static analysis, prompting, and retrieval-augmented generation to repair container-orchestrator configuration [8]. The canonical predecessor is Rahman et al.'s study of 2,039 open-source manifests across 92 repositories, which derives 11 misconfiguration categories and the SLI-KUBE linter [11]; Zhang et al. catalog 719 configuration defects and show that general-purpose scanners agree poorly with human-labeled ground truth (average precision and recall ≤ 0.28 across eight tools) [12]. Krieger et al. show that the hardening guidance itself is inconsistent across eight standards and ten scanners [17], which motivates evidence-graded rules rather than deference to any single benchmark; and KubeCap finds capability configuration absent in 74.67% of general Kubernetes projects [15], the background rate for capability-related findings.

These studies rule out broad novelty claims around generic Kubernetes misconfiguration detection, Helm chart scanning, or LLM-based repair. The present work differs in its sampling frame and assessment target: public artifacts specifically associated with LLM inference serving, including serving-specific workload identity and rules involving inference APIs, model/cache paths, GPU resources, and distributed serving components. We treat this distinction as a scope contribution, not proof that no prior work has examined any of these individual controls.

### 2.3 Positioning and research gap

The closest studies operate at different layers: deployed endpoint measurement [1, 10], reported software vulnerabilities [2], model-loading framework vulnerabilities [3], GPU data isolation [4], and general Kubernetes/Helm configuration analysis [5–8, 11, 12]. The closest overlap overall is an industry technical report that renders 15 official AI-serving Helm charts and scores their default security posture [16]; it differs from the present work in corpus construction (15 vendor charts at defaults, vs. 105 pinned bundles with workload-level eligibility and deduplication), in labeling (a binary check matrix, vs. four-valued reference labels), and in evaluation (raw scanner failure counts, vs. scanner agreement measured against reference labels). In the verified literature search completed in November 2026, we did not identify a peer-reviewed study that combines a pinned public corpus of LLM-inference Kubernetes artifacts with explicit workload eligibility, a four-valued evidence scheme, project-clustered prevalence reporting, and a scanner comparison against reference labels.

**[AUTHOR ACTION]** Complete and document the systematic database search (ACM Digital Library, IEEE Xplore, SpringerLink, USENIX, arXiv) with exact queries, dates, result counts, and screening decisions. The November 2026 expansion pass verified every citation and integrated the closest work, but the web interface used does not report database hit counts. Re-check for studies published or made available after that pass.

## 3. Study Design and Method

### 3.1 Study scope and unit of analysis

The study examines public Kubernetes manifests and rendered Helm artifacts associated with LLM inference serving. It does not use employer-private configurations, live cluster telemetry, or active endpoint probing. The primary unit is a **configuration bundle**, defined as a rendered chart/version/values combination or a raw manifest bundle represented in the corpus lockfile. Resources within a bundle provide evidence for assessment; they are not counted as independent observations.

The primary analysis contains 105 bundles selected as in-scope LLM inference configurations. These bundles map to 10 upstream project clusters: KServe (53), vLLM Production Stack (30), Ollama (6), infracloud charts (4), KubeRay (4), BerriAI LiteLLM (2), Project-HAMi (2), SGLang (2), OPEA TGI (1), and shalb charts (1). KServe and vLLM Production Stack therefore contribute 83/105 primary bundles (79%). The full Phase 2 lockfile records 202 collected or rendered bundles from 27 source entries. Of the 202 inputs, 195 parse as standalone YAML and seven are documented non-standalone or invalid inputs. The 105 primary bundles are a selected subset; supporting platform examples, generic operators, schedulers, GPU-sharing examples without an in-scope inference workload, and other non-primary artifacts are not included in the primary 105-bundle analysis.

The corpus includes artifacts associated with vLLM, KServe, KubeRay/Ray Serve, TGI, Ollama, SGLang, LiteLLM, and related serving infrastructure. The corpus snapshot was collected on 28 October 2026 and is pinned in `corpus/SOURCES.lock.json`.

**[AUTHOR ACTION]** Add a reproducible corpus-flow figure showing 202 collected inputs, parseability exceptions, primary/supporting/excluded strata, and the final 105 primary bundles. Verify every stratum count against the committed eligibility artifact and explain any source entries that contributed no primary bundles.

### 3.2 Rule catalog

We defined 28 rules in eight categories:

| Category | Rule IDs | Example properties |
|---|---|---|
| Authentication | AUTH-01–05 | API-key protection, sibling-route coverage, development/admin endpoints, CORS/auth middleware, Ingress authentication |
| Network | NET-01–05 | Service exposure type, NetworkPolicy selection, TLS evidence, distributed/Ray/KV-transfer ports, host networking |
| Secrets and RBAC | SEC-01–03 | Secret-like literals, token environment variables, ServiceAccount permissions |
| GPU and isolation | GPU-01–03 | GPU resource declarations, evidence of multi-tenant isolation, privileged/device access |
| Workload security | WL-01–05 | Non-root execution, read-only root filesystem, privilege escalation, seccomp/AppArmor, immutable image references |
| Storage and model | STOR-01–03 | Model/cache sharing, untrusted writable cache paths, privileged model-download init containers |
| Resources | RES-01–03 | CPU/memory requests and limits, PodDisruptionBudget, readiness/startup probes |
| Observability | OBS-01 | Metrics/dashboard exposure and authentication evidence |

Rule definitions, severity, assessment semantics, and automation coverage are versioned in `rules/catalog.json` and `docs/LABELING_GUIDE.md`. The scanner implements candidate generation for 13 of the 28 rules. The other 15 require manual review or future tested extractors. Rules were designed as configuration assessment criteria, not as a complete model of runtime exploitability.

### 3.3 Four-valued assessment labels

Each bundle–rule pair receives one of four labels:

- **PRESENT:** the predeclared evidence conditions for the rule are met in an in-scope resource or workload.
- **ABSENT:** the rule is applicable and the available configuration provides sufficient evidence that the defined weakness is absent.
- **U (uncertain):** static artifacts do not provide enough context to decide reliably.
- **NA (not applicable):** the rule does not apply to the bundle's in-scope workload or resource context.

PRESENT and ABSENT are used for binary prevalence denominators. U is not converted to ABSENT, and NA is not treated as an uncertain applicable case. For rule prevalence, the denominator is PRESENT + ABSENT. The uncertainty rate is U/(PRESENT + ABSENT + U). All four counts are reported to preserve the difference between lack of evidence and non-applicability.

The assessment unit is the bundle–rule pair. Where a bundle contains multiple in-scope serving workloads or templates, the bundle aggregation rule is applied as documented in the labeling guide. Evidence paths and workload identity are retained in the source artifacts where available.

### 3.4 Reference-label provenance and validation

Initial bundle–rule classifications were generated with AI assistance. The study author then human-validated all 2,940 entries (105 bundles × 28 rules) against the source artifacts and the labeling guide. We therefore call the resulting set **AI-assisted, author-validated reference labels**. This was a single-author validation process; it was not independent double annotation, and no human–human inter-rater reliability statistic is claimed.

The original AI-assisted file, `reviewer_AI1_full.csv`, is preserved. A separate frozen file, `reference_labels_author_validated_v1.csv`, records four later adjudications arising from scanner/reference disagreements. The four decisions and their evidence and rationales are recorded in `author_adjudication_history.csv`. These four rows were selected because they disagreed with scanner predictions, and the scanner predictions were visible during author review. Consequently, the post-adjudication comparison is reported only as a sensitivity analysis. The pre-adjudication author-validated labels are used for the primary scanner comparison.

### 3.5 Scanner implementation and evaluation

The conservative scanner (version 2.0.0) extracts serving-container evidence from core Kubernetes workload kinds and selected serving CRDs, including LLMInferenceService, LLMInferenceServiceConfig, ServingRuntime, ClusterServingRuntime, RayService, and Knative Services. It excludes recognized router/scheduler helper templates, init containers, and auxiliary test/migration/cache workloads from workload-hardening checks; credential checks are handled separately. CPU-only and TPU configurations are excluded from the GPU-resource candidate predicate.

Scanner outputs are candidates, not adjudicated findings. Multiple resource-level candidates within one bundle–rule pair are collapsed to one positive prediction. For the 13 implemented rules, candidate presence is compared with the pre-adjudication author-validated reference labels. U and NA rows are excluded from binary confusion matrices and retained in descriptive outputs.

We report TP, FP, FN, TN, precision, recall, specificity, F1, and accuracy where their denominators are defined. Macro-F1 is calculated over the 10 implemented rules with both PRESENT and ABSENT reference examples. Three implemented rules lack both classes and are not included in the macro average. The scanner comparison is a development-stage agreement assessment on one pinned corpus; it is not an independent benchmark against external ground truth.

### 3.6 Statistical analysis and project clustering

The 105 primary bundles map to 10 upstream project clusters. Because bundles from the same upstream project may share templates, conventions, and configuration lineage, bundle-level independence is implausible. We therefore report project-stratified counts and perform a nonparametric project-cluster bootstrap.

For each of 10,000 replicates, we sample 10 upstream projects with replacement and retain all project-level sufficient-statistic counts for each sampled project. The random seed is 20261111. We compute percentile 95% intervals for bundle-weighted prevalence and equal-project-weighted prevalence, as well as pooled and per-rule scanner metrics. The bundle-weighted prevalence estimate pools PRESENT and ABSENT counts across sampled projects; the equal-project estimate averages project-specific prevalence across projects with assessable observations. We also perform leave-one-project-out analysis to expose the influence of individual project clusters.

Only 10 clusters are available. Bootstrap intervals are therefore exploratory and may be unstable; they do not establish that the selected projects are representative of the broader LLM-serving ecosystem. For macro-F1, the set of 10 rules with both reference classes is fixed from the full corpus. A bootstrap replicate is considered non-estimable for macro-F1 if any of those rules loses one of its reference classes in that replicate; it is not silently averaged over a changing set of rules.

### 3.7 Reproducibility

The corpus lockfile pins source revisions and artifact metadata. The scanner, evaluator, cluster-bootstrap script, label files, metadata sidecars, and workflow are version-controlled. CI validates the corpus, executes scanner candidate generation, runs pre- and post-adjudication evaluations, executes both cluster-bootstrap analyses, runs unit tests, and uploads result artifacts. The scanner source hash and evaluator provenance are recorded in the evaluation output. The current successful CI run is linked from the scanner evaluation report.

## 4. Results

### 4.1 Corpus and assessment coverage

The pinned Phase 2 snapshot contains 202 bundles from 27 source entries. After parsing and eligibility review, 105 primary bundles were included in the analysis. These primary bundles represent 10 upstream project clusters. KServe and vLLM Production Stack account for 83 of the 105 bundles (79%), indicating substantial concentration in two project families.

The assessment matrix contains 105 × 28 = 2,940 bundle–rule labels. In the frozen author-validated reference set, 647 labels are PRESENT, 738 ABSENT, 697 U, and 858 NA. U represents 23.71% of all bundle–rule labels. Among non-NA labels, U represents 33.48% (697/(647 + 738 + 697)). These denominators answer different questions and should not be conflated.

### 4.2 Rule-level configuration patterns and assessability

Table 1 reports the frozen four-valued outcomes for all 28 rules. Prevalence is PRESENT/(PRESENT + ABSENT); a dash denotes a non-estimable rule with no assessable binary observations.

**Table 1. Rule-level outcomes in the frozen 105-bundle reference set**

| Rule | PRESENT | ABSENT | U | NA | Assessable | Prevalence |
|---|---:|---:|---:|---:|---:|---:|
| AUTH-01 | 51 | 3 | 45 | 6 | 54 | 94.4% |
| AUTH-02 | 0 | 0 | 99 | 6 | 0 | — |
| AUTH-03 | 0 | 0 | 99 | 6 | 0 | — |
| AUTH-04 | 0 | 0 | 99 | 6 | 0 | — |
| AUTH-05 | 1 | 0 | 0 | 104 | 1 | 100.0% |
| GPU-01 | 0 | 57 | 30 | 18 | 57 | 0.0% |
| GPU-02 | 0 | 0 | 67 | 38 | 0 | — |
| GPU-03 | 2 | 88 | 0 | 15 | 90 | 2.2% |
| NET-01 | 2 | 44 | 33 | 26 | 46 | 4.3% |
| NET-02 | 80 | 0 | 0 | 25 | 80 | 100.0% |
| NET-03 | 0 | 1 | 0 | 104 | 1 | 0.0% |
| NET-04 | 1 | 36 | 58 | 10 | 37 | 2.7% |
| NET-05 | 2 | 90 | 0 | 13 | 92 | 2.2% |
| OBS-01 | 2 | 47 | 31 | 25 | 49 | 4.1% |
| RES-01 | 51 | 27 | 14 | 13 | 78 | 65.4% |
| RES-02 | 22 | 0 | 0 | 83 | 22 | 100.0% |
| RES-03 | 27 | 56 | 7 | 15 | 83 | 32.5% |
| SEC-01 | 0 | 105 | 0 | 0 | 105 | 0.0% |
| SEC-02 | 2 | 97 | 0 | 6 | 99 | 2.0% |
| SEC-03 | 0 | 30 | 50 | 25 | 30 | 0.0% |
| STOR-01 | 0 | 0 | 30 | 75 | 0 | — |
| STOR-02 | 2 | 15 | 20 | 68 | 17 | 11.8% |
| STOR-03 | 0 | 2 | 0 | 103 | 2 | 0.0% |
| WL-01 | 77 | 13 | 0 | 15 | 90 | 85.6% |
| WL-02 | 88 | 2 | 0 | 15 | 90 | 97.8% |
| WL-03 | 77 | 13 | 0 | 15 | 90 | 85.6% |
| WL-04 | 78 | 12 | 0 | 15 | 90 | 86.7% |
| WL-05 | 82 | 0 | 15 | 8 | 82 | 100.0% |

The authentication results for AUTH-02, AUTH-03, and AUTH-04 are non-estimable, not zero-prevalence results. Static Kubernetes artifacts generally do not reveal the full route-level behavior of application middleware or external gateways. The 99 U and six NA outcomes for each rule should therefore not be interpreted as evidence that authentication controls are absent. AUTH-01 is assessable in 54 bundles; 51 were PRESENT and three ABSENT, while 45 were uncertain and six not applicable.

For NET-02, all 80 applicable bundles were labeled PRESENT because no included NetworkPolicy selected the in-scope inference workload. This is a statement about the policies included in the sampled bundle. It does not prove that the deployed workload is reachable from untrusted networks or that external network controls are absent.

For RES-02, all 22 assessable scaled bundles lacked a matching PodDisruptionBudget under the study predicate. The scaling definition was resolved during review (guide v0.5): Ray Serve application-level autoscaling declared in serveConfigV2 counts as autoscaling for the workload, which moved one KubeRay bundle from NA to PRESENT; see §5.3.

For workload-security rules WL-01 through WL-04, PRESENT counts are high among assessable bundles (77–88 of 90). WL-05 has 82 PRESENT and 15 U labels, with eight NA; no ABSENT labels were recorded under the current immutable-image predicate. These are observations about declared configuration, not direct measurements of exploitability or runtime enforcement.

For SEC-01, no in-scope secret-like literal was identified in this reference pass. This result does not establish that credentials are managed securely in deployment systems, external secret stores, runtime environment variables, or repositories outside the sampled artifacts. Several storage, RBAC, authentication, and distributed-network rules have substantial U or NA counts, illustrating that static artifact availability constrains what can be concluded.


### 4.3 Scanner agreement against the primary reference labels

The scanner implements 13 of the 28 rules. Across 989 assessable bundle–rule units, the primary pre-adjudication comparison produced 487 TP, one FP, three FN, and 498 TN.

**Table 2. Primary scanner comparison**

| Metric | Result |
|---|---:|
| True positives | 487 |
| False positives | 1 |
| False negatives | 3 |
| True negatives | 498 |
| Precision | 99.80% |
| Recall | 99.39% |
| Specificity | 99.80% |
| F1 | 99.59% |
| Accuracy | 99.60% |
| Macro-F1 (10 rules with both classes) | 99.53% |

The high pooled agreement must be interpreted in light of the selected corpus, limited implemented-rule coverage, and class distributions. Several rules have only two positive reference examples; one implemented rule has no positive examples, and another has only one negative example. The aggregate score therefore does not establish uniformly strong performance across all rule types.

The per-rule confusion counts further show uneven evidence support. LLM-RES-01 produced 51 TP, zero FP, one FN, and 26 TN. LLM-RES-03 produced 26 TP, one FP, one FN, and 55 TN. LLM-WL-01 produced 77 TP and 13 TN; LLM-WL-02 produced 88 TP and two TN. Several other rules had very small positive or negative classes, limiting meaningful interpretation of rule-specific recall or specificity.

The four scanner disagreements were reviewed separately against source manifests and the labeling guide. The author changed two PRESENT labels to ABSENT, one PRESENT label to U, and one ABSENT label to PRESENT. Because the disagreement queue was selected using scanner disagreement and the scanner predictions were visible during review, the resulting post-adjudication comparison (488 TP, zero FP, zero FN, 500 TN) is a sensitivity analysis only. It is not an independent scanner accuracy estimate and is not used as the primary result.

### 4.4 Project-cluster uncertainty and project influence

The project-cluster bootstrap produced the following exploratory 95% percentile intervals for the primary scanner comparison.

**Table 3. Project-cluster bootstrap intervals for pooled scanner metrics**

| Metric | Point estimate | 95% project-bootstrap interval |
|---|---:|---:|
| Precision | 99.80% | 99.54–100.00% |
| Recall | 99.39% | 98.63–100.00% |
| Specificity | 99.80% | 99.60–100.00% |
| F1 | 99.59% | 99.09–100.00% |
| Accuracy | 99.60% | 99.15–100.00% |
| Macro-F1 | 99.53% | 99.07–100.00% |

The macro-F1 interval is estimable in 3,526 of 10,000 replicates in which all 10 fixed macro-F1 rules retain both reference classes. Replicates that lose a required class are treated as non-estimable rather than averaging over a changing rule set.

The leave-one-project-out analysis exposes material concentration. Omitting vLLM Production Stack yields the lowest pooled accuracy (99.37%), while omitting KServe yields 100.00%. Precision ranges from 99.67% to 100.00%, recall from 99.03% to 100.00%, and macro-F1 from 99.40% to 100.00%. All four primary scanner disagreements occur in the KServe project cluster. Thus, omitting KServe removes all four observed errors. This concentration is a limitation of the evidence base and should not be presented as proof of general scanner performance.

Project weighting also changes prevalence estimates. These bootstrap prevalence estimates use the pre-adjudication author-validated matrix, consistent with the primary scanner comparison; they therefore need not equal the final frozen counts in Table 1 after the four scanner-visible adjudications. For LLM-RES-01, bundle-weighted prevalence is 66.7% (95% interval 30.1–98.0%), while equal-project weighting gives 74.4% (53.3–95.0%). For LLM-RES-03, the corresponding estimates are 32.5% (0–63.0%) and 24.4% (0–50.8%). For LLM-WL-01, they are 85.6% (72.0–100.0%) and 86.8% (66.8–100.0%). These differences show that a bundle-weighted summary can be influenced by projects that contribute many similar bundles.

NET-02 is PRESENT in all 80 assessable bundles and in all 10 project clusters. Its degenerate 100–100% bootstrap interval reflects the observed pattern in this selected corpus; it is not evidence of certainty about other projects. Rules without assessable project observations, including AUTH-02/03/04, remain non-estimable and receive no interval.

## 5. Discussion

### 5.1 Static configuration is informative, but only within a defined evidence boundary

The results show that public Kubernetes artifacts can support reproducible assessment of some properties, such as declared workload security contexts, container resource settings, Service types, and NetworkPolicy selectors. They also show that important inference-security properties are often not established by static YAML. Authentication behavior is a central example: a Kubernetes bundle may include an inference container and a Service but omit application middleware, gateway policy, or external identity configuration. In such cases, U is more defensible than inferring a missing control.

This distinction is central to the study's contribution. A binary scanner that maps every missing field to a finding can overstate security weaknesses. Conversely, a static artifact that contains no obvious secret literal does not establish that the deployed system has no credential-management issue. The four-valued assessment scheme makes these evidence boundaries visible.

### 5.2 NetworkPolicy findings should not be read as internet exposure

The NET-02 result indicates that no included NetworkPolicy selected the in-scope inference workload in the 80 assessable bundles. This may represent an opportunity for defense-in-depth, but it does not establish that traffic is unrestricted. Kubernetes network reachability depends on the cluster's network plugin, namespace policies, cloud network controls, gateway architecture, and deployment-time resources that may not be included in a public chart or manifest bundle. The paper therefore reports the observed selector relationship, not an assertion of public exposure or exploitability.

### 5.3 Availability controls and the RES-02 definition

The RES-02 finding is operationally relevant but definition-sensitive. A PodDisruptionBudget is a Kubernetes-level availability control; application-level scaling in Ray Serve does not necessarily imply a Kubernetes disruption budget is required or semantically equivalent, because the framework manages its own replica placement. The Ray Serve example identified during review demonstrates that scaling can be declared at different layers. We resolved the definition in favor of the declared configuration (guide v0.5, decided 2026-11-11): autoscaling declared in a RayService serveConfigV2 counts as scaling for the workload, on the same footing as controller autoscaling fields, so the rule measures "scaled workload without an included PDB" at whichever layer the scaling is declared. Under this definition the result is 22/22. The residual caveat is construct-level, not definitional: for framework-managed replicas, an included PDB may not be the mechanism a practitioner would actually choose, so the label records the configuration pattern the rule operationalizes, not a proven availability gap.

### 5.4 Scanner agreement is a development result, not external validation

The scanner's high agreement is encouraging for the 13 implemented rules on the pinned corpus, but several caveats are material. First, the reference labels are AI-assisted and author-validated by one person, not independent double annotation. Second, the evaluation corpus was used during scanner development, so this is not a held-out test set. Third, the four post-adjudication changes were selected by disagreement with the scanner and reviewed with its predictions visible; the resulting 100% score is potentially optimistic. Fourth, the error concentration in KServe shows that pooled metrics can hide project-specific failure modes. A future evaluation should add an independently selected holdout corpus and independent human review of a stratified sample, with scanner predictions blinded during annotation.

### 5.5 Implications for practitioners

The findings suggest several practical lessons, subject to the artifact-level scope:

- Treat inference-serving workloads as a distinct workload class during Kubernetes security review. Generic chart scans may not identify router, scheduler, model-cache, or serving-specific resource relationships.
- Evaluate NetworkPolicy selectors against the actual inference pod labels rather than merely checking whether any NetworkPolicy object exists in a bundle.
- Separate application-level authentication evidence from Kubernetes Service and Ingress declarations; static infrastructure artifacts alone may not establish route-level authorization.
- Interpret GPU resource and isolation declarations conservatively. Absence of MIG/HAMi or a vendor resource key does not prove co-location, lack of hardware isolation, or exploitable cross-tenant access.
- Review model/cache volume mounts and model-download init containers in context. A static path match is a triage signal, not proof of attacker-controlled writes or code execution.
- Preserve U and NA outcomes in security reporting. Forcing unknown cases into a binary pass/fail result can produce misleading assurance.

### 5.6 Research implications

The study points to a need for multi-layer validation. Static configuration analysis can identify declared controls and relationships, but authentication, network reachability, GPU isolation, and model-cache trust often require runtime or deployment-context evidence. A natural extension is a controlled validation subset in which a reproducible deployment harness tests selected properties—for example, API route authentication, Service reachability under known network policies, and readiness behavior—while keeping the broader corpus study static and reproducible.

## 6. Threats to Validity

### 6.1 Construct validity

The 28 rules operationalize selected security-relevant properties, but some are proxies for broader claims. A LoadBalancer Service does not prove internet exposure; missing NetworkPolicy selection does not prove unrestricted reachability; absence of GPU isolation declarations does not prove tenant co-location, and declared MIG configuration does not prove that tenant isolation holds [14]; and absence of a PDB may not be meaningful for every application-level scaling design. We mitigate this by using four-valued labels, retaining rule-specific predicates, and avoiding claims of exploitability. For RES-02, the scaling definition was amended during review to include framework-level autoscaling declarations (guide v0.5); the construct caveat for framework-managed replicas is discussed in §5.3.

### 6.2 Internal validity

Initial labels were generated with AI assistance and then human-validated by one author. The validation is not independent double annotation, and the author may have been influenced by initial AI suggestions. In addition, four scanner disagreements were reviewed with scanner predictions visible. We preserve the pre-adjudication comparison as the primary scanner result and report post-adjudication metrics only as sensitivity analysis. Future work should include independent blinded human annotation and a held-out evaluation corpus.

### 6.3 External validity

The corpus consists of public charts, examples, and manifests. It does not represent private enterprise deployments, production clusters, cloud-specific controls, or the complete universe of LLM-serving systems. The primary set contains 105 bundles but only 10 upstream project clusters, with 83 bundles from KServe and vLLM Production Stack. The bootstrap intervals are exploratory and may be unstable with so few clusters. Findings must not be generalized to production prevalence. (That prescribed-configuration violations also occur on live industry deployments, not only in public examples, is documented by Shamim et al.'s industry experience report [18]; our corpus nevertheless measures published artifacts only.)

### 6.4 Reliability and reproducibility

The corpus lockfile, scripts, labels, and CI workflow are version-controlled. However, upstream repositories and chart registries can change, and re-rendering may depend on tool versions or external availability. The pinned revisions and hashes improve reproducibility, but a fully archival release should include all legally redistributable input artifacts or durable source snapshots, exact toolchain versions, and the generated analysis artifacts.

### 6.5 Statistical conclusion validity

The effective number of independent project clusters is 10, not 105. Cluster-bootstrap intervals are sensitive to the observed cluster set and cannot compensate for limited cluster diversity. Some rules have very few positive or negative examples, and some are non-estimable. Pooled scanner metrics are dominated by rules with more assessable observations and should always be read with per-rule counts and project-level sensitivity results.

## 7. Conclusion

We presented an empirical study of security-relevant configuration patterns in public Kubernetes-based LLM inference artifacts. The study combines a pinned corpus, an explicit primary-workload selection process, a 28-rule evidence framework, four-valued bundle–rule labels, and a conservative scanner comparison. Across 105 primary bundles and 10 upstream project clusters, the frozen reference set contains 2,940 assessments, including substantial uncertainty and non-applicability. Several important inference-security properties—especially route-level authentication—cannot be established reliably from static Kubernetes artifacts alone.

The scanner agrees closely with the pre-adjudication author-validated reference labels for its 13 implemented rules on this corpus, but this result is a development-stage comparison rather than external validation. Project-level concentration, limited cluster count, single-author validation, and the absence of a held-out corpus constrain interpretation. The main conclusion is therefore not that public LLM-serving deployments are insecure or secure at a particular rate, but that reproducible assessment requires explicit workload scope, rule-specific evidence, and a disciplined distinction between observed configuration, uncertainty, and runtime security claims.

---

## References

[1] Z. Liu, L. Hu, Y. Tang, T. Zhou, F. Liu, and Z. Cai, “Exploring and Exploiting Security Vulnerabilities in Self-Hosted LLM Services,” in *Proceedings of The Web Conference 2026 (WWW '26)*, pp. 2535–2546, 2026. doi: [10.1145/3774904.3792097](https://doi.org/10.1145/3774904.3792097).

[2] J. Gomez-Rangel, Y. Lee, and B. Liu, “Security in the Wild: An Empirical Analysis of LLM-Powered Applications and Local Inference Frameworks,” in *Proceedings of the 2nd IEEE/ACM International Conference on AI-powered Software (AIware 2025)*, pp. 149–159, 2025. doi: [10.1109/AIware69974.2025.00024](https://doi.org/10.1109/AIware69974.2025.00024).

[3] S. K. Sen, H. Longoria, and B. Liu, “LIMA: Defining, Benchmarking and Detecting Cross-Layer Vulnerabilities in LLM Inference Frameworks,” in *Proceedings of the 20th USENIX WOOT Conference on Offensive Technologies (WOOT '26)*, pp. 287–303, 2026.

[4] J. Shi, X. Wang, C. Tan, and J. Gu, “Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking,” arXiv:2608.25431, 2026. **[AUTHOR ACTION: verify final publication status and full bibliographic metadata.]**

[5] S. I. Shamim, H. Hu, and A. Rahman, “On Prescription or Off Prescription? An Empirical Study of Community-Prescribed Security Configurations for Kubernetes,” in *Proceedings of the 47th IEEE/ACM International Conference on Software Engineering (ICSE 2025)*, pp. 2432–2444, 2025. doi: [10.1109/ICSE55347.2025.00170](https://doi.org/10.1109/ICSE55347.2025.00170).

[6] F. Minna, F. Massacci, and K. Tuma, “Analyzing and mitigating (with LLMs) the security misconfigurations of Helm charts from Artifact Hub,” *Empirical Software Engineering*, vol. 30, article 132, 2025. doi: [10.1007/s10664-025-10688-0](https://doi.org/10.1007/s10664-025-10688-0).

[7] M. A. Ghorab, A. Abdel Latif, and M. A. Saied, “Kubernetes Misconfigurations in the Wild: Taxonomy, Evolution, and Automated Repair with Large Language Models,” in *Proceedings of the 3rd ACM International Conference on AI-Powered Software (AIware 2026)*, 2026. doi: [10.1145/3805760.3814908](https://doi.org/10.1145/3805760.3814908).

[8] Z. Ye, T. H. M. Le, and M. A. Babar, “LLMSecConfig: An LLM-Based Approach for Fixing Software Container Misconfigurations,” in *Proceedings of the 22nd International Conference on Mining Software Repositories (MSR 2025)*, 2025. doi: [10.1109/MSR66628.2025.00099](https://doi.org/10.1109/MSR66628.2025.00099).

[9] vLLM Project, “Security,” *vLLM Documentation*. https://docs.vllm.ai/en/latest/usage/security/. Accessed 11 November 2026. **[AUTHOR ACTION: archive the exact documentation revision used to motivate rules.]**

[10] X. Hou, J. Han, Y. Zhao, and H. Wang, “Unveiling the Landscape of LLM Deployment in the Wild: An Empirical Study,” arXiv:2505.02502, 2025.

[11] A. Rahman, S. I. Shamim, D. B. Bose, and R. Pandita, “Security Misconfigurations in Open Source Kubernetes Manifests: An Empirical Study,” *ACM Transactions on Software Engineering and Methodology*, vol. 32, no. 4, 2023. doi: [10.1145/3579639](https://doi.org/10.1145/3579639).

[12] Y. Zhang, U. Paul, M. d'Amorim, and A. Rahman, “Configuration Defects in Kubernetes,” *IEEE Transactions on Software Engineering*, 2026. doi: [10.1109/TSE.2026.3659785](https://doi.org/10.1109/TSE.2026.3659785).

[13] Y. Zhao, Y. Zhao, Y. Zhang, Z. Liu, and M. L. Mazurek, “Continuous Discovery of Vulnerabilities in LLM Serving Systems with Fuzzing” (GRIEF), arXiv:2605.11202, 2026.

[14] G. Di Santi, A. Di Dio, and C. Giuffrida, “MIGraine: Practical Side-channel Attacks on NVIDIA Multi-Instance GPUs via Page Fault Contention,” preprint, Vrije Universiteit Amsterdam, 2026. **[AUTHOR ACTION: confirm venue/status before submission.]**

[15] Y. Liu, Y. Zhou, W. Liu, Y. Jia, and Z. Liu, “KubeCap: A Framework for Capability Minimization in Kubernetes via Static Analysis and LLM-Assisted Rule Inference,” arXiv:2608.26699, 2026.

[16] Sorami Consulting, “AI on Kubernetes: Default Helm Chart Security and Lateral Movement,” Sorami Technical Report, September 2026. https://sorami.com.au/research/ai-kubernetes-helm-chart-security/

[17] M. Krieger, M. Gierlinger, F. Shaikh, and M. Kahlhofer, “A Comparison of Kubernetes Compliance Standards and Configuration Scanners,” arXiv:2606.24438, 2026.

[18] S. I. Shamim, H. Hu, and A. Rahman, “Dynamic Application Security Testing for Kubernetes Deployment: An Experience Report from Industry,” in *Proceedings of the 33rd ACM International Conference on the Foundations of Software Engineering (FSE '25)*, 2025. doi: [10.1145/3696630.3728573](https://doi.org/10.1145/3696630.3728573).

---

## Submission-blocking author actions

1. **Resolve RES-02.** — **Resolved 2026-11-11.** The author extended the predicate (guide v0.5): Ray Serve application-level autoscaling in serveConfigV2 qualifies as scaling under the PDB rule. One label changed (NA → PRESENT); guide, adjudication history, the v2 frozen set, and all derived results in this draft were updated. See `docs/RES02_RAY_SERVE_DECISION.md`.
2. **Verify corpus flow.** Generate a flow diagram and reconcile all inclusion/exclusion counts against the canonical eligibility CSV and lockfile.
3. **Add source/project tables.** Report the 10 primary project clusters and their bundle counts, plus source-type and serving-stack breakdowns where supported.
4. **Audit prevalence tables.** Generate a complete 28-rule table from the frozen label file, including denominators, U rate, applicability, and project-stratified counts. Table 1 above is illustrative, not a complete result table.
5. **Add artifact availability statement.** Identify exactly which corpus inputs can be redistributed, how to reproduce restricted/unavailable inputs, and the immutable commit/release corresponding to the manuscript.
6. **Independent validation.** — **Closed by author decision, 2026-11-11: no second annotator will be sought for this submission.** The labels are described throughout as AI-assisted and author-validated (single-author validation; no inter-rater reliability claimed). A turnkey second-annotator packet exists in `results/second_rater/` and is retained unused; do not describe independent annotation as having occurred or as planned.
7. **Systematic related-work review.** — **Substantially advanced 2026-11-11:** the expansion pass verified every citation, corrected one factual error, and integrated the nine closest additional works (see `docs/RELATED_WORK_AND_NOVELTY.md` and `docs/LITERATURE_SEARCH_LOG.md`). Remaining: the database searches with recorded hit counts; screening is by the author (no independent screener — see item 6).
8. **Journal/conference formatting.** Select a target venue only after the evidence and novelty positioning are finalized; adapt length, reference style, and artifact-evaluation requirements.
