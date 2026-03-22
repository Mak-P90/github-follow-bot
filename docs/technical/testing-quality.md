# Testing and Quality

## Validación mínima recomendada

```bash
python -m py_compile bot.py check_all_followers.py
pytest -q
python bot.py doctor
mkdocs build --strict
```

## Criterio antes de merge

- Los comandos anteriores deben pasar.
- Si hay deuda previa del repo, documentar evidencia exacta y alcance.
- Cualquier cambio funcional en CLI/auth/env/persistencia/cola/observabilidad debe incluir actualización documental en el mismo PR.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

