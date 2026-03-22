# Exports

Los exports generan artefactos JSON para auditoría, operación y hardening.

## Auditoría e integridad

- `export-audit --output <file>`
- `export-sbom --output <file>`
- `export-release-manifest --output <file>`
- `verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## Migración / datos

- `export-postgres-migration-profile --output <file>`
- `export-postgres-cutover-profile --output <file>`
- `export-dual-write-consistency-report --output <file>`

## Observabilidad y seguridad

- `export-otel-bootstrap --output <file>`
- `export-otel-operations-profile --output <file>`
- `export-queue-topology-profile --output <file>`
- `export-zero-trust-profile --output <file>`
- `export-release-integrity-profile --output <file>`

## Uso operativo recomendado

1. Ejecutar `doctor`.
2. Ejecutar `run` o `worker`.
3. Exportar artefactos necesarios para auditoría o troubleshooting.
4. Guardar resultados junto al `run_id` asociado.


## Contrato de auditoría: discovery_context

`export-audit` ahora incluye `actions[].discovery_context` (JSON serializado) cuando la acción proviene de discovery.

Campos esperados en expand: `seed_login`, `seed_index`, `phase`, `page`, `discovery_mode`.
Campos esperados en followers: `discovery_mode`, `page`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

