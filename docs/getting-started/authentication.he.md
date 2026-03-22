# אימות

זמן הריצה תומך בשלושה מצבים אמיתיים (`BOT_AUTH_MODE`):

1. `pat`
2. `github_app_installation_token`
3. `github_app`

אם `BOT_AUTH_MODE` אינו מוגדר, זמן הריצה נשאר ב-`pat` ו**לא** מקדם אוטומטית את `GITHUB_APP_INSTALLATION_TOKEN`. כדי להשתמש באסימון התקנה עליך להצהיר במפורש `BOT_AUTH_MODE=github_app_installation_token`.

## 1) PAT (פשוט)

משתנים מינימליים:

- `GITHUB_USER`
- `PERSONAL_GITHUB_TOKEN`

הַמלָצָה:

- לפחות זכות,
- אין לעשות שימוש חוזר ב-PAT עם הרשאות מיותרות.

הערות מעקב אופרטיבי:

- עבור `PUT /user/following/{username}` ה-PAT הקלאסי חייב לכלול `user:follow`; ללא ההיקף הזה GitHub יכול להשיב `404` למרות שהפרופיל קיים.
- כאשר `404` מתרחש, הבוט מוסיף כעת אבחון ב-`follow_failed.reason` (מצב אימות, היקפים נצפים ומשתמש מאומת) כדי להבדיל בין הרשאות לאי-קיום אמיתי של הפרופיל.

## 2) אסימון התקנה שהונפק מראש

משתנים מינימליים:

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app_installation_token`
- `GITHUB_APP_INSTALLATION_TOKEN`

## 3) זמן ריצה של אפליקציית GitHub (`github_app`)

משתנים מינימליים:

- `GITHUB_USER`
- `BOT_AUTH_MODE=github_app`
- `GITHUB_APP_ID`
- `GITHUB_APP_INSTALLATION_ID`
- **מקור אחד** של מפתח פרטי בדיוק:
    - `GITHUB_APP_PRIVATE_KEY`
    - `GITHUB_APP_PRIVATE_KEY_FILE`
    - `GITHUB_APP_PRIVATE_KEY_COMMAND`

משתני תמיכה:

- `BOT_GITHUB_APP_KEY_COMMAND_TIMEOUT_SECONDS`
- `BOT_GITHUB_APP_TOKEN_REFRESH_SKEW_SECONDS`

## שילובים לא חוקיים

- מספר מקורות מפתח בו זמנית.
- `BOT_AUTH_MODE=github_app_installation_token` ללא `GITHUB_APP_INSTALLATION_TOKEN`.
- `BOT_AUTH_MODE=github_app` ללא `GITHUB_APP_ID`/`GITHUB_APP_INSTALLATION_ID`.
- `BOT_REQUIRE_GITHUB_APP_AUTH=true` במצב שונה מ-`github_app`.

## דוגמה להפעלה מאובטחת

```env
GITHUB_USER=your_user
BOT_AUTH_MODE=pat
PERSONAL_GITHUB_TOKEN=ghp_replace_me
BOT_DRY_RUN=true
```

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

