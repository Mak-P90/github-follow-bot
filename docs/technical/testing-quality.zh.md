# 测试与质量

## 建议的最小验证集

```bash
python -m py_compile bot.py check_all_followers.py
pytest -q
python bot.py doctor
mkdocs build --strict
```

## 合并前标准

- 上述命令应全部通过。
- 若仓库存在历史技术债导致失败，需明确记录证据与影响范围。
- 任何涉及 CLI/auth/env/持久化/队列/可观测性的功能改动，都必须在同一 PR 中更新文档。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

