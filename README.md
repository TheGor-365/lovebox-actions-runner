# Lovebox Public Actions Runner

Review-only capability proposed under private Lovebox issue #60.

```text
PRIVATE_AUTHORITY_REPOSITORY=TheGor-365/lovebox
PUBLIC_RUNNER_IS_SOURCE_OF_TRUTH=false
PRIVATE_ACTIONS_REQUIRED=false
ALLOWLISTED_GATES_ONLY=true
ARBITRARY_COMMAND_INPUT_ALLOWED=false
PUBLIC_ARTIFACTS_DEFAULT=none
ACCESS_CONFIGURED=false
RUN_AUTHORIZED=false
MERGE_AUTHORIZED=false
NO_FAKE_GREEN=true
```

Initial gates:

- `LOVEBOX_PUBLIC_RUNNER_SMOKE_V01`
- `LOVEBOX_P1_OC_EXACT_HEAD_V01`

Each run must use an allowlisted repository, branch, exact SHA, gate, and status context. This branch does not authorize dispatch or merge.
