# פעולות יומיומיות

## פקודות תפעול עיקריות

- `python bot.py run`  
  מריץ run מלא.

- `python bot.py worker --run-id <id> [--max-jobs <n>]`  
  מעבד את תור המשימות עבור run נתון.

- `python bot.py stats`  
  סיכום מצב מתמשך + run אחרון.

- `python bot.py queue-stats [--run-id <id>]`  
  מצב תור (`pending`, `done`, `failed`, `dead_letter`).

- `python bot.py doctor`  
  בדיקת config/auth/DB/hardening.

## תפעול מורחב (control plane, scheduler ו-backend תור)

- `python bot.py control-plane-status`  
  תמונת מצב של control plane בלי להרים שרת HTTP.

- `python bot.py serve-control-plane --host 127.0.0.1 --port 8080`  
  מפעיל endpoint HTTP מינימלי של control plane לתפעול מבוקר.

- `python bot.py scheduler --interval-seconds 60 --max-ticks 1 --lock-key default --lock-ttl-seconds 300`  
  מריץ לולאת scheduler עם lock למניעת טריגרים מקבילים.

- `python bot.py queue-backend-status` / `python bot.py queue-backend-verify` / `python bot.py queue-backend-smoke`  
  בודק readiness של backend התור, חוזה topology/runtime ו-smoke path.

- `python bot.py otel-runtime-status`  
  בודק readiness של tracing runtime וקורלציה של `trace_id`.

## מתי להשתמש בכל פקודה

- דיפלוי חדש או שינוי secrets: `doctor`.
- הרצה רגילה: `run`.
- תפעול מוכוון תור: `worker` + `queue-stats`.
- תפעול מבוקר/מבוזר: `scheduler` + `queue-backend-*` + `control-plane-status`.
- סקירה כללית: `stats`.

## סימנים צפויים

- `run` מחזיר JSON עם `run_id`, `followers_fetched`, `followers_followed`.
- `doctor` מחזיר auth-state, שלמות DB ודגלים תפעוליים.
- `queue-stats` מציג exhausted retries והתנהגות dead-letter.
- `otel-runtime-status` מאשר מוכנות tracing runtime עבור סביבות OTel.

## Sync status (2026-03-22)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-22**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `python bot.py control-plane-status`
- `python bot.py scheduler -h`
- `python bot.py queue-backend-status`
- `python bot.py queue-backend-verify`
- `python bot.py queue-backend-smoke`
- `python bot.py otel-runtime-status`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
