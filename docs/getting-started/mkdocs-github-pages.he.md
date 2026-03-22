# מדריך צעד אחר צעד: MkDocs + פרסום לדפי GitHub

הדרכה זו מכסה בדיוק את הזרימה הזו:

1. התקן את MkDocs באופן מקומי.
2. הכן תיעוד לפיתוח.
3. בנה את האתר הסטטי.
4. פרסם אותו בדפי GitHub.

> הקשר עבודה: `other-projects\GitHub_Follower_and_Fork_Bot_Automated-main`

---

## 1) היכנסו לפרויקט

### לינוקס/macOS

```bash
cd /workspace/hostingfinal/other-projects/GitHub_Follower_and_Fork_Bot_Automated-main
```

### Windows (PowerShell)

```powershell
cd "other-projects\GitHub_Follower_and_Fork_Bot_Automated-main"
```

---

## 2) צור והפעל סביבה וירטואלית

### לינוקס/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

---

## 3) התקנת תלות (כולל MkDocs)

```bash
pip install -r requirements.txt
```

ודא ש-MkDocs מותקן:

> הערת תאימות: פרויקט זה מצמיד `mkdocs-material==9.5.50` כדי למנוע את האזהרה המפריעה שהוצגה בענפי חומרים חדשים יותר הקשורים ל-MkDocs 2.0 ולשמור על חוויה יציבה עם `mkdocs==1.6.1`.

```bash
mkdocs --version
```

---

## 4) העלה מסמכים באופן מקומי (טעינה מחדש חמה)

```bash
mkdocs serve
```

פתח את `http://127.0.0.1:8000` כדי לסקור שינויים בזמן אמת.

---

## 5) בנה את האתר הסטטי

```bash
mkdocs build --strict
```

פלט צפוי:

- נוצרה תיקיה `site/`.
- בנה ללא אזהרות על קישורים שבורים או שגיאות תצורה.

---

## 6) פרסם בדפי GitHub (`gh-pages` סניף)

תחילה הגדר `mkdocs.yml` עם הנתונים האמיתיים שלך:

- `site_url`
- `repo_url`

ואז פרסם:

```bash
mkdocs gh-deploy --clean
```

זֶה:

- סוג `site/`,
- צור/עדכן סניף `gh-pages`,
- דוחף למאגר המרוחק.

---

## 7) הגדר את דפי GitHub במאגר

ב-GitHub:

1. ויש **הגדרות** → **דפים**.
2. He **בנייה ופריסה**, בחירה **פריסה מסניף**.
3. סניף: `gh-pages`.
4. תיקיה: `/ (root)`.
5. שמור את השינויים.

כתובת האתר הסופית תהיה דומה ל:

- `https://<user-o-org>.github.io/GitHub_Follower_and_Fork_Bot_Automated-main/`

---

## 8) זרימה מומלצת לעדכון מסמכים

בכל פעם שאתה משנה תוכן ב-`docs/` או ב-`mkdocs.yml`:

```bash
mkdocs build --strict
mkdocs gh-deploy --clean
```

עם זה אתה מפרסם את הגרסה העדכנית ביותר של הסניף `main`.

---

## 9) פתרון בעיות מהיר

- **`mkdocs: command not found`**
    - ודא שיש לך venv פעיל ושהפעלת `pip install -r requirements.txt`.
- **שגיאת דחיפה ב-`gh-deploy`**
    - בדוק שיש לך הרשאות כתיבה למאגר המרוחק.
- **העמוד לא מתעדכן**
    - המתן 1-2 דקות (מטמון/בניית דפים) וטען מחדש בדפדפן.

- **`python bot.py doctor` כשל אסימון במצב PAT**
    - השתמש בפורמט הזה:

```bash
BOT_AUTH_MODE=pat PERSONAL_GITHUB_TOKEN=dummy GITHUB_USER=dummy-user python bot.py doctor
```

- בפרויקט זה, עבור `BOT_AUTH_MODE=pat`, המשתנה הצפוי הוא `PERSONAL_GITHUB_TOKEN` (לא `GITHUB_TOKEN`).

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

