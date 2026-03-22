# 安装

## 要求

- Python **3.10+**
- 可访问 GitHub API 的网络
- `pip`
- Docker（可选，仅在你使用容器路径时需要）

## Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Windows（PowerShell）

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

## Shell / 路径说明

- Linux/macOS 使用 `/` 和 `source`。
- PowerShell 使用 `\` 和 `Activate.ps1`。
- Bot 的运行命令一致：`python bot.py <command>`。

## 可选 Docker 路径

```bash
docker build -t github-follower-bot:local .
docker run --rm --env-file .env -v bot_data:/data github-follower-bot:local doctor
```

- 该路径不替代本地 `venv` 安装；两种方式都受支持。
- 若在容器中使用 SQLite，请通过卷保持 `/data` 持久化。

## Sync status (2026-03-20)

This document was reviewed and synchronized against the current repository/runtime contracts on **2026-03-20**.

Validation baseline used for this sync:
- `python bot.py doctor`
- `python bot.py run` / `python bot.py stats`
- `python bot.py queue-stats`
- `python bot.py metrics`
- `./scripts/enterprise_verify.sh`
- `mkdocs build --strict`

