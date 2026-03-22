# Exportations

**Statut de traduction :** ✅ Vue complétée en français.

Les exports génèrent des artefacts JSON pour l’audit, l’exploitation et le hardening.

## Audit et intégrité

- `export-audit --output <file>`
- `export-sbom --output <file>`
- `export-release-manifest --output <file>`
- `verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## Migration / données

- `export-postgres-migration-profile --output <file>`
- `export-postgres-cutover-profile --output <file>`
- `export-dual-write-consistency-report --output <file>`

## Observabilité et sécurité

- `export-otel-bootstrap --output <file>`
- `export-otel-operations-profile --output <file>`
- `export-queue-topology-profile --output <file>`
- `export-zero-trust-profile --output <file>`
- `export-release-integrity-profile --output <file>`

## Usage opérationnel recommandé

1. Exécuter `doctor`.
2. Exécuter `run` ou `worker`.
3. Exporter les artefacts nécessaires pour audit ou troubleshooting.
4. Archiver les résultats avec le `run_id` associé.

## Contrat d’audit : `discovery_context`

`export-audit` inclut désormais `actions[].discovery_context` (JSON sérialisé) quand l’action provient du discovery.

Champs attendus en `expand` : `seed_login`, `seed_index`, `phase`, `page`, `discovery_mode`.
Champs attendus en `followers` : `discovery_mode`, `page`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

