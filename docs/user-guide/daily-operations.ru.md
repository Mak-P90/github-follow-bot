# Ежедневные операции

## Основные операционные команды

- `python bot.py run`  
  Выполняет полный run.

- `python bot.py worker --run-id <id> [--max-jobs <n>]`  
  Обрабатывает очередь job-ов для выбранного run.

- `python bot.py stats`  
  Сводка по сохранённому состоянию и последнему run.

- `python bot.py queue-stats [--run-id <id>]`  
  Состояние очереди (`pending`, `done`, `failed`, `dead_letter`).

- `python bot.py doctor`  
  Диагностика config/auth/DB/hardening.

## Расширенная эксплуатация (control plane, scheduler, backend очереди)

- `python bot.py control-plane-status`  
  Снимок статуса control plane без запуска HTTP-сервера.

- `python bot.py serve-control-plane --host 127.0.0.1 --port 8080`  
  Запускает минимальный HTTP endpoint control plane для контролируемой эксплуатации.

- `python bot.py scheduler --interval-seconds 60 --max-ticks 1 --lock-key default --lock-ttl-seconds 300`  
  Выполняет scheduler-цикл с lock-защитой от конкурентных запусков.

- `python bot.py queue-backend-status` / `python bot.py queue-backend-verify` / `python bot.py queue-backend-smoke`  
  Проверяет readiness backend-а, runtime/topology контракт и smoke-путь.

- `python bot.py otel-runtime-status`  
  Проверяет readiness runtime-трейсинга и корреляции `trace_id`.

## Когда использовать

- Новый деплой или смена secrets: `doctor`.
- Стандартный запуск: `run`.
- Эксплуатация через очередь: `worker` + `queue-stats`.
- Контролируемая/распределённая эксплуатация: `scheduler` + `queue-backend-*` + `control-plane-status`.
- Общий обзор: `stats`.

## Ожидаемые сигналы

- `run` возвращает JSON с `run_id`, `followers_fetched`, `followers_followed`.
- `doctor` возвращает auth-state, целостность DB и операционные флаги.
- `queue-stats` показывает исчерпание retry и поведение dead-letter.
- `otel-runtime-status` подтверждает runtime-ready состояние трассировки для OTel-сред.

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
