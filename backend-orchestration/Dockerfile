FROM python:3.12-slim

# 'ping' binary isn't in the slim image by default - needed since the
# diagnostics engine (invoked as a subprocess, see
# src/services/probe_trigger.py) runs a ping probe.
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/

# The diagnostics engine is mounted read-only at /diagnostics-engine (see
# docker-compose.yml) and invoked as a subprocess in this same container,
# so its dependencies need to be installed here too.
COPY diagnostics-engine-requirements.txt .
RUN pip install --no-cache-dir -r diagnostics-engine-requirements.txt

EXPOSE 8000
ENTRYPOINT ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
