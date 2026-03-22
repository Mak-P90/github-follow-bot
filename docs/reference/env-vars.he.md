# הפניה למשתני סביבה

טבלה קנונית של משתנים שזוהו בזמן ריצה (`bot.py`).

| משתנה                                        | חובה  | חל על                           | ברירת מחדל            | דוגמה                   | השפעה/הערות                                                                                                    |
| -------------------------------------------- | ----- | ------------------------------- | --------------------- | ----------------------- | -------------------------------------------------------------------------------------------------------------- |
| `GITHUB_USER`                                | כן    | הכל                             | -                     | `octocat`               | משתמש יעד של הבוט.                                                                                             |
| `BOT_AUTH_MODE`                              | לא    | aut                             | הסיק                  | `github_app`            | תקף: `pat`, `github_app_installation_token`, `github_app`.                                                     |
| `PERSONAL_GITHUB_TOKEN`                      | מותנה | `pat`                           | -                     | `ghp_xxx`               | אין לחשוף ביומנים/מאגר.                                                                                        |
| `GITHUB_APP_INSTALLATION_TOKEN`              | מותנה | `github_app_installation_token` | -                     | `ghs_xxx`               | אסימון שהופק מראש.                                                                                             |
| `GITHUB_APP_ID`                              | מותנה | `github_app`                    | -                     | `12345`                 | נדרש במצב זמן ריצה של האפליקציה.                                                                               |
| `GITHUB_APP_INSTALLATION_ID`                 | מותנה | `github_app`                    | -                     | `67890`                 | נדרש במצב זמן ריצה של האפליקציה.                                                                               |
| `GITHUB_APP_PRIVATE_KEY`                     | מותנה | `github_app`                    | -                     | PEM מוטבע               | בחר רק מקור מפתח אחד.                                                                                          |
| `GITHUB_APP_PRIVATE_KEY_FILE`                | מותנה | `github_app`                    | -                     | `/run/secrets/key.pem`  | קבל רשימה `,` או `:`; השתמש בקובץ הקיים הראשון.                                                                |
| `GITHUB_APP_PRIVATE_KEY_COMMAND`             | מותנה | `github_app`                    | -                     | `python -c ...`         | מבוצע עם argv ופסק זמן.                                                                                        |
| `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS` | לא    | `github_app` + פקודה            | `10`                  | `10`                    | חייב להיות >=1.                                                                                                |
| `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`  | לא    | `github_app`                    | `60`                  | `60`                    | חייב להיות >=0.                                                                                                |
| `BOT_VERIFY_FOLLOW_AFTER_PUT`                | לא    | עקוב אחר זמן ריצה               | `true`                | `false`                 | סמן את `PUT /user/following/{login}` עם `GET /user/following/{login}` כדי למנוע תוצאות חיוביות שגויות.         |
| `BOT_FOLLOW_VERIFY_MAX_RETRIES`              | לא    | עקוב אחר זמן ריצה               | `2`                   | `3`                     | ניסיונות חוזרים של אימות לאחר מעקב. חייב להיות >=1.                                                            |
| `BOT_FOLLOW_VERIFY_RETRY_DELAY_SECONDS`      | לא    | עקוב אחר זמן ריצה               | `1.0`                 | `0.5`                   | המתן בין בדיקות אימות. חייב להיות >=0.                                                                         |
| `BOT_REQUIRE_GITHUB_APP_AUTH`                | לא    | מדיניות אישור                   | `false`               | `true`                  | Fail-closed: חוסם מצבים שאינם `github_app`.                                                                    |
| `BOT_DB_PATH`                                | לא    | זמן ריצה                        | `bot_state.db`        | `bot_state.db`          | נתיב SQLite.                                                                                                   |
| `BOT_DRY_RUN`                                | לא    | זמן ריצה                        | `false`               | `true`                  | מומלץ לריצה ראשונה.                                                                                            |
| `BOT_MAX_FOLLOWS_PER_RUN`                    | לא    | זמן ריצה                        | ללא הגבלה             | `50`                    | חייב להיות >=1 אם מוגדר.                                                                                       |
| `BOT_MAX_CANDIDATES_PER_RUN`                 | לא    | להרחיב את זמן הריצה             | ללא הגבלה             | `500`                   | גילוי קצר מתרחב על ידי הגעה למועמדים בתור בכל ריצה. חייב להיות >=1.                                            |
| `BOT_MAX_API_CALLS_PER_RUN`                  | לא    | להרחיב את זמן הריצה             | ללא הגבלה             | `200`                   | תקציב שיחות גילוי כולל (`fetch_my_following`, `fetch_user_followers`, `fetch_user_following`). חייב להיות >=1. |
| `BOT_MAX_EXPAND_SEEDS_PER_RUN`               | לא    | להרחיב את זמן הריצה             | ללא הגבלה             | `20`                    | מקסימום זרעים מעובדים בכל הפעלה במצב `expand`. חייב להיות >=1.                                                 |
| `BOT_DISCOVERY_MODE`                         | לא    | זמן ריצה                        | `followers`           | `expand`                | תקף: `followers`, `expand`. `expand` משתמש בזרעים מ-`following` ובסמן מתמשך ב-`settings`.                      |
| `BOT_EXPAND_HTTP_ERROR_WINDOW`               | לא    | להרחיב חוסן                     | `20`                  | `20`                    | חלון הזזה של שגיאת HTTP עבור מפסק גילוי. חייב להיות >=1.                                                       |
| `BOT_EXPAND_HTTP_ERROR_THRESHOLD`            | לא    | להרחיב חוסן                     | `5`                   | `3`                     | סף לפי סוג HTTP (429 ו-5xx) לפתיחת מפסק ולהתרחבות. חייב להיות >=1.                                             |
| `BOT_EXPAND_FALLBACK_TO_FOLLOWERS`           | לא    | להרחיב חוסן                     | `false`               | `true`                  | אם המפסק נפתח, הוא מאפשר חזרה ל-`followers` באותה הפעלה.                                                       |
| `BOT_FOLLOW_JOB_MAX_ATTEMPTS`                | לא    | תור                             | `3`                   | `3`                     | חייב להיות >=1.                                                                                                |
| `BOT_CLEANUP_LEGACY_FILES`                   | לא    | הגירה                           | `true`                | `true`                  | העבר קבצי TXT לארכיון אל `*.migrated`.                                                                         |
| `BOT_POLICY_REQUIRE_CONSENT`                 | לא    | פוליטיקה                        | `false`               | `true`                  | חסום מעקב ללא הסכמה.                                                                                           |
| `BOT_POLICY_DENYLIST`                        | לא    | פוליטיקה                        | ריק                   | `user1,user2`           | רשימת דחייה על ידי התחברות.                                                                                    |
| `BOT_POLICY_RETENTION_DAYS`                  | לא    | פוליטיקה                        | `365`                 | `90`                    | חלון שמירה מוכרז.                                                                                              |
| `RELEASE_MANIFEST_SIGNING_KEY`               | לא    | שלמות שחרור                     | -                     | `change-me`             | חתימת מניפסט HMAC.                                                                                             |
| `RELEASE_MANIFEST_REQUIRE_SIGNATURE`         | לא    | שלמות שחרור                     | `false`               | `true`                  | דורש חתימה עם אימות.                                                                                           |
| `RELEASE_MANIFEST_MAX_AGE_SECONDS`           | לא    | שלמות שחרור                     | ללא TTL               | `300`                   | חייב להיות >=1 אם מוגדר.                                                                                       |
| `BOT_OTEL_ENABLED`                           | לא    | צפיות                           | `false`               | `true`                  | אפשר זמן ריצה של מעקב.                                                                                         |
| `OTEL_SERVICE_NAME`                          | לא    | צפיות                           | `github_follower_bot` | `github_follower_bot`   | שם שירות OTel.                                                                                                 |
| `OTEL_EXPORTER_OTLP_ENDPOINT`                | לא    | observabilidad                  | -                     | `http://localhost:4318` | נקודת קצה OTLP.                                                                                                |
| `APP_ENV`                                    | לא    | ייצוא צפיות                     | `local`               | `prod`                  | תג סביבה ב-`export-otel-bootstrap`.                                                                            |
| `BOT_COSIGN_ENABLED`                         | לא    | אפס אמון                        | `false`               | `true`                  | שלט cosign של אכיפה.                                                                                           |
| `COSIGN_KEY_REF`                             | לא    | אפס אמון                        | -                     | `cosign.pub`            | הפניה למפתח Cosign.                                                                                            |
| `BOT_DUAL_WRITE_DRY_RUN`                     | לא    | הגירה                           | `false`               | `true`                  | אות מצב צל בכתיבה כפולה.                                                                                       |
| `BOT_POSTGRES_DSN`                           | לא    | הגירה                           | -                     | `postgresql://...`      | אפשר דוחות עם הקשר Postgres.                                                                                   |

## `BOT_DISCOVERY_MODE`

מגדיר את המקור המועמד עבור `python bot.py run`.

- `followers` (ברירת מחדל): בצע מעקב באמצעות העוקבים הישירים שלך.
- `expand`: הפעל גילוי לפי זרעים על העוקבים שלך (`/users/{self.user}/following`) ועבור שני תת-שלבים לפי זרעים (`followers` ו-`following`) עם סמן מתמשך על `settings`.

### `expand` הערות תפעול

- סמן מתמיד: `expand_seed_index`, `expand_seed_login`, `expand_seed_phase`, `expand_seed_page`.
- מניעת כפילויות: הימנע מ-`self`, משתמשים שכבר עוקבים אחריהם ומשתמשים עם מעקב מוצלח רשום (`follow_actions.success=1`) כדי להימנע ממעקב חוזר אוטומטי.
- ביצוע: אינו משנה את העובד או את התור; השתמש מחדש ב-`follow_jobs` + `process_follow_queue`.
- הגבלה: כבד `BOT_MAX_FOLLOWS_PER_RUN`.

## משתנים נוספים המכוסים בזמן ריצה

- `BOT_DB_ENGINE` (default `sqlite`)
    - Controls persistence engine selection (`sqlite` / `postgres`) for runtime paths that support both backends.
- `BOT_QUEUE_BACKEND`
    - Selects distributed queue adapter mode used by queue backend status/verify/smoke commands.
- `BOT_RABBITMQ_AMQP_URL`
    - RabbitMQ broker URL used by RabbitMQ queue backend adapter.
- `BOT_RABBITMQ_QUEUE`
    - RabbitMQ primary queue name.
- `BOT_RABBITMQ_DLQ`
    - RabbitMQ dead-letter queue name.
- `BOT_MAX_FORKS_PER_RUN`
    - Operational cap for `fork-repos` bulk processing.
- `BOT_GUI_ENABLED`
    - Feature toggle for optional GUI runtime path.
- `BOT_GUI_HOST`
    - Bind host for GUI mode.
- `BOT_GUI_PORT`
    - Bind port for GUI mode.
- `BOT_GUI_LOCALE`
    - Locale for GUI i18n catalog selection.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:

- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`
