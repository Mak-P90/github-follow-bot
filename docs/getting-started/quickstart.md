# Quickstart

Secuencia mínima para ejecutar el bot de forma segura por primera vez.

## Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# edita .env con tus credenciales
python bot.py doctor
python bot.py run
python bot.py stats
```

## Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
# edita .env con tus credenciales
python .\bot.py doctor
python .\bot.py run
python .\bot.py stats
```

## Recomendación inicial

En el primer uso, activar `BOT_DRY_RUN=true` para validar flujo sin acciones de follow reales.

## Discovery mode (followers vs expand)

El bot soporta dos modos de descubrimiento controlados por `BOT_DISCOVERY_MODE`:

- `followers` (default): follow-back clásico sobre `GET /users/{self.user}/followers`.
- `expand`: usa `GET /users/{self.user}/following` como semillas y explora en fases `followers` -> `following` por semilla, persistiendo cursor en `settings` para retomar donde quedó.

Ejemplo recomendado para validar el modo `expand` sin efectos reales:

```bash
BOT_DRY_RUN=true BOT_DISCOVERY_MODE=expand python bot.py run
python bot.py queue-stats
```

En `expand` se mantiene el mismo límite operativo `BOT_MAX_FOLLOWS_PER_RUN` y la misma cola durable `follow_jobs`.

## Guardrails adicionales para expand

Variables nuevas recomendadas para controlar presupuesto y resiliencia:

```env
BOT_MAX_CANDIDATES_PER_RUN=500
BOT_MAX_API_CALLS_PER_RUN=200
BOT_MAX_EXPAND_SEEDS_PER_RUN=20
BOT_EXPAND_HTTP_ERROR_WINDOW=20
BOT_EXPAND_HTTP_ERROR_THRESHOLD=5
BOT_EXPAND_FALLBACK_TO_FOLLOWERS=false
```

Cuando se alcanza un límite, el bot registra `event=expand_budget_reached` con `run_id`/`trace_id`.

## Cobertura completa del quickstart (flujo operativo end-to-end)

Después del primer `run`, este es el flujo recomendado para operar sin huecos:

### 1) Verificación inicial (`doctor`)

```bash
python bot.py doctor
```

Contrato mínimo recomendado en `.env`:

```env
GITHUB_USER=your_user
BOT_AUTH_MODE=pat
PERSONAL_GITHUB_TOKEN=ghp_replace_me
BOT_DRY_RUN=true
```

> Si usas GitHub App o installation token, configura el modo explícito (`BOT_AUTH_MODE`) tal como se documenta en `getting-started/authentication.md`.

### 2) Primera corrida segura (dry-run)

```bash
python bot.py run
python bot.py stats
python bot.py queue-stats
```

### 3) Corrida real (cuando el dry-run esté validado)

```bash
# en .env: BOT_DRY_RUN=false (o elimina la variable)
python bot.py run
python bot.py stats
python bot.py queue-stats
```

### 4) Operación de cola por `run_id` (worker/resume/abort)

Obtén el `run_id` desde la salida JSON de `run` o con `stats`.

```bash
# procesar jobs de un run existente
python bot.py worker --run-id <id>

# continuar un run previo de forma segura
python bot.py resume --run-id <id>

# abortar un run activo dejando razón auditada
python bot.py abort --run-id <id> --reason operator_abort
```

### 5) Evidencia operativa mínima (auditoría + release)

```bash
python bot.py export-audit --output artifacts/commands/audit.json
python bot.py export-release-manifest --output artifacts/commands/release-manifest.json
python bot.py verify-release-manifest --manifest artifacts/commands/release-manifest.json --require-signature --max-age-seconds 3600
python bot.py export-sbom --output artifacts/commands/sbom.json
```

### 6) Gate enterprise recomendado antes de merge/release

```bash
./scripts/enterprise_verify.sh
```

### 7) Sanidad operativa adicional (recomendado)

```bash
python bot.py metrics
python bot.py check-file-hardening
```

### 7.5) Sanidad runtime extendida (recomendado para operación distribuida)

```bash
python bot.py control-plane-status
python bot.py scheduler --max-ticks 1 --interval-seconds 60
python bot.py queue-backend-status
python bot.py queue-backend-verify
python bot.py queue-backend-smoke
python bot.py otel-runtime-status
```

### 8) Cobertura de comandos avanzados (fuera de quickstart)

El quickstart cubre el ciclo operativo mínimo. Para capacidades avanzadas consulta:

- `getting-started/authentication.md` (modos de auth)
- `user-guide/daily-operations.md` (operación diaria)
- `reference/cli.md` (catálogo completo de comandos: scheduler, control-plane, GUI, perfiles enterprise, etc.)

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
