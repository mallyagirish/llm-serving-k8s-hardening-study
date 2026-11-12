# Related Work and Novelty Positioning

**Status:** Structured scan with a verified expansion pass completed 2026-11-11: every citation below was checked against its publisher/arXiv/Zenodo record, and the closest overlapping work (including industry grey literature) is integrated. This is still not a full systematic database review — §7 records what remains before submission. Search details: `docs/LITERATURE_SEARCH_LOG.md`.

## 1. Directly related LLM-serving security research

### LENS: deployed self-hosted LLM service exposure

Liu et al. (WWW 2026), “Exploring and Exploiting Security Vulnerabilities in Self-Hosted LLM Services,” introduce LENS and evaluate publicly reachable self-hosted LLM deployments across 16 platforms, 71,249 discovered deployment targets, and 307 API endpoints. The authors report widespread unauthenticated API interaction among responsive targets and multiple vulnerability disclosures/CVEs.  
Project page: https://cristliu.github.io/lens/

**Relationship:** LENS is a close and important predecessor for LLM-service authentication and exposure. It studies deployed, network-reachable services and probes their behavior. This repository studies the configuration artifacts (Helm renders and Kubernetes manifests) used to define deployments. These are complementary units of analysis: runtime endpoint behavior versus published deployment configuration. We must not claim to be the first empirical study of self-hosted LLM service security or public exposure.

### LLM deployment in the wild: a second runtime measurement

Hou, Han, Zhao, and Wang (2025), “Unveiling the Landscape of LLM Deployment in the Wild: An Empirical Study,” measure 320,102 public-facing LLM services across 15 frameworks and 158 API endpoints, finding widespread plain-HTTP exposure and endpoints answering unauthenticated requests. arXiv:2505.02502.

**Relationship:** Together with LENS, this closes off any claim about endpoint exposure or unauthenticated-access prevalence in *deployed* services. Our authentication and exposure rules are framed strictly as properties of published configuration artifacts; these two papers are the runtime-side evidence. Neither examines the Kubernetes configuration that produced the deployments, which is our unit of analysis.

### LLM serving isolation and GPU data security

Shi et al. (2026), “Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking,” propose GPU information-flow tracking and evaluate on vLLM and DistServe. The work addresses isolation of user data in shared serving systems and GPU-resident data, rather than Kubernetes manifest prevalence.  
Preprint: https://arxiv.org/abs/2608.25431

**Relationship:** This work motivates why GPU isolation and model-serving trust boundaries matter. It does not validate whether a Kubernetes YAML manifest proves multi-tenant isolation. Our GPU-related rules must therefore be framed as static indicators unless hardware/runtime evidence exists.

Di Santi, Di Dio, and Giuffrida (2026), “MIGraine: Practical Side-channel Attacks on NVIDIA Multi-Instance GPUs via Page Fault Contention,” show a UVM page-fault contention channel that lets a tenant on one MIG instance fingerprint co-located workloads (including vLLM-served LLM workloads) at 96% accuracy, on Ampere and Hopper. 2026 preprint (Vrije Universiteit Amsterdam); venue unconfirmed — cite as preprint.

**Relationship:** GIFT (defensive) and MIGraine (offensive) bracket our GPU rules from both sides: MIG configuration in a manifest is at most an indicator that partitioning was requested. Even correctly configured MIG does not deliver full cross-tenant confidentiality, so a PRESENT label on MIG/profile fields must never be phrased as isolation achieved.

### Fuzzing LLM serving systems

Zhao et al. (2026), “Continuous Discovery of Vulnerabilities in LLM Serving Systems with Fuzzing” (GRIEF), fuzz vLLM and SGLang with timed multi-request traces and find 15 vulnerabilities, including KV-cache isolation failures and cross-request contamination under concurrency. arXiv:2605.11202.

**Relationship:** Some of the most serious serving-layer failures are runtime-emergent and invisible to any manifest analysis. Our cache and multi-tenancy rules are static indicators only; GRIEF is the citation that explains why a clean static label cannot certify serving-layer isolation. Complementary, not competing — it tests engines, not configurations.

### Vulnerabilities in LLM applications and inference frameworks

Gomez-Rangel, Lee, and Liu, “Security in the Wild: An Empirical Analysis of LLM-Powered Applications and Local Inference Frameworks” (IEEE/ACM AIware 2025, pp. 149–159), curates and analyzes 50 publicly disclosed vulnerabilities from GitHub Security Advisories across LLM-powered applications and local inference frameworks. (An earlier draft of this document said 505; the paper's abstract says 50 — corrected 2026-11-11.) A journal extension by the same group: “Rising Fast, Prone to Risk,” *Int. J. of System Assurance Engineering and Management* 20(1):95–134, 2026.  
DOI: https://doi.org/10.1109/AIware69974.2025.00024

**Relationship:** This is software-vulnerability evidence across the LLM stack, not a Kubernetes configuration corpus. It supports the importance of studying infrastructure configuration as a distinct layer.

## 2. Kubernetes and Helm configuration measurement

### The canonical manifest prevalence study, and tool accuracy against ground truth

Rahman, Shamim, Bose, and Pandita (2023), “Security Misconfigurations in Open Source Kubernetes Manifests: An Empirical Study,” *ACM Transactions on Software Engineering and Methodology* 32(4). DOI: https://doi.org/10.1145/3579639

The direct methodological ancestor of this study: 2,039 manifests from 92 open-source repositories, 11 misconfiguration categories, 1,051 misconfigurations, and the SLI-KUBE linter. It rules out any novelty in empirically characterizing security misconfigurations in open-source Kubernetes manifests as such; our contribution must be located in the LLM-serving domain restriction, the eligibility/dedup procedure, and the explicit U/NA treatment, none of which it has. Our rule framework should acknowledge the lineage where categories overlap.

Zhang, Paul, d'Amorim, and Rahman (2026), “Configuration Defects in Kubernetes,” *IEEE Transactions on Software Engineering*. DOI: https://doi.org/10.1109/TSE.2026.3659785 (preprint arXiv:2512.05062)

719 defects from 2,260 configuration scripts in 185 repositories, 15 defect categories, and a systematic evaluation of 8 static analysis tools finding average precision and recall ≤ 0.28. This is the strongest published evidence that general-purpose K8s scanners are inaccurate against human-labeled ground truth, and the natural baseline for our scanner-agreement evaluation. Our evaluation differs in ground-truth construction (per-rule PRESENT/ABSENT/U/NA reference labels on workload-level bundles, restricted to LLM-serving artifacts) and in reporting agreement against those labels — “scanners are inaccurate” is not itself a finding we can present as new.

### Compliance standards vs. configuration scanners

Krieger, Gierlinger, Shaikh, and Kahlhofer (2026), “A Comparison of Kubernetes Compliance Standards and Configuration Scanners,” compare 8 hardening guidelines (CIS, NSA/CISA, STIG, etc.) distilled into a 79-recommendation benchmark and empirically evaluate 10 static configuration scanners, finding substantial disparities in guideline coverage and inconsistent severity scoring. arXiv:2606.24438.

**Relationship:** The guidance corpus itself is inconsistent, which justifies our rule/evidence framing — rules cite their source guidance and record applicability rather than treating any single benchmark as ground truth. Overlap is at the generic-Kubernetes level: no LLM-serving corpus, no per-workload reference labels, no uncertainty labels.

### Capability prevalence (KubeCap)

Liu et al. (2026), “KubeCap: A Framework for Capability Minimization in Kubernetes via Static Analysis and LLM-Assisted Rule Inference,” find across three open-source datasets that 74.67% of projects lack capability configurations and only 19.33% follow the least-privilege pattern. arXiv:2608.26699.

**Relationship:** Missing capability configuration is the norm in general K8s projects, so a high rate on our capability rules is expected background, not an LLM-serving-specific pathology. We compare rates rather than presenting the raw rate as a domain finding.

### Industry deployment experience report

Shamim, Hu, and Rahman (FSE 2025), “Dynamic Application Security Testing for Kubernetes Deployment: An Experience Report from Industry,” find 3,442 violated recommended security configurations on a live industry deployment and evaluate three DAST tools. DOI: https://doi.org/10.1145/3696630.3728573

**Relationship:** A companion to the same group's ICSE 2025 paper, but on a running proprietary deployment rather than mined artifacts. Useful for external validity: prescribed-configuration violations are not an artifact of public example code — while underscoring that our corpus cannot quantify production prevalence. Cite in limitations, not as a competing study.

### AI-serving Helm chart defaults (industry grey literature)

Sorami Consulting (2026), “AI on Kubernetes: Default Helm Chart Security and Lateral Movement,” Sorami Technical Report, 24 September 2026. https://sorami.com.au/research/ai-kubernetes-helm-chart-security/

Renders 15 official Helm charts for AI serving, gateways/UIs, vector databases, and Kubernetes MCP tools with default values; scores 12 security checks per chart (auth defaults, non-root enforcement, ServiceAccount token automount, RBAC breadth, NetworkPolicy presence, etc.); live-probes the 8 charts that start in a kind cluster; compares four scanners; and reports that all scanners completely skip pods declared inside Custom Resources (e.g., KubeRay's RayCluster). It also documents a concrete LiteLLM chart bug (database password in plain-text env vars in the migration Job).

**Relationship:** This is the closest overlap with our study found anywhere, and it is grey literature, not peer-reviewed. Any phrasing implying the first analysis of security defaults in AI/LLM-serving Helm charts, or the first observation that manifest scanners miss pods embedded in Custom Resources, is not available to us. Our distinctions are methodological and must be stated plainly: (i) corpus — 105 pinned bundles from the serving projects' own repositories (charts *and* example/deployment bundles) with workload-level eligibility and deduplication, vs. 15 vendor charts at defaults; (ii) labels — per-rule reference labels with explicit U and NA outcomes, vs. a binary pass/fail matrix; (iii) evaluation — scanner agreement measured against those reference labels, vs. raw scanner failure counts; (iv) scope — LLM inference serving only, vs. a mixed AI stack including vector databases and MCP tooling; (v) threat model — theirs is in-cluster lateral movement with live probing, ours is configuration characterization without runtime claims. Their check families independently validate several of ours, which can be acknowledged.

### Helm chart security and LLM remediation

Minna, Massacci, and Tuma (2025), “Analyzing and mitigating (with LLMs) the security misconfigurations of Helm charts from Artifact Hub,” *Empirical Software Engineering*, 30(5), Article 132. DOI: https://doi.org/10.1007/s10664-025-10688-0

The authors analyze 4,961 Helm chart templates using multiple security analyzers and evaluate LLM-generated fixes. (The 4,961 count is as reported by the paper; it was not independently re-verified against the paper's §4 in our 2026-11-11 citation check.) They report that context affects repair quality and that generated changes can remove unrelated configuration and break applications.

**Relationship:** This rules out novelty claims around generic Helm misconfiguration detection or generic LLM-based Helm repair. Our study's potential distinction is the curated LLM-inference deployment domain and rule-specific treatment of serving surfaces.

### Community-prescribed Kubernetes security configurations

Shamim, Hu, and Rahman (ICSE 2025), “On Prescription or Off Prescription?: An Empirical Study of Community-prescribed Security Configurations for Kubernetes,” pp. 2432–2444. DOI: https://doi.org/10.1109/ICSE55347.2025.00170  
Publication page: https://akondrahman.github.io/publication/icse25

This work studies community Kubernetes security configurations and static analyzer behavior. It is relevant to rule selection, policy interpretation, and analyzer limitations.

### Kubernetes misconfiguration taxonomy and LLM repair

Ghorab, Abdel Latif, and Saied (AIware 2026), “Kubernetes Misconfigurations in the Wild: Taxonomy, Evolution, and Automated Repair with Large Language Models.” DOI: https://doi.org/10.1145/3805760.3814908 ; preprint: https://arxiv.org/abs/2609.27030

The paper analyzes 2,662 Stack Overflow issues, derives a Kubernetes misconfiguration taxonomy, and evaluates contextual LLM remediation with schema-guided validation.

**Relationship:** Generic Kubernetes misconfiguration taxonomy and LLM repair are already covered. Do not position the companion remediation study as the first generic Kubernetes repair benchmark.

### KubeGuard: runtime-informed Kubernetes hardening

Sgan Cohen et al. (2025), “KubeGuard: LLM-Assisted Kubernetes Hardening via Configuration Files and Runtime Logs Analysis.” arXiv:2509.04191. https://arxiv.org/abs/2509.04191

KubeGuard combines Kubernetes manifests with audit, network-flow, and provenance logs to generate/refine Roles, NetworkPolicies, and Deployments. It evaluates generic microservice applications and focuses on runtime-informed least-privilege hardening.

**Relationship:** KubeGuard is adjacent to the companion remediation benchmark and establishes that runtime-informed LLM hardening of Kubernetes resources is already explored. Our remediation study must focus on LLM-serving-specific acceptance oracles rather than claim generic runtime-aware hardening as novel.

## 3. LLM-assisted infrastructure repair

### LLMSecConfig

“LLMSecConfig: An LLM-Based Approach for Fixing Software Container Misconfigurations,” MSR 2025. DOI: https://doi.org/10.1109/MSR66628.2025.00099

The paper combines static analysis and LLMs/RAG for repairing container misconfigurations and reports an evaluation on 1,000 Kubernetes configurations.

**Relationship:** This is another direct predecessor for general LLM-assisted Kubernetes/container repair. The companion remediation benchmark must distinguish itself through LLM-inference-specific serving invariants, not simply by using a different prompt or model.

### Security regressions during iterative IaC repair

Agyekum and Santos (ESEM 2026), “Does Fixing Break Security? An Empirical Study of Security Degradation in Iterative LLM-Driven Infrastructure-as-Code Repair.” Replication package: https://doi.org/10.5281/zenodo.20265184 (the DOI printed in the paper; the camera-ready package also sits at https://zenodo.org/records/21914827)

The replication package describes 5,968 scenario timelines from IaC-Eval across 15 LLM configurations, measuring security regressions during iterative repair.

**Relationship:** Security regression measurement is established. The companion study should test serving/API/model-load invariants in addition to configuration security checks, and should avoid claiming novelty for regression measurement alone.

## 4. Current LLM-serving security guidance

The vLLM security guide documents several serving-specific boundaries, including route-level/API-key limitations, Ray cluster access, process isolation, cache trust, and multi-tenant isolation.  
https://docs.vllm.ai/en/latest/usage/security/

The guide explicitly states that vLLM does not provide tenant isolation between callers sharing one server process and recommends architectural controls such as per-tenant instances and an authenticating gateway. This supports our focus on the deployment architecture around an inference process, but documentation guidance is not empirical evidence of prevalence.

### LIMA: cross-layer vulnerabilities in local inference frameworks

Sen, Longoria, and Liu (WOOT 2026), “LIMA: Defining, Benchmarking and Detecting Cross-Layer Vulnerabilities in LLM Inference Frameworks.” USENIX WOOT '26, pp. 287–303. https://www.usenix.org/conference/woot26/presentation/sen

LIMA curates 60 disclosed vulnerabilities across llama.cpp, vLLM, Ollama, and LocalAI, develops LIMABench/LIMAScan, and reports seven newly discovered vulnerabilities in model-artifact loading paths.

**Relationship:** This is direct evidence that inference engines and model artifacts have serving-specific attack surfaces. It is not a Kubernetes deployment-manifest prevalence study, but it makes model/cache and model-loading rules important and cautions against treating container hardening as the whole security story.

## 5. Defensible contribution for this study

The defensible candidate contribution is:

1. A pinned, auditable corpus of public Kubernetes/Helm artifacts specifically associated with LLM inference serving.
2. A rule/evidence framework that distinguishes direct YAML observations from context-dependent security claims.
3. A source- and workload-level eligibility and deduplication procedure that separates inference workloads from generic ML examples, operators, GPU schedulers, and tutorial fragments.
4. A reproducible characterization of security-relevant configuration patterns in public LLM-serving artifacts, with uncertainty and applicability reported rather than treating every missing field as a confirmed vulnerability.
5. Optionally, a controlled runtime validation substudy for a small subset of rules (e.g., API route authentication, Service/network reachability, and readiness), if the lab oracles can be made reproducible.

This is a candidate contribution, not yet a novelty conclusion. LENS is especially important: our paper must clearly say it studies published Kubernetes configuration artifacts, not the security of deployed public LLM endpoints.

**Post-expansion status (2026-11-11):** After the verified expansion pass, no peer-reviewed, configuration-level, LLM-serving-specific prevalence study with reference labels was found; the contribution above survives — but narrower than early framing suggested. The Helm-chart-defaults territory is occupied by industry grey literature (Sorami 2026), generic-manifest prevalence and scanner-accuracy by Rahman et al. (TOSEM 2023) and Zhang et al. (TSE 2026), and deployed-service exposure by LENS and Hou et al. The contribution therefore rests on the combination — corpus scale and construction (105 pinned bundles, workload-level eligibility and dedup), the four-valued reference-label framework, and label-referenced scanner agreement in the LLM-inference domain — and on peer-reviewed status. A negative result from the pass: no academic study of Ray cluster exposure exists (ShadowRay is industry reporting only), so Ray-related positioning rests on the runtime-measurement papers and documentation, not a dedicated predecessor.

## 6. Claims we must not make

Do not claim:
- first empirical study of self-hosted LLM service security;
- first study of public LLM endpoint exposure or missing authentication;
- first Kubernetes/Helm misconfiguration survey;
- first analysis of security defaults in AI/LLM-serving Helm charts (Sorami Consulting's September 2026 industry report covers 15 such charts);
- first observation that manifest scanners miss pods declared inside Custom Resources (also reported by Sorami 2026; our observations corroborate, they are not first);
- first LLM-based Kubernetes/Helm repair system;
- that a LoadBalancer/NodePort or missing NetworkPolicy proves public internet exposure;
- that static absence of GPU/MIG/HAMi fields proves tenant co-location or lack of hardware isolation;
- that a declared MIG/GPU configuration proves tenant isolation is achieved (MIGraine 2026 shows it does not);
- that public examples represent production deployments.

## 7. Required systematic review before submission

**Done 2026-11-11:** a targeted expansion pass over web search, publisher pages, Crossref, arXiv, USENIX, and Zenodo — every citation in this document verified against its primary record, nine additional works integrated (Hou et al.; Rahman et al. TOSEM 2023; Zhang et al. TSE 2026; Krieger et al.; Shamim et al. FSE 2025; KubeCap; GRIEF; MIGraine; Sorami 2026), one factual error corrected (50, not 505, vulnerabilities in *Security in the Wild*), and two negative results recorded (no peer-reviewed configuration-level LLM-serving prevalence study; no academic Ray-exposure study). Queries and outcomes: `docs/LITERATURE_SEARCH_LOG.md`.

**Still required before submission:** the full database pass with hit counts, which the web-search interface used for the expansion pass does not report. Search ACM Digital Library, IEEE Xplore, SpringerLink, USENIX, arXiv, and relevant cloud-native/LLM security venues. Record:
- exact database and date;
- full query string;
- result count;
- inclusion/exclusion criteria;
- screening decisions and reasons;
- all directly overlapping studies.

Suggested query families:
- Kubernetes LLM inference deployment security;
- vLLM/TGI/SGLang/Ollama Kubernetes hardening;
- LLM serving endpoint authentication and gateway security;
- Kubernetes GPU multi-tenancy and model-cache security;
- Helm chart security misconfiguration empirical study;
- Kubernetes configuration static analysis and prevalence;
- LLM-assisted infrastructure-as-code repair and regression.

If a substantially similar configuration-level LLM-serving study exists, revise the contribution rather than forcing a novelty claim.
