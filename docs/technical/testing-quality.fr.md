# Tests et qualité

**Statut de traduction :** ✅ Vue complétée en français.

**Statut de traduction :** ✅ Vue complétée en français.

## Validation minimale recommandée

```bash
python -m py_compile bot.py check_all_followers.py
pytest -q
python bot.py doctor
mkdocs build --strict
```

## Critère avant merge

- Les commandes ci-dessus doivent réussir.
- Si une dette préexistante bloque, documenter la preuve exacte et le périmètre.
- Tout changement fonctionnel sur CLI/auth/env/persistance/file/observabilité doit inclure une mise à jour documentaire dans la même PR.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

