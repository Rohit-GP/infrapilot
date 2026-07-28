FROM python:3.12-slim

# 'ping' binary isn't in the slim image by default
RUN apt-get update && apt-get install -y --no-install-recommends iputils-ping \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/

ENTRYPOINT ["python", "-m", "src.main"]
