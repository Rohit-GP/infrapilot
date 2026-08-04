# Agentic NOC

An AI-powered observability platform that analyzes system resources and network health to detect issues and identify root causes.

A user clicks "Run Diagnosis" → probes collect evidence → AI agents reason
over that evidence → a plain-English root cause + suggested fix comes back.

## Highlights

- Engineered a modular Python-based diagnostics engine supporting system (CPU, memory, disk) and network/application (DNS, Ping, TCP ports, HTTP, SSL, service) health monitoring.
- Built an extensible probe framework that produces structured evidence for AI-driven diagnosis, allowing new monitoring capabilities to be added with minimal code changes.
- Implemented an end-to-end AI-assisted observability pipeline using Spring Boot, React, Redis, Docker, and LangGraph for asynchronous diagnostics, root cause analysis, confidence scoring, and remediation suggestions.

## Repo layout

```
agentic-noc/
├── diagnostics-engine/           # Python socket probing engine (Phase 1 - build first)
│   ├── src/
│   │   ├── probes/
│   │   │   ├── network/          # ping, dns, port
│   │   │   ├── application/      # http health, ssl certificate
│   │   │   ├── system/           # cpu, memory, disk
│   │   │   └── observability/    # service/log checks
│   │   └── core/                 # models, runner, redis publisher, config
│   └── tests/                    # 27 tests, one file per probe layer
├── backend-orchestration/        # Spring Boot: job lifecycle, WebSockets, safety gate (Phase 3)
├── ai-reasoning/                 # LangGraph agents: Network / Database / Infrastructure (Phase 4)
│   └── consumer_demo.py          # Phase 2 verification only - not the real reasoning layer yet
├── frontend/                     # React dashboard (Phase 6)
└── docs/                         # architecture notes, ADRs
```

## Build order

This is a 5-service, 3-runtime system. Do NOT build each layer to completion
in isolation — integrate early. Suggested order:

1. ✅ **Repo skeleton** — stub every service so the pipeline can
   theoretically run end-to-end with fake data.
2. ✅ **Diagnostics engine** — nine probes across four layers (network,
   application, system, observability), structured JSON evidence output,
   runnable standalone from the CLI.
3. ✅ **Redis Streams** — probing engine publishes evidence to a stream
   (with a consumer group, not plain Pub/Sub) instead of stdout.
4. **Backend orchestration (Spring Boot)** ← next — job lifecycle, REST + STOMP
   WebSocket, triggers the probing engine.
5. **AI reasoning (LangGraph)** — Network/DB/Infra agents consume the stream,
   produce root cause + confidence + fix.
6. **PostgreSQL persistence** — jobs, evidence, reasoning, approvals.
7. **Safety gate + React frontend** — approval UI, live status, evidence-first
   display.

## Quickstart

```bash
# 1. Start Redis
docker compose up -d redis
# or locally without Docker: redis-server

# 2. Diagnostics engine
cd diagnostics-engine
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# runs all nine probes (network + application + system + observability)
# against the target and pushes each result onto the Redis stream
python -m src.main --target example.com --publish
# Windows: py -m src.main --target example.com --publish

# 3. (optional, separate terminal) watch evidence arrive on the stream
cd ../ai-reasoning
pip install -r requirements.txt
python consumer_demo.py

# 4. run the test suite
cd ../diagnostics-engine
pytest tests/ -v   # 27 passed
```

`--http-url` and `--service-url` are optional and point at two independent
HTTP checks (application-layer vs. observability-layer); if you don't pass
`--http-url` that probe reports `degraded` ("skipped"), not a failure — it
won't affect the process exit code. Run `python -m src.main --help` for the
full flag list (ports, dns server, log path, probe subset, etc.).

See `diagnostics-engine/README.md` and `ai-reasoning/README.md` for details.
