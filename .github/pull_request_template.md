## Summary
- Describe functional changes.
- Describe documentation changes (if applicable).

## Documentation checklist (required when touching behavior)

If this PR touches auth, CLI, env vars, persistence, queue, observability or security:

- [ ] README updated
- [ ] docs/reference/cli.md updated
- [ ] docs/reference/env-vars.md updated
- [ ] relevant getting-started pages updated
- [ ] relevant user-guide pages updated
- [ ] relevant technical pages updated
- [ ] .env.example updated (or explicitly not applicable)

## Validation
- [ ] `python -m py_compile bot.py check_all_followers.py`
- [ ] `pytest -q`
- [ ] `python bot.py doctor`
- [ ] `mkdocs build --strict`
