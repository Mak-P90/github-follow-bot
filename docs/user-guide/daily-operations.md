# Daily Operations

## Comandos operativos principales

- `python bot.py run`  
  Ejecuta una corrida completa.

- `python bot.py worker --run-id <id> [--max-jobs <n>]`  
  Procesa cola de jobs para un run.

- `python bot.py stats`  
  Resumen de estado persistido + último run.

- `python bot.py queue-stats [--run-id <id>]`  
  Estado de cola (`pending`, `done`, `failed`, `dead_letter`).

- `python bot.py doctor`  
  Diagnóstico de configuración/auth/DB/hardening.

## Operación extendida (control plane, scheduler y backend de cola)

- `python bot.py control-plane-status`  
  Snapshot del estado del control plane sin levantar servidor HTTP.

- `python bot.py serve-control-plane --host 127.0.0.1 --port 8080`  
  Inicia el endpoint HTTP mínimo de control plane para operación supervisada.

- `python bot.py scheduler --interval-seconds 60 --max-ticks 1 --lock-key default --lock-ttl-seconds 300`  
  Ejecuta el scheduler con lock para evitar corridas concurrentes.

- `python bot.py queue-backend-status` / `python bot.py queue-backend-verify` / `python bot.py queue-backend-smoke`  
  Valida readiness, contrato runtime/topología y smoke test del backend de cola.

- `python bot.py otel-runtime-status`  
  Verifica readiness de trazabilidad y correlación `trace_id`.

## ¿Cuándo usar cada uno?

- Nuevo despliegue o cambio de secrets: `doctor`.
- Ejecución normal: `run`.
- Operación orientada a cola: `worker` + `queue-stats`.
- Operación controlada/distribuida: `scheduler` + `queue-backend-*` + `control-plane-status`.
- Revisión general: `stats`.

## Señales esperadas

- `run` devuelve JSON con `run_id`, `followers_fetched`, `followers_followed`.
- `doctor` devuelve estado de auth, DB integrity y banderas operativas.
- `queue-stats` permite ver agotamiento de reintentos y dead-letter.
- `otel-runtime-status` confirma postura de trazabilidad runtime para ambientes con OTel.

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
