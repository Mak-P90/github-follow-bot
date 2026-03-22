# פתרון בעיות

## 401 / שגיאת אישור

- בדוק `BOT_AUTH_MODE`.
- אמת את המשתנים המינימליים של המצב הנבחר.
- עבור `github_app`, אשר **מקור מפתח בודד**.
- הפעל את `python bot.py doctor` ובדוק את `auth_mode`, `github_app_configured`.

## מגבלת תעריף

- סקור את `check_all_followers.py` ואת המדדים.
- הפחת את תדירות הביצוע.
- החל `BOT_MAX_FOLLOWS_PER_RUN` עבור בקרה תפעולית.

## תצורה לא שלמה

שגיאות תכופות:

- חסר `GITHUB_USER`.
- חסרים אסימון/אישורים של מצב פעיל.
- `GITHUB_APP_PRIVATE_KEY_FILE` מצביע על מסלול לא קיים.

## בעיות עם מפתח אפליקציית GitHub

- `GITHUB_APP_PRIVATE_KEY_FILE`: בדוק קיום/הרשאות.
- `GITHUB_APP_PRIVATE_KEY_COMMAND`: בדוק פלט לא ריק ופסק זמן.
- אין לשלב מוטבע/קובץ/פקודה בו-זמנית.

## ריצה יבשה

אם יש ספק תפעולי, השתמש ב:

```env
BOT_DRY_RUN=true
```

בדרך זו אתה מאמת את הזרימה ללא מעקב אמיתי.

## שגיאות סביבת Windows

- הפעלת Venv נכשלה על ידי מדיניות ביצוע:
    - הפעל את PowerShell עם מדיניות מתאימה עבור סקריפטים מקומיים.
- מסלולים עם רווחים:
    - השתמש במירכאות בנתיבי קבצים כאשר הדבר רלוונטי.

## שגיאות נתיב/הרשאות

- DB לא ניתן לכתיבה: בדוק הרשאות ספרייה/קובץ `BOT_DB_PATH`.
- רכיב סודי אינו זמין: בדוק נתיב יעיל ב-`doctor`.

## יומנים ופרשנות

- הבוט מוציא יומני JSON מובנים.
- מתאם על ידי `run_id` ו-`trace_id`.
- סקור אירועי אבטחה כאשר יש כשלי אימות או תור.

## מפסק זרם להרחבה (`expand_circuit_breaker_open`)

אם 429/5xx מעל הסף (`BOT_EXPAND_HTTP_ERROR_THRESHOLD`) חוזרים על עצמם בתוך החלון (`BOT_EXPAND_HTTP_ERROR_WINDOW`):

- הבוט מבטל את הרחבת הריצה הנוכחית;
- הירשם `security_event=expand_circuit_breaker_open`;
- פלט יומן מובנה עם `seed_login`, `phase`, `page`, `status_code`;
- אופציונלי: מעבר למצב `followers` אם `BOT_EXPAND_FALLBACK_TO_FOLLOWERS=true`.

שלבים תפעוליים:

1. בדוק את `python bot.py export-audit --output artifacts/commands/audit.json` וסנן את `security_events`.
2. התאם קצב/כרון ותקציבים (`BOT_MAX_API_CALLS_PER_RUN`, `BOT_MAX_EXPAND_SEEDS_PER_RUN`).
3. אשר אם מתאים להפעיל נפילה זמנית עבור עוקבים.

## הסמן מתרחב בצורה לא עקבית

אם `expand_seed_index` מחוץ לטווח או ש-`expand_seed_page` אינו חוקי (0/שלילי/לא מספרי), זמן הריצה מנותב מחדש למצב בטוח (אינדקס 0/עמוד 1) וממשיך ללא יוצא מן הכלל.

התור `follow_jobs` שומר על ייחודיות על ידי (`run_id`, `github_login`), הימנעות כפילויות לאותה ריצה אפילו עם סמן פגום.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

