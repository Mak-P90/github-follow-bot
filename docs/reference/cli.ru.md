# Справочник CLI

## Базовый синтаксис

```bash
python bot.py <command> [options]
```

Если команда не указана, по умолчанию выполняется `python bot.py run`.

## Основные команды

- `python bot.py run` → полный цикл синхронизации.
- `python bot.py stats` → сводка по сохранённому состоянию и последним запускам.
- `python bot.py doctor` → диагностика конфигурации, auth-режима, DB/runtime контрактов и hardening.
- `python bot.py metrics` → вывод метрик Prometheus в stdout.
- `python bot.py check-file-hardening` → проверка прав и владельцев runtime-файлов.

## Операции очереди

- `python bot.py queue-stats [--run-id <id>]`
- `python bot.py worker --run-id <id> [--max-jobs <n>]`
- `python bot.py resume --run-id <id> [--max-jobs <n>]`
- `python bot.py abort --run-id <id> [--reason <text>]`

## Экспорты и целостность релиза

- `python bot.py export-audit --output <file>`
- `python bot.py export-sbom --output <file>`
- `python bot.py export-release-manifest --output <file>`
- `python bot.py verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## Enterprise-профили и readiness

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

## Control plane, scheduler и распределённый backend очереди

### `control-plane-status`

- Команда: `python bot.py control-plane-status`
- Назначение: вывод краткого статуса control plane без запуска HTTP-сервера.

### `serve-control-plane`

- Команда: `python bot.py serve-control-plane [--host 127.0.0.1] [--port 8080]`
- Назначение: запуск минимального HTTP control plane.

### `scheduler`

- Команда: `python bot.py scheduler [--interval-seconds 60] [--max-ticks 1] [--lock-key default] [--lock-ttl-seconds 300]`
- Назначение: цикл scheduler с lock-защитой от конкурентных запусков.

### Проверка backend очереди

- `python bot.py queue-backend-status` → readiness backend-а очереди.
- `python bot.py queue-backend-verify` → проверка topo/runtime контракта backend-а.
- `python bot.py queue-backend-smoke` → smoke-тест enqueue/claim/update пути.

### Проверка OTel runtime

- `python bot.py otel-runtime-status` → состояние runtime-трейсинга и корреляции `trace_id`.

## Автоматизация fork и GUI

- `python bot.py fork-repos --username <github_user> [--owned|--forked|--all] [--profile-readme] [--fork-source] [--follow-fork-owners]`
- `python bot.py gui`

## Операционные рекомендации

- Запускайте `doctor` перед первым run и после изменения auth/secrets.
- Перед enterprise gate запускайте `queue-backend-status` и `compliance-evidence-status`.
- Для CI/hardening используйте `verify-release-manifest --require-signature --max-age-seconds <ttl>`.

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
