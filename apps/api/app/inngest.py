import logging

import inngest
from inngest import fast_api
from fastapi import FastAPI

from app.core.config import settings

logger = logging.getLogger(__name__)


def _build_client() -> inngest.Inngest:
    return inngest.Inngest(
        app_id=settings.inngest_app_id,
        env=settings.environment,
        event_key=settings.inngest_event_key or None,
        signing_key=settings.inngest_signing_key or None,
        is_production=(settings.environment == "production"),
    )


client = _build_client()


@client.create_function(
    fn_id="mrpl-demo-workflow",
    name="MRPL demo workflow",
    retries=2,
    timeouts=inngest.Timeouts(start=5_000, finish=30_000),
    trigger=inngest.TriggerEvent(event="mrpl/demo.event"),
)
def demo_workflow(ctx: inngest.ContextSync) -> dict:
    event_data = dict(ctx.event.data or {})
    if event_data.get("should_fail"):
        raise ValueError("controlled failure for Inngest verification")

    result = {
        "status": "success",
        "message": "MRPL Inngest demo workflow executed",
        "input": event_data,
        "echo": event_data.get("message", "hello"),
    }
    return result


@client.create_function(
    fn_id="mrpl-demo-failure-path",
    name="MRPL demo failure path",
    retries=1,
    timeouts=inngest.Timeouts(start=5_000, finish=10_000),
    trigger=inngest.TriggerEvent(event="mrpl/demo.failure"),
    on_failure=lambda ctx: {"status": "failed", "error": "controlled failure captured"},
)
def demo_failure_workflow(ctx: inngest.ContextSync) -> dict:
    raise RuntimeError("This is a controlled Inngest failure")


FUNCTIONS = [demo_workflow, demo_failure_workflow]


def register_inngest(app: FastAPI) -> None:
    fast_api.serve(app, client, FUNCTIONS)
    logger.info("Inngest registered on /api/inngest with workflow functions: %s", [fn.id for fn in FUNCTIONS])


def emit_demo_event(payload: dict) -> dict:
    event = inngest.Event(name="mrpl/demo.event", data=payload)
    result = client.send_sync([event])
    return {"status": "sent" if result else "unknown", "payload": payload}
