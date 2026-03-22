# Архитектура

## Актуальная карта модулей

- **Точка входа**:`bot.py`
- **Доменный контракт**:`core/domain/contracts.py`
- **Сценарий использования приложения**:`core/application/use_cases.py`
- **Адаптеры**:`adapters/*`(включает`queue/rabbitmq_adapter.py`)
- **Инфраполитика**:`infra/policy/engine.py`

## Обязанности

- `bot.py`: анализатор CLI, загрузка конфигурации/окружения, составление сервисов, выполнение команд и экспорт.
- `core/domain`: контракты для разделения вариантов использования.
- `core/application`: оркестровка вариантов использования (`execute_run`).
- `adapters`: точка интеграции для очереди/транспортов.
- `infra/policy`: правила согласия/список запретов.

## Границы

- Основной поток остается сосредоточенным на`bot.py`(разлагающийся монолит).
- Базовые уровни существуют, но не обеспечивают полного разделения всех задач.

ADR-червь:`docs/adr/0001-layered-module-boundaries.ru.md`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
