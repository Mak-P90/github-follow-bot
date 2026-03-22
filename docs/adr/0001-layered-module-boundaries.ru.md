#ADR-0001: Введение многоуровневых ограничений для уменьшения связанности.`bot.py`

## Состояние

Принял

## Контекст

Оценка предприятия выявила высокую степень взаимосвязи между`bot.py`(конфигурация + ввод-вывод + правила + CLI). Чтобы снизить риск регресса, определяется первый многоуровневый разрез без нарушения существующего контракта CLI.

## Решение

Представлен скелет многоуровневых модулей:

- `core/domain/contracts.py`: доменные контракты (`RunExecutor`) для вариантов использования.
- `core/application/use_cases.py`: вариант использования`execute_run`.
- `adapters/`и`infra/`— Базовые пакеты для перемещения адаптеров API/постоянства и инфраструктуры в последующих итерациях.

Команда`run`перестань ссылаться`FollowBackService.run()`напрямую и проходит через вариант использования`execute_run(...)`формализовать границу приложения/домена.

## Последствия

- Немедленная выгода: единая точка оркестрации`run`на прикладном уровне.
- Совместимость: сохраняется текущий CLI (`python bot.py run|stats|doctor|worker|export-*`).
- Следующая работа: постепенно перенести клиент GitHub, хранилище и возможности наблюдения на`adapters/*`является`infra/*`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

