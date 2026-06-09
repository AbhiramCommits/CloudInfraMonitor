# CloudInfraMonitor

A Python monitoring agent that collects system metrics and exports them via FastAPI.

## Setup

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Run

```bash
python main.py
```

## Test

```bash
pytest tests/
```

## Project Structure

```
CloudInfraMonitor/
  src/
    collectors/   # metric collection logic
    exporters/    # metric export integrations
    api/          # FastAPI routes
  tests/          # test suite
  main.py         # application entry point
```
