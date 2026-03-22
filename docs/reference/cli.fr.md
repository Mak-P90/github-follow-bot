# Référence CLI

**Statut de traduction :** ✅ Vue complétée en français.

## Syntaxe de base

```bash
python bot.py <command> [options]
```

Si aucune commande n'est fournie, le comportement par défaut est équivalent à `python bot.py run`.

## Commandes principales

- `python bot.py run` → exécute un cycle complet.
- `python bot.py stats` → résume l'état persistant et les dernières exécutions.
- `python bot.py doctor` → valide configuration, mode d'auth, contrats DB/runtime et contrôles de hardening.
- `python bot.py metrics` → imprime les métriques Prometheus en format texte.
- `python bot.py check-file-hardening` → vérifie permissions/propriétés minimales des fichiers runtime.

## Opérations de file

- `python bot.py queue-stats [--run-id <id>]`
- `python bot.py worker --run-id <id> [--max-jobs <n>]`
- `python bot.py resume --run-id <id> [--max-jobs <n>]`
- `python bot.py abort --run-id <id> [--reason <texte>]`

## Exports et intégrité de release

- `python bot.py export-audit --output <file>`
- `python bot.py export-sbom --output <file>`
- `python bot.py export-release-manifest --output <file>`
- `python bot.py verify-release-manifest --manifest <file> [--require-signature] [--max-age-seconds N]`

## Profils enterprise et readiness

- `python bot.py export-postgres-migration-profile --output <file>`
- `python bot.py export-postgres-cutover-profile --output <file>`
- `python bot.py export-dual-write-consistency-report --output <file>`
- `python bot.py export-otel-bootstrap --output <file>`
- `python bot.py export-otel-operations-profile --output <file>`
- `python bot.py export-queue-topology-profile --output <file>`
- `python bot.py export-zero-trust-profile --output <file>`
- `python bot.py export-release-integrity-profile --output <file>`
- `python bot.py export-governance-profile --output <file>`
- `python bot.py export-enterprise-readiness-report --output <file> [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-readiness-gate [--evidence-dir artifacts/enterprise-evidence] [--allow-partial]`
- `python bot.py enterprise-backlog-status [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-remaining-work [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py enterprise-handoff-report [--evidence-dir artifacts/enterprise-evidence]`
- `python bot.py compliance-evidence-status [--evidence-dir artifacts/enterprise-evidence]`

## Control plane, scheduler et backend de file distribué

### `control-plane-status`

- Commande : `python bot.py control-plane-status`
- Rôle : produit un état compact du control plane sans lancer le serveur HTTP.

### `serve-control-plane`

- Commande : `python bot.py serve-control-plane [--host 127.0.0.1] [--port 8080]`
- Rôle : démarre le service HTTP minimal de control plane.

### `scheduler`

- Commande : `python bot.py scheduler [--interval-seconds 60] [--max-ticks 1] [--lock-key default] [--lock-ttl-seconds 300]`
- Rôle : exécute la boucle scheduler avec protection par verrou.

### Validation du backend de file

- `python bot.py queue-backend-status` → état de readiness du backend.
- `python bot.py queue-backend-verify` → validation des contrats topo/runtime du backend de file.
- `python bot.py queue-backend-smoke` → smoke test rapide enqueue/claim/update.

### Inspection runtime OTel

- `python bot.py otel-runtime-status` → état runtime de la corrélation tracing/`trace_id`.

## Automatisation de forks et GUI

- `python bot.py fork-repos --username <github_user> [--owned|--forked|--all] [--profile-readme] [--fork-source] [--follow-fork-owners]`
- `python bot.py gui`

## Conseils opérationnels

- Exécuter `doctor` avant un premier run ou après changement auth/secrets.
- Exécuter `queue-backend-status` et `compliance-evidence-status` avant un gate enterprise.
- En CI/hardening, utiliser `verify-release-manifest --require-signature --max-age-seconds <ttl>`.

## Sync status (2026-03-22)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-22**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `python bot.py control-plane-status`
- `python bot.py scheduler -h`
- `python bot.py serve-control-plane -h`
- `python bot.py queue-backend-status`
- `python bot.py queue-backend-verify`
- `python bot.py queue-backend-smoke`
- `python bot.py otel-runtime-status`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
