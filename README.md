# CloudInfraMonitor

A Python monitoring agent that collects system and Docker container metrics and exports them to Prometheus, CloudWatch, and a JSON API.

## Architecture

```
+-----------+       scrape /metrics       +------------+       dashboards       +---------+
|           | ---------------------------> |            | <----------------------- |         |
|   app     |       every 15s             | Prometheus |                         | Grafana |
|  :8000    |                              |   :9090    |                         |  :3000  |
|           |                              |            |                         |         |
+-----------+                              +------------+                         +---------+
      |
      |  put_metric_data()
      v
+------------+
| CloudWatch |
| (optional) |
+------------+
```

## Setup

### Local

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
cp .env.example .env      # edit with your credentials
python main.py
```

### Docker Compose

```bash
docker compose up --build
```

This starts three services: the app, Prometheus, and Grafana. The app bind-mounts `/var/run/docker.sock` for container metrics.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Status + uptime |
| GET | `/metrics` | Prometheus scrape endpoint |
| GET | `/metrics/system` | Latest system metrics JSON |
| GET | `/metrics/containers` | Latest container metrics JSON |
| GET | `/metrics/summary` | Aggregated summary JSON |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CLOUDWATCH_ENABLED` | `false` | Set `true` to publish to CloudWatch |
| `AWS_REGION` | `us-east-1` | AWS region for CloudWatch |
| `AWS_ACCESS_KEY_ID` | | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | | AWS secret key |

## Test

```bash
pytest tests/
```

## Project Structure

```
CloudInfraMonitor/
  src/
    collectors/         # metric collection (system, docker)
    exporters/          # prometheus, cloudwatch exporters
    api/                # FastAPI routes
  tests/                # test suite
  provisioning/         # Grafana datasource config
  main.py               # application entry point
  Dockerfile
  docker-compose.yml
  prometheus.yml
```

## Grafana Dashboard

> Screenshot placeholder — replace with your dashboard image.

![Grafana Dashboard](docs/dashboard.png)
