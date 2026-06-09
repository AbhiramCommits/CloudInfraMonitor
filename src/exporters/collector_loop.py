import asyncio
import logging

from src.collectors.docker_collector import DockerCollector
from src.collectors.system_collector import SystemCollector

logger = logging.getLogger(__name__)


class CollectorLoop:
    def __init__(self, exporter, interval: float = 15.0):
        self._exporter = exporter
        self._interval = interval
        self._system = SystemCollector()
        self._docker = DockerCollector()
        self._task: asyncio.Task | None = None

    async def _run(self) -> None:
        while True:
            try:
                system_metrics = self._system.collect_all()
                container_metrics = self._docker.collect()
                self._exporter.update(system_metrics, container_metrics)
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
