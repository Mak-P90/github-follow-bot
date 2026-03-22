# תיעוד GitHub Follower Bot

תיעוד תפעולי וטכני לבוט, מתפרסם מענף `main` כזרם חי יחיד (ללא גרסאות לפי release/tag).

## למי זה מיועד?

- **מפעילים**: התקנה, אימות, הרצה ואבחון.
- **מתחזקים**: הבנת ארכיטקטורה, runtime, התמדה ואבטחה.

## מסלולים מהירים

1. [התקנה](getting-started/installation.he.md)
2. [אימות](getting-started/authentication.he.md)
3. [Quickstart](getting-started/quickstart.he.md)
4. [מדריך MkDocs + GitHub Pages](getting-started/mkdocs-github-pages.he.md)
5. [תפעול יומי](user-guide/daily-operations.he.md)
6. [תפעול GUI](user-guide/gui.he.md)
7. [פתרון תקלות](user-guide/troubleshooting.he.md)
8. [ארכיטקטורה טכנית](technical/architecture.he.md)
9. [ייחוס CLI](reference/cli.he.md)
10. [ייחוס משתני סביבה](reference/env-vars.he.md)

## מדיניות תיעוד

- מקור פרסום: **`main`**.
- ללא גרסאות תיעוד (`mike`, תגיות, עצי release: לא).
- כל PR עם שינוי פונקציונלי משמעותי חייב לכלול עדכון תיעוד באותו PR.

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
