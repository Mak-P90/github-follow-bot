# Tutoriel pas à pas : MkDocs + publication sur GitHub Pages

**Statut de traduction :** ✅ Vue complétée en français.

Ce tutoriel couvre ce flux exact :

1. Installer MkDocs en local.
2. Lancer la documentation pour le développement.
3. Construire le site statique.
4. Publier sur GitHub Pages.

> Contexte de travail : `other-projects\GitHub_Follower_and_Fork_Bot_Automated-main`

## 1) Entrer dans le projet

### Linux/macOS

```bash
cd /workspace/hostingfinal/other-projects/GitHub_Follower_and_Fork_Bot_Automated-main
```

### Windows (PowerShell)

```powershell
cd "other-projects\GitHub_Follower_and_Fork_Bot_Automated-main"
```

## 2) Créer et activer l’environnement virtuel

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

## 3) Installer les dépendances (inclut MkDocs)

```bash
pip install -r requirements.txt
```

Vérifiez l’installation de MkDocs :

> Note de compatibilité : ce projet fixe `mkdocs-material==9.5.50` pour éviter le warning perturbateur des branches plus récentes de Material liées à MkDocs 2.0, et conserver une expérience stable avec `mkdocs==1.6.1`.

```bash
mkdocs --version
```

## 4) Lancer les docs en local (hot reload)

```bash
mkdocs serve
```

Ouvrez `http://127.0.0.1:8000` pour prévisualiser les changements en direct.

## 5) Construire le site statique

```bash
mkdocs build --strict
```

## 6) Publier sur GitHub Pages

```bash
mkdocs gh-deploy --clean
```

## 7) CI/CD recommandé

- Build docs en PR : `mkdocs build --strict`.
- Déploiement Pages depuis `main` uniquement.
- En cas d’échec CI, corriger d’abord les erreurs de navigation/liens.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

