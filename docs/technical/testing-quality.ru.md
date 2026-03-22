# Тестирование и качество

## Минимальная рекомендуемая проверка

```bash
python -m py_compile bot.py check_all_followers.py
pytest -q
python bot.py doctor
mkdocs build --strict
```

## Критерий перед слиянием

- Вышеуказанные команды должны пройти.
- Если ранее существовала задолженность по репо, задокументируйте точные доказательства и объем сделки.
- Любое функциональное изменение в CLI/auth/env/persistence/queue/observability должно включать документальное обновление в том же PR.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

