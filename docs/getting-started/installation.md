# Installation

## Requisitos

- Python **3.10+**
- Acceso a internet para GitHub API
- `pip`
- Docker (opcional, solo si usarás la ruta de contenedor)

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

## Notas de shell/ruta

- En Linux/macOS usar `/` y `source`.
- En PowerShell usar `\` y `Activate.ps1`.
- El comando de ejecución del bot es el mismo: `python bot.py <comando>`.

## Ruta opcional con Docker

```bash
docker build -t github-follower-bot:local .
docker run --rm --env-file .env -v bot_data:/data github-follower-bot:local doctor
```

- Esta ruta no reemplaza la instalación local con `venv`; ambas se soportan.
- Si usas SQLite en contenedor, mantén `/data` persistente mediante volumen.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

