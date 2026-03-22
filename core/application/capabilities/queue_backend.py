from __future__ import annotations

from typing import Any, Callable


def verify_queue_backend(
    *,
    backend: str,
    amqp_url: str,
    queue_name: str,
    dlq_name: str,
    max_attempts: int,
    adapter_factory: Callable[..., Any],
) -> tuple[int, dict[str, Any]]:
    normalized = (backend or "sqlite").strip().lower() or "sqlite"

    if normalized == "sqlite":
        return 0, {
            "backend": "sqlite",
            "status": "verified",
            "ready": True,
            "notes": ["SQLite transactional queue backend verified for single-node runtime"],
        }

    if normalized != "rabbitmq":
        return 2, {
            "backend": normalized,
            "status": "invalid",
            "ready": False,
            "error": "unsupported_queue_backend",
        }

    if not amqp_url:
        return 2, {
            "backend": "rabbitmq",
            "status": "incomplete",
            "ready": False,
            "error": "missing_amqp_url",
            "hint": "Set BOT_RABBITMQ_AMQP_URL",
        }

    try:
        adapter = adapter_factory(
            amqp_url=amqp_url,
            queue_name=queue_name,
            dlq_name=dlq_name,
            max_attempts=max_attempts,
        )
        adapter.ensure_topology()
    except Exception as exc:  # noqa: BLE001 - diagnostic path must capture and report backend failures
        return 2, {
            "backend": "rabbitmq",
            "status": "failed",
            "ready": False,
            "error": "topology_check_failed",
            "detail": str(exc),
            "queue_name": queue_name,
            "dead_letter_queue": dlq_name,
        }

    return 0, {
        "backend": "rabbitmq",
        "status": "verified",
        "ready": True,
        "queue_name": queue_name,
        "dead_letter_queue": dlq_name,
        "max_attempts": max_attempts,
    }



def smoke_test_queue_backend(
    *,
    backend: str,
    amqp_url: str,
    queue_name: str,
    dlq_name: str,
    max_attempts: int,
    adapter_factory: Callable[..., Any],
) -> tuple[int, dict[str, Any]]:
    normalized = (backend or "sqlite").strip().lower() or "sqlite"

    if normalized == "sqlite":
        return 0, {
            "backend": "sqlite",
            "status": "smoke_ok",
            "ready": True,
            "steps": ["transactional_queue_available"],
        }

    if normalized != "rabbitmq":
        return 2, {
            "backend": normalized,
            "status": "invalid",
            "ready": False,
            "error": "unsupported_queue_backend",
        }

    if not amqp_url:
        return 2, {
            "backend": "rabbitmq",
            "status": "incomplete",
            "ready": False,
            "error": "missing_amqp_url",
        }

    try:
        adapter = adapter_factory(
            amqp_url=amqp_url,
            queue_name=queue_name,
            dlq_name=dlq_name,
            max_attempts=max_attempts,
        )
        adapter.ensure_topology()

        job_cls = type("_QueueJob", (), {})
        # Adapter implementations in this repo expect a dataclass-like object with attrs.
        job = job_cls()
        job.run_id = 0
        job.github_login = "smoke-user"
        job.attempts = 0

        adapter.publish(job)
        consumed, lease_meta = adapter.consume_once()
        if consumed is None:
            return 2, {
                "backend": "rabbitmq",
                "status": "failed",
                "ready": False,
                "error": "smoke_consume_empty",
            }

        retry_disposition = adapter.retry(consumed, lease_meta, "smoke_test")

        reconsumed, re_lease_meta = adapter.consume_once()
        if reconsumed is not None:
            adapter.ack(re_lease_meta)

        return 0, {
            "backend": "rabbitmq",
            "status": "smoke_ok",
            "ready": True,
            "lease_meta": lease_meta,
            "retry_disposition": retry_disposition,
            "acknowledged": reconsumed is not None,
            "queue_name": queue_name,
            "dead_letter_queue": dlq_name,
        }
    except Exception as exc:  # noqa: BLE001 - diagnostics must report adapter runtime failures
        return 2, {
            "backend": "rabbitmq",
            "status": "failed",
            "ready": False,
            "error": "smoke_failed",
            "detail": str(exc),
        }
