#!/usr/bin/env bash
set -uo pipefail

PRIVATE_ROOT="${1:-}"
[[ -n "$PRIVATE_ROOT" && -d "$PRIVATE_ROOT" ]] || {
  printf '%s\n' "RESULT=ERROR" "ERROR_CODE=PRIVATE_ROOT_MISSING"
  exit 2
}

case "${GATE_ID:-}" in
  LOVEBOX_PUBLIC_RUNNER_SMOKE_V01|LOVEBOX_P1_OC_EXACT_HEAD_V01) ;;
  *)
    printf '%s\n' "RESULT=ERROR" "ERROR_CODE=GATE_NOT_ALLOWLISTED"
    exit 2
    ;;
esac

[[ "${PRIVATE_REPO:-}" == "TheGor-365/lovebox" ]] || exit 2
[[ "${PRIVATE_SHA:-}" =~ ^[0-9a-f]{40}$ ]] || exit 2
[[ "${PRIVATE_PR:-}" == "52" ]] || exit 2

TMP_DIR="$(mktemp -d "${RUNNER_TEMP:-/tmp}/lovebox-gate.XXXXXX")"
trap 'rm -rf -- "$TMP_DIR"' EXIT

declare -a STAGES=()
declare -A STAGE_RC=()

run_stage() {
  local stage="$1"
  shift
  local log="$TMP_DIR/${stage}.log"
  STAGES+=("$stage")
  (
    cd "$PRIVATE_ROOT"
    "$@"
  ) >"$log" 2>&1
  local rc=$?
  STAGE_RC["$stage"]=$rc
  printf '%s=%s\n' "$stage" "$rc" >"$TMP_DIR/${stage}.status"
  return 0
}

run_stage PRIVATE_REPOSITORY_MARKERS bash -c 'test -f Gemfile && test -f bin/rails && test -f bin/validate_operating_center'
run_stage RUBY_VERSION ruby --version
run_stage NODE_VERSION node --version

if [[ "$GATE_ID" == "LOVEBOX_P1_OC_EXACT_HEAD_V01" ]]; then
  run_stage OC_SELF_TEST ruby bin/validate_operating_center self-test
  run_stage OC_AGGREGATE env LOVEBOX_CHANGED_PATHS='00_control/CURRENT_STATE.json,00_control/ACTIVE_WORK_ORDER.json,00_control/ACTIVE_IMPLEMENTATION_TRACK.json,00_control/IMPLEMENTATION_LEDGER.json,00_control/OWNER_DECISION_LEDGER.json,00_control/ACCEPTANCE_LEDGER.json,00_control/DEVELOPMENT_HISTORY.md,00_control/CHAT_HANDOFF_CONTRACT.md,00_control/WORK_ORDER_STATUS_SCHEMA.json,docs/operating_center/OPERATING_CENTER.md,docs/operating_center/PRODUCTION_EXECUTION_MAP.md,docs/operating_center/DEVELOPMENT_STANDARDS.md,docs/operating_center/PATCH_VERIFICATION_STANDARD.md,docs/operating_center/LOVEBOX_UI_SYSTEM_CONTRACT.md,docs/operating_center/STUDIO_STATE_ORCHESTRATION_CONTRACT.md,docs/product/PRODUCT_PASSPORT.md,docs/product/PRODUCT_PASSPORT.yaml,docs/product/PRODUCT_ROADMAP.md,docs/research/RESEARCH_REGISTRY.json,docs/research/RESEARCH_SYNTHESIS.md,docs/research/REJECTED_AND_SUPERSEDED_DECISIONS.md,bin/validate_operating_center,spec/operating_center/validator_spec.rb' ruby bin/validate_operating_center all

  STAGES+=("OC_TARGETED_RSPEC")
  (
    cd "$PRIVATE_ROOT"
    bundle exec rspec spec/operating_center/validator_spec.rb --format json --out "$TMP_DIR/targeted_rspec.json"
  ) >"$TMP_DIR/OC_TARGETED_RSPEC.log" 2>&1
  STAGE_RC["OC_TARGETED_RSPEC"]=$?
  printf 'OC_TARGETED_RSPEC=%s\n' "${STAGE_RC[OC_TARGETED_RSPEC]}" >"$TMP_DIR/OC_TARGETED_RSPEC.status"

  STAGES+=("FULL_RSPEC")
  (
    cd "$PRIVATE_ROOT"
    bundle exec rspec --format json --out "$TMP_DIR/full_rspec.json"
  ) >"$TMP_DIR/FULL_RSPEC.log" 2>&1
  STAGE_RC["FULL_RSPEC"]=$?
  printf 'FULL_RSPEC=%s\n' "${STAGE_RC[FULL_RSPEC]}" >"$TMP_DIR/FULL_RSPEC.status"

  STAGES+=("RUBOCOP")
  (
    cd "$PRIVATE_ROOT"
    bundle exec rubocop --format json --out "$TMP_DIR/rubocop.json"
  ) >"$TMP_DIR/RUBOCOP.log" 2>&1
  STAGE_RC["RUBOCOP"]=$?
  printf 'RUBOCOP=%s\n' "${STAGE_RC[RUBOCOP]}" >"$TMP_DIR/RUBOCOP.status"

  STAGES+=("BRAKEMAN")
  (
    cd "$PRIVATE_ROOT"
    bundle exec brakeman -q -f json -o "$TMP_DIR/brakeman.json"
  ) >"$TMP_DIR/BRAKEMAN.log" 2>&1
  STAGE_RC["BRAKEMAN"]=$?
  printf 'BRAKEMAN=%s\n' "${STAGE_RC[BRAKEMAN]}" >"$TMP_DIR/BRAKEMAN.status"

  run_stage BUNDLE_AUDIT bundle exec bundle-audit check --update
  run_stage ZEITWERK bin/rails zeitwerk:check
  run_stage JS_BUILD yarn build
  run_stage CSS_BUILD yarn build:css
fi

overall_rc=0
for stage in "${STAGES[@]}"; do
  rc="${STAGE_RC[$stage]}"
  if [[ "$rc" -ne 0 && "$overall_rc" -eq 0 ]]; then
    overall_rc="$rc"
  fi
done

python scripts/sanitize_gate_summary.py \
  --stage-dir "$TMP_DIR" \
  --gate-id "$GATE_ID" \
  --private-repo "$PRIVATE_REPO" \
  --private-branch "$PRIVATE_BRANCH" \
  --private-sha "$PRIVATE_SHA" \
  --private-pr "$PRIVATE_PR" \
  --status-context "$STATUS_CONTEXT" \
  --overall-exit-code "$overall_rc" \
  --github-output "${GITHUB_OUTPUT:-}"

exit "$overall_rc"
