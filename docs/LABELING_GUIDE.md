# Human Reference-Labeling Guide

**Version:** 0.2 draft — freeze and independently review before confirmatory labeling. (0.2, 2026-11-05: reviewer labels renamed TP/FP → PRESENT/ABSENT before any sheets were generated, because reviewers record reference classifications of rule conditions, not scanner outcomes; U/NA unchanged.)

## 1. What the labels mean

For each rule × configuration bundle:

Reviewers assign **reference classifications of the rule condition** in each bundle. Reviewers never see scanner predictions, so these labels are not scanner true/false positives:

- **PRESENT — rule condition observed:** the predeclared positive evidence for the rule's misconfiguration condition is present in the bundle.
- **ABSENT — rule condition not observed:** the rule applies and the bundle provides enough context to establish that the condition is absent.
- **U — uncertain:** required context is absent, incomplete, ambiguous, or outside static YAML.
- **NA — not applicable:** the bundle has no resource/workload to which the rule applies.

These are reference labels for the rule predicate. They become scanner confusion-matrix quantities (TP/FP/FN/TN) only later, when adjudicated reference labels are compared against scanner output on the same independently labeled unit — that comparison is an analysis step, not something a reviewer records.

Record the exact file, YAML document index, resource name, field path, and a short rationale. Never copy actual credential values into labels, logs, CSVs, or the paper. Redact values and record only key names and location.

## 2. General adjudication rules

1. Use the full bundle, not an isolated YAML fragment, when deciding whether another resource provides a control.
2. Do not infer cluster-wide state from a chart bundle. A missing NetworkPolicy in one chart does not prove no policy exists in the cluster.
3. Distinguish a static configuration indicator from exploitability, public internet reachability, or runtime impact.
4. Treat placeholders such as YOUR_TOKEN, ${API_KEY}, changeme, and obvious examples as placeholders, not confirmed leaked secrets.
5. Account for pod-level and container-level securityContext precedence. An explicitly set container value overrides the pod-level value for that container.
6. If a control may be enforced outside the bundle (cloud firewall, external gateway, admission policy, service mesh, cluster-wide NetworkPolicy), use U unless the artifact contains sufficient evidence.
7. A bundle can contain multiple resources. Aggregate a rule as PRESENT if at least one in-scope resource satisfies its positive predicate; preserve resource-level evidence for that decision.
8. Keep tutorial/example bundles distinct from chart defaults in analysis and writing.

## 3. Rule-specific evidence

| Rule | PRESENT evidence | ABSENT evidence | Use U / NA when |
|---|---|---|---|
| LLM-AUTH-01 | An exposed inference API is configured without API-key/auth enforcement in the serving process or included gateway. | Explicit auth enforcement is configured for the relevant API routes. | Gateway/auth config is outside the bundle or the serving API is not identifiable. |
| LLM-AUTH-02 | A key protects only selected routes while sibling inference/ops routes remain reachable without an allowlist/auth layer. | Included gateway/proxy blocks or authenticates all sensitive sibling routes. | Only a serving Deployment is present and route-level gateway behavior is unavailable. |
| LLM-AUTH-03 | Tokenizer, admin, profiler, or development endpoints/flags are explicitly enabled. | Relevant flags are explicitly disabled and no such endpoint is configured. | Engine version or effective flags cannot be determined. |
| LLM-AUTH-04 | Wildcard CORS is configured in a way that permits untrusted origins, especially with credentials, or auth middleware is explicitly disabled. | Origins are restricted and auth middleware is enabled. | CORS/auth behavior is application- or gateway-defined outside the bundle. |
| LLM-AUTH-05 | Ingress/HTTPRoute exposes an inference backend and the complete included routing config has no auth filter/annotation. | An included auth filter, external-auth integration, or equivalent gate protects the route. | Controller-level or external auth configuration is missing from the bundle. |
| LLM-NET-01 | Inference Service has type LoadBalancer or NodePort. | Service is ClusterIP/headless and no matching externally exposed Service exists in the bundle. | No Service is present or the Service-to-workload mapping is unclear. PRESENT is an exposure indicator, not proof of public internet access. |
| LLM-NET-02 | A complete chart/bundle for the workload contains no NetworkPolicy selecting it and no included default-deny policy. | A policy selects the workload and constrains ingress/egress as specified by the rule. | Bundle completeness or namespace-wide policy state is unknown. Do not infer cluster-wide absence. |
| LLM-NET-03 | Ingress has no TLS section, or the relevant Gateway listener is HTTP-only without an included TLS termination path. | TLS is explicitly configured on the relevant listener/route. | TLS terminates upstream or in an external load balancer not represented in the bundle. |
| LLM-NET-04 | Service/host networking exposes recognized Ray, distributed, or KV-transfer control ports beyond the intended trusted boundary. | Relevant control ports are absent or explicitly isolated by included policies. | Port purpose or network boundary cannot be determined. ClusterIP alone does not prove safe isolation. |
| LLM-NET-05 | Inference PodSpec sets hostNetwork: true or hostPID: true. | Both are explicitly false or omitted under a documented policy that enforces false. | Resource is not an inference workload or effective PodSpec is unavailable. |
| LLM-SEC-01 | A non-placeholder credential/token is embedded in a ConfigMap, values file, or other non-Secret field. | No literal credential is present and credentials are referenced through Secret objects/refs. | String is a placeholder, ambiguous, or secret scanning is inconclusive. Never reproduce the value. |
| LLM-SEC-02 | Token-like environment variable uses a literal non-placeholder value instead of valueFrom.secretKeyRef. | The variable is populated using secretKeyRef or a documented secure mechanism. | Environment variable purpose or placeholder status is unclear. |
| LLM-SEC-03 | A ServiceAccount used by the inference workload is bound to cluster-admin or broad wildcard permissions. | Included Role/RoleBinding grants only documented least-privilege permissions. | ServiceAccount-to-binding mapping is incomplete or roles are defined outside the bundle. |
| LLM-GPU-01 | A workload clearly requiring GPU inference has no vendor GPU resource request/limit. | The GPU resource is explicitly requested/limited, or the workload is explicitly CPU-only. | Workload hardware requirements or scheduler/device-plugin context is unknown. |
| LLM-GPU-02 | Runtime/node evidence shows multiple tenants share GPU resources without the claimed isolation boundary. | Runtime evidence establishes a dedicated GPU or effective partition/isolation boundary. | Static YAML alone is insufficient to establish co-location, MIG state, device-plugin behavior, or tenant isolation. Usually U in this corpus. |
| LLM-GPU-03 | Inference container is privileged, adds dangerous capabilities (e.g. SYS_ADMIN, SYS_PTRACE, ALL), or mounts sensitive host device paths without a documented requirement. | Privileged mode is false, dangerous capabilities are absent, and device access is narrowly scoped. | Hardware/runtime requirements or compensating controls are unknown. |
| LLM-WL-01 | Effective runAsNonRoot is not true for the inference container. | Effective value is true, accounting for container-over-pod precedence. | PodSpec or container identity is unavailable. This is a configuration finding, not proof the process runs as root. |
| LLM-WL-02 | Inference container does not set readOnlyRootFilesystem: true. | It is explicitly true and required writable paths are mounted separately. | Serving engine requires writable paths and the requirement is not documented. |
| LLM-WL-03 | allowPrivilegeEscalation is not explicitly false. | It is explicitly false at container level. | Admission/runtime policy may enforce the value but is not represented in the bundle. |
| LLM-WL-04 | No seccomp profile is configured and no relevant AppArmor profile/annotation is present. | RuntimeDefault/Localhost seccomp or an explicit AppArmor policy is configured. | Admission defaults or node runtime policy are external to the bundle. |
| LLM-WL-05 | Image uses latest, an unpinned tag, or no immutable digest under the predeclared predicate. Record latest and non-digest tags separately. | Image is pinned by immutable digest. | Registry policy proves tags immutable or image reference cannot be resolved. |
| LLM-STOR-01 | Evidence shows model/cache storage shared across workloads with RWX/world-writable access or broad filesystem permissions. | Access is constrained to the intended workload/tenant with documented ownership and permissions. | YAML only shows RWX/PVC but not filesystem permissions or actual sharing. |
| LLM-STOR-02 | hostPath or untrusted/shared writable volume is mounted at a model/cache path (e.g. HF/vLLM compile cache) without trust/ownership controls. | Model/cache storage is isolated and permissions/ownership are explicitly constrained. | Mount path purpose or volume trust model is unclear. |
| LLM-STOR-03 | Model-download initContainer runs privileged/root unnecessarily, mounts sensitive host paths, or receives a literal token. | InitContainer is least-privileged and credentials use Secret references. | The initContainer's role or required privileges cannot be established. |
| LLM-RES-01 | Inference container lacks one or more CPU/memory requests or limits under the frozen rule predicate. | CPU and memory requests/limits are explicitly configured. | Namespace defaults, VPA, or workload sizing context materially changes interpretation. |
| LLM-RES-02 | A production-oriented replicated inference workload has no matching PDB in a complete bundle. | Matching PDB protects the workload with a meaningful disruption budget. | Bundle is incomplete, workload is a tutorial/single replica, or production intent is unknown. |
| LLM-RES-03 | Inference container has neither readiness nor startup probe, or uses only a liveness probe for model readiness. | Readiness/startup behavior is configured to prevent traffic before model initialization. | Probe behavior is external or the serving runtime manages readiness outside the PodSpec. |
| LLM-OBS-01 | Metrics/dashboard/Ray control endpoint is externally exposed by Service/Ingress without an included auth boundary. | Endpoint is internal and/or protected by an included authentication/authorization layer. | External auth/network boundaries are not represented in the bundle. |

## 4. Label record format

Each row in the human reference-label dataset should include:
- bundle_path, bundle_sha256, rule_id;
- label (PRESENT/ABSENT/U/NA);
- resource_kind, resource_name, container_name where applicable;
- yaml_document_index and evidence_path;
- rationale (one to three sentences);
- reviewer_id, review_timestamp, protocol_version;
- adjudication_status and adjudication_reason.

## 5. Independent review protocol

Two human reviewers independently label the same blinded sample. They must not see scanner candidates or AI-generated pre-labels during the independent pass. Lock labels before adjudication. Report raw agreement, class-wise agreement, a chance-corrected statistic with confidence intervals, and the disagreement/adjudication process.

AI-assisted triage can help locate evidence, but it must not be counted as a second human reviewer.
