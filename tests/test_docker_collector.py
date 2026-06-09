from unittest.mock import MagicMock, patch

from src.collectors.docker_collector import DockerCollector


def fake_stats():
    return {
        "cpu_stats": {
            "cpu_usage": {
                "total_usage": 2000000000,
                "percpu_usage": [500000000, 500000000, 500000000, 500000000],
            },
            "system_cpu_usage": 50000000000,
            "online_cpus": 4,
        },
        "precpu_stats": {
            "cpu_usage": {"total_usage": 1000000000},
            "system_cpu_usage": 30000000000,
        },
        "memory_stats": {
            "usage": 100000000,
            "limit": 500000000,
        },
        "networks": {
            "eth0": {"rx_bytes": 5000, "tx_bytes": 3000},
            "eth1": {"rx_bytes": 1200, "tx_bytes": 800},
        },
    }


def _make_mock_container(short_id="abc123def456", name="/myapp", image="nginx:latest"):
    c = MagicMock()
    c.short_id = short_id
    c.name = name
    c.image = MagicMock()
    c.image.tags = [image]
    c.stats = MagicMock(return_value=fake_stats())
    return c


class TestDockerCollector:
    def test_collect_parses_cpu_percent(self):
        collector = DockerCollector()
        stats = fake_stats()
        container = _make_mock_container()

        entry = collector._parse_container(container, stats)

        cpu_delta = 2000000000 - 1000000000  # = 1_000_000_000
        system_delta = 50000000000 - 30000000000  # = 20_000_000_000
        expected_cpu = (cpu_delta / system_delta) * 4 * 100.0  # = 20.0

        assert entry["cpu_percent"] == round(expected_cpu, 2)
        assert entry["cpu_percent"] == 20.0

    def test_collect_parses_memory_percent(self):
        collector = DockerCollector()
        stats = fake_stats()
        container = _make_mock_container()

        entry = collector._parse_container(container, stats)

        assert entry["memory_usage_bytes"] == 100000000
        assert entry["memory_limit_bytes"] == 500000000
        assert entry["memory_percent"] == 20.0

    def test_collect_parses_network_bytes(self):
        collector = DockerCollector()
        stats = fake_stats()
        container = _make_mock_container()

        entry = collector._parse_container(container, stats)

        assert entry["network_rx_bytes"] == 6200
        assert entry["network_tx_bytes"] == 3800

    def test_collect_parses_container_metadata(self):
        collector = DockerCollector()
        stats = fake_stats()
        container = _make_mock_container()

        entry = collector._parse_container(container, stats)

        assert entry["container_id"] == "abc123def456"
        assert entry["name"] == "myapp"
        assert entry["image"] == "nginx:latest"

    def test_collect_returns_empty_list_when_docker_unavailable(self):
        collector = DockerCollector()
        collector._client = False

        result = collector.collect()

        assert result == []

    def test_collect_with_mocked_client(self):
        collector = DockerCollector()
        mock_container = _make_mock_container()
        mock_client = MagicMock()
        mock_client.containers.list.return_value = [mock_container]
        collector._client = mock_client

        result = collector.collect()

        assert len(result) == 1
        entry = result[0]
        assert entry["cpu_percent"] == 20.0
        assert entry["memory_percent"] == 20.0
        assert entry["network_rx_bytes"] == 6200
        assert entry["network_tx_bytes"] == 3800

    def test_zero_system_delta_yields_zero_cpu(self):
        collector = DockerCollector()
        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 2000000000},
                "system_cpu_usage": 30000000000,
                "online_cpus": 4,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 1000000000},
                "system_cpu_usage": 30000000000,
            },
            "memory_stats": {"usage": 0, "limit": 0},
            "networks": {},
        }
        container = _make_mock_container()

        entry = collector._parse_container(container, stats)

        assert entry["cpu_percent"] == 0.0

    def test_memory_limit_zero_yields_zero_percent(self):
        collector = DockerCollector()
        stats = {
            "cpu_stats": {
                "cpu_usage": {"total_usage": 0},
                "system_cpu_usage": 0,
                "online_cpus": 1,
            },
            "precpu_stats": {
                "cpu_usage": {"total_usage": 0},
                "system_cpu_usage": 0,
            },
            "memory_stats": {"usage": 500000000, "limit": 0},
            "networks": {},
        }
        container = _make_mock_container()

        entry = collector._parse_container(container, stats)

        assert entry["memory_percent"] == 0.0

    def test_collect_skips_container_with_bad_stats(self):
        collector = DockerCollector()
        bad_container = _make_mock_container()
        bad_container.stats = MagicMock(side_effect=RuntimeError("fail"))
        good_container = _make_mock_container(short_id="good123456789")

        mock_client = MagicMock()
        mock_client.containers.list.return_value = [bad_container, good_container]
        collector._client = mock_client

        result = collector.collect()

        assert len(result) == 1
        assert result[0]["container_id"] == "good123456789"
