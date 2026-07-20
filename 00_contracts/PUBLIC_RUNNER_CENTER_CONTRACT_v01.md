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
write_status=true|false
write_pr_comment=true|false
```

Repository, branch, gate, and status context are choice-restricted. Gate and status
context must form an exact approved pair. No command, path, URL, script fragment,
environment assignment, artifact name, or arbitrary repository input exists.

## Exact-SHA and credential boundary

The validation job:

1. checks out this public runner without persisted credentials;
2. validates all structured inputs;
3. checks out the allowlisted private branch with a read-only credential supplied only
   to that checkout step;
4. proves the resolved branch head equals `private_sha`;
5. detaches the exact SHA;
6. removes credential-bearing Git configuration before any private command executes;
7. runs only the selected fixed gate;
8. deletes the private checkout in an `always()` cleanup step.

The private read credential is not exported to test commands. The private write
credential is referenced only by the separate writeback job, which never checks out or
executes private code. No credential value may be printed, stored, included in status
descriptions, included in comments, or uploaded.

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
ERROR=policy, checkout, setup, runner, or infrastructure failure
BLOCKED=required authorization or access is unavailable
```

`ERROR` and `BLOCKED` are not validator failures. No step and no command output means
no semantic result.

## Sanitized evidence

Only compact metadata may be printed or written back:

```text
PRIVATE_REPO
PRIVATE_BRANCH
PRIVATE_SHA
PRIVATE_PR
GATE_ID
STATUS_CONTEXT
RESULT
EXIT_CODE
STAGE_RESULTS
RSPEC_EXAMPLE_COUNT
RSPEC_FAILURE_COUNT
RUBOCOP_OFFENSE_COUNT
BRAKEMAN_WARNING_COUNT
PRIVATE_CONTENT_PUBLIC_EXPOSURE=false
PUBLIC_ARTIFACT_COUNT=0
NO_FAKE_GREEN=true
```

Raw test names, stack traces, source excerpts, file contents, prompts, user content,
recipient data, environment dumps, credentials, and private archives are forbidden in
public logs and artifacts.

## Initial gate boundary

`LOVEBOX_PUBLIC_RUNNER_SMOKE_V01` proves structured policy, exact checkout, detached
SHA, runtime setup, and fixed repository markers.

`LOVEBOX_P1_OC_EXACT_HEAD_V01` may execute the frozen Operating Center manifest,
Operating Center self-test and aggregate, targeted Operating Center RSpec, full RSpec,
RuboCop, Brakeman, bundle-audit, Zeitwerk, JavaScript build, and CSS build. Raw output
is captured to ephemeral files and only counts/result codes are exported.

## Current stop boundary

This bootstrap commit does not configure repository access, run a workflow, write a
private status, write a private PR comment, merge the public PR, retire the legacy
private workflow, or accept P1.
