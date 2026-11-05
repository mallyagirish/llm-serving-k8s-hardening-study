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
metadata:
  name: vllm-api
spec:
  selector:
    matchLabels: {app: vllm-api}
  template:
    metadata:
      labels: {app: vllm-api}
    spec:
      hostNetwork: true
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        securityContext:
          privileged: true
""")
        ids = {r["rule_id"] for r in rows}
        self.assertIn("LLM-NET-05", ids)
        self.assertIn("LLM-GPU-03", ids)
        self.assertIn("LLM-WL-05", ids)
        self.assertIn("LLM-WL-03", ids)
        self.assertTrue(all(r["status"] == "candidate_for_human_review" for r in rows))

    def test_non_llm_deployment_is_not_scanned(self):
        self.assertEqual(self.scan_text("""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ordinary-web
spec:
  selector:
    matchLabels: {app: ordinary-web}
  template:
    metadata:
      labels: {app: ordinary-web}
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
        self.assertIn("LLM-WL-01", {r["rule_id"] for r in rows})
        self.assertNotIn("LLM-WL-03", {r["rule_id"] for r in rows})
        self.assertNotIn("LLM-WL-05", {r["rule_id"] for r in rows})

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


if __name__ == "__main__":
    unittest.main()
