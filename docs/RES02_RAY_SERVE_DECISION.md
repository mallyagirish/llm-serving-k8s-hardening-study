# RES-02 × Ray Serve — decision memo

**Prepared:** 2026-11-11 · **Status:** awaiting author decision
**Scope:** guide v0.4 predicate for LLM-RES-02 vs Ray Serve `serveConfigV2`
application-level autoscaling. Flagged earlier in
`docs/SCANNER_EVALUATION_REPORT.md` ("should be resolved before final
publication") and in the full-pass quality audit notes.

## The verified facts

Guide v0.4 defines RES-02 PRESENT as: a **scaled** inference workload
(replicas > 1 on in-bundle workload fields, an HPA, controller autoscaling
fields permitting > 1 replica, or a Knative Service) with no
selector-matching PDB. NA when no workload is scaled. The predicate reads
Kubernetes/controller fields; it does not parse Ray Serve's
`serveConfigV2` string, where Serve declares per-deployment scaling in two
dialects:

- classic: `applications[].deployments[].autoscaling_config`
  (`min_replicas` / `max_replicas`) or `num_replicas`;
- LLM API (`ray.serve.llm:build_openai_app`):
  `applications[].args.llm_configs[].deployment_config.autoscaling_config`.

Corpus check (2026-11-11, all rendered bundles scanned for
`serveConfigV2`): exactly 6 bundles contain it; 4 are primary:

| Bundle (primary) | serveConfigV2 scaling | Frozen v1 RES-02 | Basis of frozen label |
|---|---|---|---|
| kuberay-sample-ray-service.llm-serve | LLM-API `autoscaling_config` **min 1, max 4** | **NA** | workerGroupSpecs[0].replicas = 1; rationale says "no autoscaling configuration" |
| kuberay-sample-ray-service.deepseek | LLM-API `autoscaling_config` min 1, **max 1** | PRESENT | workerGroupSpecs[0].replicas = 2 (K8s level) |
| kuberay-sample-ray-service.high-throughput-llm | none declared | PRESENT | worker-group replicas (K8s level) |
| kuberay-sample-ray-service.vllm-tpu-v6e-singlehost | classic `num_replicas: 1`, no autoscaling | NA | single replica everywhere |

(The two non-primary `serveConfigV2` bundles — custom-serve-service,
supporting, all `num_replicas: 1`; no-ray-serve-replica, excluded — are
unaffected under either reading.)

**Net effect: exactly one primary cell is contested** —
`kuberay-sample-ray-service.llm-serve` / LLM-RES-02, frozen NA. Its Serve
application autoscales 1 → 4 replicas, so under an application-level
reading it is a scaled workload with no PDB in the bundle: PRESENT. The
frozen rationale's phrase "no autoscaling configuration" is inaccurate as
written; the autoscaling is declared, just in the Serve dialect the
predicate does not read.

## Options

**A. Extend the predicate (guide v0.5 amendment).** Add to the RES-02
"scaled" definition: a RayService whose `serveConfigV2` declares, in
either dialect, `autoscaling_config` with `max_replicas > 1` (or
`min_replicas > 1`), or a classic deployment with `num_replicas > 1`,
counts as autoscaling for the workload. Apply through the study's normal
machinery: a dated guide amendment (v0.5, recorded as a post-freeze
amendment, author-decided), one row in
`results/labels/author_adjudication_history.csv`, and a re-issued frozen
set `reference_labels_author_validated_v2.csv` (v1 preserved untouched).
Resulting deltas: that one cell NA → PRESENT; corpus counts PRESENT
646 → 647, NA 859 → 858; RES-02 row 21 PRESENT / 0 ABSENT / 84 NA becomes
22 / 0 / 83; scanner metrics recomputed (the cell is NA in v1, so it sits
outside the scanner binary matrix in both versions — no scanner number
moves).

**B. Keep the predicate; scope the claim.** Guide and manuscript state
explicitly that RES-02 reads Kubernetes-level scaling declarations only,
and that framework-level autoscaling (Ray Serve `serveConfigV2`) is out
of scope for this rule; the llm-serve case is named as a known instance
(1 of 105 bundles) in a limitations note. No labels change. Cost: the
frozen rationale sentence "no autoscaling configuration" still needs a
correcting note, and a reviewer can fairly say the rule undercounts
scaled workloads in the one dialect it cannot read.

## Recommendation

**Option A.** The PRESENT definition already counts "controller
autoscaling fields permitting more than one replica" as scaling;
`serveConfigV2` is the same declaration in the serving framework's own
dialect, in-bundle and observable. Excluding it is an artifact of which
YAML subtree the predicate reads, not a construct distinction — and the
affected population is exactly one cell, so the amendment is cheap,
fully auditable, and matches how every earlier predicate decision in
this study was made (versioned guide amendment + adjudication record,
originals preserved).

## Exact artifacts if A is approved

1. `docs/LABELING_GUIDE.md` → v0.5: RES-02 PRESENT cell gains the
   serveConfigV2 clause; changelog entry dated and marked post-freeze,
   author-decided, referencing this memo.
2. `results/labels/author_adjudication_history.csv`: one appended row
   (bundle, rule, prior NA, scanner n/a, final PRESENT, evidence =
   manifest path + `deployment_config.autoscaling_config` lines,
   rationale, status author_confirmed).
3. `results/labels/reference_labels_author_validated_v2.csv` + `.meta.json`
   sidecar (source v1 + this amendment; new SHA-256); v1 untouched.
4. `docs/REFERENCE_LABEL_VALIDATION.md`: a dated update section recording
   the v0.5 amendment and the v2 freeze, same pattern as the 2026-11-11
   update.
5. `docs/SCANNER_EVALUATION_REPORT.md`: the RES-02 sensitivity paragraph
   replaced with the resolution; metrics re-run (expected: unchanged).
6. Full test suite re-run; prevalence figures regenerated from v2.

No other rule reads `serveConfigV2` scaling today, and no other primary
bundle declares it, so the blast radius is provably this one cell.
