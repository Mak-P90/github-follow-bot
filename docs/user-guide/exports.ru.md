# Экспорт

При экспорте создаются артефакты JSON для аудита, эксплуатации и усиления защиты.

## Аудит и целостность

- `export-audit --output <file>`
- `export-sbom --output <file>`
- `export-release-manifest --output <file>`
- `verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## Миграция/данные

- `export-postgres-migration-profile --output <file>`
- `export-postgres-cutover-profile --output <file>`
- `export-dual-write-consistency-report --output <file>`

## Наблюдаемость и безопасность

- `export-otel-bootstrap --output <file>`
- `export-otel-operations-profile --output <file>`
- `export-queue-topology-profile --output <file>`
- `export-zero-trust-profile --output <file>`
- `export-release-integrity-profile --output <file>`

## Рекомендуемое эксплуатационное использование

1. Бежать`doctor`.
2. Бегите`run`о`worker`.
3. Экспортируйте артефакты, необходимые для аудита или устранения неполадок.
4. Сохраните результаты рядом с`run_id`связанный.

## Контракт аудита: Discovery_context

`export-audit`теперь включает в себя`actions[].discovery_context`(сериализованный JSON), когда действие происходит в результате обнаружения.

Ожидаемые поля в развертывании:`seed_login`, `seed_index`, `phase`, `page`, `discovery_mode`.
Ожидаемые поля в подписчиках:`discovery_mode`, `page`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

