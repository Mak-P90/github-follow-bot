# יכולת תצפית

## רישום

- יומנים מובנים של JSON.
- אירועי אבטחה מתמשכים.
- מתאם לפי `run_id` ו-`trace_id`.

## מדדים ואבחון

- `python bot.py metrics` עבור פלט Prometheus.
- `python bot.py doctor` עבור מצב ריצה/אישור/DB.
- `python bot.py stats` להוספת סטטוס.

## OpenTelemetry

- `BOT_OTEL_ENABLED=true` מאפשר מעקב אחר זמן ריצה.
- `OTEL_EXPORTER_OTLP_ENDPOINT` להגדיר את דסטינו OTLP.
- `export-otel-bootstrap` ו-`export-otel-operations-profile` יוצרים חפצי אינטגרציה/פעולה.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

