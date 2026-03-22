# Порядок выполнения

## Фактический расход (команда`run`)

1. Анализ CLI (`build_parser`).
2. Загрузка/проверка среды (`BotConfig.from_env`).
3. Инициализация логгера с секретной записью.
4. Инициализация хранилища SQLite.
5. Выполнение варианта использования (`execute_run` -> `FollowBackService.run`).
6. Постоянство запусков, действий, событий безопасности.
7. Вывод результата в формате JSON.

## Рабочий поток

1. Разбор`worker --run-id`.
2. Конфиг груза + логгер + хранилище. 3.`process_follow_queue`с дополнительным`--max-jobs`.
3. Вывод JSON с помощью`run_id`, `processed`, `trace_id`.

## Экспортный поток

- Каждая команда`export-*`генерирует полезную нагрузку JSON и записывает ее в`--output`.
- `verify-release-manifest`возвращает статус и ненулевой код выхода в случае сбоя.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

