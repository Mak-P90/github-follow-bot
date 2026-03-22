# אַדְרִיכָלוּת

## מפה אמיתית של מודולים

- **נקודת כניסה**: `bot.py`
- **חוזה דומיין**: `core/domain/contracts.py`
- **מקרה שימוש באפליקציה**: `core/application/use_cases.py`
- **מתאמים**: `adapters/*` (כולל `queue/rabbitmq_adapter.py`)
- **מדיניות אינפרא**: `infra/policy/engine.py`

## אחריות

- `bot.py`: מנתח CLI, טעינת config/env, הרכב שירות, ביצוע פקודות וייצוא.
- `core/domain`: חוזים לניתוק מקרה שימוש.
- `core/application`: השתמש בתזמור מקרים (`execute_run`).
- `adapters`: נקודת אינטגרציה לתור/הובלות.
- `infra/policy`: כללי הסכמה/הכחשה.

## גבולות

- הזרימה הראשית עדיין מתרכזת ב-`bot.py` (מונוליט מתכלה).
- יש שכבות בסיסיות, אבל לא הפרדה מוחלטת של כל החששות.

Ver ADR: `docs/adr/0001-layered-module-boundaries.he.md`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
