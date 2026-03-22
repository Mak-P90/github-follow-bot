# Упорство

## Фактический бэкэнд

- SQLite (`bot_state.db`по умолчанию, настраивается с помощью`BOT_DB_PATH`).

## Ключевые операционные организации

- `bot_runs`
- `followers`
- `follow_actions`
- `follow_jobs`
- `security_events`

## Идемпотентность и корреляция

- Расы коррелируются по`run_id`.
- Следуйте потоку с постоянной очередью и состояниями (`pending`, `done`, `failed`, `dead_letter`).
- Контролируемые повторы`BOT_FOLLOW_JOB_MAX_ATTEMPTS`.

## Миграция

— Имеются команды экспорта для профиля SQLite -> PostgreSQL, переключения и двойной записи.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

