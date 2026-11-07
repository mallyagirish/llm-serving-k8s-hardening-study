import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "scan_candidates.py"
spec = importlib.util.spec_from_file_location("scan_candidates", SCRIPT)
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


class CandidateScannerTests(unittest.TestCase):
    def scan_text(self, text):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "input.yaml"
            p.write_text(text, encoding="utf-8")
            return scanner.scan_file(p)

    def test_llm_deployment_emits_static_candidates(self):
        rows = self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: vllm-api}
spec:
  selector: {matchLabels: {app: vllm-api}}
  template:
    metadata: {labels: {app: vllm-api}}
    spec:
      hostNetwork: true
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        securityContext: {privileged: true}
""")
        ids = {r["rule_id"] for r in rows}
        self.assertIn("LLM-NET-05", ids)
        self.assertIn("LLM-GPU-03", ids)
        self.assertIn("LLM-WL-05", ids)
        self.assertIn("LLM-WL-03", ids)
        self.assertTrue(all(r["status"] == "candidate_for_human_review" for r in rows))

    def test_dangerous_capabilities_and_host_device_mount_are_candidates(self):
        rows = self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: vllm-api}
spec:
  template:
    spec:
      volumes:
      - name: gpu-devices
        hostPath: {path: /dev}
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        securityContext:
          capabilities:
            add: ["SYS_ADMIN"]
""")
        gpu_rows = [r for r in rows if r["rule_id"] == "LLM-GPU-03"]
        self.assertEqual(len(gpu_rows), 2)

    def test_non_llm_host_device_mount_is_not_flagged(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: ordinary-worker}
spec:
  volumes:
  - name: host-dev
    hostPath: {path: /dev}
  containers:
  - name: worker
    image: nginx:1.27
""")
        self.assertEqual(rows, [])

    def test_literal_token_env_is_flagged_without_leaking_value(self):
        secret = "hf_super_secret_value_123"
        rows = self.scan_text(f"""
apiVersion: v1
kind: Pod
metadata: {{name: vllm-api}}
spec:
  containers:
  - name: vllm
    image: vllm/vllm-openai:latest
    env:
    - name: HUGGING_FACE_HUB_TOKEN
      value: {secret}
""")
        row = next(r for r in rows if r["rule_id"] == "LLM-SEC-02")
        self.assertIn("HUGGING_FACE_HUB_TOKEN", row["evidence"])
        self.assertNotIn(secret, str(row))

    def test_placeholder_token_env_is_not_flagged(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: vllm-api}
spec:
  containers:
  - name: vllm
    image: vllm/vllm-openai:latest
    env:
    - name: HUGGING_FACE_HUB_TOKEN
      value: YOUR_HF_TOKEN
""")
        self.assertNotIn("LLM-SEC-02", {r["rule_id"] for r in rows})

    def test_missing_seccomp_profile_is_candidate(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: vllm-api}
spec:
  containers:
  - name: vllm
    image: vllm/vllm-openai:latest
""")
        self.assertIn("LLM-WL-04", {r["rule_id"] for r in rows})

    def test_gpu_engine_without_gpu_resource_is_candidate(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: vllm-api}
spec:
  containers:
  - name: vllm
    image: vllm/vllm-openai:latest
    resources:
      requests: {cpu: "2", memory: "8Gi"}
      limits: {cpu: "4", memory: "16Gi"}
""")
        self.assertIn("LLM-GPU-01", {r["rule_id"] for r in rows})

    def test_gpu_engine_with_vendor_gpu_resource_is_not_candidate(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: vllm-api}
spec:
  containers:
  - name: vllm
    image: vllm/vllm-openai:latest
    resources:
      limits: {nvidia.com/gpu: 1}
""")
        self.assertNotIn("LLM-GPU-01", {r["rule_id"] for r in rows})

    def test_llm_ingress_without_tls_is_candidate(self):
        rows = self.scan_text("""
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata: {name: vllm-api}
spec:
  rules:
  - host: llm.example.test
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: vllm-api
            port: {number: 8000}
""")
        self.assertIn("LLM-NET-03", {r["rule_id"] for r in rows})

    def test_non_llm_deployment_is_not_scanned(self):
        self.assertEqual(self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: ordinary-web}
spec:
  selector: {matchLabels: {app: ordinary-web}}
  template:
    metadata: {labels: {app: ordinary-web}}
    spec:
      containers:
      - name: web
        image: nginx:1.27
"""), [])

    def test_container_false_overrides_pod_true_for_run_as_non_root(self):
        rows = self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: vllm-api}
spec:
  selector: {matchLabels: {app: vllm}}
  template:
    metadata: {labels: {app: vllm}}
    spec:
      securityContext: {runAsNonRoot: true}
      containers:
      - name: vllm
        image: vllm/vllm-openai@sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa
        securityContext: {runAsNonRoot: false, allowPrivilegeEscalation: false, readOnlyRootFilesystem: true}
""")
        ids = {r["rule_id"] for r in rows}
        self.assertIn("LLM-WL-01", ids)
        self.assertNotIn("LLM-WL-03", ids)
        self.assertNotIn("LLM-WL-05", ids)

    def test_cronjob_nested_pod_template_is_scanned(self):
        rows = self.scan_text("""
apiVersion: batch/v1
kind: CronJob
metadata: {name: llm-cache-maintenance}
spec:
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: llm-maintenance
            image: example/llm-maintenance:1.0
""")
        self.assertIn("LLM-WL-01", {r["rule_id"] for r in rows})

    def test_namespace_argument_does_not_make_hami_operator_an_llm_workload(self):
        rows = self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: scan-hami-scheduler, labels: {app.kubernetes.io/name: hami}}
spec:
  selector: {matchLabels: {app: hami}}
  template:
    metadata: {labels: {app: hami}}
    spec:
      containers:
      - name: kube-scheduler
        image: registry.example/kube-scheduler:v1
        args: ["--leader-election-namespace=llm-scan"]
""")
        self.assertEqual(rows, [])

    def test_generic_inference_container_is_not_assumed_to_be_llm(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: npod}
spec:
  containers:
  - name: npod
    image: public.ecr.aws/neuron/pytorch-inference-neuron:1.13.1
""")
        self.assertEqual(rows, [])

    def test_llm_finetuning_workload_is_not_inference(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: model-finetune}
spec:
  containers:
  - name: trainer
    image: registry.example/llm-finetune:latest
""")
        self.assertEqual(rows, [])

    def test_sidecar_is_not_mislabeled_as_inference_container(self):
        rows = self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: vllm-api}
spec:
  selector: {matchLabels: {app: vllm-api}}
  template:
    metadata: {labels: {app: vllm-api}}
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
      - name: metrics-sidecar
        image: prom/statsd-exporter:v0.27
""")
        self.assertTrue(rows)
        self.assertNotIn("metrics-sidecar", {r["container_name"] for r in rows})


    def test_llm_inference_service_crd_is_scanned(self):
        rows = self.scan_text("""
apiVersion: serving.kserve.io/v1alpha1
kind: LLMInferenceService
metadata: {name: qwen-llm}
spec:
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d-cuda:v0.9.0
      resources:
        limits: {nvidia.com/gpu: "1"}
""")
        self.assertIn("LLM-WL-01", {r["rule_id"] for r in rows})
        self.assertIn("LLM-WL-02", {r["rule_id"] for r in rows})

    def test_ray_service_worker_containers_are_scanned(self):
        rows = self.scan_text("""
apiVersion: ray.io/v1
kind: RayService
metadata: {name: deepseek-r1}
spec:
  rayClusterConfig:
    workerGroupSpecs:
    - groupName: gpu
      template:
        spec:
          securityContext: {runAsNonRoot: true}
          containers:
          - name: ray-worker
            image: rayproject/ray-llm:2.52.0
            securityContext: {allowPrivilegeEscalation: false}
            resources:
              limits: {nvidia.com/gpu: "1"}
""")
        ids = {r["rule_id"] for r in rows}
        self.assertNotIn("LLM-WL-01", ids)
        self.assertIn("LLM-WL-02", ids)

    def test_helm_test_connection_pod_is_excluded_from_serving_checks(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: scan-vllm-test-connection}
spec:
  containers:
  - name: wget
    image: busybox
""")
        self.assertEqual(rows, [])

    def test_migration_job_secret_is_detected_but_workload_hardening_is_not(self):
        rows = self.scan_text("""
apiVersion: batch/v1
kind: Job
metadata: {name: scan-litellm-migrations}
spec:
  template:
    spec:
      containers:
      - name: prisma-migrations
        image: ghcr.io/berriai/litellm:v1.85.1
        env:
        - name: DATABASE_URL
          value: postgresql://user:password@db/litellm
""")
        ids = {r["rule_id"] for r in rows}
        self.assertIn("LLM-SEC-02", ids)
        self.assertNotIn("LLM-WL-01", ids)
        self.assertNotIn("LLM-RES-03", ids)

    def test_redacted_secret_placeholder_is_not_flagged(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: sglang-api}
spec:
  containers:
  - name: sglang
    image: lmsysorg/sglang:latest
    env:
    - name: HF_TOKEN
      value: "<secret>"
""")
        self.assertNotIn("LLM-SEC-02", {r["rule_id"] for r in rows})

    def test_huggingface_offline_flag_is_not_a_secret(self):
        rows = self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: huggingface-model}
spec:
  template:
    spec:
      containers:
      - name: mongodb
        image: bitnami/mongodb:7
        env:
        - name: HUGGINGFACE_OFFLINE
          value: "false"
""")
        self.assertNotIn("LLM-SEC-02", {r["rule_id"] for r in rows})

    def test_remote_gpu_resource_is_recognized(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: vllm-remote-gpu}
spec:
  containers:
  - name: vllm
    image: vllm/vllm-openai:latest
    resources:
      limits:
        nvidia.com/remote-gpu: 2
        nvidia.com/remote-gpu-memory: 20480
""")
        self.assertNotIn("LLM-GPU-01", {r["rule_id"] for r in rows})

    def test_init_container_does_not_create_missing_probe_candidate(self):
        rows = self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: vllm-api}
spec:
  template:
    spec:
      initContainers:
      - name: vllm-init
        image: vllm/vllm-openai:latest
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        readinessProbe:
          httpGet: {path: /health, port: 8000}
""")
        self.assertNotIn("LLM-RES-03", {r["rule_id"] for r in rows})


    def test_llm_inference_service_config_nested_prefill_template_is_scanned(self):
        rows = self.scan_text("""
apiVersion: serving.kserve.io/v1alpha2
kind: LLMInferenceServiceConfig
metadata: {name: llm-config}
spec:
  prefill:
    template:
      containers:
      - name: main
        image: ghcr.io/llm-d/llm-d-cuda:v0.9.0
  decode:
    template:
      containers:
      - name: main
        image: vllm/vllm-openai:v0.31.0
""")
        ids = {r["rule_id"] for r in rows}
        self.assertIn("LLM-WL-01", ids)
        self.assertIn("LLM-WL-05", ids)

    def test_cluster_serving_runtime_with_huggingface_annotation_is_scanned(self):
        rows = self.scan_text("""
apiVersion: serving.kserve.io/v1alpha1
kind: ClusterServingRuntime
metadata:
  name: kserve-huggingfaceserver
  annotations:
    serving.kserve.io/server-type: huggingfaceserver
spec:
  containers:
  - name: kserve-container
    image: huggingfaceserver:replace
""")
        self.assertIn("LLM-WL-05", {r["rule_id"] for r in rows})

    def test_cpu_only_vllm_sample_does_not_get_gpu_candidate(self):
        rows = self.scan_text("""
apiVersion: serving.kserve.io/v1alpha2
kind: LLMInferenceService
metadata: {name: facebook-opt-125m-cpu}
spec:
  template:
    containers:
    - name: main
      image: vllm/vllm-openai:latest
""")
        self.assertNotIn("LLM-GPU-01", {r["rule_id"] for r in rows})

    def test_tpu_ray_service_does_not_get_gpu_candidate(self):
        rows = self.scan_text("""
apiVersion: ray.io/v1
kind: RayService
metadata: {name: vllm-tpu}
spec:
  rayClusterConfig:
    workerGroupSpecs:
    - template:
        spec:
          containers:
          - name: ray-worker
            image: "$VLLM_IMAGE"
            resources:
              limits: {google.com/tpu: "8"}
""")
        self.assertNotIn("LLM-GPU-01", {r["rule_id"] for r in rows})


    def test_router_scheduler_helper_template_is_not_scanned_as_inference_container(self):
        rows = self.scan_text("""
apiVersion: serving.kserve.io/v1alpha2
kind: LLMInferenceServiceConfig
metadata: {name: llm-config}
spec:
  template:
    containers:
    - name: main
      image: ghcr.io/llm-d/llm-d-cuda:v0.9.0
      securityContext: {runAsNonRoot: true}
      readinessProbe:
        httpGet: {path: /health, port: 8000}
  router:
    scheduler:
      template:
        containers:
        - name: main
          image: ghcr.io/llm-d/llm-d-router-endpoint-picker:v1.0.0
""")
        ids = {r["rule_id"] for r in rows}
        self.assertNotIn("LLM-WL-01", ids)
        self.assertNotIn("LLM-RES-03", ids)

    def test_boolean_allow_empty_password_is_not_a_literal_secret(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: litellm-api}
spec:
  containers:
  - name: litellm
    image: ghcr.io/berriai/litellm:v1.85.1
    env:
    - name: ALLOW_EMPTY_PASSWORD
      value: "no"
""")
        self.assertNotIn("LLM-SEC-02", {r["rule_id"] for r in rows})

    def test_master_key_literal_is_a_secret_candidate(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: litellm-api}
spec:
  containers:
  - name: litellm
    image: ghcr.io/berriai/litellm:v1.85.1
    env:
    - name: PROXY_MASTER_KEY
      value: sk-test-literal-value
""")
        self.assertIn("LLM-SEC-02", {r["rule_id"] for r in rows})

    def test_secrets_config_version_is_not_a_secret_candidate(self):
        rows = self.scan_text("""
apiVersion: v1
kind: Pod
metadata: {name: vllm-api}
spec:
  containers:
  - name: vllm
    image: vllm/vllm-openai:latest
    env:
    - name: KSERVE_PULL_SECRETS_CONFIG_VERSION
      value: "1"
""")
        self.assertNotIn("LLM-SEC-02", {r["rule_id"] for r in rows})


if __name__ == "__main__":
    unittest.main()
