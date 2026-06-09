from prometheus_client import Gauge, CollectorRegistry, make_asgi_app


METRICS_PREFIX = "infra"
CONTAINER_PREFIX = "container"


class PrometheusExporter:
    def __init__(self, registry: CollectorRegistry | None = None):
        self._registry = registry or CollectorRegistry()
        self._init_gauges()

    def _init_gauges(self):
        self._cpu = Gauge(
            f"{METRICS_PREFIX}_cpu_usage_percent",
            "CPU usage percent per core",
            ["core"],
            registry=self._registry,
        )
        self._memory = Gauge(
            f"{METRICS_PREFIX}_memory_usage_bytes",
            "Memory usage in bytes",
            ["type"],
            registry=self._registry,
        )
        self._disk = Gauge(
            f"{METRICS_PREFIX}_disk_usage_percent",
            "Disk usage percent per mountpoint",
            ["mountpoint"],
            registry=self._registry,
        )
        self._network = Gauge(
            f"{METRICS_PREFIX}_network_bytes_total",
            "Network bytes sent or received since last collection",
            ["direction"],
            registry=self._registry,
        )
        self._container_cpu = Gauge(
            f"{CONTAINER_PREFIX}_cpu_usage_percent",
            "Container CPU usage percent",
            ["container_name", "image"],
            registry=self._registry,
        )
        self._container_memory = Gauge(
            f"{CONTAINER_PREFIX}_memory_usage_bytes",
            "Container memory usage in bytes",
            ["container_name", "image"],
            registry=self._registry,
        )

    def update(self, system_metrics: dict, container_metrics: list[dict]) -> None:
        self._update_system(system_metrics)
        self._update_containers(container_metrics)

    def _update_system(self, metrics: dict) -> None:
        for key, value in metrics.items():
            if key.startswith("cpu_percent_core_"):
                core = key[len("cpu_percent_core_"):]
                self._cpu.labels(core=core).set(value)
            elif key == "cpu_percent_total":
                self._cpu.labels(core="total").set(value)
            elif key == "memory_used_bytes":
                self._memory.labels(type="used").set(value)
            elif key == "memory_available_bytes":
                self._memory.labels(type="available").set(value)
            elif key.startswith("disk_percent"):
                mountpoint = key[len("disk_percent"):] or "/"
                self._disk.labels(mountpoint=mountpoint).set(value)
            elif key == "network_bytes_sent_delta":
                self._network.labels(direction="sent").set(value)
            elif key == "network_bytes_recv_delta":
                self._network.labels(direction="recv").set(value)

    def _update_containers(self, containers: list[dict]) -> None:
        for c in containers:
            self._container_cpu.labels(
                container_name=c["name"], image=c["image"]
            ).set(c["cpu_percent"])
            self._container_memory.labels(
                container_name=c["name"], image=c["image"]
            ).set(c["memory_usage_bytes"])

    def get_registry(self) -> CollectorRegistry:
        return self._registry

    def asgi_app(self):
        return make_asgi_app(registry=self._registry)
