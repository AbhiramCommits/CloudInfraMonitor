from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request):
    start_time = request.app.state.start_time
    import time

    return {"status": "ok", "uptime_seconds": round(time.time() - start_time, 2)}


@router.get("/metrics/system")
def metrics_system(request: Request):
    return request.app.state.collector_loop.latest_system


@router.get("/metrics/containers")
def metrics_containers(request: Request):
    return request.app.state.collector_loop.latest_containers


@router.get("/metrics/summary")
def metrics_summary(request: Request):
    loop = request.app.state.collector_loop
    system = loop.latest_system
    containers = loop.latest_containers

    if containers:
        top = max(containers, key=lambda c: c.get("cpu_percent", 0))
        top_cpu = {"name": top["name"], "percent": top["cpu_percent"]}
    else:
        top_cpu = None

    return {
        "total_cpu_avg": system.get("cpu_percent_total", 0),
        "total_memory_percent": system.get("memory_percent", 0),
        "container_count": len(containers),
        "top_cpu_container": top_cpu,
    }
