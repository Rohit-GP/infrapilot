# AI Reasoning Layer (LangGraph) — Phase 4

Consumes probe evidence from Redis Streams, runs it through specialized
agents, and merges their findings into one root-cause hypothesis.

Not started yet — build after Redis Streams integration is in place.

Planned agents:
- `network_agent.py` — reasons over ping/DNS/port evidence
- `database_agent.py` — reasons over DB connection/query evidence
- `infrastructure_agent.py` — reasons over container/process/CPU/mem evidence
- `coordinator.py` — merges agent outputs into final verdict + confidence + fix
