from __future__ import annotations

import re
from typing import Any

SENSITIVE_KEY_PARTS = ("token", "secret", "authorization", "private_key", "password")
SENSITIVE_TEXT_PATTERNS = (
    re.compile(r"(?i)(authorization\s*[:=]\s*(?:bearer|token)\s+)([^\s,;\"']+)"),
    re.compile(r"(?i)(x-?(?:api-)?token\s*[:=]\s*\"?)([^\s,;\"'}]+)"),
    re.compile(r"(?i)(\"?private_key\"?\s*[:=]\s*\"?)([^\s,;\"'}]+)"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----"),
)


def _is_sensitive_key(key: str) -> bool:
    lowered = key.lower()
    return any(part in lowered for part in SENSITIVE_KEY_PARTS)


def _redact_text(value: str) -> str:
    redacted = value
    for pattern in SENSITIVE_TEXT_PATTERNS:
        if pattern.groups >= 2:
            redacted = pattern.sub(r"\1***REDACTED***", redacted)
        else:
            redacted = pattern.sub("***REDACTED_PRIVATE_KEY***", redacted)
    return redacted


def redact_gui_payload(payload: Any) -> Any:
    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if _is_sensitive_key(str(key)):
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = redact_gui_payload(value)
        return sanitized
    if isinstance(payload, list):
        return [redact_gui_payload(item) for item in payload]
    if isinstance(payload, tuple):
        return tuple(redact_gui_payload(item) for item in payload)
    if isinstance(payload, str):
        return _redact_text(payload)
    return payload
