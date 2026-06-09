import time
import psutil


class SystemCollector:
    def __init__(self):
        self._prev_net = psutil.net_io_counters()

    def collect_cpu_percent(self) -> dict:
        percents = psutil.cpu_percent(interval=0.1, percpu=True)
        result = {}
        for i, pct in enumerate(percents):
            result[f"cpu_percent_core_{i}"] = pct
        result["cpu_percent_total"] = sum(percents) / len(percents) if percents else 0.0
        return result

    def collect_memory(self) -> dict:
        mem = psutil.virtual_memory()
        return {
            "memory_used_bytes": mem.used,
            "memory_available_bytes": mem.available,
            "memory_percent": mem.percent,
        }

    def collect_disk_usage(self) -> dict:
        result = {}
        for part in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(part.mountpoint)
            except PermissionError:
                continue
            mount = part.mountpoint.replace("/", "_").replace("\\", "_")
            result[f"disk_total_bytes{mount}"] = usage.total
            result[f"disk_used_bytes{mount}"] = usage.used
            result[f"disk_free_bytes{mount}"] = usage.free
            result[f"disk_percent{mount}"] = usage.percent
        return result

    def collect_network(self) -> dict:
        current = psutil.net_io_counters()
        sent = current.bytes_sent - self._prev_net.bytes_sent
        recv = current.bytes_recv - self._prev_net.bytes_recv
        self._prev_net = current
        return {
            "network_bytes_sent_delta": sent,
            "network_bytes_recv_delta": recv,
        }

    def collect_all(self) -> dict:
        data = {}
        data.update(self.collect_cpu_percent())
        data.update(self.collect_memory())
        data.update(self.collect_disk_usage())
        data.update(self.collect_network())
        data["timestamp"] = time.time()
        return data
