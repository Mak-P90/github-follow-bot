# Persistence

## Backend actual

- SQLite (`bot_state.db` por defecto, configurable con `BOT_DB_PATH`).

## Entidades operativas clave

- `bot_runs`
- `followers`
- `follow_actions`
- `follow_jobs`
- `security_events`

## Idempotencia y correlación

- Corridas correlacionadas por `run_id`.
- Flujo de follow con cola persistente y estados (`pending`, `done`, `failed`, `dead_letter`).
- Reintentos controlados por `BOT_FOLLOW_JOB_MAX_ATTEMPTS`.

## Migración

- Existen comandos de export para perfil SQLite -> PostgreSQL, cutover y dual-write.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

