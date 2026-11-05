import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_workload_inventory.py"
spec = importlib.util.spec_from_file_location("build_workload_inventory", SCRIPT)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class WorkloadInventoryTests(unittest.TestCase):
    def test_upstream_project_mapping_groups_versions_and_repositories(self):
        self.assertEqual(
            inventory.upstream_project_for_bundle("rendered/vllm-stack-0.1.13/default.yaml"),
            "vllm-project/production-stack",
        )
        self.assertEqual(
            inventory.upstream_project_for_bundle("rendered/kserve-v0.15.0/default.yaml"),
            "kserve/kserve",
        )

    def test_cronjob_pod_template_is_extracted(self):
        pod = inventory.get_pod_spec({
            "kind": "CronJob",
            "spec": {"jobTemplate": {"spec": {"template": {"spec": {
                "containers": [{"name": "vllm", "image": "vllm/vllm-openai:latest"}]
            }}}}}
        })
        self.assertEqual(pod["containers"][0]["name"], "vllm")

    def test_llm_inference_service_is_primary_candidate(self):
        stratum, _ = inventory.propose_stratum(
            "LLMInferenceService", "prod-llm", "kserve", "rendered/test.yaml"
        )
        self.assertEqual(stratum, "primary_candidate")

    def test_llm_inference_service_config_is_primary_candidate(self):
        stratum, _ = inventory.propose_stratum(
            "LLMInferenceServiceConfig", "decode-config", "kserve", "llmisvc.yaml"
        )
        self.assertEqual(stratum, "primary_candidate")

    def test_finetuning_is_not_primary_inference(self):
        stratum, _ = inventory.propose_stratum(
            "Pod", "llm-finetune trainer registry/llm-finetune:latest", "hami", "hami-example.yaml"
        )
        self.assertEqual(stratum, "supporting_platform_candidate")

    def test_generic_neuron_inference_pod_is_not_primary_llm(self):
        stratum, _ = inventory.propose_stratum(
            "Pod", "npod public.ecr.aws/neuron/pytorch-inference-neuron:1.13.1", "hami", "hami-example.yaml"
        )
        self.assertEqual(stratum, "supporting_platform_candidate")

    def test_generic_controller_in_llm_chart_is_not_primary(self):
        stratum, _ = inventory.propose_stratum(
            "Deployment", "hami scheduler kube-scheduler image", "vllm-stack", "vllm-stack.yaml"
        )
        self.assertEqual(stratum, "supporting_platform_candidate")

    def test_helm_test_connection_pod_is_not_primary(self):
        stratum, _ = inventory.propose_stratum(
            "Pod", "scan-vllm-test-connection wget busybox", "vllm-chart", "vllm.yaml"
        )
        self.assertEqual(stratum, "supporting_platform_candidate")

    def test_generic_kserve_control_plane_is_supporting(self):
        stratum, _ = inventory.propose_stratum(
            "Deployment", "kserve-controller-manager controller image", "kserve", "kserve.yaml"
        )
        self.assertEqual(stratum, "supporting_platform_candidate")

    def test_bundle_review_aggregates_resource_candidates(self):
        rows = [
            {"bundle_path": "rendered/a.yaml", "proposed_stratum": "primary_candidate", "resource_kind": "Deployment", "resource_name": "vllm"},
            {"bundle_path": "rendered/a.yaml", "proposed_stratum": "supporting_platform_candidate", "resource_kind": "Service", "resource_name": "gateway"},
        ]
        bundles = [
            {"path": "rendered/a.yaml", "source": "vllm", "kind": "helm-default"},
            {"path": "rendered/b.yaml", "source": "generic", "kind": "manifest"},
            {"path": "rendered/bad.yaml", "source": "kserve", "kind": "manifest"},
        ]
        reviewed = inventory.build_bundle_review(rows, {"bundles": bundles}, {"rendered/bad.yaml"})
        self.assertEqual(reviewed[0]["preliminary_bundle_stratum"], "primary_candidate")
        self.assertEqual(reviewed[0]["primary_resource_candidates"], 1)
        self.assertEqual(reviewed[1]["preliminary_bundle_stratum"], "non_llm_or_unclear")
        self.assertEqual(reviewed[2]["preliminary_bundle_stratum"], "exclude_pending")

    def test_build_inventory_writes_resource_records_from_locked_bundle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "corpus" / "rendered").mkdir(parents=True)
            yaml_path = root / "corpus" / "rendered" / "test.yaml"
            yaml_path.write_text("""
apiVersion: apps/v1
kind: Deployment
metadata: {name: vllm-api}
spec:
  template:
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
""", encoding="utf-8")
            lock_path = root / "lock.json"
            lock_path.write_text(json.dumps({
                "bundles": [{"path": "rendered/test.yaml", "source": "vllm-stack", "kind": "helm-default"}]
            }), encoding="utf-8")
            rows, summary = inventory.build_inventory(root, lock_path)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["proposed_stratum"], "primary_candidate")
            self.assertEqual(summary["resource_records"], 1)


if __name__ == "__main__":
    unittest.main()
