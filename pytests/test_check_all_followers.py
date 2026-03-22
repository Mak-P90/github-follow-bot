import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import check_all_followers


def test_operational_report_contains_run_id(monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_DB_PATH", str(tmp_path / "state.db"))

    monkeypatch.setattr(check_all_followers.GitHubClient, "check_rate_limit", lambda self: (5000, 1234567890))

    rc = check_all_followers.main()
    assert rc == 0

    out = capsys.readouterr().out
    payload = json.loads(out)
    assert payload["run_id"].startswith("report-")
    assert payload["trace_id"].startswith("trace-")
    assert payload["auth_mode"] == "pat"
    assert "followers_total_seen" in payload
