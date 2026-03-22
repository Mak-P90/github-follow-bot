from __future__ import annotations

from typing import Any


def build_telemetry_attributes(
    *,
    capability: str,
    run_id: int | None = None,
    trace_id: str | None = None,
    job_id: str | int | None = None,
    **extra: Any,
) -> dict[str, Any]:
    attrs: dict[str, Any] = {"capability": capability}
    if run_id is not None:
        attrs["run_id"] = run_id
    if trace_id:
        attrs["trace_id"] = trace_id
    if job_id is not None:
        attrs["job_id"] = str(job_id)
    attrs.update(extra)
    return attrs
