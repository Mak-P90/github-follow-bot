# הַתקָנָה

## דרישות

- Python **3.10+**
- גישה לאינטרנט עבור GitHub API
- `pip`
- Docker (אופציונלי, רק אם תשתמש בנתיב המכולה)

## לינוקס/macOS

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

## הערות מעטפת/נתיב

- ב-Linux/macOS השתמש ב-`/` ו-`source`.
- ב-PowerShell השתמש ב-`\` ו-`Activate.ps1`.
- פקודת ביצוע הבוט זהה: `python bot.py <comando>`.

## מסלול אופציונלי עם Docker

```bash
docker build -t github-follower-bot:local .
docker run --rm --env-file .env -v bot_data:/data github-follower-bot:local doctor
```

- נתיב זה אינו מחליף את ההתקנה המקומית ב-`venv`; שניהם תומכים אחד בשני.
- אם אתה משתמש ב-SQLite מכולות, שמור על `/data` קבוע באמצעות אמצעי אחסון.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

