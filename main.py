import time
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI

from src.api.routes import router
from src.exporters.cloudwatch_exporter import CloudWatchExporter
from src.exporters.collector_loop import CollectorLoop
from src.exporters.prometheus_exporter import PrometheusExporter

load_dotenv()

prom_exporter = PrometheusExporter()
cloudwatch_exporter = CloudWatchExporter()
collector_loop = CollectorLoop(exporters=[prom_exporter, cloudwatch_exporter])


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.start_time = time.time()
    app.state.collector_loop = collector_loop
    collector_loop.start()
    yield
    await collector_loop.stop()


app = FastAPI(title="CloudInfraMonitor", lifespan=lifespan)
app.include_router(router)
app.mount("/metrics", prom_exporter.asgi_app())
