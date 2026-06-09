import time
from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    from main import app

    app.state.start_time = time.time()
    mock_loop = MagicMock()
    mock_loop.latest_system = {
        "cpu_percent_core_0": 25.0,
        "cpu_percent_core_1": 30.0,
        "cpu_percent_total": 27.5,
        "memory_used_bytes": 4_000_000_000,
        "memory_available_bytes": 12_000_000_000,
        "memory_percent": 25.0,
        "network_bytes_sent_delta": 5000,
        "network_bytes_recv_delta": 7000,
        "timestamp": time.time(),
    }
    mock_loop.latest_containers = [
        {
            "container_id": "abc123",
            "name": "webapp",
            "image": "nginx:latest",
            "cpu_percent": 10.5,
            "memory_usage_bytes": 128_000_000,
            "memory_limit_bytes": 1_000_000_000,
            "memory_percent": 12.8,
            "network_rx_bytes": 1000,
            "network_tx_bytes": 2000,
        },
        {
            "container_id": "def456",
            "name": "db",
            "image": "postgres:15",
            "cpu_percent": 3.2,
            "memory_usage_bytes": 256_000_000,
            "memory_limit_bytes": 1_000_000_000,
            "memory_percent": 25.6,
            "network_rx_bytes": 500,
            "network_tx_bytes": 300,
        },
    ]
    app.state.collector_loop = mock_loop
    return app


@pytest.mark.anyio
async def test_health_returns_ok_and_uptime(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["uptime_seconds"] >= 0


@pytest.mark.anyio
async def test_metrics_system_returns_all_expected_keys(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/metrics/system")
    assert resp.status_code == 200
    data = resp.json()
    assert "cpu_percent_total" in data
    assert "memory_used_bytes" in data
    assert "memory_available_bytes" in data
    assert "memory_percent" in data
    assert "network_bytes_sent_delta" in data
    assert "network_bytes_recv_delta" in data
    assert "timestamp" in data


@pytest.mark.anyio
async def test_metrics_containers_returns_list(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/metrics/containers")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "webapp"
    assert data[1]["name"] == "db"


@pytest.mark.anyio
async def test_metrics_summary_returns_aggregated(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/metrics/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_cpu_avg"] == 27.5
    assert data["total_memory_percent"] == 25.0
    assert data["container_count"] == 2
    assert data["top_cpu_container"] == {"name": "webapp", "percent": 10.5}


@pytest.mark.anyio
async def test_metrics_summary_no_containers():
    from main import app

    mock_loop = MagicMock()
    mock_loop.latest_system = {"cpu_percent_total": 5.0, "memory_percent": 40.0}
    mock_loop.latest_containers = []
    app.state.collector_loop = mock_loop

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        resp = await client.get("/metrics/summary")
    data = resp.json()
    assert data["container_count"] == 0
    assert data["top_cpu_container"] is None
