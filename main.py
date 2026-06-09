from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from src.exporters.collector_loop import CollectorLoop
from src.exporters.prometheus_exporter import PrometheusExporter

exporter = PrometheusExporter()
collector_loop = CollectorLoop(exporter)


@asynccontextmanager
async def lifespan(app: FastAPI):
    collector_loop.start()
    yield
    await collector_loop.stop()


app = FastAPI(title="CloudInfraMonitor", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}


app.mount("/metrics", exporter.asgi_app())
