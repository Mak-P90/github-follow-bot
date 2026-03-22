from __future__ import annotations

import json
from pathlib import Path
from typing import Any

I18N_DIR = Path(__file__).resolve().parent / "locales"


def _read_locale(locale: str) -> dict[str, Any]:
    file_path = I18N_DIR / f"{locale}.json"
    if not file_path.exists():
        return {}
    return json.loads(file_path.read_text(encoding="utf-8"))


class GuiI18n:
    def __init__(self, locale: str, fallback_locale: str = "en") -> None:
        self.catalog = _read_locale(locale)
        self.fallback_catalog = _read_locale(fallback_locale)

    def t(self, key: str) -> str:
        if key in self.catalog:
            return str(self.catalog[key])
        if key in self.fallback_catalog:
            return str(self.fallback_catalog[key])
        return key
