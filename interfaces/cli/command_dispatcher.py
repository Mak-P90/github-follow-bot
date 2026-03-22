from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Callable


@dataclass(frozen=True)
class CliCommandContext:
    config: Any
    logger: Any
    storage: Any
    build_follow_back_service: Callable[..., Any]
    build_storage: Callable[[Any], Any]
    execute_run: Callable[..., Any]
    handle_default_run_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_worker_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_resume_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_abort_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_fork_repos_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_scheduler_command: Callable[..., tuple[int, dict[str, Any]]]
    handle_control_plane_status: Callable[..., tuple[int, dict[str, Any]]]
    serve_control_plane: Callable[..., None]
    verify_queue_backend: Callable[..., tuple[int, dict[str, Any]]]
    smoke_test_queue_backend: Callable[..., tuple[int, dict[str, Any]]]
    queue_adapter_factory: Any
    doctor_report: Callable[..., dict[str, Any]]
    runtime_file_hardening_check: Callable[..., dict[str, Any]]
    export_queue_backend_status: Callable[..., dict[str, Any]]
    export_compliance_evidence_status: Callable[..., dict[str, Any]]
    export_otel_runtime_status: Callable[..., dict[str, Any]]
    export_otel_bootstrap: Callable[..., dict[str, Any]]
    export_otel_operations_profile: Callable[..., dict[str, Any]]
    export_queue_worker_topology_profile: Callable[..., dict[str, Any]]
    export_postgres_cutover_profile: Callable[..., dict[str, Any]]
    export_dual_write_consistency_report: Callable[..., dict[str, Any]]
    export_zero_trust_profile: Callable[..., dict[str, Any]]
    export_release_integrity_profile: Callable[..., dict[str, Any]]
    export_governance_profile: Callable[..., dict[str, Any]]
    export_enterprise_readiness_report: Callable[..., dict[str, Any]]
    evaluate_enterprise_readiness_gate: Callable[..., tuple[int, dict[str, Any]]]
    export_enterprise_backlog_status: Callable[..., dict[str, Any]]
    export_enterprise_remaining_work: Callable[..., dict[str, Any]]
    export_enterprise_handoff_report: Callable[..., dict[str, Any]]
    resolve_command_output_path: Callable[[str], Any]
    launch_gui: Callable[..., tuple[int, dict[str, Any]]]


def _queue_backend_env() -> tuple[str, str, str, str]:
    backend = os.getenv("BOT_QUEUE_BACKEND", "sqlite")
    amqp_url = os.getenv("BOT_RABBITMQ_AMQP_URL", "").strip()
    queue_name = os.getenv("BOT_RABBITMQ_QUEUE", "follow_jobs").strip() or "follow_jobs"
    dlq_name = os.getenv("BOT_RABBITMQ_DLQ", "follow_jobs.dead_letter").strip() or "follow_jobs.dead_letter"
    return backend, amqp_url, queue_name, dlq_name


def dispatch_cli_command(command: str, args: Any, ctx: CliCommandContext) -> int:
    config = ctx.config
    storage = ctx.storage

    if command == "stats":
        stats = storage.get_stats()
        stats["last_run"] = storage.get_last_run()
        print(json.dumps(stats, indent=2))
        return 0

    if command == "doctor":
        print(json.dumps(ctx.doctor_report(config, storage), indent=2))
        return 0

    if command == "control-plane-status":
        status, payload = ctx.handle_control_plane_status(storage, config)
        print(json.dumps(payload, indent=2))
        return status

    if command == "otel-runtime-status":
        payload = ctx.export_otel_runtime_status(config)
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "ready" else 2

    if command == "metrics":
        print(storage.export_prometheus_metrics(), end="")
        return 0

    if command == "check-file-hardening":
        payload = ctx.runtime_file_hardening_check(config)
        print(json.dumps(payload, indent=2))
        return 0 if payload["ok"] else 2

    if command == "queue-backend-status":
        payload = ctx.export_queue_backend_status(config)
        print(json.dumps(payload, indent=2))
        return 0 if payload.get("ready") else 2

    if command == "queue-backend-verify":
        backend, amqp_url, queue_name, dlq_name = _queue_backend_env()
        status, payload = ctx.verify_queue_backend(
            backend=backend,
            amqp_url=amqp_url,
            queue_name=queue_name,
            dlq_name=dlq_name,
            max_attempts=config.follow_job_max_attempts,
            adapter_factory=ctx.queue_adapter_factory,
        )
        print(json.dumps(payload, indent=2))
        return status

    if command == "queue-backend-smoke":
        backend, amqp_url, queue_name, dlq_name = _queue_backend_env()
        status, payload = ctx.smoke_test_queue_backend(
            backend=backend,
            amqp_url=amqp_url,
            queue_name=queue_name,
            dlq_name=dlq_name,
            max_attempts=config.follow_job_max_attempts,
            adapter_factory=ctx.queue_adapter_factory,
        )
        print(json.dumps(payload, indent=2))
        return status

    if command == "compliance-evidence-status":
        payload = ctx.export_compliance_evidence_status(args.evidence_dir)
        print(json.dumps(payload, indent=2))
        return 0 if payload["status"] == "ready" else 2

    if command == "queue-stats":
        print(json.dumps(storage.get_follow_job_stats(run_id=getattr(args, "run_id", None)), indent=2))
        return 0

    if command == "worker":
        service = ctx.build_follow_back_service(config, ctx.logger)
        status, payload = ctx.handle_worker_command(service, run_id=args.run_id, max_jobs=args.max_jobs)
        print(json.dumps(payload, indent=2))
        return status

    if command == "resume":
        service = ctx.build_follow_back_service(config, ctx.logger)
        status, payload = ctx.handle_resume_command(storage, service, run_id=args.run_id, max_jobs=args.max_jobs)
        print(json.dumps(payload, indent=2))
        return status

    if command == "abort":
        status, payload = ctx.handle_abort_command(storage, run_id=args.run_id, reason=args.reason)
        print(json.dumps(payload, indent=2))
        return status

    if command == "fork-repos":
        service = ctx.build_follow_back_service(config, ctx.logger, storage=storage)
        status, payload = ctx.handle_fork_repos_command(
            service,
            target_username=args.username,
            owned=bool(args.owned or args.all),
            forked=bool(args.forked or args.all),
            include_profile_readme=bool(args.profile_readme),
            fork_source=bool(args.fork_source),
            follow_fork_owners=bool(args.follow_fork_owners),
        )
        if status == 0:
            storage.commit()
        print(json.dumps(payload, indent=2))
        return status

    if command == "scheduler":
        service = ctx.build_follow_back_service(config, ctx.logger)
        status, payload = ctx.handle_scheduler_command(
            service,
            run_executor=ctx.execute_run,
            interval_seconds=args.interval_seconds,
            max_ticks=args.max_ticks,
            storage=storage,
            lock_key=args.lock_key,
            lock_ttl_seconds=args.lock_ttl_seconds,
        )
        print(json.dumps(payload, indent=2))
        return status

    if command == "serve-control-plane":

        def _status_provider() -> dict[str, Any]:
            request_storage = ctx.build_storage(config)
            try:
                _status, payload = ctx.handle_control_plane_status(request_storage, config)
            finally:
                request_storage.close()
            payload["source"] = "control_plane_http"
            return payload

        ctx.serve_control_plane(args.host, args.port, status_provider=_status_provider)
        return 0

    if command == "export-audit":
        payload = storage.export_recent_audit()
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "runs": len(payload["runs"]), "actions": len(payload["actions"])}, indent=2))
        return 0

    if command == "export-sbom":
        payload = storage.export_sbom()
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "components": len(payload["components"])}, indent=2))
        return 0

    if command == "export-release-manifest":
        payload = storage.export_release_manifest(signing_key=config.release_manifest_signing_key)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "artifacts": len(payload["artifacts"])}, indent=2))
        return 0

    if command == "verify-release-manifest":
        result = storage.verify_release_manifest(
            args.manifest,
            signing_key=config.release_manifest_signing_key,
            require_signature=(config.release_manifest_require_signature or args.require_signature),
            max_age_seconds=(config.release_manifest_max_age_seconds if config.release_manifest_max_age_seconds is not None else args.max_age_seconds),
        )
        print(json.dumps(result, indent=2))
        return 0 if result["ok"] else 2

    if command == "export-postgres-migration-profile":
        payload = storage.export_postgres_migration_profile()
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "tables": len(payload["tables"])}, indent=2))
        return 0

    if command == "export-otel-bootstrap":
        payload = ctx.export_otel_bootstrap(config)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["status"]}, indent=2))
        return 0

    if command == "export-otel-operations-profile":
        payload = ctx.export_otel_operations_profile(config)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["status"]}, indent=2))
        return 0

    if command == "export-queue-topology-profile":
        payload = ctx.export_queue_worker_topology_profile(config)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["status"]}, indent=2))
        return 0

    if command == "export-postgres-cutover-profile":
        payload = ctx.export_postgres_cutover_profile()
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["status"]}, indent=2))
        return 0

    if command == "export-dual-write-consistency-report":
        payload = ctx.export_dual_write_consistency_report(config, storage)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["status"], "consistency": payload["consistency"]}, indent=2))
        return 0

    if command == "export-zero-trust-profile":
        payload = ctx.export_zero_trust_profile(config)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["status"]}, indent=2))
        return 0

    if command == "export-release-integrity-profile":
        payload = ctx.export_release_integrity_profile(config)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["status"]}, indent=2))
        return 0

    if command == "export-governance-profile":
        payload = ctx.export_governance_profile(config)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["status"]}, indent=2))
        return 0

    if command == "export-enterprise-readiness-report":
        payload = ctx.export_enterprise_readiness_report(config, storage, evidence_dir=args.evidence_dir)
        output_path = ctx.resolve_command_output_path(args.output)
        output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        print(json.dumps({"written": str(output_path), "status": payload["overall_status"], "blocking_items": len(payload["blocking_items"])}, indent=2))
        return 0 if payload["overall_status"] == "ready" else 2

    if command == "enterprise-readiness-gate":
        status, payload = ctx.evaluate_enterprise_readiness_gate(
            config,
            storage,
            evidence_dir=args.evidence_dir,
            allow_partial=bool(args.allow_partial),
        )
        print(json.dumps(payload, indent=2))
        return status

    if command == "enterprise-backlog-status":
        payload = ctx.export_enterprise_backlog_status(config, storage, evidence_dir=args.evidence_dir)
        print(json.dumps(payload, indent=2))
        return 0 if payload["overall_status"] == "closed" else 2

    if command == "enterprise-remaining-work":
        payload = ctx.export_enterprise_remaining_work(config, storage, evidence_dir=args.evidence_dir)
        print(json.dumps(payload, indent=2))
        return 0 if payload["overall_status"] == "no_remaining_work" else 2

    if command == "enterprise-handoff-report":
        payload = ctx.export_enterprise_handoff_report(config, storage, evidence_dir=args.evidence_dir)
        print(json.dumps(payload, indent=2))
        return 0 if payload["closure_ready"] else 2

    if command == "gui":
        status, payload = ctx.launch_gui(config, ctx.logger, storage)
        if payload:
            print(json.dumps(payload, indent=2))
        return status

    service = ctx.build_follow_back_service(config, ctx.logger)
    status, payload = ctx.handle_default_run_command(service, run_executor=ctx.execute_run)
    print(json.dumps(payload, indent=2))
    return status
