## Reglas de trabajo (resumen)

1. **Arquitectura por capas**
    - Mantener separación entre dominio/aplicación/adapters/infra.
    - Evitar mezclar lógica de negocio con IO de red/DB en funciones grandes.


2. **Persistencia y trazabilidad**
    - Persistencia operativa en SQLite/PostgreSQL (no TXT como fuente principal).
    - Mantener `run_id` en ejecuciones y eventos críticos.

3. **Seguridad de secretos**
    - No hardcodear credenciales.
    - No exponer secretos en logs/errores.

4. **Calidad mínima al tocar Python**
    - Ejecutar:
        - `python -m py_compile bot.py check_all_followers.py`
        - `pytest -q`
        - `python bot.py doctor`

5. **Documentación viva (sin ruido)**
    - Actualizar `README.md` cuando cambie el comportamiento visible.
    - Actualizar `ENTERPRISE_HARDENING_ASSESSMENT.md` cuando cambie el estado de hardening.
    - Evitar checklists históricas y planes cerrados en docs públicas.

6. **Higiene de repositorio**
    - No versionar logs, `.db`, caches ni artefactos locales.
    - Mantener `.gitignore` al día cuando aparezcan nuevos artefactos.

## Criterio práctico

Si una regla detallada ya está automatizada en `scripts/enterprise_verify.sh` o CI, no duplicarla como checklist manual extensa en documentación.