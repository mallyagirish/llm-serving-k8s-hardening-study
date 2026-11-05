# Related Work and Novelty Positioning

**Status:** Preliminary structured scan, not yet a systematic review. Search databases, query strings, and screening decisions must be recorded before submission.

## 1. Directly related LLM-serving security research

### LENS: deployed self-hosted LLM service exposure

Liu et al. (WWW 2026), “Exploring and Exploiting Security Vulnerabilities in Self-Hosted LLM Services,” introduce LENS and evaluate publicly reachable self-hosted LLM deployments across 16 platforms, 71,249 discovered deployment targets, and 307 API endpoints. The authors report widespread unauthenticated API interaction among responsive targets and multiple vulnerability disclosures/CVEs.  
Project page: https://cristliu.github.io/lens/

**Relationship:** LENS is a close and important predecessor for LLM-service authentication and exposure. It studies deployed, network-reachable services and probes their behavior. This repository studies the configuration artifacts (Helm renders and Kubernetes manifests) used to define deployments. These are complementary units of analysis: runtime endpoint behavior versus published deployment configuration. We must not claim to be the first empirical study of self-hosted LLM service security or public exposure.

### LLM serving isolation and GPU data security

Shi et al. (2026), “Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking,” propose GPU information-flow tracking and evaluate on vLLM and DistServe. The work addresses isolation of user data in shared serving systems and GPU-resident data, rather than Kubernetes manifest prevalence.  
Preprint: https://arxiv.org/abs/2608.25431

**Relationship:** This work motivates why GPU isolation and model-serving trust boundaries matter. It does not validate whether a Kubernetes YAML manifest proves multi-tenant isolation. Our GPU-related rules must therefore be framed as static indicators unless hardware/runtime evidence exists.

### Vulnerabilities in LLM applications and inference frameworks

“Security in the Wild: An Empirical Analysis of LLM-Powered Applications and Local Inference Frameworks” (IEEE/ACM AIware 2025) curates and analyzes 505 reported vulnerabilities across LLM-powered applications and local inference frameworks.  
DOI: https://doi.org/10.1109/AIware69974.2025.00024

**Relationship:** This is software-vulnerability evidence across the LLM stack, not a Kubernetes configuration corpus. It supports the importance of studying infrastructure configuration as a distinct layer.

## 2. Kubernetes and Helm configuration measurement

### Helm chart security and LLM remediation

Minna, Massacci, and Tuma (2025), “Analyzing and mitigating (with LLMs) the security misconfigurations of Helm charts from Artifact Hub,” *Empirical Software Engineering*, 30(5), Article 132. DOI: https://doi.org/10.1007/s10664-025-10688-0

The authors analyze 4,961 Helm chart templates using multiple security analyzers and evaluate LLM-generated fixes. They report that context affects repair quality and that generated changes can remove unrelated configuration and break applications.

**Relationship:** This rules out novelty claims around generic Helm misconfiguration detection or generic LLM-based Helm repair. Our study's potential distinction is the curated LLM-inference deployment domain and rule-specific treatment of serving surfaces.

### Community-prescribed Kubernetes security configurations

Shamim, Hu, and Rahman (ICSE 2025), “On Prescription or Off Prescription?: An Empirical Study of Community-prescribed Security Configurations for Kubernetes.”  
Publication page: https://akondrahman.github.io/publication/icse25

This work studies community Kubernetes security configurations and static analyzer behavior. It is relevant to rule selection, policy interpretation, and analyzer limitations.

### Kubernetes misconfiguration taxonomy and LLM repair

Ghorab, Abdel Latif, and Saied (AIware 2026), “Kubernetes Misconfigurations in the Wild: Taxonomy, Evolution, and Automated Repair with Large Language Models.” DOI: https://doi.org/10.1145/3805760.3814908 ; preprint: https://arxiv.org/abs/2609.27030

The paper analyzes 2,662 Stack Overflow issues, derives a Kubernetes misconfiguration taxonomy, and evaluates contextual LLM remediation with schema-guided validation.

**Relationship:** Generic Kubernetes misconfiguration taxonomy and LLM repair are already covered. Do not position the companion remediation study as the first generic Kubernetes repair benchmark.

## 3. LLM-assisted infrastructure repair

### LLMSecConfig

“LLMSecConfig: An LLM-Based Approach for Fixing Software Container Misconfigurations,” MSR 2025. DOI: https://doi.org/10.1109/MSR66628.2025.00099

The paper combines static analysis and LLMs/RAG for repairing container misconfigurations and reports an evaluation on 1,000 Kubernetes configurations.

**Relationship:** This is another direct predecessor for general LLM-assisted Kubernetes/container repair. The companion remediation benchmark must distinguish itself through LLM-inference-specific serving invariants, not simply by using a different prompt or model.

### Security regressions during iterative IaC repair

Agyekum and Santos (ESEM 2026), “Does Fixing Break Security? An Empirical Study of Security Degradation in Iterative LLM-Driven Infrastructure-as-Code Repair.” Replication package: https://zenodo.org/records/21914827

The replication package describes 5,968 scenario timelines from IaC-Eval across 15 LLM configurations, measuring security regressions during iterative repair.

**Relationship:** Security regression measurement is established. The companion study should test serving/API/model-load invariants in addition to configuration security checks, and should avoid claiming novelty for regression measurement alone.

## 4. Current LLM-serving security guidance

The vLLM security guide documents several serving-specific boundaries, including route-level/API-key limitations, Ray cluster access, process isolation, cache trust, and multi-tenant isolation.  
https://docs.vllm.ai/en/latest/usage/security/

The guide explicitly states that vLLM does not provide tenant isolation between callers sharing one server process and recommends architectural controls such as per-tenant instances and an authenticating gateway. This supports our focus on the deployment architecture around an inference process, but documentation guidance is not empirical evidence of prevalence.

## 5. Defensible contribution for this study

The defensible candidate contribution is:

1. A pinned, auditable corpus of public Kubernetes/Helm artifacts specifically associated with LLM inference serving.
2. A rule/evidence framework that distinguishes direct YAML observations from context-dependent security claims.
3. A source- and workload-level eligibility and deduplication procedure that separates inference workloads from generic ML examples, operators, GPU schedulers, and tutorial fragments.
4. A reproducible characterization of security-relevant configuration patterns in public LLM-serving artifacts, with uncertainty and applicability reported rather than treating every missing field as a confirmed vulnerability.
5. Optionally, a controlled runtime validation substudy for a small subset of rules (e.g., API route authentication, Service/network reachability, and readiness), if the lab oracles can be made reproducible.

This is a candidate contribution, not yet a novelty conclusion. LENS is especially important: our paper must clearly say it studies published Kubernetes configuration artifacts, not the security of deployed public LLM endpoints.

## 6. Claims we must not make

Do not claim:
- first empirical study of self-hosted LLM service security;
- first study of public LLM endpoint exposure or missing authentication;
- first Kubernetes/Helm misconfiguration survey;
- first LLM-based Kubernetes/Helm repair system;
- that a LoadBalancer/NodePort or missing NetworkPolicy proves public internet exposure;
- that static absence of GPU/MIG/HAMi fields proves tenant co-location or lack of hardware isolation;
- that public examples represent production deployments.

## 7. Required systematic review before submission

Search ACM Digital Library, IEEE Xplore, SpringerLink, USENIX, arXiv, and relevant cloud-native/LLM security venues. Record:
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
