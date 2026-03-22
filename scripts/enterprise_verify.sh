#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

: "${GITHUB_USER:?Set GITHUB_USER before running enterprise_verify.sh}"

auth_mode="${BOT_AUTH_MODE:-pat}"
case "$auth_mode" in
  pat|github_app_installation_token)
    if [[ -z "${PERSONAL_GITHUB_TOKEN:-}" && -z "${GITHUB_APP_INSTALLATION_TOKEN:-}" ]]; then
      echo "Set PERSONAL_GITHUB_TOKEN or GITHUB_APP_INSTALLATION_TOKEN before running enterprise_verify.sh" >&2
      exit 1
    fi
    ;;
  github_app)
    : "${GITHUB_APP_ID:?Set GITHUB_APP_ID when BOT_AUTH_MODE=github_app}"
    : "${GITHUB_APP_INSTALLATION_ID:?Set GITHUB_APP_INSTALLATION_ID when BOT_AUTH_MODE=github_app}"
    key_sources=0
    [[ -n "${GITHUB_APP_PRIVATE_KEY:-}" ]] && ((key_sources+=1))
    [[ -n "${GITHUB_APP_PRIVATE_KEY_FILE:-}" ]] && ((key_sources+=1))
    [[ -n "${GITHUB_APP_PRIVATE_KEY_COMMAND:-}" ]] && ((key_sources+=1))
    if [[ "$key_sources" -ne 1 ]]; then
      echo "Set exactly one key source for BOT_AUTH_MODE=github_app: GITHUB_APP_PRIVATE_KEY or GITHUB_APP_PRIVATE_KEY_FILE or GITHUB_APP_PRIVATE_KEY_COMMAND" >&2
      exit 1
    fi
    if [[ -n "${GITHUB_APP_PRIVATE_KEY_FILE:-}" ]]; then
      key_file_raw="${GITHUB_APP_PRIVATE_KEY_FILE}"
      key_file_delim=":"
      if [[ "$key_file_raw" == *","* ]]; then
        key_file_delim=","
      fi
      key_file_exists=false
      IFS="$key_file_delim" read -r -a key_file_candidates <<< "$key_file_raw"
      for candidate in "${key_file_candidates[@]}"; do
        candidate="${candidate//[[:space:]]/}"
        if [[ -n "$candidate" && -f "$candidate" ]]; then
          key_file_exists=true
          break
        fi
      done
      if [[ "$key_file_exists" != "true" ]]; then
        echo "GITHUB_APP_PRIVATE_KEY_FILE must point to an existing file (or list candidates separated by ','/pathsep)" >&2
        exit 1
      fi
    fi
    if [[ -n "${GITHUB_APP_PRIVATE_KEY_COMMAND:-}" ]]; then
      first_cmd_word="${GITHUB_APP_PRIVATE_KEY_COMMAND%% *}"
      if [[ -z "$first_cmd_word" ]] || ! command -v "$first_cmd_word" >/dev/null 2>&1; then
        echo "GITHUB_APP_PRIVATE_KEY_COMMAND must start with an installed command" >&2
        exit 1
      fi
    fi
    ;;
  *)
    echo "Unsupported BOT_AUTH_MODE=$auth_mode. Use pat, github_app_installation_token or github_app" >&2
    exit 1
    ;;
esac

if ! command -v pip-audit >/dev/null 2>&1; then
  echo "pip-audit is required. Install it with: pip install pip-audit" >&2
  exit 1
fi

TMP_DIR="$(mktemp -d)"
EVIDENCE_DIR="${BOT_EVIDENCE_DIR:-}"
cleanup() {
  if [[ -z "$EVIDENCE_DIR" ]]; then
    rm -rf "$TMP_DIR"
  fi
}
trap cleanup EXIT

if [[ -n "$EVIDENCE_DIR" ]]; then
  mkdir -p "$EVIDENCE_DIR"
fi

export BOT_DB_PATH="$TMP_DIR/enterprise_verify.db"
export RELEASE_MANIFEST_SIGNING_KEY="${RELEASE_MANIFEST_SIGNING_KEY:-enterprise-local-test-key}"
export RELEASE_MANIFEST_REQUIRE_SIGNATURE="${RELEASE_MANIFEST_REQUIRE_SIGNATURE:-true}"
export RELEASE_MANIFEST_MAX_AGE_SECONDS="${RELEASE_MANIFEST_MAX_AGE_SECONDS:-300}"

python -m py_compile bot.py check_all_followers.py
python scripts/check_requirements_pinned.py
# Keep tests hermetic: avoid leaking operator auth env into pytest configuration tests.
env -u BOT_AUTH_MODE \
    -u GITHUB_APP_ID \
    -u GITHUB_APP_INSTALLATION_ID \
    -u GITHUB_APP_PRIVATE_KEY \
    -u GITHUB_APP_PRIVATE_KEY_FILE \
    -u GITHUB_APP_PRIVATE_KEY_COMMAND \
    -u GITHUB_APP_INSTALLATION_TOKEN \
    -u PERSONAL_GITHUB_TOKEN \
    pytest -q
python bot.py doctor >"$TMP_DIR/doctor_report.json"
python bot.py check-file-hardening >"$TMP_DIR/file_hardening_report.json"
python bot.py metrics >"$TMP_DIR/metrics_report.prom"
python bot.py export-audit --output "$TMP_DIR/audit.json" >"$TMP_DIR/audit_export.json"
python bot.py export-sbom --output "$TMP_DIR/sbom_ci.json" >"$TMP_DIR/sbom_export.json"
python bot.py export-postgres-migration-profile --output "$TMP_DIR/postgres_migration_profile.json" >"$TMP_DIR/postgres_migration_profile_export.json"
python bot.py export-otel-bootstrap --output "$TMP_DIR/otel_bootstrap.json" >"$TMP_DIR/otel_bootstrap_export.json"
python bot.py export-zero-trust-profile --output "$TMP_DIR/zero_trust_profile.json" >"$TMP_DIR/zero_trust_profile_export.json"
python bot.py export-otel-operations-profile --output "$TMP_DIR/otel_operations_profile.json" >"$TMP_DIR/otel_operations_profile_export.json"
BOT_OTEL_ENABLED=true OTEL_EXPORTER_OTLP_ENDPOINT=http://collector:4318 python bot.py otel-runtime-status >"$TMP_DIR/otel_runtime_status_report.json"
python bot.py export-queue-topology-profile --output "$TMP_DIR/queue_topology_profile.json" >"$TMP_DIR/queue_topology_profile_export.json"
python bot.py queue-backend-status >"$TMP_DIR/queue_backend_status_report.json"
python bot.py queue-backend-verify >"$TMP_DIR/queue_backend_verify_report.json"
python bot.py queue-backend-smoke >"$TMP_DIR/queue_backend_smoke_report.json"
python bot.py export-release-manifest --output "$TMP_DIR/release_manifest_ci.json" >"$TMP_DIR/release_manifest_export.json"
python bot.py compliance-evidence-status --evidence-dir "$TMP_DIR" >"$TMP_DIR/compliance_evidence_status_report.json"
python bot.py export-postgres-cutover-profile --output "$TMP_DIR/postgres_cutover_profile.json" >"$TMP_DIR/postgres_cutover_profile_export.json"
python bot.py export-release-integrity-profile --output "$TMP_DIR/release_integrity_profile.json" >"$TMP_DIR/release_integrity_profile_export.json"
python bot.py export-governance-profile --output "$TMP_DIR/governance_profile.json" >"$TMP_DIR/governance_profile_export.json"
python bot.py export-enterprise-readiness-report --output "$TMP_DIR/enterprise_readiness_report.json" --evidence-dir "$TMP_DIR" >"$TMP_DIR/enterprise_readiness_report_export.json" || true
python bot.py enterprise-readiness-gate --evidence-dir "$TMP_DIR" --allow-partial >"$TMP_DIR/enterprise_readiness_gate_report.json"
python bot.py enterprise-backlog-status --evidence-dir "$TMP_DIR" >"$TMP_DIR/enterprise_backlog_status_report.json" || true
python bot.py enterprise-remaining-work --evidence-dir "$TMP_DIR" >"$TMP_DIR/enterprise_remaining_work_report.json" || true
python bot.py enterprise-handoff-report --evidence-dir "$TMP_DIR" >"$TMP_DIR/enterprise_handoff_report.json" || true
python bot.py verify-release-manifest --manifest "$TMP_DIR/release_manifest_ci.json" --require-signature --max-age-seconds "$RELEASE_MANIFEST_MAX_AGE_SECONDS" >"$TMP_DIR/release_manifest_verify.json"
pip-audit -r requirements.txt >"$TMP_DIR/pip_audit.json"

python - "$TMP_DIR/release_manifest_ci.json" "$TMP_DIR/zero_trust_profile.json" "$TMP_DIR/release_integrity_profile.json" "$TMP_DIR/compliance_evidence_status_report.json" <<'PY'
import json
import sys
from pathlib import Path

manifest = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
artifacts = manifest.get("artifacts") or []
if not artifacts:
    raise SystemExit("Release manifest must contain at least one artifact")
for item in artifacts:
    digest = str(item.get("sha256", "")).strip()
    if len(digest) != 64:
        raise SystemExit("Release manifest includes artifact without a valid SHA-256 digest")

zero_trust = json.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
if "cosign" not in zero_trust:
    raise SystemExit("Zero-trust profile must include cosign hardening contract")
if "verify" not in (zero_trust.get("cosign") or {}):
    raise SystemExit("Zero-trust profile must include cosign verify guidance")

release_integrity = json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
required_steps = {"export-sbom", "verify-release-manifest", "cosign verify"}
configured_steps = set(release_integrity.get("recommended_gate_order") or [])
if not required_steps.issubset(configured_steps):
    raise SystemExit("Release integrity profile missing required zero-trust gate ordering")

compliance_status = json.loads(Path(sys.argv[4]).read_text(encoding="utf-8"))
if compliance_status.get("status") != "ready":
    raise SystemExit("Compliance evidence bundle must be ready before publishing release artifacts")
PY

signature_verified="$(python - "$TMP_DIR/release_manifest_verify.json" <<'PY'
import json
import sys
from pathlib import Path
payload = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
signature_ok = payload.get("signature", {}).get("verified") is True
age = payload.get("age", {})
age_ok = age.get("checked") is True and age.get("reason") is None
print("true" if (signature_ok and age_ok) else "false")
PY
)"

if [[ "$signature_verified" != "true" ]]; then
  echo "Release manifest signature verification did not pass" >&2
  exit 1
fi



if [[ -n "$EVIDENCE_DIR" ]]; then
  cp "$TMP_DIR"/* "$EVIDENCE_DIR"/
fi

echo "enterprise_verify.sh completed successfully"
