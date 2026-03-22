import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from interfaces.gui.security import redact_gui_payload


def test_redact_gui_payload_redacts_sensitive_keys_and_patterns():
    payload = {
        "token": "ghp_secret",
        "nested": {
            "authorization_header": "Bearer abc123",
            "message": "authorization=Bearer abc123",
            "private_key": "-----BEGIN PRIVATE KEY-----\nabc\n-----END PRIVATE KEY-----",
        },
        "items": [{"api_token": "secret-2"}, "x-api-token=secret-3"],
    }

    redacted = redact_gui_payload(payload)
    assert redacted["token"] == "***REDACTED***"
    assert redacted["nested"]["authorization_header"] == "***REDACTED***"
    assert "***REDACTED***" in redacted["nested"]["message"]
    assert redacted["nested"]["private_key"] == "***REDACTED***"
    assert redacted["items"][0]["api_token"] == "***REDACTED***"
    assert "***REDACTED***" in redacted["items"][1]


def test_redact_gui_payload_preserves_non_sensitive_values():
    payload = {"event": "run_started", "run_id": 7, "stats": {"followers_total": 10}}
    redacted = redact_gui_payload(payload)
    assert redacted == payload
