# Пошаговое руководство: MkDocs + публикация на страницах GitHub

В этом уроке рассматривается именно этот поток:

1. Установите MkDocs локально.
2. Подготовить документацию для разработки.
3. Создайте статический сайт.
4. Опубликуйте его на страницах GitHub.

> Рабочий контекст:`other-projects\GitHub_Follower_and_Fork_Bot_Automated-main`

---

## 1) Войдите в проект

### Linux/macOS

```bash
cd /workspace/hostingfinal/other-projects/GitHub_Follower_and_Fork_Bot_Automated-main
```

### Windows (PowerShell)

```powershell
cd "other-projects\GitHub_Follower_and_Fork_Bot_Automated-main"
```

---

## 2) Создайте и активируйте виртуальную среду.

### Linux/macOS

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

## 3) Установите зависимости (включая MkDocs)

```bash
pip install -r requirements.txt
```

Убедитесь, что MkDocs установлен:

> Примечание о совместимости: этот проект исправляет`mkdocs-material==9.5.50`чтобы избежать тревожного предупреждения, представленного в новых ветках материалов, связанных с MkDocs 2.0, и поддерживать стабильную работу с`mkdocs==1.6.1`.

```bash
mkdocs --version
```

---

## 4) Загрузить документы локально (горячая перезагрузка)

```bash
mkdocs serve
```

Открыть`http://127.0.0.1:8000`просматривать изменения в реальном времени.

---

## 5) Создайте статический сайт

```bash
mkdocs build --strict
```

Ожидаемый результат:

- Файл`site/`генерируется.
- Сборка без предупреждений о неработающих ссылках или ошибках конфигурации.

---

## 6) Публикация на страницах GitHub (ветвь`gh-pages`)

Сначала настройте`mkdocs.yml`с вашими реальными данными:

- `site_url`
- `repo_url`

Затем опубликуйте:

```bash
mkdocs gh-deploy --clean
```

Этот:

- роды`site/`,
- создать/обновить ветку`gh-pages`,
  — отправляет в удаленный репозиторий.

---

## 7) Настройте страницы GitHub в репозитории.

На Гитхабе:

1. Откройте **Настройки** → **Страницы**.
2. В разделе **Сборка и развертывание** выберите **Развертывание из ветки**.
3. Филиал:`gh-pages`.
4. Папка:`/ (root)`.
5. Сохраните изменения.

Конечный URL будет похож на:

- `https://<user-o-org>.github.io/GitHub_Follower_and_Fork_Bot_Automated-main/`

---

## 8) Рекомендуемый порядок обновления документов

Каждый раз, когда вы меняете контент в`docs/`о`mkdocs.yml`:

```bash
mkdocs build --strict
mkdocs gh-deploy --clean
```

При этом вы публикуете самую последнюю версию ветки`main`.

---

## 9) Быстрое устранение неполадок

- **`mkdocs: command not found`**
- Убедитесь, что у вас активен venv и вы запустили`pip install -r requirements.txt`.
- ** Вставить ошибку`gh-deploy`**
- Убедитесь, что у вас есть права на запись в удаленный репозиторий.
- **Страница не обновляется**
- Подождите 1–2 минуты (кэш/сборка страниц) и выполните полную перезагрузку браузера.

- **`python bot.py doctor`сбой токена в режиме PAT**
- Используйте этот формат:

```bash
BOT_AUTH_MODE=pat PERSONAL_GITHUB_TOKEN=dummy GITHUB_USER=dummy-user python bot.py doctor
```

- В этом проекте`BOT_AUTH_MODE=pat`, ожидаемая переменная равна`PERSONAL_GITHUB_TOKEN`(нет`GITHUB_TOKEN`).

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

