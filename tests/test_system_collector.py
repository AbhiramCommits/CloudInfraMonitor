from src.collectors.system_collector import SystemCollector


def test_collect_all_keys():
    collector = SystemCollector()
    data = collector.collect_all()

    assert "timestamp" in data
    assert "cpu_percent_total" in data
    assert "memory_used_bytes" in data
    assert "memory_available_bytes" in data
    assert "memory_percent" in data
    assert "network_bytes_sent_delta" in data
    assert "network_bytes_recv_delta" in data

    assert data["timestamp"] > 0
    assert data["memory_used_bytes"] >= 0
    assert data["memory_available_bytes"] >= 0
    assert 0 <= data["memory_percent"] <= 100
    assert data["network_bytes_sent_delta"] >= 0
    assert data["network_bytes_recv_delta"] >= 0


def test_collect_all_values_non_negative():
    collector = SystemCollector()
    data = collector.collect_all()
    for key, value in data.items():
        if key == "timestamp":
            assert value > 0
        else:
            assert value >= 0, f"{key} is negative: {value}"
