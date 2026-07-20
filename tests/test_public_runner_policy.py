from __future__ import annotations

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class PublicRunnerPolicyTest(unittest.TestCase):
    def setUp(self) -> None:
        self.workflow = (ROOT / ".github/workflows/run-private-validator.yml").read_text()
        self.contract = (ROOT / "00_contracts/PUBLIC_RUNNER_CENTER_CONTRACT_v01.md").read_text()
        self.allowlist = json.loads((ROOT / "00_contracts/GATE_ALLOWLIST_v01.json").read_text())
        self.gate_script = (ROOT / "scripts/run_allowlisted_gate.sh").read_text()
        self.status_script = (ROOT / "scripts/write_private_commit_status.sh").read_text()
        self.comment_script = (ROOT / "scripts/write_private_pr_comment.sh").read_text()

    def test_workflow_is_manual_and_read_only(self) -> None:
        self.assertIn("workflow_dispatch:", self.workflow)
        for forbidden in ("pull_request:", "pull_request_target:", "push:", "schedule:", "repository_dispatch:"):
            self.assertNotIn(forbidden, self.workflow)
        self.assertRegex(self.workflow, r"permissions:\n  contents: read")
        self.assertNotIn("upload-artifact", self.workflow)
        self.assertNotIn("actions/cache@", self.workflow)
        self.assertNotIn("command:", self.workflow)

    def test_official_actions_are_full_sha_pinned(self) -> None:
        pins = re.findall(r"uses:\s+([^@\s]+)@([0-9a-f]{40})", self.workflow)
        self.assertGreaterEqual(len(pins), 5)
        self.assertNotRegex(self.workflow, r"uses:\s+[^\s]+@(v\d+|main|master)\b")

    def test_allowlist_has_only_two_fixed_gates(self) -> None:
        self.assertFalse(self.allowlist["source_of_truth"])
        self.assertFalse(self.allowlist["arbitrary_command_input_allowed"])
        self.assertFalse(self.allowlist["private_content_public_exposure_allowed"])
        self.assertEqual(self.allowlist["public_artifacts_default"], "none")
        self.assertEqual(
            [g["gate_id"] for g in self.allowlist["gates"]],
            ["LOVEBOX_PUBLIC_RUNNER_SMOKE_V01", "LOVEBOX_P1_OC_EXACT_HEAD_V01"],
        )

    def test_exact_private_binding_and_no_eval(self) -> None:
        self.assertIn("TheGor-365/lovebox", self.workflow)
        self.assertIn("prod/lovebox-prod-dev-001-oc-baseline", self.workflow)
        self.assertIn(r"^[0-9a-f]{40}$", self.workflow)
        for script in (self.gate_script, self.status_script, self.comment_script):
            self.assertNotIn("eval ", script)
            self.assertNotIn("bash -c \"$", script)
        self.assertIn("persist-credentials: false", self.workflow)
        self.assertIn("CHECKOUT_CREDENTIAL_REMOVED=true", self.workflow)

    def test_writeback_is_absent_from_bootstrap_workflow(self) -> None:
        self.assertNotIn("writeback-result:", self.workflow)
        self.assertNotIn("PRIVATE_REPO_WRITE_TOKEN", self.workflow)
        self.assertNotIn("write_status:", self.workflow)
        self.assertNotIn("write_pr_comment:", self.workflow)

    def test_contract_keeps_authority_and_acceptance_separate(self) -> None:
        for required in (
            "PUBLIC_RUNNER_SOURCE_OF_TRUTH=false",
            "ACCESS_CONFIGURATION_AUTHORIZED=false",
            "WORKFLOW_DISPATCH_AUTHORIZED=false",
            "MERGE_AUTHORIZED=false",
            "PUBLIC_ARTIFACT_POLICY=none",
            "NO_FAKE_GREEN=true",
        ):
            self.assertIn(required, self.contract)

    def test_input_surface_is_structured_and_fixed(self) -> None:
        for required in (
            "private_repo:",
            "private_branch:",
            "private_sha:",
            "private_pr:",
            "gate_id:",
            "status_context:",
        ):
            self.assertIn(required, self.workflow)
        for forbidden in ("raw_command:", "command_input:", "artifact_name:", "private_url:"):
            self.assertNotIn(forbidden, self.workflow)

    def test_private_read_token_is_confined_to_checkout(self) -> None:
        self.assertEqual(self.workflow.count("secrets.PRIVATE_REPO_READ_TOKEN"), 1)
        before_gate = self.workflow.split("- name: Run allowlisted gate", 1)[0]
        self.assertIn("secrets.PRIVATE_REPO_READ_TOKEN", before_gate)
        gate_and_after = self.workflow.split("- name: Run allowlisted gate", 1)[1]
        self.assertNotIn("secrets.PRIVATE_REPO_READ_TOKEN", gate_and_after)
        self.assertNotIn("PRIVATE_REPO_WRITE_TOKEN", self.workflow)

    def test_branch_sha_mismatch_and_successor_head_are_rejected(self) -> None:
        self.assertIn('actual_sha="$(git -C private-checkout rev-parse HEAD)"', self.workflow)
        self.assertIn('[[ "$actual_sha" == "$EXPECTED_SHA" ]]', self.workflow)
        self.assertIn('[[ "$(git -C private-checkout rev-parse HEAD)" == "$EXPECTED_SHA" ]]', self.workflow)

    def test_bundle_path_persists_and_full_setup_is_gate_scoped(self) -> None:
        self.assertIn('BUNDLE_PATH: ${{ runner.temp }}/bundle', self.workflow)
        self.assertIn(
            "- name: Install locked dependencies\n"
            "        if: ${{ inputs.gate_id == 'LOVEBOX_P1_OC_EXACT_HEAD_V01' }}",
            self.workflow,
        )
        self.assertIn(
            "- name: Prepare test database\n"
            "        if: ${{ inputs.gate_id == 'LOVEBOX_P1_OC_EXACT_HEAD_V01' }}",
            self.workflow,
        )
        smoke_prefix = self.workflow.split("- name: Run allowlisted gate", 1)[0]
        self.assertNotIn('export BUNDLE_PATH="$RUNNER_TEMP/bundle"', smoke_prefix)

    def test_sanitizer_failure_is_fail_closed(self) -> None:
        self.assertIn("if ! python scripts/sanitize_gate_summary.py", self.gate_script)
        self.assertIn("ERROR_CODE=SANITIZER_FAILURE", self.gate_script)
        self.assertRegex(self.gate_script, r"ERROR_CODE=SANITIZER_FAILURE\"\n  exit 2")

    def test_writeback_is_fail_closed_until_separate_authority(self) -> None:
        for script in (self.status_script, self.comment_script):
            self.assertIn("WRITEBACK_RESULT=BLOCKED", script)
            self.assertIn("NO_PRIVATE_WRITE_PERFORMED=true", script)
            self.assertNotIn("curl ", script)
            self.assertNotIn("Authorization:", script)
        self.assertIn("WRITEBACK_IMPLEMENTATION_STATUS=DEFERRED_FAIL_CLOSED", self.contract)


if __name__ == "__main__":
    unittest.main()
