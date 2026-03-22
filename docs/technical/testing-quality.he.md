# בדיקה ואיכות

## מינימום אימות מומלץ

```bash
python -m py_compile bot.py check_all_followers.py
pytest -q
python bot.py doctor
mkdocs build --strict
```

## קריטריון לפני מיזוג

- הפקודות לעיל צריכות לעבור.
- אם יש חוב ריפו קודם, תעדו ראיות והיקף מדויקים.
- כל שינוי פונקציונלי ב-CLI/auth/env/persistence/queue/observability חייב לכלול עדכון מסמך באותו יחסי ציבור.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

