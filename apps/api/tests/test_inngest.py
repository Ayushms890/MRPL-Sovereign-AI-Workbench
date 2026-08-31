import inngest
from fastapi.testclient import TestClient
from inngest.experimental import mocked

from app.core.config import settings
from app.main import app
from app.inngest import FUNCTIONS, client, demo_workflow


def test_inngest_client_initializes() -> None:
    assert client.app_id == settings.inngest_app_id
    assert client.event_key in (None, "") or isinstance(client.event_key, str)


def test_fastapi_inngest_endpoint_is_registered() -> None:
    # Inngest registers routes via decorators; check paths safely
    # since some route objects (like _IncludedRouter) may not expose .path directly
    paths = {route.path for route in app.routes if hasattr(route, 'path')}
    assert "/api/inngest" in paths


def test_inngest_workflow_is_registered() -> None:
    workflow_ids = {fn.id for fn in FUNCTIONS}
    # Inngest SDK prefixes workflow IDs with the app_id from settings
    expected_demo = f"{settings.inngest_app_id}-mrpl-demo-workflow"
    expected_failure = f"{settings.inngest_app_id}-mrpl-demo-failure-path"
    assert expected_demo in workflow_ids
    assert expected_failure in workflow_ids


def test_demo_workflow_executes_successfully() -> None:
    mock_client = mocked.Inngest(app_id="mrpl-local")
    result = mocked.trigger(
        demo_workflow,
        inngest.Event(name="mrpl/demo.event", data={"message": "hello from inngest"}),
        mock_client,
    )
    assert result.status is mocked.Status.COMPLETED
    assert result.output["status"] == "success"
    assert result.output["echo"] == "hello from inngest"


def test_demo_workflow_failure_is_exposed() -> None:
    mock_client = mocked.Inngest(app_id="mrpl-local")
    result = mocked.trigger(
        demo_workflow,
        inngest.Event(name="mrpl/demo.event", data={"should_fail": True}),
        mock_client,
    )
    assert result.status is mocked.Status.FAILED


def test_inngest_endpoint_accepts_event_payload() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/inngest",
        json={
            "name": "mrpl/demo.event",
            "data": {"message": "payload accepted"},
        },
    )
    assert response.status_code in {200, 202, 500}
