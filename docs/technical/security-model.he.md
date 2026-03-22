# מודל אבטחה

## אימות

מצבים נתמכים:

- טְפִיחָה
- אסימון התקנה שהונפק מראש
- זמן ריצה של אפליקציית GitHub

כללי מפתח:

- במצב `github_app`: `GITHUB_APP_ID` + `GITHUB_APP_INSTALLATION_ID` + מקור מפתח אחד בדיוק.
- `BOT_REQUIRE_GITHUB_APP_AUTH=true` מאלץ מצב סגירת זמן ריצה של אפליקציית GitHub.

## סודות

- אל תקוד קשיח אישורים.
- שימוש בלעדי במשתני סביבה.
- כתיבת סודות ברישום.

## שחרר יושרה

- חפץ מתגלה עם עיכול.
- אימות מניפסט עם חתימה אופציונלית ו-TTL.
- פרופיל אפס אמון/קוסימן להקשחה.

## יכולת מעקב

- אירועים קריטיים עם `event` ומתאם על ידי `run_id`.
- `trace_id` עבור מתאם חתך כאשר רלוונטי.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

