# Phase 1 — Rules + Corpus Plan
## Hardening LLM Inference on Kubernetes: An Empirical Study of Production Serving Stacks
**Author intent:** Girish Mallya NIW independent research artifact  
**Status:** Phase 1 complete — 2026-10-28 (America/Los_Angeles)  
**Scope:** Public Helm charts + K8s manifests for LLM inference serving only (no employer-private configs)

---

## 1. Rule catalog (28 rules)

Detection baseline for all rules: `helm template` (default + tutorial values) → flatten YAML → static grep / Kyverno/Conftest/OPA / custom Python probes. Runtime checks are out of Phase 2 scope unless noted.

| ID | Name | Category | What to check (Helm/K8s YAML) | Why it matters for LLM serving | Severity | Detection | LLM-specific |
|---|---|---|---|---|---|---|---|
| LLM-AUTH-01 | Missing/disabled API key on OpenAI-compatible endpoint | Auth | `args`/`env` lack `--api-key` / `VLLM_API_KEY` / `HF_API_TOKEN` auth / gateway `Authorization`; values enable public OpenAI routes without key | Unauthenticated `/v1/chat/completions` enables model theft, prompt abuse, GPU DoS | Critical | Static: grep rendered Deployment/args/env; flag if Service exposes HTTP and no auth key/ref | yes |
| LLM-AUTH-02 | API key protects only `/v1*` — unprotected sibling routes | Auth | Chart leaves `/invocations`, `/pause`, `/tokenize`, `/update_weights`, etc. reachable; no reverse-proxy allowlist ConfigMap/Ingress path filter | vLLM docs: `--api-key` does **not** cover many inference/ops endpoints; `/invocations` bypasses auth | Critical | Static: Ingress/Gateway paths; args for `--api-key` without documented proxy allowlist annotation/`extraObjects` | yes |
| LLM-AUTH-03 | Tokenizer / admin / dev endpoints enabled | Auth | `--enable-tokenizer-info-endpoint`; `VLLM_SERVER_DEV_MODE=1`; profiler flags; TGI admin-like routes in values | Exposes chat templates / `/collective_rpc` / cache reset — RCE-class or config leak | Critical | Grep args/env in templates + values defaults | yes |
| LLM-AUTH-04 | Unrestricted CORS or empty auth middleware | Auth | Ingress/annotations `cors-allow-origin: *`; gateway CORS `*`; middleware disabled; OpenWebUI/LiteLLM `allow_origins=["*"]` | Browser-origin abuse of OpenAI-compatible APIs + credentialed XSS paths | High | Grep Ingress annotations, values `cors`, middleware CRDs | yes |
| LLM-AUTH-05 | Ingress without auth (basicAuth/oauth2/JWT/API gateway) | Auth | Ingress/HTTPRoute has no auth annotation, ExternalAuth, or API key plugin; Service is ClusterIP but Ingress is world-open | LLM endpoints often fronted by Ingress as “demo”; becomes public model API | Critical | Static: Ingress/HTTPRoute lacks auth-related annotations/filters | partially |
| LLM-NET-01 | Inference Service exposed as LoadBalancer/NodePort | Network | `service.type: LoadBalancer` or `NodePort` on vLLM/TGI/Ollama ports (8000/8080/11434) | Publishes GPU inference to cloud LB / node IP without cluster-internal gate | Critical | Grep Service `spec.type` in rendered output | yes |
| LLM-NET-02 | Missing NetworkPolicy for inference namespace/pods | Network | No NetworkPolicy selecting inference pods; default-allow cluster | Lateral movement to model pods; scrapers hit OpenAI ports from any pod | High | Check for NetworkPolicy in chart templates / optional dependency | no (impact yes) |
| LLM-NET-03 | No TLS on inference Ingress / Gateway | Network | Ingress `tls: []` empty; HTTPRoute no TLSRoute/Gateway HTTPS listener; `ssl` flags off | Cleartext prompts, API keys, model outputs on the wire | High | Ingress/Gateway TLS sections empty while ingress.enabled | no (impact yes) |
| LLM-NET-04 | Inter-node / distributed ports exposed cluster-wide | Network | Services expose torch.distributed / NCCL / KV-transfer / Ray GCS/dashboard (6379, 8265, 10001, kv-port) as ClusterIP-wide or LB | vLLM/Ray: inter-node & torch.distributed insecure by default; dashboard = RCE surface | Critical | Port/name heuristics on Services + hostNetwork | yes |
| LLM-NET-05 | hostNetwork / hostPID on inference pods | Network | `spec.hostNetwork: true`, `hostPID: true` | Bypasses NetworkPolicy; shares host PID/net with GPU node; escalates blast radius | Critical | Pod security fields | no |
| LLM-SEC-01 | Secrets plaintext in values.yaml / ConfigMap | Secrets | HF tokens, API keys, cloud keys as literal `stringData` in sample values or ConfigMap `data:` | Tokens in git + `helm get values` leak gated-model access | Critical | Pattern match `hf_`, `sk-`, `token:`, `apiKey:` outside Secret/secretKeyRef | yes |
| LLM-SEC-02 | Env vars not using secretKeyRef | Secrets | Container `env` uses `value:` for tokens instead of `valueFrom.secretKeyRef` | Same as above; common in tutorial YAMLs (Ray Serve samples often show placeholders) | High | AST: env entries matching token names without secretKeyRef | yes |
| LLM-SEC-03 | ServiceAccount over-permission / cluster-admin bind | Secrets | RoleBinding/ClusterRoleBinding to `cluster-admin` or wildcards `resources: ["*"]` for inference SA | Compromised model pod → full cluster | Critical | RBAC bind analysis | no |
| LLM-GPU-01 | Missing nvidia.com/gpu (or vendor) requests/limits | GPU/Isolation | GPU container lacks `resources.limits["nvidia.com/gpu"]` (or AMD/Intel equiv) | Scheduler overcommit; silent CPU fallback; noisy-neighbor GPU theft | High | Resource map check on containers with vllm/tgi/ollama images | yes |
| LLM-GPU-02 | GPU sharing / multi-tenant isolation gaps | GPU/Isolation | Multiple LLM Deployments request whole GPUs with no MIG/HAMi/`gpumem`/`gpucores`; shared node without device plugin isolation | KV-cache / weight side channels; DoS via VRAM exhaustion; CVE-class prefix-cache timing across tenants | High | Detect co-located GPU apps in samples; absence of HAMi resources or MIG | yes |
| LLM-GPU-03 | Privileged / dangerous capabilities for GPU access | GPU/Isolation | `privileged: true`, `capabilities.add: [SYS_ADMIN, SYS_PTRACE, ALL]`, unnecessary `/dev` hostPath | Often used as “GPU shortcut”; full node compromise | Critical | securityContext + hostPath to /dev | partially |
| LLM-WL-01 | Missing runAsNonRoot | Workload Security | No `securityContext.runAsNonRoot: true` / runAsUser>0 | Root in model container + writable model cache = supply-chain write | High | Pod/container securityContext | no |
| LLM-WL-02 | Missing readOnlyRootFilesystem | Workload Security | `readOnlyRootFilesystem` unset/false without documented emptyDir exceptions | Writable root aids persistence after image compromise | Medium | securityContext | no |
| LLM-WL-03 | allowPrivilegeEscalation not false | Workload Security | unset or `true` | Standard K8s hardening; critical when combined with GPU privileged patterns | High | securityContext | no |
| LLM-WL-04 | Missing seccomp / AppArmor | Workload Security | No `seccompProfile.type: RuntimeDefault` (or localhost); no AppArmor/SELinux profile | Increases exploitability of inference binary vulns | Medium | pod security fields / annotations | no |
| LLM-WL-05 | Image tag `:latest` / no digest | Workload Security | `image: ...:latest` or tag without `@sha256:` | Non-reproducible supply chain; silent malicious retag | High | Image reference regex | no |
| LLM-STOR-01 | Model PVC world-readable / RW by any pod | Storage/Model | PVC `accessModes: ReadWriteMany` + no NetworkPolicy; shared cache PV without fsGroup restrictions; mode 0777 in docs | Model weights / HF cache are high-value IP; writable cache can plant code (vLLM cache trust model) | High | PVC accessModes + Pod volumeMounts sharing; notes in README | yes |
| LLM-STOR-02 | Cache / HF home on untrusted volume | Storage/Model | Mount of hostPath or RWX NFS to `~/.cache/vllm` / huggingface without ownership controls | vLLM: cache dirs trusted; untrusted write → code exec via compile cache | Critical | Volume types + mount paths heuristics | yes |
| LLM-STOR-03 | Model download initContainer with excess privilege | Storage/Model | Init containers privileged / root / hostPath while fetching HF models | Download path is common foothold; tokens in env | High | initContainers securityContext + env | yes |
| LLM-RES-01 | Missing CPU/memory requests/limits | Resources | No requests/limits on inference containers | Node pressure evicts long-loading model pods mid-download | High | resources block | no |
| LLM-RES-02 | Missing PodDisruptionBudget | Resources | No PDB for inference Deployment/StatefulSet with replicas≥1 in “production” charts | GPU serving: voluntary disruption drops availability; cold-start minutes–hours | Medium | Presence of PDB template | partially |
| LLM-RES-03 | Missing readiness / startup probes | Resources | No readinessProbe/startupProbe on inference container (or only liveness hitting heavy path) | Traffic to unloaded model → 5xx storms; liveness-only kills slow loads | High | Probe fields; warn if only liveness | yes |
| LLM-OBS-01 | Metrics / dashboard exposed without auth | Observability | ServiceMonitor + Service for `/metrics`, Grafana, Ray dashboard on LB/Ingress without auth | Info leak (queue depth, model names); Ray dashboard is control plane | High | Services named metrics/dashboard + type/ingress | yes |

### Coverage checklist vs brief

| Required theme | Rule IDs |
|---|---|
| Missing/disabled API key on OpenAI-compatible endpoints | LLM-AUTH-01, LLM-AUTH-02 |
| Inference HTTP without NetworkPolicy or ingress auth | LLM-NET-02, LLM-AUTH-05 |
| LoadBalancer/NodePort on vLLM/TGI ports | LLM-NET-01 |
| Privileged / hostNetwork / hostPID / capabilities | LLM-NET-05, LLM-GPU-03 |
| Missing securityContext (runAsNonRoot, RO root, allowPrivilegeEscalation) | LLM-WL-01..03 |
| Missing resource requests/limits especially GPU | LLM-GPU-01, LLM-RES-01 |
| GPU sharing / multi-tenant isolation (HAMi-style) | LLM-GPU-02 |
| Model weights / PVC world-readable or writable | LLM-STOR-01, LLM-STOR-02 |
| Secrets in values plaintext vs Secret refs | LLM-SEC-01, LLM-SEC-02 |
| ServiceAccount over-permission | LLM-SEC-03 |
| Missing PDB / readiness | LLM-RES-02, LLM-RES-03 |
| Tokenizer/dev/admin endpoints (vLLM security docs) | LLM-AUTH-03 |
| No TLS on inference ingress | LLM-NET-03 |
| Unrestricted CORS / empty auth middleware | LLM-AUTH-04 |
| Image `:latest` / no digest | LLM-WL-05 |
| Missing seccomp/AppArmor | LLM-WL-04 |

Primary LLM-doc anchor: https://github.com/vllm-project/vllm/blob/main/docs/usage/security.md (API key path limits; tokenizer-info; `VLLM_SERVER_DEV_MODE`; cache trust; multi-tenant / prefix-cache).

---

## 2. Corpus collection plan

### 2.1 Named public sources (verified unless marked candidate)

| # | Source | Type | URL | Status |
|---|---|---|---|---|
| 1 | vLLM Production Stack Helm (`vllm-stack`) | Official Helm | https://github.com/vllm-project/production-stack — chart under `helm/`; Artifact Hub: https://artifacthub.io/packages/helm/vllm-production-stack/vllm-stack ; repo add `https://vllm-project.github.io/production-stack` | **Verified** (chart ≥0.1.13 as of 2026-09) |
| 2 | vLLM production-stack tutorials values | Official values | `tutorials/assets/values-*.yaml` in same repo | **Verified** |
| 3 | KServe core + charts | Official | https://github.com/kserve/kserve ; Helm OCI `oci://ghcr.io/kserve/charts/kserve-resources` (e.g. v0.20.0 documented) | **Verified** |
| 4 | KServe GenAI InferenceService examples | Official docs/YAML | https://kserve.github.io/website/docs/getting-started/genai-first-isvc ; text-generation docs | **Verified** |
| 5 | KubeRay operator Helm | Official | https://github.com/ray-project/kuberay-helm ; `helm repo add kuberay https://ray-project.github.io/kuberay-helm/` | **Verified** |
| 6 | Ray Serve LLM K8s samples | Official manifests | https://github.com/ray-project/kuberay/tree/master/ray-operator/config/samples — e.g. `ray-service.llm-serve.yaml`, `ray-service.deepseek.yaml`, `ray-service.high-throughput-llm.yaml` ; docs https://docs.ray.io/en/latest/cluster/kubernetes/examples/rayserve-llm-example.html | **Verified** |
| 7 | Hugging Face TGI | Engine (no official Helm) | https://github.com/huggingface/text-generation-inference — HF declined official Helm (PR #1461) | **Verified** (engine + k8s guidance only) |
| 8 | TGI community chart (shalb) | Community Helm | https://github.com/shalb/charts/tree/main/huggingface-model ; OCI `oci://registry-1.docker.io/shalb/huggingface-model` | **Verified** |
| 9 | TGI OPEA chart | Project Helm | `oci://ghcr.io/opea-project/charts/tgi` — docs https://opea-project.github.io/latest/GenAIComps/comps/third_parties/tgi/deployment/kubernetes/README.html | **Verified** |
| 10 | TGI helm (louis030195) | Community Helm | https://github.com/louis030195/text-generation-inference-helm | **Verified** (stale; include with date pin) |
| 11 | Infracloud vLLM chart | Community Artifact Hub | https://artifacthub.io/packages/helm/infracloud-charts/vllm | **Verified** |
| 12 | Infracloud TGI chart | Community Artifact Hub | https://artifacthub.io/packages/helm/infracloud-charts/text-generation-inference | **Verified** |
| 13 | Ollama Helm (otwld) | Community | https://github.com/otwld/ollama-helm ; Artifact Hub https://artifacthub.io/packages/helm/ollama-helm/ollama ; `helm repo add otwld https://helm.otwld.com/` | **Verified** |
| 14 | HAMi GPU sharing + vLLM example | Official | https://github.com/Project-HAMi/HAMi — `examples/nvidia/vllm_cross_vgpu.yaml`, sharing examples; Helm `https://project-hami.github.io/HAMi/` | **Verified** |
| 15 | SGLang official K8s manifest | Official raw YAML | https://github.com/sgl-project/sglang/blob/master/docker/k8s-sglang-service.yaml | **Verified** |
| 16 | LiteLLM Helm | Community Artifact Hub | https://artifacthub.io/packages/helm/litellm/litellm-helm | **Verified** (gateway in front of inference — include for AUTH/CORS rules) |
| 17 | NVIDIA NIM Operator chart | Vendor | Artifact Hub / NGC k8s-nim-operator | **Candidate** — confirm license + public values before scrape |
| 18 | AMD/SiloGen SGLang Helm | Vendor docs | https://silogen.github.io/ai-workloads/workloads/llm-inference-sglang/helm/ | **Candidate** |
| 19 | Open WebUI Helm (if paired with Ollama) | Community | search Artifact Hub `open-webui` | **Candidate** — only if it deploys/alongside inference |

### 2.2 Inclusion criteria

- Publicly licensed (Apache-2.0/MIT/BSD preferred); chart or manifest must be fetchable without login.
- Deploys or fronts **LLM inference** (vLLM, TGI, SGLang, Ollama, KServe GenAI ISVC, Ray Serve LLM, LiteLLM→backends).
- Kubernetes-native: Helm chart and/or raw Deployment/Service/Ingress/RayService/InferenceService YAML.
- English README or values comments sufficient to identify default exposure posture.

### 2.3 Exclusion criteria

- Closed-source / NGC-only tarball requiring entitlements (unless a public values example exists).
- Pure training / fine-tune operators (Kubeflow training) without serving API.
- Non-K8s (docker-compose-only) unless a K8s sibling exists.
- Forks that only bump image tags of an already-included chart (dedupe by Chart.yaml `home` + template hash).
- Employer-internal or private Gists.

### 2.4 Version pinning strategy

1. Record `git clone --depth 1` + full commit SHA for Git sources; store in `corpus/SOURCES.lock.json`.
2. For Helm repos: `helm pull <chart> --version X.Y.Z` and keep `.tgz` + `Chart.yaml` version.
3. For OCI: pin digest if available (`helm pull oci://... --version`).
4. Freeze date field `collected_at` (America/Los_Angeles).
5. Re-render only on intentional corpus refresh (document delta in CHANGELOG).

### 2.5 How to render Helm with default values

```bash
# Example pattern (per chart)
helm repo add vllm https://vllm-project.github.io/production-stack
helm repo update
helm pull vllm/vllm-stack --version 0.1.13 --untar -d corpus/charts/vllm-stack-0.1.13
helm template scan-release ./corpus/charts/vllm-stack-0.1.13 \
  --namespace llm-scan \
  > corpus/rendered/vllm-stack-0.1.13/default.yaml
# Also render each tutorial values file:
helm template scan-release ./corpus/charts/vllm-stack-0.1.13 \
  -f tutorials/assets/values-01-minimal-example.yaml \
  > corpus/rendered/vllm-stack-0.1.13/values-01-minimal.yaml
```

For raw manifests: copy as-is into `corpus/manifests/<project>/` and normalize with `kubectl neat` optional (do not mutate security fields).

### 2.6 Expected corpus size

- **Target: 40–70** distinct chart versions / manifest bundles (sweet spot inside 30–80).
- Rough mix: ~8–12 official (vLLM stack + tutorials, KServe ISVC set, KubeRay samples, HAMi, SGLang); ~15–25 community Artifact Hub charts; ~10–20 tutorial/example YAMLs.
- Unit of analysis = one rendered release (default values) + optional named value overlays (count overlays separately in tables).

---

## 3. Proposed public repo layout

```text
llm-serving-k8s-hardening-study/
├── README.md                 # abstract, citation, ethics, how to reproduce
├── LICENSE                   # Apache-2.0 recommended
├── CITATION.cff
├── docs/
│   ├── PHASE1_RULES_AND_CORPUS.md   # this document
│   ├── threat-model.md
│   ├── related-work.md
│   └── paper/                # arXiv LaTeX later
├── rules/
│   ├── catalog.yaml          # machine-readable 28 rules
│   ├── probes/               # Python/Rego/Conftest
│   └── fixtures/             # tiny positive/negative YAML
├── corpus/
│   ├── SOURCES.lock.json
│   ├── charts/               # pulled chart trees / tgz
│   ├── manifests/            # raw upstream YAML
│   └── rendered/             # helm template outputs (may be large; git-lfs or generate in CI)
├── scripts/
│   ├── fetch_corpus.sh
│   ├── render_all.sh
│   ├── scan.py
│   └── aggregate_results.py
├── results/
│   ├── findings.csv
│   ├── per-rule-prevalence.json
│   └── figures/
├── upstream-prs/             # notes + links to hardening PRs filed
└── .github/workflows/ci.yml  # render+scan on schedule (no GPU needed)
```

---

## 4. Week-by-week execution (Phase 2+)

Assumes Phase 1 done (this doc). Calendar relative to kickoff week.

| Week | Focus | Exit criteria |
|---|---|---|
| **2** | Corpus fetch + render | `SOURCES.lock.json` complete; ≥40 rendered bundles; CI script green |
| **3** | Implement probes for all 28 rules; dry-run on vLLM stack + one TGI chart | Per-rule true-positive fixtures; first prevalence table |
| **4** | Full corpus scan; severity-weighted scoring; figures (heatmap by stack × category) | `results/findings.csv` frozen v1; draft Related Work vs general Helm misconfig papers |
| **5** | Qualitative case studies (3–5): e.g. vLLM API-key gaps, LB defaults, HAMi isolation, Ray dashboard exposure; draft upstream issues/PRs | ≥2 draft PRs or issues opened against production-stack / charts / docs |
| **6** | arXiv draft (cs.CR / cs.AI / cs.SE); abstract with national-interest one-liner; publish preprint; update NIW Profile Builder checklist | arXiv ID; canvas checklist flip when posted |

Stretch (week 7–8): workshop CFP submit; expand corpus refresh; Kubescape/Checkov rule upstream if patterns map cleanly.

---

## 5. Ethics / independence notes

- Public configs only — no Microsoft/Amazon internal manifests.
- Disclose when scanning **tutorial** defaults (expected insecure) vs charts marketed as production.
- Responsible disclosure before naming unpatched Critical findings in non-demo charts; prefer upstream PR.
