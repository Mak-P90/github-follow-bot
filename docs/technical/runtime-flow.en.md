# Runtime Flow

> Status: ✅ Completed in British English.

## High-level sequence

1. Validate configuration/auth with `doctor`.
2. Run discovery (`followers` or `expand`).
3. Enqueue and process follow jobs.
4. Persist outcomes with run correlation.
5. Emit structured logs and metrics/exports for auditability.

## Notes

- `run` orchestrates the end-to-end flow.
- `worker` supports queue-centric processing by `run_id`.
- Operational budgets and retry controls prevent unsafe escalation.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

