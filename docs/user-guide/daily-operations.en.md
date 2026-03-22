# Daily Operations

> Status: ✅ Completed in British English.

## Main operational commands

- `python bot.py run`  
  Executes a complete run.

- `python bot.py worker --run-id <id> [--max-jobs <n>]`  
  Processes queued jobs for a run.

- `python bot.py stats`  
  Summary of persisted state + latest run.

- `python bot.py queue-stats [--run-id <id>]`  
  Queue status (`pending`, `done`, `failed`, `dead_letter`).

- `python bot.py doctor`  
  Diagnostics for config/auth/DB/hardening.

## Extended operations (control plane, scheduler, queue backend)

- `python bot.py control-plane-status`  
  Emits a control-plane status snapshot without launching HTTP mode.

- `python bot.py serve-control-plane --host 127.0.0.1 --port 8080`  
  Starts the minimal control-plane HTTP endpoint for supervised operations.

- `python bot.py scheduler --interval-seconds 60 --max-ticks 1 --lock-key default --lock-ttl-seconds 300`  
  Runs the scheduler loop with lock protection to avoid concurrent triggering.

- `python bot.py queue-backend-status` / `python bot.py queue-backend-verify` / `python bot.py queue-backend-smoke`  
  Checks backend readiness, runtime/topology contract, and smoke path.

- `python bot.py otel-runtime-status`  
  Validates runtime tracing readiness and `trace_id` correlation posture.

## When to use each

- New deployment or secrets change: `doctor`.
- Standard execution: `run`.
- Queue-driven operations: `worker` + `queue-stats`.
- Controlled/distributed operation: `scheduler` + `queue-backend-*` + `control-plane-status`.
- General review: `stats`.

## Expected signals

- `run` returns JSON with `run_id`, `followers_fetched`, `followers_followed`.
- `doctor` returns auth state, DB integrity, and operational flags.
- `queue-stats` shows retries and dead-letter behaviour.
- `otel-runtime-status` reports runtime tracing readiness for OTel-enabled environments.

## Sync status (2026-03-22)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-22**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `python bot.py control-plane-status`
- `python bot.py scheduler -h`
- `python bot.py queue-backend-status`
- `python bot.py queue-backend-verify`
- `python bot.py queue-backend-smoke`
- `python bot.py otel-runtime-status`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
