import importlib.util
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "build_workload_inventory.py"
spec = importlib.util.spec_from_file_location("build_workload_inventory", SCRIPT)
inventory = importlib.util.module_from_spec(spec)
spec.loader.exec_module(inventory)


class WorkloadInventoryTests(unittest.TestCase):
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

    def test_finetuning_is_not_primary_inference(self):
        stratum, _ = inventory.propose_stratum(
            "Pod", "llm-finetune trainer registry/llm-finetune:latest", "hami", "hami-example.yaml"
        )
        self.assertEqual(stratum, "supporting_platform_candidate")

    def test_generic_kserve_control_plane_is_supporting(self):
        stratum, _ = inventory.propose_stratum(
            "Deployment", "kserve-controller-manager controller image", "kserve", "kserve.yaml"
        )
        self.assertEqual(stratum, "supporting_platform_candidate")


if __name__ == "__main__":
    unittest.main()
