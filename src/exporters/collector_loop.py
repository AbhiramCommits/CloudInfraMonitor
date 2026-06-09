import asyncio
import logging

from src.collectors.docker_collector import DockerCollector
from src.collectors.system_collector import SystemCollector

logger = logging.getLogger(__name__)


class CollectorLoop:
    def __init__(self, exporters: list | None = None, interval: float = 15.0):
        self._exporters = exporters or []
        self._interval = interval
        self._system = SystemCollector()
        self._docker = DockerCollector()
        self._task: asyncio.Task | None = None
        self.latest_system: dict = {}
        self.latest_containers: list[dict] = []

    async def _run(self) -> None:
        while True:
            try:
                self.latest_system = self._system.collect_all()
                self.latest_containers = self._docker.collect()
                for exp in self._exporters:
                    try:
                        exp.update(self.latest_system, self.latest_containers)
                    except Exception:
                        logger.exception("Exporter %s failed", type(exp).__name__)
            except Exception:
                logger.exception("Collector loop iteration failed")
            await asyncio.sleep(self._interval)

    def start(self) -> None:
        self._task = asyncio.create_task(self._run())

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
