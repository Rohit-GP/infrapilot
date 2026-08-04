# AI Reasoning Layer (LangGraph) - Phase 4

Consumes probe evidence from Redis Streams, runs it through specialized
agents, and merges their findings into one root-cause hypothesis.

## Right now (Phase 2 verification only)

`consumer_demo.py` is **not** the real reasoning layer - it's a minimal
script that proves the Redis Streams pipeline works end-to-end, using the
same consumer-group read pattern the real LangGraph agents will use later.

```bash
pip install -r requirements.txt
python consumer_demo.py
```

Leave it running, then in another terminal:

```bash
cd ../diagnostics-engine
python -m src.main --target example.com --publish
```

You should see each probe's evidence printed here as it arrives, e.g.:

```
[1234567890-0] probe=port     status=ok       target=example.com -> All checked ports open: [80, 443]
```

Delete `consumer_demo.py` once the real LangGraph agents replace it in
Phase 4.

## Planned agents (Phase 4, not started)

- `network_agent.py` — reasons over ping/DNS/port evidence
- `database_agent.py` — reasons over DB connection/query evidence
- `infrastructure_agent.py` — reasons over container/process/CPU/mem evidence
- `coordinator.py` — merges agent outputs into final verdict + confidence + fix
