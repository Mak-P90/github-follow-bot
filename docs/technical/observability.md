# Observability

## Logging

- Logs estructurados JSON.
- Eventos de seguridad persistidos.
- Correlación por `run_id` y `trace_id`.

## Métricas y diagnósticos

- `python bot.py metrics` para salida Prometheus.
- `python bot.py doctor` para estado de runtime/auth/DB.
- `python bot.py stats` para estado agregado.

## OpenTelemetry

- `BOT_OTEL_ENABLED=true` habilita tracing runtime.
- `OTEL_EXPORTER_OTLP_ENDPOINT` define destino OTLP.
- `export-otel-bootstrap` y `export-otel-operations-profile` generan artefactos de integración/operación.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

