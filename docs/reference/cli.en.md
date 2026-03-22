# CLI Reference

> Status: ✅ Completed in British English.

## Base syntax

```bash
python bot.py <command> [options]
```

If no command is supplied, the default behaviour is equivalent to `python bot.py run`.

## Core commands

- `python bot.py run` → executes a full run.
- `python bot.py stats` → summarises persisted state and recent run data.
- `python bot.py doctor` → validates configuration, authentication mode, DB/runtime contracts, and hardening controls.
- `python bot.py metrics` → prints Prometheus metrics in text format.
- `python bot.py check-file-hardening` → validates runtime file permissions and ownership expectations.

## Queue operations

- `python bot.py queue-stats [--run-id <id>]`
- `python bot.py worker --run-id <id> [--max-jobs <n>]`
- `python bot.py resume --run-id <id> [--max-jobs <n>]`
- `python bot.py abort --run-id <id> [--reason <text>]`

## Exports and release integrity

- `python bot.py export-audit --output <file>`
- `python bot.py export-sbom --output <file>`
- `python bot.py export-release-manifest --output <file>`
- `python bot.py verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## Enterprise profiles and readiness

- `python bot.py export-postgres-migration-profile --output <file>`
- `python bot.py export-postgres-cutover-profile --output <file>`
- `python bot.py export-dual-write-consistency-report --output <file>`
- `python bot.py export-otel-bootstrap --output <file>`
- `python bot.py export-otel-operations-profile --output <file>`
- `python bot.py export-queue-topology-profile --output <file>`
- `python bot.py export-zero-trust-profile --output <file>`
- `python bot.py export-release-integrity-profile --output <file>`
- `python bot.py export-governance-profile --output <file>`
- `python bot.py export-enterprise-readiness-report --output <file> [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-readiness-gate [--evidence-dir artifacts/enterprise-evidence] [--allow-partial]`
- `python bot.py enterprise-backlog-status [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-remaining-work [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-handoff-report [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py compliance-evidence-status [--evidence-dir artifacts/enterprise-evidence]`

## Control plane, scheduler, and distributed queue backend

### `control-plane-status`

- Command: `python bot.py control-plane-status`
- Purpose: emits a compact control-plane readiness/status payload without launching HTTP server mode.

### `serve-control-plane`

- Command: `python bot.py serve-control-plane [--host 127.0.0.1] [--port 8080]`
- Purpose: starts the minimal control-plane HTTP service.

### `scheduler`

- Command: `python bot.py scheduler [--interval-seconds 60] [--max-ticks 1] [--lock-key default] [--lock-ttl-seconds 300]`
- Purpose: runs the dedicated scheduler tick loop with lock protection.

### Queue backend validation commands

- `python bot.py queue-backend-status` → reports backend readiness.
- `python bot.py queue-backend-verify` → validates queue topology/runtime contract.
- `python bot.py queue-backend-smoke` → executes a smoke path for enqueue/claim/update flow.

### OTel runtime inspection

- `python bot.py otel-runtime-status` → reports runtime tracing readiness and `trace_id` correlation posture.

## Fork automation and GUI

- `python bot.py fork-repos --username <github_user> [--owned|--forked|--all] [--profile-readme] [--fork-source] [--follow-fork-owners]`
- `python bot.py gui`

## Operational guidance

- Run `doctor` before the first run and after any auth/secret change.
- Run `queue-backend-status` and `compliance-evidence-status` before enforcing enterprise readiness gates.
- Use `verify-release-manifest --require-signature --max-age-seconds <ttl>` in CI/hardening validations.

## Sync status (2026-03-22)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-22**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `python bot.py control-plane-status`
- `python bot.py scheduler -h`
- `python bot.py serve-control-plane -h`
- `python bot.py queue-backend-status`
- `python bot.py queue-backend-verify`
- `python bot.py queue-backend-smoke`
- `python bot.py otel-runtime-status`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
