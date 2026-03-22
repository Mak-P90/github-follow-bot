# Step-by-step guide: MkDocs + GitHub Pages publication

> Status: ✅ Completed in British English.

This guide covers this exact flow:

1. Install MkDocs locally.
2. Run docs locally for development.
3. Build the static site.
4. Publish to GitHub Pages.

> Working context: `other-projects/GitHub_Follower_and_Fork_Bot_Automated-main`

## 1) Enter the project

### Linux/macOS

```bash
cd /workspace/hostingfinal/other-projects/GitHub_Follower_and_Fork_Bot_Automated-main
```

### Windows (PowerShell)

```powershell
cd "other-projects\GitHub_Follower_and_Fork_Bot_Automated-main"
```

## 2) Create and activate virtual environment

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

## 3) Install dependencies (including MkDocs)

```bash
pip install -r requirements.txt
```

Compatibility note: this project pins `mkdocs-material==9.5.50` to avoid disruptive warnings introduced in newer Material branches related to MkDocs 2.0, maintaining a stable experience with `mkdocs==1.6.1`.

```bash
mkdocs --version
```

## 4) Run docs locally (hot reload)

```bash
mkdocs serve
```

Open `http://127.0.0.1:8000` to review live changes.

## 5) Build static site

```bash
mkdocs build --strict
```

Expected output:

- `site/` folder generated.
- Build completes without broken-link warnings or configuration errors.

## 6) Publish to GitHub Pages (`gh-pages` branch)

First configure `mkdocs.yml` with real values:

- `site_url`
- `repo_url`

Then publish:

```bash
mkdocs gh-deploy --clean
```

This command:

- generates `site/`,
- creates/updates the `gh-pages` branch,
- pushes to the remote repository.

## 7) Configure GitHub Pages in repository settings

On GitHub:

1. Go to **Settings** → **Pages**.
2. In **Build and deployment**, select **Deploy from a branch**.
3. Branch: `gh-pages`.
4. Folder: `/ (root)`.
5. Save.

Final URL will look like:

- `https://<user-or-org>.github.io/GitHub_Follower_and_Fork_Bot_Automated-main/`

## 8) Recommended update flow

Whenever you change `docs/` or `mkdocs.yml`:

```bash
mkdocs build --strict
mkdocs gh-deploy --clean
```

This publishes the latest version from `main`.

## 9) Quick troubleshooting

- **`mkdocs: command not found`**
    - Ensure the virtual environment is active and you ran `pip install -r requirements.txt`.
- **Push error on `gh-deploy`**
    - Confirm you have write permissions on the remote repo.
- **Page not updating**
    - Wait 1–2 minutes (Pages cache/build delay) and force-refresh your browser.

- **`python bot.py doctor` fails for token in PAT mode**
    - Use:

```bash
BOT_AUTH_MODE=pat PERSONAL_GITHUB_TOKEN=dummy GITHUB_USER=dummy-user python bot.py doctor
```

In this project, `BOT_AUTH_MODE=pat` expects `PERSONAL_GITHUB_TOKEN` (not `GITHUB_TOKEN`).

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

