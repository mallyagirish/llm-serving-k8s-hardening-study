# Annotator instructions — independent labeling sample

Thank you for labeling this sample. You are the **independent** annotator
for a study of security-relevant configuration in public Kubernetes/Helm
artifacts for LLM inference serving. Your labels will be compared with
the study's reference labels to measure how reliable the labeling
protocol is. Your independence is the point — please read the rules
below before starting.

## Rules

1. **Work only from this packet**: the manifests in `manifests/`, the
   labeling guide (`LABELING_GUIDE.md`), and the sheet
   (`annotation_sheet.csv`).
2. **Do not look at any existing labels.** If you have access to the
   study repository, do not open `results/labels/`, the frozen reference
   file, scanner outputs, or any adjudication notes. Do not discuss
   specific bundles or labels with the study author before you finish.
3. **One label per row**, from exactly: `PRESENT`, `ABSENT`, `U`, `NA` —
   with the meanings in the guide (§2 and each rule's row):
   - `PRESENT` — the rule's condition is observably true in this bundle.
   - `ABSENT` — the rule was decidable for this bundle and the condition
     is observably false (including "protected by the mechanism the rule
     names").
   - `U` — the bundle leaves the question genuinely undecidable from
     static YAML (say why in the rationale).
   - `NA` — the rule's scope condition is not met for this bundle.
4. **Cite evidence** for every decided (PRESENT/ABSENT) row: put the
   manifest filename plus the object/field you relied on in
   `evidence_path`, and one or two sentences in `rationale`. For U/NA,
   the rationale states what is missing or out of scope.
5. **Never copy a credential value** into the sheet if a rule involves
   secrets — refer to the field by name only (guide §: SEC rules).
6. Work bundle by bundle (the sheet is grouped by bundle). If you run
   out of time, finish whole bundles rather than scattering rows, and
   note which bundles you completed.
7. If the guide genuinely does not decide a case, use `U` and write the
   ambiguity in the rationale — those notes are valuable data, not
   failures.

## What you are labeling

Each row is one (bundle, rule) pair: whether the bundle's rendered
Kubernetes YAML exhibits the configuration condition the rule defines.
The 28 rules cover authentication, network exposure, secrets handling,
container/workload hardening, GPU sharing, model loading/caching, and
resilience (probes, resources, disruption protection). The guide's rule
table (§3) is the contract: use its PRESENT/ABSENT/U/NA definitions
exactly, including the v0.4 RES-02 decision record.

## Returning your work

Return the completed `annotation_sheet.csv` with `label`,
`evidence_path`, `rationale`, and `review_timestamp` filled in (leave
`reviewer_id` as given). A short note listing any guide ambiguities you
hit is very welcome — send it alongside, not in the sheet.

Questions about logistics (files, format, deadlines): ask the study
author. Questions about how to label a specific case: the guide decides,
or it is a `U` — please do not ask the author to resolve label content,
as that would compromise the independence this exercise exists to
provide.
