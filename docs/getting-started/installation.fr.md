# Installation

**Statut de traduction :** ✅ Vue complétée en français.

## Prérequis

- Python **3.10+**
- Accès Internet pour l’API GitHub
- `pip`
- Docker (optionnel, uniquement si vous utilisez la voie conteneur)

## Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Notes shell/chemins

- Sous Linux/macOS, utiliser `/` et `source`.
- Sous PowerShell, utiliser `\` et `Activate.ps1`.
- La commande d’exécution reste la même : `python bot.py <commande>`.

## Option Docker

```bash
docker build -t github-follower-bot:local .
docker run --rm --env-file .env -v bot_data:/data github-follower-bot:local doctor
```

- Cette voie ne remplace pas l’installation locale avec `venv`; les deux sont supportées.
- Si vous utilisez SQLite en conteneur, gardez `/data` persistant via un volume.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

