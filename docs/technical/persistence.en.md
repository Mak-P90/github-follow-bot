# Persistence

> Status: ✅ Completed in British English.

## Model

- Operational state is persisted transactionally.
- SQLite is the baseline store with migration-oriented exports for PostgreSQL readiness.

## Queue

- Durable queue table `follow_jobs` tracks lifecycle states:
    - `pending`
    - `done`
    - `failed`
    - `dead_letter`

## Principles

- Avoid legacy text files as the source of truth.
- Keep per-run auditability using `run_id`.
- Preserve idempotency and retry limits.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

