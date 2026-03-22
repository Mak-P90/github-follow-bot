# Поиск неисправностей

##401 / ошибка авторизации

- Чтобы проверить`BOT_AUTH_MODE`.
- Проверьте минимальные переменные выбранного режима.
- Для`github_app`, подтвердите **единственный** источник ключа.
- Выполнять`python bot.py doctor`и обзор`auth_mode`, `github_app_configured`.

## Ограничение скорости

- Обзор`check_all_followers.py`и метрики.
- Уменьшите частоту выполнения.
- Применять`BOT_MAX_FOLLOWS_PER_RUN`для оперативного контроля.

## Неполная конфигурация

Частые ошибки:

- Отсутствующий`GITHUB_USER`.
- Отсутствует токен/учетные данные активного режима.
- `GITHUB_APP_PRIVATE_KEY_FILE`указывает на несуществующий маршрут.

## Проблемы с ключом приложения GitHub

- `GITHUB_APP_PRIVATE_KEY_FILE`: проверить наличие/разрешения.
- `GITHUB_APP_PRIVATE_KEY_COMMAND`: проверьте непустой вывод и тайм-аут.
- Не объединяйте строку/файл/команду одновременно.

## Сухой прогон

Если есть эксплуатационные сомнения, используйте:

```env
BOT_DRY_RUN=true
```

Таким образом, вы подтверждаете поток без реального отслеживания.

## Ошибки среды Windows

- Активация Venv не удалась из-за политики выполнения:
- запустите PowerShell с соответствующей политикой для локальных сценариев.
- Маршруты с пробелами:
- используйте кавычки в путях к файлам, когда это применимо.

## Ошибки пути/разрешений

- БД недоступна для записи: проверьте права доступа к каталогу/файлу.`BOT_DB_PATH`.
- Секретное крепление недоступно: проверьте эффективный путь в`doctor`.

## Журналы и интерпретация

- Бот выводит структурированные журналы JSON.
- Сопоставить по`run_id`й`trace_id`.
- Просмотрите события безопасности при сбоях аутентификации или очереди.

## Расширительный выключатель (`expand_circuit_breaker_open`)

Если 429/5xx повторяются выше порога (`BOT_EXPAND_HTTP_ERROR_THRESHOLD`) внутри окна (`BOT_EXPAND_HTTP_ERROR_WINDOW`):

- бот прерывает развертывание текущего запуска;
- зарегистрироваться`security_event=expand_circuit_breaker_open`;
- выдает структурированный журнал с`seed_login`, `phase`, `page`, `status_code`;
- необязательно: запасной вариант a`followers`и`BOT_EXPAND_FALLBACK_TO_FOLLOWERS=true`.

Операционные шаги:

1. Обзор`python bot.py export-audit --output artifacts/commands/audit.json`и фильтровать`security_events`.
2. Скорректируйте темп/хрон и бюджеты (`BOT_MAX_API_CALLS_PER_RUN`, `BOT_MAX_EXPAND_SEEDS_PER_RUN`).
3. Подтвердите, целесообразно ли активировать временный резерв для подписчиков.

## Курсор расширяется непоследовательно

И`expand_seed_index`находится вне диапазона или`expand_seed_page`недопустимо (0/отрицательное/нечисловое), среда выполнения перенаправляется в безопасное состояние (индекс 0/страница 1) и продолжается без фатальных исключений.

хвост`follow_jobs`сохраняет уникальность (`run_id`, `github_login`), избегая дубликатов для одного запуска даже при поврежденном курсоре.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

