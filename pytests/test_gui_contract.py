import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import bot
from interfaces.gui.i18n import GuiI18n
from interfaces.gui.i18n import _read_locale


def _set_base_env(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_USER", "user")
    monkeypatch.setenv("PERSONAL_GITHUB_TOKEN", "token")
    monkeypatch.setenv("BOT_DB_PATH", str(tmp_path / "state.db"))


def test_gui_i18n_fallback():
    i18n = GuiI18n(locale="es", fallback_locale="en")
    assert i18n.t("nav.dashboard") == "Panel"
    assert i18n.t("non.existing.key") == "non.existing.key"


def test_gui_i18n_locale_key_parity():
    en = _read_locale("en")
    es = _read_locale("es")
    assert set(en.keys()) == set(es.keys())


def test_cli_gui_disabled_by_default(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)

    exit_code = bot.main(["gui"])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["event"] == "gui_disabled"


def test_cli_gui_missing_dependency(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_GUI_ENABLED", "true")

    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "nicegui":
            raise ModuleNotFoundError("No module named 'nicegui'")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    exit_code = bot.main(["gui"])
    assert exit_code == 2

    payload = json.loads(capsys.readouterr().out)
    assert payload["event"] == "gui_dependency_missing"


def test_cli_gui_launches_when_enabled(monkeypatch, tmp_path, capsys):
    _set_base_env(monkeypatch, tmp_path)
    monkeypatch.setenv("BOT_GUI_ENABLED", "true")
    monkeypatch.setenv("BOT_GUI_HOST", "127.0.0.1")
    monkeypatch.setenv("BOT_GUI_PORT", "8099")
    monkeypatch.setenv("BOT_GUI_LOCALE", "es")

    monkeypatch.setattr(bot, "run_gui", lambda *_args, **_kwargs: None)
    real_import = __import__

    def fake_import(name, *args, **kwargs):
        if name == "nicegui":
            return object()
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr("builtins.__import__", fake_import)

    exit_code = bot.main(["gui"])
    assert exit_code == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["event"] == "gui_started"
    assert payload["port"] == 8099
    assert payload["locale"] == "es"
