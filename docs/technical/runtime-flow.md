# Runtime Flow

## Flujo real (comando `run`)

1. Parse de CLI (`build_parser`).
2. Carga/validación de entorno (`BotConfig.from_env`).
3. Inicialización de logger con redacción de secretos.
4. Inicialización de storage SQLite.
5. Ejecución del caso de uso (`execute_run` -> `FollowBackService.run`).
6. Persistencia de run, acciones, eventos de seguridad.
7. Emisión de resultado JSON.

## Flujo de worker

1. Parse de `worker --run-id`.
2. Carga config + logger + storage.
3. `process_follow_queue` con opcional `--max-jobs`.
4. Salida JSON con `run_id`, `processed`, `trace_id`.

## Flujo de exports

- Cada comando `export-*` genera payload JSON y lo escribe en `--output`.
- `verify-release-manifest` devuelve estado y código de salida no-cero si falla.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

