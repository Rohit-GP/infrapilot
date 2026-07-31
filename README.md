# Agentic NOC

Autonomous, AI-agent-driven network diagnostics and incident analysis system.
A user clicks "Run Diagnosis" → probes collect evidence → AI agents reason
over that evidence → a plain-English root cause + suggested fix comes back.

## Repo layout

```
agentic-noc/
├── diagnostics-engine/     # Python socket probing engine (Phase 1 - build first)
│   ├── src/
│   │   ├── probes/         # ping, dns, port, service/log probes
│   │   └── core/           # models, runner, redis publisher, config
│   └── tests/
├── backend-orchestration/  # Spring Boot: job lifecycle, WebSockets, safety gate (Phase 3)
├── ai-reasoning/           # LangGraph agents: Network / Database / Infrastructure (Phase 4)
├── frontend/               # React dashboard (Phase 6)
└── docs/                   # architecture notes, ADRs
```

## Build order

This is a 5-service, 3-runtime system. Do NOT build each layer to completion
in isolation — integrate early. Suggested order:

1. ✅ **Repo skeleton** — stub every service so the pipeline can
   theoretically run end-to-end with fake data.
2. ✅ **Diagnostics engine** — ping/DNS/port/service probes, structured JSON
   evidence output, runnable standalone from the CLI.
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

# 2. Diagnostics engine
cd diagnostics-engine
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m src.main --target example.com --ports 80,443 --publish

# 3. (optional, separate terminal) watch evidence arrive on the stream
cd ../ai-reasoning
pip install -r requirements.txt
python consumer_demo.py
```

See `diagnostics-engine/README.md` and `ai-reasoning/README.md` for details.
