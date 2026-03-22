# Reglas para Pull Requests de traducción

Este apartado define los criterios mínimos para aceptar cambios de traducción de documentación.

## 1. Alcance y estructura

- Mantener el mismo árbol de archivos que la documentación base en español.
- Usar el sufijo por idioma en cada página (`.en.md`, `.fr.md`, `.he.md`, `.ru.md`, `.zh.md`).
- No eliminar secciones técnicas del documento original durante la traducción.

## 2. Calidad del contenido

- Conservar significado técnico, comandos y ejemplos de configuración.
- No traducir nombres de variables, flags CLI, nombres de tablas o identificadores de código.
- Mantener bloques de código y formatos Markdown intactos.

## 3. Consistencia de terminología

- Reutilizar glosario existente del proyecto para términos recurrentes.
- Si se introduce un término nuevo, documentarlo en la misma PR.
- Evitar traducciones literales que cambien el contexto operativo.

## 4. Requisitos de revisión

- Incluir en la PR la lista de páginas afectadas por idioma.
- Adjuntar evidencia de build local de MkDocs sin errores.
- Solicitar al menos una revisión de alguien con contexto técnico del módulo tocado.

## 5. Checklist mínimo en la PR

- [ ] Archivos traducidos creados/actualizados con sufijo correcto.
- [ ] Navegación de `mkdocs.yml` validada para los nuevos idiomas.
- [ ] Build de documentación ejecutado localmente.
- [ ] Terminología técnica revisada y consistente.
- [ ] Cambios de alcance documentados (si aplica).
- [ ] Si se agregan comandos/flags o runbooks operativos, se actualizan **todas** las variantes de idioma disponibles en la misma PR.

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
