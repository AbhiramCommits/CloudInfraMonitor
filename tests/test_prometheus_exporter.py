import pytest
from prometheus_client import CollectorRegistry

from src.exporters.prometheus_exporter import PrometheusExporter


@pytest.fixture
def exporter():
    return PrometheusExporter()


def _system_metrics():
    return {
        "cpu_percent_core_0": 45.2,
        "cpu_percent_core_1": 32.1,
        "cpu_percent_total": 38.65,
        "memory_used_bytes": 8_589_934_592,
        "memory_available_bytes": 7_516_192_768,
        "memory_percent": 53.3,
        "disk_percent_": 62.1,  # root mount /
        "disk_percent_Volumes_data": 44.7,
        "network_bytes_sent_delta": 102400,
        "network_bytes_recv_delta": 204800,
        "timestamp": 1717948800.0,
    }


def _container_metrics():
    return [
        {
            "container_id": "abc123def456",
            "name": "webapp",
            "image": "nginx:latest",
            "cpu_percent": 12.34,
            "memory_usage_bytes": 256_000_000,
            "memory_limit_bytes": 1_073_741_824,
            "memory_percent": 23.84,
            "network_rx_bytes": 5000,
            "network_tx_bytes": 3000,
        },
        {
            "container_id": "xyz999aaa111",
            "name": "worker",
            "image": "python:3.11",
            "cpu_percent": 5.67,
            "memory_usage_bytes": 128_000_000,
            "memory_limit_bytes": 536_870_912,
            "memory_percent": 23.84,
            "network_rx_bytes": 1000,
            "network_tx_bytes": 800,
        },
    ]


class TestPrometheusExporter:
    def test_cpu_gauges_set_per_core_and_total(self, exporter):
        exporter.update(_system_metrics(), [])

        reg = exporter.get_registry()
        assert reg.get_sample_value("infra_cpu_usage_percent", {"core": "0"}) == 45.2
        assert reg.get_sample_value("infra_cpu_usage_percent", {"core": "1"}) == 32.1
        assert (
            reg.get_sample_value("infra_cpu_usage_percent", {"core": "total"}) == 38.65
        )

    def test_memory_gauges_set_used_and_available(self, exporter):
        exporter.update(_system_metrics(), [])

        reg = exporter.get_registry()
        assert (
            reg.get_sample_value("infra_memory_usage_bytes", {"type": "used"})
            == 8_589_934_592
        )
        assert (
            reg.get_sample_value("infra_memory_usage_bytes", {"type": "available"})
            == 7_516_192_768
        )

    def test_disk_gauge_set_per_mountpoint(self, exporter):
        exporter.update(_system_metrics(), [])

        reg = exporter.get_registry()
        assert (
            reg.get_sample_value("infra_disk_usage_percent", {"mountpoint": "_"}) == 62.1
        )
        assert (
            reg.get_sample_value("infra_disk_usage_percent", {"mountpoint": "_Volumes_data"})
            == 44.7
        )

    def test_network_gauge_set_sent_and_recv(self, exporter):
        exporter.update(_system_metrics(), [])

        reg = exporter.get_registry()
        assert (
            reg.get_sample_value("infra_network_bytes_total", {"direction": "sent"})
            == 102400
        )
        assert (
            reg.get_sample_value("infra_network_bytes_total", {"direction": "recv"})
            == 204800
        )

    def test_container_cpu_gauge_set(self, exporter):
        exporter.update({}, _container_metrics())

        reg = exporter.get_registry()
        assert (
            reg.get_sample_value(
                "container_cpu_usage_percent",
                {"container_name": "webapp", "image": "nginx:latest"},
            )
            == 12.34
        )
        assert (
            reg.get_sample_value(
                "container_cpu_usage_percent",
                {"container_name": "worker", "image": "python:3.11"},
            )
            == 5.67
        )

    def test_container_memory_gauge_set(self, exporter):
        exporter.update({}, _container_metrics())

        reg = exporter.get_registry()
        assert (
            reg.get_sample_value(
                "container_memory_usage_bytes",
                {"container_name": "webapp", "image": "nginx:latest"},
            )
            == 256_000_000
        )
        assert (
            reg.get_sample_value(
                "container_memory_usage_bytes",
                {"container_name": "worker", "image": "python:3.11"},
            )
            == 128_000_000
        )

    def test_ignores_unknown_system_keys(self, exporter):
        exporter.update({"some_random_key": 999, "cpu_percent_total": 10.0}, [])

        reg = exporter.get_registry()
        assert reg.get_sample_value("infra_cpu_usage_percent", {"core": "total"}) == 10.0
