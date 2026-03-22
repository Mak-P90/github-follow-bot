# ADR-0001: הצג מגבלות שכבות כדי לצמצם צימוד `bot.py`

## מְדִינָה

מְקוּבָּל

## הֶקשֵׁר

הערכת הארגון מזהה צימוד גבוה ב-`bot.py` (תצורה + IO + כללים + CLI). כדי להפחית את הסיכון לרגרסיה, מוגדר חיתוך שכבה ראשון מבלי לשבור את חוזה ה-CLI הקיים.

## הַחְלָטָה

מוצג שלד של מודולים שכבות:

- `core/domain/contracts.py`: חוזי תחום (`RunExecutor`) למקרי שימוש.
- `core/application/use_cases.py`: השתמש במקרה `execute_run`.
- `adapters/` ו-`infra/`: חבילות בסיס להזזת מתאמי API/התמדה ותשתית באיטרציות עוקבות.

הפקודה `run` מפסיקה להפעיל את `FollowBackService.run()` באופן ישיר ועוברת את מקרה השימוש `execute_run(...)` כדי לעצב את גבול היישום/התחום.

## השלכות

- תועלת מיידית: נקודה אחת של `run` תזמור בשכבת היישום.
- תאימות: ה-CLI הנוכחי (`python bot.py run|stats|doctor|worker|export-*`) נשמר.
- העבודה הבאה: העבר בהדרגה את לקוח GitHub, אחסון וצפייה ל-`adapters/*` ו-`infra/*`.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

