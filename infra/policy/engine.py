"""Consent/retention/deletion policy checks before follow actions."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FollowDecision:
    allowed: bool
    reason: str


class PolicyEngine:
    """Minimal policy gate to enforce enterprise controls before follow actions."""

    def __init__(
        self,
        require_consent: bool = False,
        denylist: set[str] | None = None,
        retention_window_days: int = 365,
    ) -> None:
        self.require_consent = require_consent
        self.denylist = {entry.lower() for entry in (denylist or set())}
        self.retention_window_days = retention_window_days

    def evaluate_follow(self, username: str, has_consent: bool = True) -> FollowDecision:
        lowered = username.lower().strip()
        if lowered in self.denylist:
            return FollowDecision(allowed=False, reason="denylist")
        if self.require_consent and not has_consent:
            return FollowDecision(allowed=False, reason="missing_consent")
        return FollowDecision(allowed=True, reason="allowed")
