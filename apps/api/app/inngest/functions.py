import asyncio
import logging
import inngest

from app.inngest.client import inngest_client
from app.jobs.chat_agent import run_chat_agent_job
from app.jobs.document_ingestion import run_document_ingestion_job
from app.jobs.entities import JobStatus
from app.jobs.queue import build_job_queue

logger = logging.getLogger(__name__)


def _update_job_status(job_id: str | None, status: JobStatus, result: dict | None = None, error: str | None = None) -> None:
    if not job_id:
        return
    queue = build_job_queue()
    if queue is None:
        return
    try:
        queue.update_status(job_id, status, result=result, error=error)
    except Exception as exc:
        logger.warning("Failed to update Inngest-backed job %s to %s: %s", job_id, status.value, exc)


@inngest_client.create_function(
    fn_id="chat-agent-run",
    trigger=inngest.TriggerEvent(event="ai-os/chat.requested"),
    retries=1,
)
async def chat_agent_fn(ctx: inngest.Context) -> dict:
    payload = ctx.event.data
    job_id = payload.get("job_id")
    logger.info("Inngest executing chat agent run for conversation %s", payload.get("conversation_id"))
    _update_job_status(job_id, JobStatus.RUNNING)

    async def _execute():
        try:
            return await asyncio.to_thread(run_chat_agent_job, payload)
        except Exception as exc:
            logger.exception("Inngest chat agent step failed: %s", exc)
            raise

    try:
        result = await ctx.step.run("execute-chat-agent", _execute)
        _update_job_status(job_id, JobStatus.SUCCEEDED, result=result or {})
        return result or {}
    except Exception as exc:
        _update_job_status(job_id, JobStatus.FAILED, error=str(exc))
        raise


@inngest_client.create_function(
    fn_id="document-ingestion",
    trigger=inngest.TriggerEvent(event="ai-os/document.uploaded"),
    retries=1,
)
async def document_ingestion_fn(ctx: inngest.Context) -> dict:
    payload = ctx.event.data
    job_id = payload.get("job_id")
    logger.info("Inngest executing document ingestion for user %s, title %s", payload.get("user_id"), payload.get("title"))
    _update_job_status(job_id, JobStatus.RUNNING)

    async def _ingest():
        try:
            return await asyncio.to_thread(run_document_ingestion_job, payload)
        except Exception as exc:
            logger.exception("Inngest document ingestion step failed: %s", exc)
            raise

    try:
        result = await ctx.step.run("ingest-document-chunks", _ingest)
        _update_job_status(job_id, JobStatus.SUCCEEDED, result=result or {})
        return result or {}
    except Exception as exc:
        _update_job_status(job_id, JobStatus.FAILED, error=str(exc))
        raise


inngest_functions = [chat_agent_fn, document_ingestion_fn]
