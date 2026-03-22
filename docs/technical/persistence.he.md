# הַתמָדָה

## קצה אחורי בפועל

- SQLite (`bot_state.db` כברירת מחדל, ניתן להגדרה עם `BOT_DB_PATH`).

## גופים תפעוליים מרכזיים

- `bot_runs`
- `followers`
- `follow_actions`
- `follow_jobs`
- `security_events`

## אימפוטנציה ומתאם

- גזעים בקורלציה על ידי `run_id`.
- עקוב אחר זרימה עם תור ומצבים מתמשכים (`pending`, `done`, `failed`, `dead_letter`).
- ניסיונות חוזרים נשלטים על ידי `BOT_FOLLOW_JOB_MAX_ATTEMPTS`.

## הֲגִירָה

- ישנן פקודות ייצוא עבור פרופיל SQLite -> PostgreSQL, cutover ו-dual-write.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

