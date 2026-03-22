# Translation Pull Request Rules

This section defines the minimum criteria to accept documentation translation changes.

## 1. Scope and structure

- Keep the same file tree as the Spanish base documentation.
- Use language suffixes on every page (`.en.md`, `.fr.md`, `.he.md`, `.ru.md`, `.zh.md`).
- Do not remove technical sections from the original document during translation.

## 2. Content quality

- Preserve technical meaning, commands, and configuration examples.
- Do not translate variable names, CLI flags, table names, or code identifiers.
- Keep code blocks and Markdown formatting intact.

## 3. Terminology consistency

- Reuse the project glossary for recurring terms.
- If a new term is introduced, document it in the same PR.
- Avoid literal translations that alter operational context.

## 4. Review requirements

- Include in the PR the list of affected pages by language.
- Attach evidence of a successful local MkDocs build.
- Request at least one review from someone with technical context for the touched module.

## 5. Minimum PR checklist

- [ ] Translated files created/updated with the correct suffix.
- [ ] `mkdocs.yml` navigation validated for new languages.
- [ ] Documentation build executed locally.
- [ ] Technical terminology reviewed and consistent.
- [ ] Scope changes documented (if applicable).
- [ ] If operational commands/flags/runbooks are added, every available language variant is updated in the same PR.

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
