from __future__ import annotations

import asyncio
import json

from core.application.control_plane_adapter import ControlPlaneAdapter
from interfaces.gui.i18n import GuiI18n
from interfaces.gui.security import redact_gui_payload


def run_gui(adapter: ControlPlaneAdapter, *, host: str, port: int, locale: str) -> None:
    from nicegui import ui

    i18n = GuiI18n(locale=locale)

    @ui.page("/")
    def main_page() -> None:
        ui.page_title(i18n.t("app.title"))
        result = ui.code("", language="json").classes("w-full")

        def show(payload: dict) -> None:
            result.set_content(json.dumps(redact_gui_payload(payload), indent=2, ensure_ascii=False))

        async def run_in_background(task):
            try:
                return await asyncio.to_thread(task)
            except Exception as exc:  # pragma: no cover - defensive UI boundary
                return {"status_code": 2, "event": "gui_task_failed", "payload": {"error": str(exc)}}

        with ui.header().classes("items-center gap-4"):
            ui.label(i18n.t("app.title")).classes("text-lg")

        with ui.row().classes("w-full gap-6"):
            with ui.column().classes("w-72"):
                ui.label(i18n.t("nav.dashboard")).classes("font-bold")
                refresh_btn = ui.button(i18n.t("dashboard.refresh"))

                ui.label(i18n.t("nav.runs")).classes("font-bold mt-4")
                run_id = ui.number(i18n.t("runs.run_id"), value=1, min=1, step=1).classes("w-full")
                max_jobs = ui.number(i18n.t("runs.max_jobs"), value=10, min=1, step=1).classes("w-full")
                reason = ui.input(i18n.t("runs.reason"), value=i18n.t("runs.reason.default")).classes("w-full")
                start_btn = ui.button(i18n.t("runs.start"))
                resume_btn = ui.button(i18n.t("runs.resume"))
                abort_btn = ui.button(i18n.t("runs.abort"))

                ui.label(i18n.t("nav.diagnostics")).classes("font-bold mt-4")
                diagnostics_btn = ui.button(i18n.t("diagnostics.load"))

                ui.label(i18n.t("nav.queue")).classes("font-bold mt-4")
                queue_btn = ui.button(i18n.t("queue.load"))

                ui.label(i18n.t("nav.exports")).classes("font-bold mt-4")
                output = ui.input(i18n.t("exports.output"), value="gui-audit.json").classes("w-full")
                audit_btn = ui.button(i18n.t("exports.audit"))

                action_buttons = [refresh_btn, start_btn, resume_btn, abort_btn, diagnostics_btn, queue_btn, audit_btn]

                async def execute_action(task):
                    for button in action_buttons:
                        button.disable()
                    try:
                        show(await run_in_background(task))
                    finally:
                        for button in action_buttons:
                            button.enable()

                refresh_btn.on("click", lambda: asyncio.create_task(execute_action(adapter.dashboard)))
                start_btn.on("click", lambda: asyncio.create_task(execute_action(adapter.run_start)))
                resume_btn.on(
                    "click",
                    lambda: asyncio.create_task(execute_action(lambda: adapter.run_resume(int(run_id.value), int(max_jobs.value)))),
                )
                abort_btn.on("click", lambda: asyncio.create_task(execute_action(lambda: adapter.run_abort(int(run_id.value), str(reason.value)))))
                diagnostics_btn.on("click", lambda: asyncio.create_task(execute_action(adapter.diagnostics)))
                queue_btn.on("click", lambda: asyncio.create_task(execute_action(lambda: adapter.queue_metrics(run_id=int(run_id.value)))))
                audit_btn.on("click", lambda: asyncio.create_task(execute_action(lambda: adapter.export_audit(str(output.value)))))


            with ui.column().classes("flex-1"):
                ui.label(i18n.t("common.result")).classes("font-bold")
                show(adapter.dashboard())

    ui.run(host=host, port=port, reload=False, show=False)
