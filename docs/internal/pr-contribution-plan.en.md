# Pull Request Contribution Plan

> Status: ✅ Completed in British English.

This document defines the **minimum mandatory guide** for proposing changes through Pull Requests (PRs) in a consistent, auditable way aligned with this repository’s rules.

## Summary flow

1. Create a branch from `main` with a clear name (`feat/...`, `fix/...`, `docs/...`).
2. Complete the PR template using this plan’s sections.
3. Run the required validations (based on change type).
4. Open the PR with technical evidence and a compliance checklist.
5. Address review feedback while preserving traceability.

## Required PR structure

### 1) Documentation

Include enough context so reviewers and operators understand the change:

- **Short summary** (what changed and why).
- **Scope** (affected modules/files).
- **Operational impact** (if execution, auth, queue, persistence, or security changed).
- **Updated documentation**:
    - `README.md` when visible behaviour changes.
    - `ENTERPRISE_HARDENING_ASSESSMENT.md` when enterprise/hardening controls are affected.

### 2) Problem

Describe the root issue with evidence:

- Observable symptom.
- Context (when it occurs, who is affected, severity).
- Reproducible evidence (logs, command output, tests, linked issue).
- Risk if left unresolved.

### 3) Solution

Explain the selected strategy:

- Primary technical decision and discarded alternatives.
- Changes by layer (configuration, domain, adapters, persistence, CLI, docs).
- Backward compatibility and migration plan (if contracts changed).
- Residual risks and mitigations.

### 4) Minimum required standards

Checklist to complete before requesting merge:

- [ ] Responsibility boundaries respected (no giant functions mixing network + SQL + business logic).
- [ ] Secrets kept out of code and logs sanitised.
- [ ] Idempotency preserved (when follow/queue flows are touched).
- [ ] Validation evidence included in the PR.
- [ ] Documentation updated (`README.md` and/or assessment when applicable).
- [ ] Repository hygiene respected (no local artefacts: `.db`, logs, `__pycache__`, etc.).

If Python code is modified, include output for:

- `python -m py_compile bot.py check_all_followers.py`
- `pytest -q`
- `python bot.py doctor`

### 5) Optional standards (recommended)

- [ ] Add/update ADR if architecture or key contracts changed.
- [ ] Include an explicit rollback plan.
- [ ] Provide CLI usage examples before/after.
- [ ] Add expected metrics (latency, volume, error rate) for observability.
- [ ] Propose bounded next steps for technical debt.

### 6) Standards not met because...

If any standard is not met, declare it **explicitly**:

- unmet standard,
- concrete reason,
- temporary mitigation,
- closure plan.

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

