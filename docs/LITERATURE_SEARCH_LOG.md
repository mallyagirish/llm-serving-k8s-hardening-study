# Exploratory Literature Search Log

**Search date:** 2026-11-05  
**Status:** Exploratory web search only; this is not a systematic database review.

## Queries used

1. Kubernetes LLM inference serving security hardening empirical study vLLM TGI SGLang GPU multi-tenancy model cache 2024–2026
2. LLM serving security Kubernetes API authentication route authorization Ray dashboard exposure model cache security research
3. Kubernetes Helm chart security misconfiguration empirical study LLM repair automated remediation 2025–2026
4. Kubernetes GPU multi-tenancy isolation security HAMi MIG inference workload research
5. vLLM security documentation API key endpoints tokenizer dev mode cache security
6. site:dl.acm.org Kubernetes LLM inference deployment security configuration
7. site:usenix.org LLM serving Kubernetes security inference infrastructure
8. site:arxiv.org Kubernetes LLM serving security configuration misconfiguration
9. site:ieeexplore.ieee.org Kubernetes LLM inference serving security deployment

## Relevant studies identified

| Work | Venue/year | Relation to this study |
|---|---|---|
| LENS: Exploring and Exploiting Security Vulnerabilities in Self-Hosted LLM Services | WWW 2026 | Direct runtime/public endpoint security study; our unit is public Kubernetes configuration artifacts, not live endpoint scanning. |
| LIMA: Defining, Benchmarking and Detecting Cross-Layer Vulnerabilities in LLM Inference Frameworks | USENIX WOOT 2026 | Model-artifact loading and inference framework vulnerability taxonomy; relevant to model/cache rule motivation. |
| KubeGuard: LLM-Assisted Kubernetes Hardening via Configuration Files and Runtime Logs Analysis | arXiv 2025 | Runtime-informed Kubernetes hardening; adjacent to the companion remediation benchmark. |
| LLMSecConfig: An LLM-Based Approach for Fixing Software Container Misconfigurations | MSR 2025 | General Kubernetes/container configuration repair; rules out generic LLM repair novelty. |
| Analyzing and mitigating (with LLMs) the security misconfigurations of Helm charts from Artifact Hub | Empirical Software Engineering 2025 | General Helm misconfiguration and LLM fixes; close predecessor for generic chart analysis. |
| On Prescription or Off Prescription?: An Empirical Study of Community-prescribed Security Configurations for Kubernetes | ICSE 2025 | General Kubernetes configuration recommendations and analyzer behavior. |
| Kubernetes Misconfigurations in the Wild: Taxonomy, Evolution, and Automated Repair with Large Language Models | AIware 2026 | General Kubernetes taxonomy and LLM repair; close predecessor for companion study. |
| Security in the Wild: An Empirical Analysis of LLM-Powered Applications and Local Inference Frameworks | AIware 2025 | Vulnerability evidence across LLM applications/frameworks; not Kubernetes manifest prevalence. |
| Here is a GIFT: Enforcing User Data Isolation in LLM Serving via GPU Information Flow Tracking | arXiv 2026 | GPU data isolation in serving; supports caution about inferring isolation from YAML. |
| Does Fixing Break Security? An Empirical Study of Security Degradation in Iterative LLM-Driven Infrastructure-as-Code Repair | ESEM 2026 | Security regressions in iterative IaC repair; relevant to companion study outcomes. |

## Important exclusions/background

The search also surfaced LLM serving performance/system papers such as OpenTela (OSDI 2026), PlanetServe (NSDI 2026), ServeGen (NSDI 2026), and Strata (OSDI 2026). These are relevant to the broader serving ecosystem but do not directly evaluate Kubernetes security configuration prevalence. Cite only if needed to explain serving architecture/context.

## Next systematic-review steps

- Search ACM Digital Library, IEEE Xplore, SpringerLink, USENIX proceedings, arXiv, and relevant cloud-native security venues directly.
- Save exact queries, result counts, dates, and inclusion/exclusion decisions.
- Search for papers on vLLM/TGI/SGLang/Ollama deployment security, Kubernetes LLMInferenceService configuration, Ray Serve security, GPU multi-tenancy, model cache security, and public endpoint authentication.
- Have a second researcher independently screen titles/abstracts for directly overlapping work.
- Update novelty claims if any more direct configuration-level LLM-serving study is found.
