# ממשק GUI תפעולי (NiceGUI)

ה־GUI הוא משטח תפעולי **אופציונלי** מעל ה־CLI.

## הפעלה בטוחה

```bash
BOT_GUI_ENABLED=true BOT_GUI_HOST=127.0.0.1 BOT_GUI_PORT=8081 python bot.py gui
```

- ברירת מחדל לקשירה מקומית: `127.0.0.1`.
- אם `nicegui` לא מותקן, הפקודה נכשלת בצורה מבוקרת עם קוד יציאה `2`.

## משתנים

- `BOT_GUI_ENABLED` (ברירת מחדל: `false`)
- `BOT_GUI_HOST` (ברירת מחדל: `127.0.0.1`)
- `BOT_GUI_PORT` (ברירת מחדל: `8081`)
- `BOT_GUI_LOCALE` (ברירת מחדל: `en`, נפילה ל־`en`)

## היקף MVP

- Dashboard
- Runs (start/resume/abort)
- Diagnostics (`doctor`)
- Queue/Metrics
- Exports (`export-audit`)

## חוזה אינטגרציה

ה־GUI מבצע דלגציה דרך המתאם `control_plane` ואינו מריץ לוגיקה עסקית או קריאות GitHub ישירות.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

