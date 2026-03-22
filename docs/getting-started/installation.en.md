# Installation

> Status: ✅ Completed in British English.

## Requirements

- Python 3.10+
- `pip`
- Git

## Clone repository

```bash
git clone <your-fork-or-repo-url>
cd GitHub_Follower_and_Fork_Bot_Automated-main
```

## Create virtual environment

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## Install dependencies

```bash
pip install -r requirements.txt
```

## Configure environment

```bash
cp .env.example .env
```

Then edit `.env` with your selected authentication mode and credentials.

## Verify setup

```bash
python bot.py doctor
```

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

