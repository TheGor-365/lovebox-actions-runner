from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sanitizer", ROOT / "scripts/sanitize_gate_summary.py"
)
assert SPEC and SPEC.loader
sanitizer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(sanitizer)


class SanitizerTest(unittest.TestCase):
    def test_compact_counts_without_raw_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stage_dir = Path(tmp)
            (stage_dir / "FULL_RSPEC.status").write_text("FULL_RSPEC=1\n")
            (stage_dir / "RUBOCOP.status").write_text("RUBOCOP=0\n")
            (stage_dir / "full_rspec.json").write_text(json.dumps({
                "summary": {"example_count": 123, "failure_count": 2},
                "examples": [{"full_description": "PRIVATE TEST NAME"}],
            }))
            (stage_dir / "rubocop.json").write_text(json.dumps({
                "summary": {"offense_count": 7},
                "files": [{"path": "PRIVATE/PATH"}],
            }))
            (stage_dir / "brakeman.json").write_text(json.dumps({
                "warnings": [{"message": "PRIVATE SOURCE DETAIL"}]
            }))
            args = Namespace(
                stage_dir=str(stage_dir),
                gate_id="LOVEBOX_P1_OC_EXACT_HEAD_V01",
                private_repo="TheGor-365/lovebox",
                private_branch="prod/lovebox-prod-dev-001-oc-baseline",
                private_sha="550e741d4120f2076d1f2d4afe5dfd37351ec2de",
                private_pr="52",
                status_context="public-runner/lovebox/p1-oc-exact-head",
                overall_exit_code=1,
            )
            summary = sanitizer.build_summary(args)
            encoded = json.dumps(summary, sort_keys=True)
            self.assertEqual(summary["result"], "FAIL")
            self.assertEqual(summary["rspec_example_count"], 123)
            self.assertEqual(summary["rspec_failure_count"], 2)
            self.assertEqual(summary["rubocop_offense_count"], 7)
            self.assertEqual(summary["brakeman_warning_count"], 1)
            self.assertNotIn("PRIVATE TEST NAME", encoded)
            self.assertNotIn("PRIVATE/PATH", encoded)
            self.assertNotIn("PRIVATE SOURCE DETAIL", encoded)
            self.assertFalse(summary["private_content_public_exposure"])
            self.assertEqual(summary["public_artifact_count"], 0)

    def test_rejects_wrong_context_and_sha(self) -> None:
        base = dict(
            stage_dir=".",
            gate_id="LOVEBOX_PUBLIC_RUNNER_SMOKE_V01",
            private_repo="TheGor-365/lovebox",
            private_branch="prod/lovebox-prod-dev-001-oc-baseline",
            private_sha="550e741d4120f2076d1f2d4afe5dfd37351ec2de",
            private_pr="52",
            status_context="public-runner/lovebox/smoke",
            overall_exit_code=0,
        )
        wrong_context = Namespace(**{**base, "status_context": "public-runner/lovebox/p1-oc-exact-head"})
        with self.assertRaises(ValueError):
            sanitizer.validate_args(wrong_context)
        wrong_sha = Namespace(**{**base, "private_sha": "abc"})
        with self.assertRaises(ValueError):
            sanitizer.validate_args(wrong_sha)

    def test_rejects_unallowlisted_repository_and_gate(self) -> None:
        base = dict(
            stage_dir=".",
            gate_id="LOVEBOX_PUBLIC_RUNNER_SMOKE_V01",
            private_repo="TheGor-365/lovebox",
            private_branch="prod/lovebox-prod-dev-001-oc-baseline",
            private_sha="550e741d4120f2076d1f2d4afe5dfd37351ec2de",
            private_pr="52",
            status_context="public-runner/lovebox/smoke",
            overall_exit_code=0,
        )
        wrong_repo = Namespace(**{**base, "private_repo": "TheGor-365/other"})
        with self.assertRaises(ValueError):
            sanitizer.validate_args(wrong_repo)
        wrong_gate = Namespace(**{**base, "gate_id": "ARBITRARY_GATE"})
        with self.assertRaises(ValueError):
            sanitizer.validate_args(wrong_gate)

    def test_github_output_contains_only_compact_fields(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            stage_dir = Path(tmp)
            (stage_dir / "RUBY_VERSION.status").write_text("RUBY_VERSION=0\n")
            args = Namespace(
                stage_dir=str(stage_dir),
                gate_id="LOVEBOX_PUBLIC_RUNNER_SMOKE_V01",
                private_repo="TheGor-365/lovebox",
                private_branch="prod/lovebox-prod-dev-001-oc-baseline",
                private_sha="550e741d4120f2076d1f2d4afe5dfd37351ec2de",
                private_pr="52",
                status_context="public-runner/lovebox/smoke",
                overall_exit_code=0,
            )
            summary = sanitizer.build_summary(args)
            output = Path(tmp) / "github_output"
            sanitizer.write_github_output(str(output), summary)
            rendered = output.read_text()
            self.assertIn("result=PASS", rendered)
            self.assertIn("summary_json=", rendered)
            self.assertNotIn("PRIVATE SOURCE", rendered)


if __name__ == "__main__":
    unittest.main()
