# Public Runner Center Contract v01

```text
CONTRACT_ID=LOVEBOX_PUBLIC_RUNNER_CENTER_CONTRACT_v01
WORK_ORDER_ID=RWO-LOVEBOX-PROD-DEV-002_PUBLIC_RUNNER_BOOTSTRAP
PRIVATE_AUTHORITY_REPOSITORY=TheGor-365/lovebox
PUBLIC_RUNNER_REPOSITORY=TheGor-365/lovebox-actions-runner
PUBLIC_RUNNER_SOURCE_OF_TRUTH=false
WORKFLOW=.github/workflows/run-private-validator.yml
TRIGGER=workflow_dispatch_only
GLOBAL_PERMISSION=contents:read
PUBLIC_ARTIFACT_POLICY=none
CACHE_POLICY=none
ACCESS_CONFIGURATION_AUTHORIZED=false
WRITEBACK_IMPLEMENTATION_STATUS=DEFERRED_FAIL_CLOSED
WORKFLOW_DISPATCH_AUTHORIZED=false
MERGE_AUTHORIZED=false
NO_FAKE_GREEN=true
```

## Authority

The private Lovebox repository remains the source of product, implementation, review,
acceptance, and release truth. A public runner result is evidence only for the named
gate on the supplied exact private SHA. It cannot accept P1, authorize PR-ready or
merge, promote readiness, deploy, or start runtime work.

## Structured dispatch

The workflow accepts only:

```text
private_repo=TheGor-365/lovebox
private_branch=main|prod/lovebox-prod-dev-001-oc-baseline
private_sha=<exact lowercase 40-character SHA>
private_pr=52
gate_id=LOVEBOX_PUBLIC_RUNNER_SMOKE_V01|LOVEBOX_P1_OC_EXACT_HEAD_V01
status_context=public-runner/lovebox/smoke|public-runner/lovebox/p1-oc-exact-head
```

Repository, branch, gate, and status context are choice-restricted. Gate and status
context must form an exact approved pair. No command, path, URL, script fragment,
environment assignment, artifact name, or arbitrary repository input exists.

## Exact-SHA boundary

The validation job checks out this runner without persisted credentials, validates all
structured inputs, resolves the allowlisted private branch, proves branch head equality,
detaches the exact SHA, removes checkout authorization from Git configuration, runs
only the fixed gate, and deletes the checkout in an `always()` cleanup step.

The read authorization is not exported to test commands. This bootstrap workflow has
no writeback job and does not reference a private write credential. The retained
writeback scripts fail closed and are not invoked. Actual status/comment implementation,
minimum write access, and one-run authorization require a separate bounded successor.

## Action pins

```text
actions/checkout=11bd71901bbe5b1630ceea73d27597364c9af683
actions/setup-python=a26af69be951a213d495a4c3e4e4022e16d87065
ruby/setup-ruby=003a5c4d8d6321bd302e38f6f0ec593f77f06600
actions/setup-node=b789df37d6b7526a863bf51b65df64f3f56ffe4f
```

## Result vocabulary

```text
PASS=all commands in the selected gate executed and returned zero
FAIL=at least one allowlisted command executed and returned nonzero
ERROR=policy checkout setup runner or infrastructure failure
BLOCKED=required authority or access is unavailable
```

`ERROR` and `BLOCKED` are not validator failures.

## Sanitized evidence

Only compact metadata may be printed: repository, branch, SHA, PR, gate, context,
result, exit code, stage results and numeric counts. Raw test names, stack traces,
source excerpts, file contents, user content, environment dumps and private archives
are forbidden in public logs and artifacts. Public artifacts remain zero.

## Initial gates

`LOVEBOX_PUBLIC_RUNNER_SMOKE_V01` proves structured policy, exact checkout, detached
SHA, runtime setup and fixed repository markers. It does not install private dependencies
or prepare the application database.

`LOVEBOX_P1_OC_EXACT_HEAD_V01` may install locked dependencies, prepare the test database,
and execute the Operating Center self-test and aggregate, targeted Operating Center
RSpec, full RSpec, RuboCop, Brakeman, bundle-audit, Zeitwerk, JavaScript build and CSS
build. Raw output remains ephemeral.

## Stop boundary

This branch does not configure access, run a workflow, write private status/comment,
merge the public PR, retire the legacy private workflow, or accept P1.
