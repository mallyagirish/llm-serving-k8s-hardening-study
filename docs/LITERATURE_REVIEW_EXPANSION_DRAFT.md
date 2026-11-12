# Literature Review Expansion — Draft

**Date of searches and verification:** 2026-11-11 (PT)
**Scope:** Verification of every citation in `docs/RELATED_WORK_AND_NOVELTY.md`, plus a
targeted search for additional work (2023–2026) in the three families required by §7 of
that document: (a) Kubernetes/Helm/IaC misconfiguration prevalence and static-analyzer
accuracy; (b) security of LLM serving/inference infrastructure; (c) evaluations of
Kubernetes security configuration guidance.

**Method note:** Each existing citation was checked against its publisher page, DOI
record (Crossref), arXiv abstract page, USENIX page, Zenodo record, or author/project
page, opened directly. New works are included only if their primary page (publisher,
arXiv, or author PDF) was opened and read. Works whose venue could not be confirmed are
flagged as such and are excluded from the positioning section's load-bearing claims.
This is an expansion pass, not the full systematic review: the web search interface used
here does not report total hit counts, so the counts logged in §2 are the number of
results returned/screened per query (typically ~10), not database totals.

---

## 1. Verification of existing citations in RELATED_WORK_AND_NOVELTY.md

| # | Citation as written in the doc | Verified bibliographic record | Status |
|---|---|---|---|
| 1 | Liu et al. (WWW 2026), "Exploring and Exploiting Security Vulnerabilities in Self-Hosted LLM Services" (LENS) | Zhihuang Liu, Ling Hu, Yonghao Tang, Tongqing Zhou, Fang Liu, Zhiping Cai. *Proc. The Web Conference 2026 (WWW '26)*. BibTeX on the project page (cristliu.github.io/lens) confirms title, venue, year, and author order. All quantitative claims in the doc match the project page: 16 platforms, 71,249 discovered targets, 307 API endpoints, 75% of responsive targets allowing unauthenticated API interaction, 7 CVE IDs. | **Verified** |
| 2 | Shi et al. (2026), "Here is a GIFT…", arXiv:2608.25431 | Jiacheng Shi, Xunjie Wang, Cheng Tan, Jinyu Gu. arXiv:2608.25431 [cs.CR], submitted 26 Aug 2026. Implemented on vLLM and DistServe; 4–10.7% throughput overhead. Preprint only; no venue. The arXiv ID that looked fabricated is real. | **Verified** |
| 3 | "Security in the Wild: An Empirical Analysis of LLM-Powered Applications and Local Inference Frameworks" (IEEE/ACM AIware 2025), DOI 10.1109/AIware69974.2025.00024, "505 reported vulnerabilities" | Julia Gomez-Rangel, Young Lee, Bozhen Liu. *AIware 2025* (2nd ACM Int. Conf. on AI-Powered Software; proceedings published by IEEE), pp. 149–159. DOI 10.1109/AIware69974.2025.00024 confirmed exactly via Crossref. **Content correction:** the paper's own abstract states it curates and analyzes **50** publicly disclosed vulnerabilities from GitHub Security Advisories — not 505. The "505" figure in the doc is wrong and must be fixed wherever it propagates. | **Corrected** (citation valid; "505" → 50) |
| 4 | Minna, Massacci, and Tuma (2025), "Analyzing and mitigating (with LLMs) the security misconfigurations of Helm charts from Artifact Hub," *Empirical Software Engineering*, 30(5), Article 132. DOI 10.1007/s10664-025-10688-0 | Francesco Minna, Fabio Massacci, Katja Tuma. *Empirical Software Engineering* 30(5), 2025 (online 4 Jul 2025). DOI confirmed exactly via Crossref and the Springer article page. One residual: the prose claim that the study analyzes **4,961** chart templates could not be re-confirmed from the metadata/abstract pages opened in this pass (the number appears in neither the Crossref record nor the abstract); treat that specific count as unverified until checked against the paper's §4. | **Verified** (citation); corpus-size figure **unverified** |
| 5 | Shamim, Hu, and Rahman (ICSE 2025), "On Prescription or Off Prescription?: An Empirical Study of Community-prescribed Security Configurations for Kubernetes" | Shazibul Islam Shamim, Hanyang Hu, Akond Rahman. *Proc. IEEE/ACM ICSE 2025*, pp. 2432–2444. DOI **10.1109/ICSE55347.2025.00170** (missing from the doc; add it). Method details in the doc match the abstract: 53 CIS-recommended configurations, 544 configuration files, 5 SAST tools, best precision 0.41/0.43 and recall 0.53/0.65. | **Verified** (add DOI and pages) |
| 6 | Ghorab, Abdel Latif, and Saied (AIware 2026), "Kubernetes Misconfigurations in the Wild…", DOI 10.1145/3805760.3814908; arXiv:2609.27030 | Mostafa Anouar Ghorab, Ahmad Abdel Latif (ORCID record spells "Abdellatif"), Mohamed Aymen Saied. *Proc. 3rd ACM Int. Conf. on AI-Powered Software (AIware 2026)*. The ACM DOI is real: arXiv's OAI metadata and the third author's ORCID record both bind DOI 10.1145/3805760.3814908 to this exact title and author set. arXiv:2609.27030 confirmed (submitted 22 Sep 2026): 2,662 Stack Overflow issues, taxonomy, contextual LLM repair (89.06% best standalone), Kubecurity schema-guided validation (98.50%). Note the asymmetry: AIware 2025 proceedings are IEEE-published (10.1109) while AIware 2026 proceedings are ACM-published (10.1145) — both DOIs in the doc are correct as written. | **Verified** |
| 7 | Sgan Cohen et al. (2025), "KubeGuard…", arXiv:2509.04191 | Omri Sgan Cohen, Ehud Malul, Yair Meidan, Dudu Mimran, Yuval Elovici, Asaf Shabtai. arXiv:2509.04191 [cs.CR], submitted 4 Sep 2025. Content as described (manifests + audit/network/provenance logs; Roles, NetworkPolicies, Deployments). Preprint. | **Verified** |
| 8 | "LLMSecConfig: An LLM-Based Approach for Fixing Software Container Misconfigurations," MSR 2025. DOI 10.1109/MSR66628.2025.00099 | Ziyang Ye, Triet Huynh Minh Le, M. Ali Babar. *Proc. 2025 IEEE/ACM 22nd Int. Conf. on Mining Software Repositories (MSR)*, pp. 629–641. DOI confirmed exactly via Crossref; also arXiv:2502.02009. Evaluation on 1,000 real-world Kubernetes configurations, 94% repair success — matches the doc. | **Verified** |
| 9 | Agyekum and Santos (ESEM 2026), "Does Fixing Break Security?…", replication package at zenodo.org/records/21914827 | Benjamin Agyekum, Fabio Santos. *20th Int. Symposium on Empirical Software Engineering and Measurement (ESEM 2026)*, LIPIcs Vol. 394, Article 49; paper DOI 10.4230/LIPIcs.ESEM.2026.49; full version arXiv:2608.13404. Zenodo record 21914827 exists and is the camera-ready (v2) replication package; 5,968 IaC-Eval scenario timelines across 15 LLM configurations — matches the doc. **Citation-hygiene note:** the paper's own reference list cites the package as Zenodo DOI 10.5281/zenodo.20265184; cite that DOI (or both records) rather than only the bare record URL. | **Verified** (with Zenodo DOI note) |
| 10 | Sen, Longoria, and Liu (WOOT 2026), "LIMA: Defining, Benchmarking and Detecting Cross-Layer Vulnerabilities in LLM Inference Frameworks," USENIX WOOT '26, pp. 287–303 | Sanjib Kumar Sen, Hanna Longoria, Bozhen Liu. *USENIX Workshop on Offensive Technologies (WOOT '26)*. USENIX presentation page and the senior author's publication list confirm title, venue, authors, and content: 60 disclosed vulnerabilities across llama.cpp, vLLM, Ollama, LocalAI; LIMABench/LIMAScan; 7 newly discovered vulnerabilities in model-artifact loading paths. The page range 287–303 was not displayed on the USENIX page opened in this pass; treat the page range as plausible but not independently re-confirmed. | **Verified** (page range not re-confirmed) |
| 11 | vLLM security guide, docs.vllm.ai/en/latest/usage/security (documentation, §4 of the doc) | Live page verified. It documents, among other things: inter-node communication insecure by default (torch.distributed TCPStore listening on all interfaces), `--api-key` protecting only the `/v1`, `/v2`, `/inference`, `/cohere` route prefixes while operational endpoints (`/pause`, `/update_weights`, `/metrics`, etc.) remain unauthenticated, and dev-mode endpoints gated by `VLLM_SERVER_DEV_MODE=1`. This supports the doc's characterization of route-level/API-key limitations and process/network boundaries. Documentation is guidance, not empirical evidence — the doc already treats it that way. | **Verified** (as documentation) |

**Summary of verification:** No citation in the current set is fabricated. The two
identifiers singled out as most suspicious — arXiv:2608.25431 (GIFT) and
arXiv:2609.27030 (Kubernetes Misconfigurations in the Wild) — both resolve to real
papers with the stated titles and authors, and the AIware 2026 ACM DOI
(10.1145/3805760.3814908) is genuine. The real defects found are: (i) the "505
vulnerabilities" figure for *Security in the Wild* is wrong — the paper analyzes **50**;
(ii) the ICSE 2025 paper's DOI/pages were missing; (iii) the Agyekum & Santos package
should be cited by the Zenodo DOI printed in the paper; (iv) Minna et al.'s "4,961
charts" count and LIMA's page range remain unverified details.

---

## 2. Search log (this pass)

All searches run 2026-11-11 via web search with publisher/arXiv pages opened directly.
The search interface does not expose total hit counts; "screened" = results returned and
inspected (typically the top ~10). Crossref bibliographic lookups were used for DOI
resolution and are listed as fetches, not searches.

| # | Query string (exact) | Screened | Outcome |
|---|---|---|---|
| S1 | `LLMSecConfig LLM-Based Approach Fixing Software Container Misconfigurations MSR 2025 10.1109/MSR66628.2025.00099` | ~5 relevant | Paper, venue, authors confirmed (arXiv:2502.02009; MSR 2025 program). |
| S2 | `"10.1145/3805760.3814908" Kubernetes Misconfigurations AIware` | ~7 | DOI bound to the Ghorab et al. paper via arXiv OAI metadata and ORCID. |
| S3 | `"Security in the Wild" empirical analysis LLM-powered applications local inference frameworks AIware 2025 vulnerabilities 505` | ~7 | Paper and preprint found; "505" contradicted by the paper's own abstract (50). |
| S4 | `"MSR66628.2025.00099" LLMSecConfig` | ~10 (mostly noise) | No direct hit; DOI instead confirmed via Crossref record fetch. |
| S5 | `"Does Fixing Break Security" ESEM 2026 Agyekum Santos IaC repair authors` | ~6 | Authors, LIPIcs volume/article, arXiv:2608.13404, and both Zenodo records confirmed. |
| S6 | `empirical study Kubernetes misconfiguration prevalence static analysis tools accuracy precision recall manifests` | ~4 relevant of ~10 | Surfaced Zhang et al. (TSE 2026, "Configuration Defects in Kubernetes") and KubeCap. |
| S7 | `LLM serving infrastructure security empirical study vLLM KServe Ray Serve Triton deployment vulnerabilities` | ~4 | Surfaced GRIEF (fuzzing LLM serving systems); remainder was vendor/blog material. |
| S8 | `GPU multi-tenancy security study MIG MPS sharing isolation machine learning inference workloads` | ~4 relevant | Surfaced MIGraine and Behind Bars (MIG side channels); rest grey literature. |
| S9 | `CIS Kubernetes Benchmark compliance evaluation empirical study security configurations adoption` | ~4 relevant | Surfaced Shamim et al. FSE '25 industry report and Krieger et al. (compliance standards vs. scanners). One student-thesis result excluded (not a publication). |
| S10 | `"Configuration Defects in Kubernetes" ConShifu empirical study journal 719 defects static analysis tools` | ~7 | Bibliographic record confirmed: IEEE TSE 2026, DOI 10.1109/TSE.2026.3659785; arXiv:2512.05062. |
| S11 | `MIGraine side-channel NVIDIA Multi-Instance GPU Di Santi Giuffrida USENIX Security` | ~4 | Paper PDF and authors confirmed; venue not confirmable from the PDF (see N8 note). |
| S12 | `KServe OR LLMInferenceService OR llm-d Helm chart security configuration empirical analysis study` | ~5 | **Key find:** Sorami (2026) technical report on AI-serving Helm chart security defaults. No peer-reviewed KServe/LLMInferenceService configuration study found. |
| S13 | `Ray cluster dashboard Jobs API security exposure academic study ShadowRay analysis` | ~5 | No peer-reviewed empirical study of Ray exposure found; evidence base is industry reporting (Oligo ShadowRay) plus the multi-framework measurement papers (N1, LENS). Recorded as a negative result. |

Direct fetches used for verification: arXiv abstract pages (2608.25431, 2609.27030,
2509.04191, 2505.02502, 2606.24438, 2608.26699, 2605.11202), Crossref records
(10.1007/s10664-025-10688-0, 10.1109/MSR66628.2025.00099, 10.1109/AIware69974.2025.00024,
10.1145/3579639, and a bibliographic query resolving 10.1109/ICSE55347.2025.00170),
Springer article page, USENIX WOOT page, Zenodo record 21914827, LENS project page,
Rahman publication page, vLLM security documentation, Sorami report page.

---

## 3. New works, with positioning notes

### N1. Hou, Han, Zhao, & Wang (2025) — LLM deployment measurement (family b)

Xinyi Hou, Jiahao Han, Yanjie Zhao, Haoyu Wang. "Unveiling the Landscape of LLM
Deployment in the Wild: An Empirical Study." arXiv:2505.02502 [cs.CR] (submitted 5 May
2025; v2 Aug 2025). Internet-wide measurement: 320,102 public-facing LLM services across
15 frameworks, 158 API endpoints in 12 functional categories; >40% of endpoints over
plain HTTP, >210,000 endpoints lacking valid TLS metadata; Ollama deployments answered
>35% of unauthenticated API requests.

**Positioning:** This is the second large runtime-measurement study of deployed LLM
services, alongside LENS, and the current draft omits it. Together, LENS and Hou et al.
close off any claim about endpoint exposure or unauthenticated-access *prevalence in
deployed services*; our study's authentication/exposure rules must be framed strictly
as properties of published configuration artifacts, with these two papers cited as the
runtime-side evidence. Distinction: neither measurement study examines the Kubernetes
configuration that produced the deployments, which is precisely our unit of analysis.

### N2. Rahman, Shamim, Bose, & Pandita (2023) — the canonical K8s manifest prevalence study (family a)

Akond Rahman, Shazibul Islam Shamim, Dibyendu Brinto Bose, Rahul Pandita. "Security
Misconfigurations in Open Source Kubernetes Manifests: An Empirical Study." *ACM
Transactions on Software Engineering and Methodology* 32(4), Article 1–36 (published
online 26 May 2023). DOI 10.1145/3579639. (Note: some secondary sources cite this as
TOSEM 33(1); the Crossref record for the DOI gives 32(4).) Empirical study of 2,039
manifests from 92 OSS repositories; 11 misconfiguration categories; 1,051
misconfigurations; builds the SLI-KUBE linter.

**Positioning:** This is the direct methodological ancestor of our study — manifest
mining, category derivation, prevalence counting — and it is conspicuously absent from
the current related-work doc. A reviewer will expect it. It rules out any novelty in
"empirically characterizing security misconfigurations in open-source Kubernetes
manifests" as such; our contribution must be located in the LLM-serving domain
restriction, the eligibility/dedup procedure, and the explicit uncertainty (U/NA)
treatment, none of which this paper has. Its categories also overlap several of our 28
rules, so the rule framework should acknowledge the lineage.

### N3. Zhang, Paul, d'Amorim, & Rahman (2026) — configuration defects and tool accuracy (family a)

Yue Zhang, Uchswas Paul, Marcelo d'Amorim, Akond Rahman. "Configuration Defects in
Kubernetes." *IEEE Transactions on Software Engineering* (2026). DOI
10.1109/TSE.2026.3659785; preprint arXiv:2512.05062. 719 defects from 2,260 configuration
scripts in 185 repositories; 15 defect categories; systematic evaluation of 8 static
analysis tools (Checkov, Datree, Kube-score, KubeLinter, Kubesec, Kube-conform,
SLI-KUBE, Yamllint), finding average precision and recall ≤ 0.28 across tools; the
authors' ConShifu linter covers two categories no tool detects.

**Positioning:** This is the strongest published evidence that general-purpose K8s
scanners are inaccurate against human-labeled ground truth, and it is the natural
baseline for our scanner-agreement evaluation. Our evaluation differs in ground-truth
construction (per-rule PRESENT/ABSENT/U/NA reference labels on workload-level bundles,
restricted to LLM-serving artifacts) and in reporting agreement rather than raw
precision/recall alone — the paper should say so explicitly and cite Zhang et al.'s
≤0.28 figures as the expectation our results should be read against. It also means
"scanners are inaccurate" is not itself a finding we can present as new.

### N4. Krieger, Gierlinger, Shaikh, & Kahlhofer (2026) — guidance-vs-scanner comparison (family c)

Michael Krieger, Markus Gierlinger, Farooq Shaikh, Mario Kahlhofer. "A Comparison of
Kubernetes Compliance Standards and Configuration Scanners." arXiv:2606.24438 [cs.CR]
(submitted 23 Jun 2026). Systematic comparison of 8 hardening guidelines (CIS, NSA/CISA,
STIG, etc.), distilled into a 79-recommendation benchmark, plus a structured empirical
evaluation of 10 static configuration scanners; finds substantial disparities in
guideline coverage and inconsistent scanner severity scoring.

**Positioning:** This is the closest existing work to the "guidance evaluation" leg of
our study: it shows the guidance corpus itself is inconsistent, which justifies our
rule/evidence framing (rules cite their source guidance and record applicability rather
than treating any single benchmark as ground truth). Overlap is at the generic-K8s
level; it has no LLM-serving corpus, no per-workload reference labels, and no
uncertainty labels. Cite it when motivating why our 28 rules are evidence-graded rather
than copied from one benchmark.

### N5. Shamim, Hu, & Rahman (2025) — industry DAST experience report (families a/c)

Shazibul Islam Shamim, Hanyang Hu, Akond Rahman. "Dynamic Application Security Testing
for Kubernetes Deployment: An Experience Report from Industry." *Proc. 33rd ACM Int.
Conf. on the Foundations of Software Engineering (FSE '25)*, Trondheim, 2025. DOI
10.1145/3696630.3728573. On a live industry deployment ("Company-Z"), the authors find
3,442 violated recommended security configurations and evaluate three DAST tools
(Kubescape and kube-bench showing the broadest support, 14 configuration types).

**Positioning:** A companion to the same group's ICSE '25 paper, but on a *running
proprietary deployment* rather than mined artifacts. It is useful for the external-
validity discussion: it shows prescribed-configuration violations are not an artifact
of public example code, which partially answers the "public examples ≠ production"
objection — while also underscoring that our corpus cannot quantify production
prevalence. Cite in limitations, not as a competing study.

### N6. Liu et al. (2026) — KubeCap: capability prevalence and minimization (family a)

Yuhao Liu, Yingnan Zhou, Weijie Liu, Yan Jia, Zheli Liu. "KubeCap: A Framework for
Capability Minimization in Kubernetes via Static Analysis and LLM-Assisted Rule
Inference." arXiv:2608.26699 [cs.CR] (submitted 27 Aug 2026). Empirical study over three
open-source datasets finds 74.67% of projects lack capability configurations and only
19.33% follow the least-privilege pattern; the framework then infers minimal capability
sets and generates repaired manifests.

**Positioning:** Directly relevant to our capability-related rules (add/drop ALL,
privilege escalation): KubeCap establishes that missing capability configuration is the
norm in general K8s projects, so a high ABSENT/PRESENT rate for capability rules in our
corpus is expected background, not an LLM-serving-specific pathology. Our positioning
should compare rates rather than present the raw rate as a domain finding, and the
companion remediation study must note that automated capability minimization already
exists for generic workloads.

### N7. Zhao et al. (2026) — GRIEF: fuzzing LLM serving systems (family b)

Yunze Zhao, Yibo Zhao, Yuchen Zhang, Zaoxing Liu, Michelle L. Mazurek. "Continuous
Discovery of Vulnerabilities in LLM Serving Systems with Fuzzing." arXiv:2605.11202
[cs.CR] (submitted 11 May 2026). Greybox fuzzing of vLLM and SGLang with timed
multi-request traces; 15 vulnerabilities (10 developer-confirmed, 2 CVEs), including
KV-cache isolation failures and cross-request contamination under concurrency.

**Positioning:** GRIEF shows that some of the most serious serving-layer failures
(KV-cache cross-request leakage, noisy-neighbor DoS) are *runtime-emergent* and invisible
to any manifest analysis. This strengthens the paper's scoping discipline: our cache and
multi-tenancy rules are static indicators only, and GRIEF is the citation that explains
why a clean static label cannot certify serving-layer isolation. Complementary, not
competing — it tests engines, not deployments or configurations.

### N8. Di Santi, Di Dio, & Giuffrida (2026) — MIGraine: MIG side channel (family b)

Giovanni Di Santi, Andrea Di Dio, Cristiano Giuffrida. "MIGraine: Practical Side-channel
Attacks on NVIDIA Multi-Instance GPUs via Page Fault Contention." Vrije Universiteit
Amsterdam, 2026 (authors' PDF, download.vusec.net). A UVM page-fault contention channel
lets a tenant on one MIG instance fingerprint co-located workloads, including LLM
workloads served by vLLM, at 96% accuracy, on Ampere and Hopper and in vGPU deployments.
(Venue: the PDF filename suggests a USENIX Security 2027 submission/acceptance, but the
venue could not be confirmed from the paper itself in this pass — cite as a 2026
preprint until confirmed.)

**Positioning:** Together with GIFT (defensive isolation) this brackets our GPU rules
from both sides: MIG configuration in a manifest is at most an indicator that
partitioning was requested. MIGraine demonstrates that even correctly configured MIG
does not deliver full cross-tenant confidentiality, so the paper must not phrase a
PRESENT label on MIG/profile fields as "isolation achieved" — it should cite MIGraine
(and GIFT) exactly where the current draft already urges caution, upgrading that
caution from argument to evidence.

### N9. Sorami Consulting (2026) — AI-serving Helm chart security defaults (grey literature; families a+b)

Sorami Consulting. "AI on Kubernetes: Default Helm Chart Security and Lateral Movement."
Sorami Technical Report, 24 September 2026. https://sorami.com.au/research/ai-kubernetes-helm-chart-security/
Renders 15 official Helm charts for AI serving, gateways/UIs, vector databases, and
Kubernetes MCP tools with default values; scores 12 security checks per chart (auth
defaults, non-root enforcement, ServiceAccount token automount, RBAC breadth,
NetworkPolicy presence, etc.); live-probes the 8 charts that start in a kind cluster;
compares four scanners (Checkov 720, Trivy 1,015, kube-linter 240 failures) and reports
that **all scanners completely skip pods declared inside Custom Resources (e.g.,
KubeRay's RayCluster)**; documents a concrete LiteLLM chart bug (F-13: database password
in plain-text env vars in the migration Job). Findings: 10/14 API charts omit native
auth by default; 10/15 do not enforce non-root; 14/15 ship no NetworkPolicy.

**Positioning:** This is the closest overlap with our study found anywhere, and it is
grey literature (an industry technical report, not peer-reviewed). Overlap: rendered
Helm artifacts of AI/LLM-serving systems, default security posture, scanner comparison,
and several identical check families (auth, non-root, SA token, NetworkPolicy). Our
distinctions are methodological and must be stated plainly: (i) corpus — 105 pinned
bundles drawn from the serving projects' own repositories (charts *and* example/
deployment bundles) with workload-level eligibility and deduplication, vs. 15 vendor
charts at defaults; (ii) labels — per-rule reference labels with explicit U
(undecidable) and NA (not applicable) outcomes, vs. a binary pass/fail matrix;
(iii) evaluation — scanner agreement measured *against those reference labels*, vs.
raw scanner failure counts; (iv) scope — LLM inference serving only, vs. a mixed AI
stack including vector databases and MCP/agent tooling; (v) threat model — theirs is
in-cluster lateral movement with live probing, ours is configuration characterization
without runtime claims. The paper must cite this report; claiming the territory as
unstudied would be wrong. Their LiteLLM F-13 finding also sits inside our corpus domain
(LiteLLM bundles) and is worth an explicit cross-check in our data: if the same
migration-Job pattern appears in a labeled bundle, the labels should reflect it.

### Background note (not counted as a new work)

Gomez-Rangel, Vazquez, Lee, Demir, & Liu, "Rising Fast, Prone to Risk: A Comprehensive
Study of Security Risks in Open-Source LLM-Powered Applications," *International Journal
of System Assurance Engineering and Management* (ijsc) 20(1):95–134, March 2026 (per the
senior author's publication list and researchr). This is the journal extension of the
*Security in the Wild* line (citation #3); cite it alongside that paper if the
vulnerability-ecosystem framing needs a fuller source.

---

## 4. Works that force a contribution-claim revision

1. **Sorami (2026), "AI on Kubernetes" (N9) — the only genuinely claim-threatening
   find.** Any phrasing implying the first analysis of security defaults in
   AI/LLM-serving Helm charts, or the first observation that manifest scanners miss
   pods embedded in Custom Resources such as RayCluster, is no longer available: a
   September 2026 industry report did both, including on charts (KServe, KubeRay/Ray,
   LiteLLM, Ollama) that overlap our corpus. The contribution must be re-anchored on
   corpus scale and method (105 pinned bundles, workload-level eligibility/dedup,
   U/NA reference labels, label-referenced scanner agreement) and on peer-reviewed
   status — and the report must be cited and distinguished explicitly. Note this also
   validates several of our check families independently, which can be acknowledged.

2. **Hou et al. (2025) (N1), with LENS — runtime exposure claims are doubly closed.**
   Two independent internet-scale measurement studies now cover deployed-service
   exposure and unauthenticated access. No revision to the contribution is needed (the
   draft already disclaims this), but Hou et al. must be added next to LENS, or the
   related-work section will look a year out of date on its most important predecessor
   topic.

3. **Rahman et al. TOSEM 2023 (N2) and Zhang et al. TSE 2026 (N3) — prevalence and
   scanner-inaccuracy framings must be demoted to background.** The current doc's
   predecessor set jumps from Shamim et al. (ICSE '25) to Minna et al. (EMSE '25) and
   omits the two most canonical manifest-prevalence/tool-accuracy studies. Any
   contribution sentence of the form "we characterize misconfiguration prevalence in
   Kubernetes manifests" or "we show scanners disagree with ground truth" reads as
   claimed novelty unless these are cited and the claim is narrowed to the LLM-serving
   corpus and the U/NA label framework, as §5 of the novelty doc already intends.

4. **Correction, not a new work: the "505 vulnerabilities" error (citation #3).** If
   this figure has propagated into the manuscript draft's description of *Security in
   the Wild*, it must be corrected to 50 before submission; a reviewer who knows the
   paper will read it as carelessness about the closest LLM-stack predecessor.

5. **MIGraine (N8) — wording-level revision to GPU-isolation claims.** The draft's
   existing caution (static fields cannot prove isolation) is correct but is currently
   argued from principle; with MIGraine and GIFT in the literature, any sentence that
   treats a MIG/profile PRESENT label as evidence of achieved tenant isolation would
   now be contradicted by published attack results. Keep the labels, cite both papers,
   and phrase GPU rules strictly as configuration indicators.

**Bottom line:** After this pass, no peer-reviewed, configuration-level,
LLM-serving-specific prevalence study with reference labels was found; the study's core
contribution as framed in §5 of the novelty doc survives. But it survives *narrower*
than the current draft's framing: the Helm-chart-defaults territory is occupied by
industry grey literature (Sorami 2026), the generic-manifest prevalence and
scanner-accuracy territory by TOSEM '23 / TSE '26 / ICSE '25, and the deployed-service
exposure territory by LENS + Hou et al. The related-work section needs all of N1–N9
integrated before the §7 systematic review is written up, and the "505" error needs
fixing in the source doc (out of scope for this draft, which changes nothing else).
