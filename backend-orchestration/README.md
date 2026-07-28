# Backend Orchestration (Spring Boot) — Phase 3

Owns job lifecycle (queued → running → complete/failed), REST endpoints,
STOMP WebSocket push to the frontend, and the human-in-the-loop safety gate
for destructive remediation actions.

Not started yet — build after the diagnostics engine works standalone.

Planned modules:
- `job` — Job entity, status enum, JobService
- `websocket` — STOMP config, status broadcast
- `probe-trigger` — invokes the Python diagnostics engine (subprocess or HTTP)
- `safety-gate` — intercepts destructive suggested actions, requests approval
