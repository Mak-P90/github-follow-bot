# Troubleshooting

## 401 / auth error

- Verificar `BOT_AUTH_MODE`.
- Validar variables mínimas del modo elegido.
- Para `github_app`, confirmar **una sola** fuente de key.
- Ejecutar `python bot.py doctor` y revisar `auth_mode`, `github_app_configured`.

## Rate limit

- Revisar `check_all_followers.py` y métricas.
- Reducir frecuencia de ejecución.
- Aplicar `BOT_MAX_FOLLOWS_PER_RUN` para control operativo.

## Configuración incompleta

Errores frecuentes:
- Falta `GITHUB_USER`.
- Falta token/credenciales del modo activo.
- `GITHUB_APP_PRIVATE_KEY_FILE` apunta a ruta inexistente.

## Problemas con GitHub App key

- `GITHUB_APP_PRIVATE_KEY_FILE`: comprobar existencia/permisos.
- `GITHUB_APP_PRIVATE_KEY_COMMAND`: comprobar salida no vacía y timeout.
- No combinar inline/file/command simultáneamente.

## Dry-run

Si hay duda operativa, usar:

```env
BOT_DRY_RUN=true
```

Así validas flujo sin follow real.

## Errores de entorno Windows

- Activación de venv fallida por execution policy:
  - ejecutar PowerShell con política adecuada para scripts locales.
- Rutas con espacios:
  - usar comillas en rutas de archivo cuando aplique.

## Errores de path/permisos

- DB no escribible: revisar permisos del directorio/archivo `BOT_DB_PATH`.
- Secret mount no disponible: verificar ruta efectiva en `doctor`.

## Logs e interpretación

- El bot emite logs JSON estructurados.
- Correlacionar por `run_id` y `trace_id`.
- Revisar eventos de seguridad cuando haya fallos de auth o cola.


## Circuit breaker de expand (`expand_circuit_breaker_open`)

Si se repiten 429/5xx sobre el umbral (`BOT_EXPAND_HTTP_ERROR_THRESHOLD`) dentro de la ventana (`BOT_EXPAND_HTTP_ERROR_WINDOW`):

- el bot aborta el expand de la corrida actual;
- registra `security_event=expand_circuit_breaker_open`;
- emite log estructurado con `seed_login`, `phase`, `page`, `status_code`;
- opcional: fallback a `followers` si `BOT_EXPAND_FALLBACK_TO_FOLLOWERS=true`.

Pasos operativos:
1. Revisar `python bot.py export-audit --output artifacts/commands/audit.json` y filtrar `security_events`.
2. Ajustar ritmo/cron y budgets (`BOT_MAX_API_CALLS_PER_RUN`, `BOT_MAX_EXPAND_SEEDS_PER_RUN`).
3. Confirmar si conviene activar fallback temporal a followers.

## Cursor expand inconsistente

Si `expand_seed_index` está fuera de rango o `expand_seed_page` es inválido (0/negativo/no numérico), el runtime reencauza a estado seguro (índice 0 / página 1) y continúa sin excepción fatal.

La cola `follow_jobs` mantiene unicidad por (`run_id`, `github_login`), evitando duplicados para una misma corrida incluso con cursor corrupto.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

