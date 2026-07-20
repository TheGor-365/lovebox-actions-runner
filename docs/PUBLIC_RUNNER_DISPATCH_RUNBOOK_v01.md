# Public Runner Dispatch Runbook v01

## Current state

The runner capability is review-only. Do not dispatch until the public pull request is
independently approved and merged, minimum repository access is configured outside Git,
and private Lovebox authority permits one exact run.

The bootstrap writeback scripts fail closed and perform no network write. Status or PR
comment implementation requires a separate bounded successor.

## Bootstrap dispatch candidate

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

A later bounded run may select `LOVEBOX_P1_OC_EXACT_HEAD_V01` with its matching context.
A branch/SHA mismatch stops before gate execution.

## Evidence

Record only public run/job IDs, exact private repository/branch/SHA, gate version,
compact stage results, numeric counts, result, exit code, public artifact count and
private-content exposure count. Do not copy raw command output.

## Failure classes

```text
POLICY_ERROR=invalid structured input or branch/SHA mismatch
SETUP_ERROR=dependency or database preparation failure
VALIDATOR_FAIL=an allowlisted command executed and returned nonzero
VALIDATOR_PASS=all selected allowlisted commands returned zero
INFRA_ERROR=runner or platform failure before semantic execution
BLOCKED=required authority or repository access is absent
```

## Security sequence

1. verify the public PR exact head and changed paths;
2. run policy and sanitizer tests;
3. independently review action pins, input allowlists and authorization separation;
4. merge only after explicit owner acceptance;
5. configure minimum read access outside Git;
6. authorize one smoke run with both write inputs false;
7. verify visible steps and zero artifacts;
8. authorize the P1 quality gate separately;
9. implement writeback separately if required;
10. retire private same-repository execution only after the public gate is accepted.
