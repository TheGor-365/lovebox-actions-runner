# Public Runner Dispatch Runbook v01

## Status

The repository capability may be reviewed before access is configured. Do not dispatch
the workflow until the public runner pull request is independently approved, merged,
and a separate private authority records access configuration and a one-run gate.

## Required repository settings

Names only; never store values in Git:

```text
PRIVATE_REPO_READ_TOKEN
PRIVATE_REPO_WRITE_TOKEN
```

The read credential should be read-only and limited to `TheGor-365/lovebox`. The write
credential is optional and must be separately authorized for compact status/comment
writeback. Validation must work with both write inputs set to false.

## Bootstrap dispatch

Use:

```text
private_repo=TheGor-365/lovebox
private_branch=prod/lovebox-prod-dev-001-oc-baseline
private_sha=550e741d4120f2076d1f2d4afe5dfd37351ec2de
private_pr=52
gate_id=LOVEBOX_PUBLIC_RUNNER_SMOKE_V01
status_context=public-runner/lovebox/smoke
write_status=false
write_pr_comment=false
```

A later bounded run may select `LOVEBOX_P1_OC_EXACT_HEAD_V01` with its matching status
context. A branch/SHA mismatch is a policy error and stops before gate execution.

## Evidence collection

Record only:

- public run and job IDs;
- exact private repository, branch, and SHA;
- gate and validator version;
- compact stage results and counts;
- result and exit code;
- public artifact count;
- private-content exposure count.

Do not copy raw public logs into the private repository if they contain private source
details. The workflow is designed to print only compact sanitized fields.

## Failure classes

```text
POLICY_ERROR=invalid structured input or branch/SHA mismatch
SETUP_ERROR=dependency or database preparation failure
VALIDATOR_FAIL=an allowlisted command executed and returned nonzero
VALIDATOR_PASS=all selected allowlisted commands returned zero
INFRA_ERROR=runner or platform failure before semantic execution
BLOCKED=required authority or repository access is absent
```

## Writeback

Writeback is a separate job and is disabled unless explicitly selected. It never checks
out private code. It can write only:

- one status context selected by workflow choice;
- one compact comment to private PR `#52`.

Unknown results, unknown contexts, unknown repositories, malformed SHA values, or a PR
other than `52` stop without writing.

## Security checks before first run

1. verify the public PR exact head;
2. run the policy and sanitizer unit tests;
3. verify the changed-path allowlist;
4. independently review action pins and credential separation;
5. merge only after explicit owner acceptance;
6. configure minimum access outside Git;
7. authorize one smoke run;
8. verify visible steps and zero artifacts;
9. authorize the full P1 gate separately;
10. retire or disable private same-repository gate execution only after the public
    exact-SHA gate is accepted.
