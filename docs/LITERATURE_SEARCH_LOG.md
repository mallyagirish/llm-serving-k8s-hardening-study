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
- Screening is performed by the author (with the AI-assisted workflow disclosed); no independent second screener or annotator — author decision, 2026-11-11.
- Update novelty claims if any more direct configuration-level LLM-serving study is found.

---

## Expansion pass — 2026-11-11

Targeted verification + gap search (author-directed). Method: every citation in
`docs/RELATED_WORK_AND_NOVELTY.md` checked against its publisher page, Crossref/DOI
record, arXiv abstract page, USENIX page, Zenodo record, or author/project page,
opened directly. New works included only if their primary page was opened and read.
The web search interface used does not report total hit counts; "screened" = results
returned and inspected (typically the top ~10). This pass was an expansion, not the
full systematic database review — the database pass with hit counts remains open
(see `docs/RELATED_WORK_AND_NOVELTY.md` §7).

### Queries (exact strings)

| # | Query | Screened | Outcome |
|---|---|---|---|
| S1 | `LLMSecConfig LLM-Based Approach Fixing Software Container Misconfigurations MSR 2025 10.1109/MSR66628.2025.00099` | ~5 | Paper, venue, authors confirmed (arXiv:2502.02009). |
| S2 | `"10.1145/3805760.3814908" Kubernetes Misconfigurations AIware` | ~7 | DOI bound to Ghorab et al. via arXiv OAI metadata and ORCID. |
| S3 | `"Security in the Wild" empirical analysis LLM-powered applications local inference frameworks AIware 2025 vulnerabilities 505` | ~7 | Paper found; "505" contradicted by the paper's own abstract (50). |
| S4 | `"MSR66628.2025.00099" LLMSecConfig` | ~10 (mostly noise) | No direct hit; DOI confirmed via Crossref instead. |
| S5 | `"Does Fixing Break Security" ESEM 2026 Agyekum Santos IaC repair authors` | ~6 | Authors, LIPIcs record, arXiv:2608.13404, both Zenodo records confirmed. |
| S6 | `empirical study Kubernetes misconfiguration prevalence static analysis tools accuracy precision recall manifests` | ~4 relevant of ~10 | Surfaced Zhang et al. (TSE 2026) and KubeCap. |
| S7 | `LLM serving infrastructure security empirical study vLLM KServe Ray Serve Triton deployment vulnerabilities` | ~4 | Surfaced GRIEF; remainder vendor/blog material. |
| S8 | `GPU multi-tenancy security study MIG MPS sharing isolation machine learning inference workloads` | ~4 relevant | Surfaced MIGraine; rest grey literature. |
| S9 | `CIS Kubernetes Benchmark compliance evaluation empirical study security configurations adoption` | ~4 relevant | Surfaced Shamim et al. FSE '25 and Krieger et al. One student thesis excluded (not a publication). |
| S10 | `"Configuration Defects in Kubernetes" ConShifu empirical study journal 719 defects static analysis tools` | ~7 | Record confirmed: IEEE TSE 2026, DOI 10.1109/TSE.2026.3659785; arXiv:2512.05062. |
| S11 | `MIGraine side-channel NVIDIA Multi-Instance GPU Di Santi Giuffrida USENIX Security` | ~4 | Authors confirmed from the paper PDF; venue not confirmable — cited as a 2026 preprint. |
| S12 | `KServe OR LLMInferenceService OR llm-d Helm chart security configuration empirical analysis study` | ~5 | Key find: Sorami (2026) industry report on AI-serving Helm chart defaults. No peer-reviewed KServe/LLMInferenceService configuration study found. |
| S13 | `Ray cluster dashboard Jobs API security exposure academic study ShadowRay analysis` | ~5 | Negative result: no peer-reviewed empirical study of Ray exposure; industry reporting (Oligo ShadowRay) only. |

Direct fetches used for verification: arXiv abstract pages (2608.25431, 2609.27030, 2509.04191, 2505.02502, 2606.24438, 2608.26699, 2605.11202); Crossref records (10.1007/s10664-025-10688-0, 10.1109/MSR66628.2025.00099, 10.1109/AIware69974.2025.00024, 10.1145/3579639, and the query resolving 10.1109/ICSE55347.2025.00170); Springer article page; USENIX WOOT page; Zenodo record 21914827; LENS project page; Rahman publication page; vLLM security documentation; Sorami report page.

### Verification outcomes for the pre-existing set

No citation was fabricated. The two most suspicious identifiers — arXiv:2608.25431 (GIFT) and arXiv:2609.27030 (Ghorab et al.) — are real, as is the AIware 2026 ACM DOI 10.1145/3805760.3814908. Defects found and fixed in `docs/RELATED_WORK_AND_NOVELTY.md` / `docs/references.bib`: (i) *Security in the Wild* analyzes **50** vulnerabilities, not 505; (ii) Shamim et al. ICSE 2025 DOI (10.1109/ICSE55347.2025.00170) and pages (2432–2444) added; (iii) Agyekum & Santos package cited by the Zenodo DOI printed in the paper (10.5281/zenodo.20265184). Left flagged as unverified: Minna et al.'s "4,961 charts" count and LIMA's page range (287–303).

### Works added by this pass

| Work | Venue/year | Relation to this study |
|---|---|---|
| Hou et al., "Unveiling the Landscape of LLM Deployment in the Wild" | arXiv:2505.02502, 2025 | Second internet-scale runtime measurement (320,102 services); with LENS, closes deployed-exposure claims. |
| Rahman et al., "Security Misconfigurations in Open Source Kubernetes Manifests" | ACM TOSEM 32(4), 2023 | Canonical manifest-prevalence ancestor (2,039 manifests, SLI-KUBE); rules out generic-manifest novelty. |
| Zhang et al., "Configuration Defects in Kubernetes" | IEEE TSE, 2026 | 719 defects; 8 scanners at avg precision/recall ≤ 0.28 — the scanner-accuracy baseline. |
| Krieger et al., "A Comparison of Kubernetes Compliance Standards and Configuration Scanners" | arXiv:2606.24438, 2026 | Guidance corpus is itself inconsistent; justifies our evidence-graded rules. |
| Shamim et al., "Dynamic Application Security Testing for Kubernetes Deployment" | FSE '25 (industry report) | Violations on a live industry deployment; external-validity support, cited in limitations. |
| Liu et al., "KubeCap" | arXiv:2608.26699, 2026 | Capability-configuration absence is the norm (74.67%); background rate for our capability rules. |
| Zhao et al., "GRIEF: Continuous Discovery of Vulnerabilities in LLM Serving Systems with Fuzzing" | arXiv:2605.11202, 2026 | Runtime-emergent serving failures (KV-cache isolation) invisible to manifest analysis. |
| Di Santi et al., "MIGraine" | Preprint, 2026 (venue unconfirmed) | MIG side channel; PRESENT on MIG fields is an indicator, never proof of isolation. |
| Sorami Consulting, "AI on Kubernetes: Default Helm Chart Security and Lateral Movement" | Industry technical report, Sep 2026 | Closest overlap overall (15 AI-serving Helm charts, scanner comparison, CR-blindness); grey literature — contribution re-anchored on corpus/method/labels, see novelty doc §2 and §5. |

### Bottom line of this pass

No peer-reviewed, configuration-level, LLM-serving-specific prevalence study with reference labels was found; the study's core contribution survives, narrower. The full database systematic review (with hit counts) remains a pre-submission step.
