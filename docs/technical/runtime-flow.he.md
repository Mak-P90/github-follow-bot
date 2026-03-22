# זרימת זמן ריצה

## זרימה בפועל (פקודה `run`)

1. ניתוח CLI (`build_parser`).
2. טעינת/אימות סביבה (`BotConfig.from_env`).
3. אתחול לוגר עם כתיבה סודית.
4. אתחול אחסון SQLite.
5. ביצוע מקרה השימוש (`execute_run` -> `FollowBackService.run`).
6. הפעל התמדה, פעולות, אירועי אבטחה.
7. פלט תוצאת JSON.

## זרימת עובדים

1. ניתוח של `worker --run-id`.
2. Carga config + לוגר + אחסון.
3. `process_follow_queue` עם `--max-jobs` אופציונלי.
4. פלט JSON עם `run_id`, `processed`, `trace_id`.

## זרימת יצוא

- כל פקודה `export-*` יוצרת מטען JSON וכותבת אותו אל `--output`.
- `verify-release-manifest` מחזיר סטטוס וקוד יציאה שאינו אפס אם הוא נכשל.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

