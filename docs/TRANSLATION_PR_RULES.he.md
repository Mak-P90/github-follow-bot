# כללים ל-Pull Request של תרגום

סעיף זה מגדיר את הקריטריונים המינימליים לקבלת שינויים בתרגום התיעוד.

## 1. היקף ומבנה

- לשמור על אותו עץ קבצים כמו בסיס התיעוד בספרדית.
- להשתמש בסיומות שפה בכל עמוד (`.en.md`, `.fr.md`, `.he.md`, `.ru.md`, `.zh.md`).
- לא להסיר סעיפים טכניים מהמסמך המקורי בזמן התרגום.

## 2. איכות תוכן

- לשמר משמעות טכנית, פקודות ודוגמאות תצורה.
- לא לתרגם שמות משתנים, דגלי CLI, שמות טבלאות או מזהי קוד.
- לשמור על בלוקי קוד ועיצוב Markdown.

## 3. עקביות טרמינולוגית

- לעשות שימוש חוזר בגלוסר הפרויקט למונחים חוזרים.
- אם נוסף מונח חדש, לתעד אותו באותה PR.
- להימנע מתרגום מילולי שמשנה הקשר תפעולי.

## 4. דרישות סקירה

- לכלול ב-PR רשימת עמודים מושפעים לפי שפה.
- לצרף הוכחה לבניית MkDocs מקומית מוצלחת.
- לבקש לפחות סקירה אחת ממי שיש לו הקשר טכני למודול שנגעתם בו.

## 5. Checklist מינימלי ל-PR

- [ ] קבצי תרגום נוצרו/עודכנו עם הסיומת הנכונה.
- [ ] ניווט `mkdocs.yml` נבדק עבור שפות חדשות.
- [ ] בוצעה בניית תיעוד מקומית.
- [ ] טרמינולוגיה טכנית נבדקה ונשמרה עקבית.
- [ ] שינויי היקף תועדו (אם רלוונטי).
- [ ] אם נוספו פקודות/דגלים/runbooks תפעוליים, כל וריאציות השפה הזמינות עודכנו באותה PR.

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
