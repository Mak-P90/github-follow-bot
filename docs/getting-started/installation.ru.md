# Установка

## Требования

- Питон **3.10+**
- Доступ в Интернет для API GitHub.
- `pip`
- Docker (необязательно, только если вы будете использовать путь к контейнеру)

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

## Примечания к оболочке/пути

- При использовании Linux/macOS`/`й`source`.
- Пользователь PowerShell`\`й`Activate.ps1`.
- Команда выполнения бота та же:`python bot.py <comando>`.

## Необязательный маршрут с Docker

```bash
docker build -t github-follower-bot:local .
docker run --rm --env-file .env -v bot_data:/data github-follower-bot:local doctor
```

- Этот путь не заменяет локальную установку на`venv`; оба поддерживают друг друга.
- Если вы используете контейнерный SQLite, сохраните`/data`стойкий через объем.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

