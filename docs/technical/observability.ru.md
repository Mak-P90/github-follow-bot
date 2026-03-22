# Наблюдаемость

## Ведение журнала

- Структурированные журналы JSON.
- Постоянные события безопасности.
- Корреляция по`run_id`й`trace_id`.

## Метрики и диагностика

- `python bot.py metrics`для вывода Прометея.
- `python bot.py doctor`для статуса времени выполнения/аутентификации/БД.
- `python bot.py stats`для совокупного статуса.

## OpenTelemetry

- `BOT_OTEL_ENABLED=true`включить отслеживание времени выполнения.
- `OTEL_EXPORTER_OTLP_ENDPOINT`определить назначение OTLP.
- `export-otel-bootstrap`й`export-otel-operations-profile`генерировать артефакты интеграции/операции.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

