# CLI Reference

## Sintaxis base

```bash
python bot.py <command> [options]
```

Si no se especifica comando, se ejecuta `run`.

## Comandos core

### `run`

Ejecuta sincronización completa.

### `stats`

Muestra estado persistido y último run.

### `doctor`

Muestra diagnóstico runtime (auth, DB, hardening flags).

### `metrics`

Exporta métricas Prometheus en stdout.

### `check-file-hardening`

```bash
python bot.py check-file-hardening
```

Valida permisos mínimos de archivos runtime (DB/log).

## Operaciones de cola

### `queue-stats`

```bash
python bot.py queue-stats [--run-id <id>]
```

### `worker`

```bash
python bot.py worker --run-id <id> [--max-jobs <n>]
```

### `resume`

```bash
python bot.py resume --run-id <id> [--max-jobs <n>]
```

Reanuda procesamiento de cola para un `run_id` existente.

### `abort`

```bash
python bot.py abort --run-id <id> [--reason <texto>]
```

Marca una corrida en estado `running` como `aborted` preservando progreso.

## Exports y release integrity

### `export-audit`

```bash
python bot.py export-audit --output artifacts/commands/audit.json
```

### `export-sbom`

```bash
python bot.py export-sbom --output artifacts/commands/sbom.json
```

### `export-release-manifest`

```bash
python bot.py export-release-manifest --output artifacts/commands/release-manifest.json
```

### `verify-release-manifest`

```bash
python bot.py verify-release-manifest --manifest artifacts/commands/release-manifest.json [--require-signature] [--max-age-seconds 300]
```

## Perfiles enterprise y readiness

### `export-postgres-migration-profile`

```bash
python bot.py export-postgres-migration-profile --output artifacts/commands/postgres-migration-profile.json
```

### `export-otel-bootstrap`

```bash
python bot.py export-otel-bootstrap --output artifacts/commands/otel-bootstrap.json
```

### `export-otel-operations-profile`

```bash
python bot.py export-otel-operations-profile --output artifacts/commands/otel-operations-profile.json
```

### `export-queue-topology-profile`

```bash
python bot.py export-queue-topology-profile --output artifacts/commands/queue-topology-profile.json
```

### `export-postgres-cutover-profile`

```bash
python bot.py export-postgres-cutover-profile --output artifacts/commands/postgres-cutover-profile.json
```

### `export-dual-write-consistency-report`

```bash
python bot.py export-dual-write-consistency-report --output artifacts/commands/dual-write-consistency.json
```

### `export-zero-trust-profile`

```bash
python bot.py export-zero-trust-profile --output artifacts/commands/zero-trust-profile.json
```

### `export-release-integrity-profile`

```bash
python bot.py export-release-integrity-profile --output artifacts/commands/release-integrity-profile.json
```

### `export-governance-profile`

```bash
python bot.py export-governance-profile --output artifacts/commands/governance-profile.json
```

### `export-enterprise-readiness-report`

```bash
python bot.py export-enterprise-readiness-report --output artifacts/commands/enterprise-readiness.json [--evidence-dir artifacts/enterprise-evidence]
```

### `enterprise-readiness-gate`

```bash
python bot.py enterprise-readiness-gate [--evidence-dir artifacts/enterprise-evidence] [--allow-partial]
```

### `enterprise-backlog-status`

```bash
python bot.py enterprise-backlog-status [--evidence-dir artifacts/enterprise-evidence]
```

### `enterprise-remaining-work`

```bash
python bot.py enterprise-remaining-work [--evidence-dir artifacts/enterprise-evidence]
```

### `enterprise-handoff-report`

```bash
python bot.py enterprise-handoff-report [--evidence-dir artifacts/enterprise-evidence]
```

### `compliance-evidence-status`

```bash
python bot.py compliance-evidence-status [--evidence-dir artifacts/enterprise-evidence]
```

Valida el bundle mínimo de evidencia enterprise (`doctor_report.json`, `audit.json`, `sbom_ci.json`, `release_manifest_ci.json`, `queue_backend_status_report.json`, `otel_runtime_status_report.json`).

## Runtime extendido: control plane, scheduler y backend de cola

### `control-plane-status`

```bash
python bot.py control-plane-status
```

Muestra estado operativo resumido del control plane sin levantar servidor HTTP.

### `serve-control-plane`

```bash
python bot.py serve-control-plane [--host 127.0.0.1] [--port 8080]
```

Levanta un endpoint HTTP mínimo para health, estado de cola y checks de control plane.

### `scheduler`

```bash
python bot.py scheduler [--interval-seconds 60] [--max-ticks 1] [--lock-key default] [--lock-ttl-seconds 300]
```

Ejecuta el loop de scheduler con lock distribuible para evitar corridas concurrentes.

### `queue-backend-status`

```bash
python bot.py queue-backend-status
```

Informa readiness del backend de cola configurado (sqlite/postgres) y capacidad de lock.

### `queue-backend-verify`

```bash
python bot.py queue-backend-verify
```

Verifica topología/capacidades del backend de cola para ejecución distribuida.

### `queue-backend-smoke`

```bash
python bot.py queue-backend-smoke
```

Ejecuta smoke test rápido de encolado/procesamiento para validar wiring operativo.

### `otel-runtime-status`

```bash
python bot.py otel-runtime-status
```

Resume readiness de trazabilidad OTel runtime y correlación `trace_id`.

## GUI y automatización de forks

### `gui`

```bash
python bot.py gui
```

Inicia la interfaz web opcional (NiceGUI) para operación local.

Variables relacionadas:

- `BOT_GUI_ENABLED=false` (default).
- `BOT_GUI_HOST=127.0.0.1` (bind local por defecto).
- `BOT_GUI_PORT=8081`.
- `BOT_GUI_LOCALE=en` (catálogos en `interfaces/gui/locales/*.json`, fallback a `en`).

Si NiceGUI no está instalado, el comando finaliza con código `2` y mensaje operativo controlado.

### `fork-repos`

```bash
python bot.py fork-repos --username <github_user> [--owned|--forked|--all] [--profile-readme] [--fork-source] [--follow-fork-owners]
```

Fork masivo con filtros granulares de repos y opciones de cadena de source/owners.

## Ejemplos Linux/macOS

```bash
python bot.py doctor
python bot.py check-file-hardening
python bot.py worker --run-id 1 --max-jobs 10
python bot.py resume --run-id 1 --max-jobs 10
python bot.py abort --run-id 1 --reason "operator_request"
python bot.py scheduler --interval-seconds 60 --max-ticks 2
python bot.py serve-control-plane --host 127.0.0.1 --port 8080
python bot.py compliance-evidence-status --evidence-dir artifacts/enterprise-evidence
python bot.py fork-repos --username octocat --owned --profile-readme
```

## Ejemplos Windows PowerShell

```powershell
python .\bot.py doctor
python .\bot.py check-file-hardening
python .\bot.py worker --run-id 1 --max-jobs 10
python .\bot.py resume --run-id 1 --max-jobs 10
python .\bot.py abort --run-id 1 --reason "operator_request"
python .\bot.py scheduler --interval-seconds 60 --max-ticks 2
python .\bot.py compliance-evidence-status --evidence-dir .\artifacts\enterprise-evidence
python .\bot.py export-audit --output .\artifacts\commands\audit.json
```

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
