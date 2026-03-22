# Plan de Pull Requests para contribuciones

Este documento define la **guía mínima obligatoria** para que cualquier dev proponga cambios por Pull Request (PR) de forma consistente, auditable y alineada con las reglas de este repositorio.

## Flujo resumido

1. Preparar rama desde `main` con nombre claro (`feat/...`, `fix/...`, `docs/...`).
2. Completar la plantilla de PR siguiendo las secciones de este plan.
3. Ejecutar validaciones mínimas obligatorias (según tipo de cambio).
4. Abrir PR con evidencia técnica y checklist de cumplimiento.
5. Atender review sin perder trazabilidad (comentarios, decisiones y cambios).

---

## Estructura obligatoria del PR

### 1) Doc

Incluye documentación clara para que reviewers y operadores entiendan el cambio:

- **Resumen corto** (qué cambia y por qué).
- **Alcance** (módulos/archivos afectados).
- **Impacto operativo** (si cambia ejecución, auth, colas, persistencia o seguridad).
- **Documentación actualizada**:
  - `README.md` cuando cambie comportamiento visible.
  - `ENTERPRISE_HARDENING_ASSESSMENT.md` cuando aplique a controles enterprise/hardening.

### 2) Problema

Describe el problema de origen con evidencia:

- Síntoma observable.
- Contexto (cuándo ocurre, a quién afecta, severidad).
- Evidencia reproducible (logs, salida de comandos, tests, issue vinculada).
- Riesgo de no corregir.

### 3) Solución

Explica la estrategia aplicada:

- Decisión técnica principal y alternativas descartadas.
- Cambios realizados por capa (configuración, dominio, adapters, persistencia, CLI, docs).
- Compatibilidad hacia atrás y plan de migración (si hay cambios de contrato).
- Riesgos residuales y mitigaciones.

### 4) Normas cumplidas mínimas

Checklist mínimo que debe estar marcado antes de pedir merge:

- [ ] Cambio dividido por responsabilidad (sin funciones gigantes mezclando red + SQL + negocio).
- [ ] Secretos fuera de código y logs sanitizados.
- [ ] Idempotencia preservada (si toca follow/colas).
- [ ] Evidencia de validación incluida en el PR.
- [ ] Documentación actualizada (`README.md` y/o assessment cuando aplique).
- [ ] Artefactos locales no versionados (`.db`, logs, `__pycache__`, etc.).

**Si se modifica código Python**, adjuntar salida de:

- `python -m py_compile bot.py check_all_followers.py`
- `pytest -q`
- `python bot.py doctor`

### 5) Normas opcionales (recomendadas)

No bloquean por sí solas, pero mejoran la calidad del PR:

- [ ] Añadir/actualizar ADR si cambia arquitectura o contratos relevantes.
- [ ] Incluir plan de rollback explícito.
- [ ] Adjuntar ejemplos de uso CLI antes/después.
- [ ] Añadir métricas esperadas (latencia, volumen, errores) para facilitar observabilidad.
- [ ] Proponer tareas futuras (tech debt) con alcance acotado.

### 6) Normas no cumplidas por...

Si algo no se cumple, se debe declarar **de forma explícita**:

- Norma no cumplida.
- Motivo concreto (deuda previa, dependencia externa, limitación de entorno, etc.).
- Riesgo asumido.
- Plan y fecha estimada de cierre.
- Responsable de seguimiento.

> No se acepta “pendiente” sin owner ni plan.

---

## Plantilla sugerida para descripción del PR

```md
## 1) Doc
- Resumen:
- Alcance:
- Impacto operativo:
- Docs actualizadas:

## 2) Problema
- Síntoma:
- Contexto:
- Evidencia:
- Riesgo:

## 3) Solución
- Estrategia:
- Cambios por capa:
- Compatibilidad/migración:
- Riesgos residuales:

## 4) Normas cumplidas mínimas
- [ ] Arquitectura por capas respetada
- [ ] Secretos/logging conforme
- [ ] Idempotencia preservada
- [ ] Validación ejecutada
- [ ] README/Assessment actualizados cuando aplica
- [ ] Higiene de repo conforme

### Evidencia de validación
- `python -m py_compile bot.py check_all_followers.py`
- `pytest -q`
- `python bot.py doctor`

## 5) Normas opcionales
- [ ] ADR actualizado
- [ ] Plan de rollback
- [ ] Ejemplos CLI antes/después
- [ ] Métricas esperadas

## 6) Normas no cumplidas por...
- Norma:
- Motivo:
- Riesgo:
- Plan de cierre:
- Responsable:
```

## Criterio de aceptación para merge

Un PR está listo para merge cuando:

1. Secciones 1-6 completas (sin campos críticos vacíos).
2. Validaciones mínimas ejecutadas o excepción justificada con owner + plan.
3. No introduce regresiones de seguridad, persistencia o contratos de auth.
4. Mantiene trazabilidad suficiente para auditoría posterior.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

