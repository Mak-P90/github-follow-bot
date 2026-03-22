# Démarrage rapide

**Statut de traduction :** ✅ Vue complétée en français.

Séquence minimale pour exécuter le bot en toute sécurité pour la première fois.

## Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# éditez .env avec vos identifiants
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
# éditez .env avec vos identifiants
python .\bot.py doctor
python .\bot.py run
python .\bot.py stats
```

## Recommandation initiale

Pour le premier usage, activez `BOT_DRY_RUN=true` afin de valider le flux sans follow réel.

## Mode Discovery (followers vs expand)

Le bot supporte deux modes de découverte via `BOT_DISCOVERY_MODE` :

- `followers` (par défaut) : follow-back classique via `GET /users/{self.user}/followers`.
- `expand` : utilise `GET /users/{self.user}/following` comme graines puis explore `followers` -> `following` par graine, avec curseur persistant dans `settings`.

Exemple recommandé pour valider `expand` sans impact réel :

```bash
BOT_DRY_RUN=true BOT_DISCOVERY_MODE=expand python bot.py run
```

## Full quickstart coverage (end-to-end operational flow)

After the first `run`, use this complete lifecycle to operate without gaps:

### 1) Initial health verification (`doctor`)

```bash
python bot.py doctor
```

Recommended minimum `.env` contract:

```env
GITHUB_USER=your_user
BOT_AUTH_MODE=pat
PERSONAL_GITHUB_TOKEN=ghp_replace_me
BOT_DRY_RUN=true
```

> If you use GitHub App or installation token, set explicit auth mode (`BOT_AUTH_MODE`) as documented in `getting-started/authentication.fr.md`.

### 2) First safe execution (dry-run)

```bash
python bot.py run
python bot.py stats
python bot.py queue-stats
```

### 3) Real execution (after dry-run validation)

```bash
# in .env: BOT_DRY_RUN=false (or remove the variable)
python bot.py run
python bot.py stats
python bot.py queue-stats
```

### 4) Queue lifecycle with `run_id` (worker/resume/abort)

Get `run_id` from `run` JSON output or from `stats`.

```bash
# process jobs for an existing run
python bot.py worker --run-id <id>

# safely continue a previous run
python bot.py resume --run-id <id>

# abort an active run with persisted reason
python bot.py abort --run-id <id> --reason operator_abort
```

### 5) Minimum operational evidence (audit + release)

```bash
python bot.py export-audit --output artifacts/commands/audit.json
python bot.py export-release-manifest --output artifacts/commands/release-manifest.json
python bot.py verify-release-manifest --manifest artifacts/commands/release-manifest.json --require-signature --max-age-seconds 3600
python bot.py export-sbom --output artifacts/commands/sbom.json
```

### 6) Recommended enterprise gate before merge/release

```bash
./scripts/enterprise_verify.sh
```

### 7) Optional extra operational sanity (recommended)

```bash
python bot.py metrics
python bot.py check-file-hardening
```

### 7.5) Extended runtime sanity (recommended for distributed operation)

```bash
python bot.py control-plane-status
python bot.py scheduler --max-ticks 1 --interval-seconds 60
python bot.py queue-backend-status
python bot.py queue-backend-verify
python bot.py queue-backend-smoke
python bot.py otel-runtime-status
```

### 8) Advanced commands coverage (out of quickstart scope)

Quickstart covers the minimum operational lifecycle. For advanced capabilities, see:

- `getting-started/authentication.fr.md` (auth modes)
- `user-guide/daily-operations.fr.md` (day-2 operations)
- `reference/cli.fr.md` (full command catalog: scheduler, control-plane, GUI, enterprise profiles, etc.)

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
