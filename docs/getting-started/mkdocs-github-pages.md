# Tutorial paso a paso: MkDocs + publicación en GitHub Pages

Este tutorial cubre exactamente este flujo:

1. Instalar MkDocs en local.
2. Levantar la documentación para desarrollo.
3. Construir el sitio estático.
4. Publicarlo en GitHub Pages.

> Contexto de trabajo: `other-projects\GitHub_Follower_and_Fork_Bot_Automated-main`

---

## 1) Entrar al proyecto

### Linux/macOS

```bash
cd /workspace/hostingfinal/other-projects/GitHub_Follower_and_Fork_Bot_Automated-main
```

### Windows (PowerShell)

```powershell
cd "other-projects\GitHub_Follower_and_Fork_Bot_Automated-main"
```

---

## 2) Crear y activar entorno virtual

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

## 3) Instalar dependencias (incluye MkDocs)

```bash
pip install -r requirements.txt
```

Verifica que MkDocs quedó instalado:


> Nota de compatibilidad: este proyecto fija `mkdocs-material==9.5.50` para evitar el warning disruptivo introducido en ramas más nuevas de Material relacionadas con MkDocs 2.0 y mantener una experiencia estable con `mkdocs==1.6.1`.


```bash
mkdocs --version
```

---

## 4) Levantar docs en local (hot reload)

```bash
mkdocs serve
```

Abre `http://127.0.0.1:8000` para revisar cambios en vivo.

---

## 5) Construir el sitio estático

```bash
mkdocs build --strict
```

Salida esperada:

- Carpeta `site/` generada.
- Build sin warnings de enlaces rotos ni errores de configuración.

---

## 6) Publicar en GitHub Pages (rama `gh-pages`)

Primero configura `mkdocs.yml` con tus datos reales:

- `site_url`
- `repo_url`

Luego publica:

```bash
mkdocs gh-deploy --clean
```

Esto:

- genera `site/`,
- crea/actualiza la rama `gh-pages`,
- hace push al remoto del repositorio.

---

## 7) Configurar GitHub Pages en el repositorio

En GitHub:

1. Ve a **Settings** → **Pages**.
2. En **Build and deployment**, selecciona **Deploy from a branch**.
3. Branch: `gh-pages`.
4. Folder: `/ (root)`.
5. Guarda los cambios.

La URL final quedará similar a:

- `https://<user-o-org>.github.io/GitHub_Follower_and_Fork_Bot_Automated-main/`

---

## 8) Flujo recomendado para actualizar docs

Cada vez que cambies contenido en `docs/` o `mkdocs.yml`:

```bash
mkdocs build --strict
mkdocs gh-deploy --clean
```

Con eso publicas la versión más reciente del branch `main`.

---

## 9) Troubleshooting rápido

- **`mkdocs: command not found`**
  - Asegúrate de tener el venv activo y haber ejecutado `pip install -r requirements.txt`.
- **Error de push en `gh-deploy`**
  - Revisa que tengas permisos de escritura en el repo remoto.
- **Página no actualiza**
  - Espera 1-2 minutos (caché/build de Pages) y recarga duro en navegador.

- **`python bot.py doctor` falla por token en modo PAT**
  - Usa este formato:

```bash
BOT_AUTH_MODE=pat PERSONAL_GITHUB_TOKEN=dummy GITHUB_USER=dummy-user python bot.py doctor
```

  - En este proyecto, para `BOT_AUTH_MODE=pat`, la variable esperada es `PERSONAL_GITHUB_TOKEN` (no `GITHUB_TOKEN`).

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

