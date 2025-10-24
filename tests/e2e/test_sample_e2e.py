import httpx
import pytest

from tests.e2e.orchestrator import TestOrchestrator as Orchestrator


@pytest.mark.e2e
@pytest.mark.asyncio
async def test_health_endpoint_smoke():
    """Simple smoke test that verifies backend health endpoint if available.

    The test will be skipped if the service is unreachable to avoid CI failures when
    services are not started. This provides a safe default while the orchestrator and
    infra are brought up.
    """
    orch = Orchestrator()
    base_url = orch.get("base_url")

    async with httpx.AsyncClient(
        base_url=base_url, timeout=orch.get("default_timeout_seconds", 10)
    ) as client:
        try:
            resp = await client.get("/api/v1/health")
        except Exception as exc:
            pytest.skip(f"Backend not available for E2E smoke test: {exc}")

        assert (
            resp.status_code == 200
        ), f"Unexpected status: {resp.status_code} - {resp.text}"
