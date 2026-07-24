from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from app.jobs.entities import Job, JobStatus
from app.jobs.queue import JobQueue


def test_job_add_execution_step() -> None:
    mock_redis = MagicMock()
    queue = JobQueue(url="https://fake-redis.upstash.io", token="fake-token")
    queue.client = mock_redis

    fake_job = Job(
        id="job-123",
        job_type="chat_agent_run",
        status=JobStatus.RUNNING,
        payload={"content": "test"},
        result=None,
        error=None,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        execution_steps=[],
    )

    with patch.object(queue, "get", return_value=fake_job):
        queue.add_execution_step("job-123", "planner", "Planner analyzing prompt...", "running")
        assert len(fake_job.execution_steps) == 1
        assert fake_job.execution_steps[0]["step"] == "planner"
        assert fake_job.execution_steps[0]["label"] == "Planner analyzing prompt..."
        mock_redis.set.assert_called_once()
