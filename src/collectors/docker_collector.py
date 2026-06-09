import logging

logger = logging.getLogger(__name__)


class DockerCollector:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is not None:
            return self._client
        try:
            import docker

            self._client = docker.from_env()
        except Exception as e:
            logger.warning("Docker not available: %s", e)
            self._client = False
        return self._client

    def collect(self) -> list[dict]:
        client = self._get_client()
        if not client:
            return []

        result = []
        for container in client.containers.list():
            try:
                stats = container.stats(stream=False)
            except Exception:
                continue

            entry = self._parse_container(container, stats)
            if entry:
                result.append(entry)
        return result

    def _parse_container(self, container, stats: dict) -> dict:
        cpu_stats = stats.get("cpu_stats", {})
        precpu_stats = stats.get("precpu_stats", {})
        mem_stats = stats.get("memory_stats", {})

        total_usage = cpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        prev_total = precpu_stats.get("cpu_usage", {}).get("total_usage", 0)
        system_usage = cpu_stats.get("system_cpu_usage", 0)
        prev_system = precpu_stats.get("system_cpu_usage", 0)
        online_cpus = cpu_stats.get("online_cpus", 1)

        cpu_delta = total_usage - prev_total
        system_delta = system_usage - prev_system

        if system_delta > 0 and cpu_delta >= 0:
            cpu_percent = (cpu_delta / system_delta) * online_cpus * 100.0
        else:
            cpu_percent = 0.0

        mem_usage = mem_stats.get("usage", 0)
        mem_limit = mem_stats.get("limit", 0)
        mem_percent = (mem_usage / mem_limit * 100.0) if mem_limit else 0.0

        net_rx = 0
        net_tx = 0
        for iface_stats in (stats.get("networks") or {}).values():
            net_rx += iface_stats.get("rx_bytes", 0)
            net_tx += iface_stats.get("tx_bytes", 0)

        name = container.name.lstrip("/")
        image_tags = container.image.tags
        image = image_tags[0] if image_tags else "unknown"

        return {
            "container_id": container.short_id,
            "name": name,
            "image": image,
            "cpu_percent": round(cpu_percent, 2),
            "memory_usage_bytes": mem_usage,
            "memory_limit_bytes": mem_limit,
            "memory_percent": round(mem_percent, 2),
            "network_rx_bytes": net_rx,
            "network_tx_bytes": net_tx,
        }
