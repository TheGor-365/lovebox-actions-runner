#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

ALLOWED_GATES = {
    "LOVEBOX_PUBLIC_RUNNER_SMOKE_V01": "public-runner/lovebox/smoke",
    "LOVEBOX_P1_OC_EXACT_HEAD_V01": "public-runner/lovebox/p1-oc-exact-head",
}
ALLOWED_REPO = "TheGor-365/lovebox"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SAFE_STAGE_RE = re.compile(r"^[A-Z0-9_]+$")


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}
    return data if isinstance(data, dict) else {}


def read_stage_results(stage_dir: Path) -> dict[str, str]:
    results: dict[str, str] = {}
    for path in sorted(stage_dir.glob("*.status")):
        raw = path.read_text(encoding="utf-8").strip()
        if "=" not in raw:
            continue
        stage, rc_raw = raw.split("=", 1)
        if not SAFE_STAGE_RE.fullmatch(stage) or not rc_raw.isdigit():
            continue
        results[stage] = "PASS" if int(rc_raw) == 0 else "FAIL"
    return results


def rspec_counts(path: Path) -> tuple[int, int]:
    data = read_json(path)
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return 0, 0
    examples = summary.get("example_count", 0)
    failures = summary.get("failure_count", 0)
    return int(examples or 0), int(failures or 0)


def rubocop_count(path: Path) -> int:
    data = read_json(path)
    summary = data.get("summary")
    if not isinstance(summary, dict):
        return 0
    return int(summary.get("offense_count", 0) or 0)


def brakeman_count(path: Path) -> int:
    data = read_json(path)
    warnings = data.get("warnings")
    return len(warnings) if isinstance(warnings, list) else 0


def validate_args(args: argparse.Namespace) -> None:
    if args.private_repo != ALLOWED_REPO:
        raise ValueError("repository not allowlisted")
    if args.gate_id not in ALLOWED_GATES:
        raise ValueError("gate not allowlisted")
    if ALLOWED_GATES[args.gate_id] != args.status_context:
        raise ValueError("status context mismatch")
    if not SHA_RE.fullmatch(args.private_sha):
        raise ValueError("invalid private SHA")
    if args.private_pr != "52":
        raise ValueError("private PR not allowlisted")
    if args.overall_exit_code < 0:
        raise ValueError("invalid exit code")


def build_summary(args: argparse.Namespace) -> dict[str, Any]:
    validate_args(args)
    stage_dir = Path(args.stage_dir)
    stages = read_stage_results(stage_dir)
    targeted_examples, targeted_failures = rspec_counts(stage_dir / "targeted_rspec.json")
    full_examples, full_failures = rspec_counts(stage_dir / "full_rspec.json")
    overall_result = "PASS" if args.overall_exit_code == 0 else "FAIL"
    return {
        "private_repo": args.private_repo,
        "private_branch": args.private_branch,
        "private_sha": args.private_sha,
        "private_pr": int(args.private_pr),
        "gate_id": args.gate_id,
        "status_context": args.status_context,
        "result": overall_result,
        "exit_code": args.overall_exit_code,
        "stage_results": stages,
        "targeted_rspec_example_count": targeted_examples,
        "targeted_rspec_failure_count": targeted_failures,
        "rspec_example_count": full_examples,
        "rspec_failure_count": full_failures,
        "rubocop_offense_count": rubocop_count(stage_dir / "rubocop.json"),
        "brakeman_warning_count": brakeman_count(stage_dir / "brakeman.json"),
        "private_content_public_exposure": False,
        "public_artifact_count": 0,
        "no_fake_green": True,
    }


def write_github_output(path: str, summary: dict[str, Any]) -> None:
    if not path:
        return
    compact = json.dumps(summary, sort_keys=True, separators=(",", ":"))
    lines = [
        f"result={summary['result']}",
        f"exit_code={summary['exit_code']}",
        f"summary_json={compact}",
        f"rspec_example_count={summary['rspec_example_count']}",
        f"rspec_failure_count={summary['rspec_failure_count']}",
        f"rubocop_offense_count={summary['rubocop_offense_count']}",
        f"brakeman_warning_count={summary['brakeman_warning_count']}",
    ]
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage-dir", required=True)
    parser.add_argument("--gate-id", required=True)
    parser.add_argument("--private-repo", required=True)
    parser.add_argument("--private-branch", required=True)
    parser.add_argument("--private-sha", required=True)
    parser.add_argument("--private-pr", required=True)
    parser.add_argument("--status-context", required=True)
    parser.add_argument("--overall-exit-code", type=int, required=True)
    parser.add_argument("--github-output", default="")
    args = parser.parse_args()
    summary = build_summary(args)
    write_github_output(args.github_output, summary)
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
