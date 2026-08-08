# Backend Orchestration (FastAPI) - Phase 3

Owns the diagnostic job lifecycle (`queued → running → complete/failed`),
REST API endpoints, real-time status updates to the React frontend,
JWT-based authentication and authorization, and the human-in-the-loop
safety gate for destructive remediation actions.

Not started yet - build after the diagnostics engine works standalone.

Planned modules:
- `job` — Job entity, status enum, JobService
- `websocket` — STOMP config, status broadcast
- `probe-trigger` — invokes the Python diagnostics engine (subprocess or HTTP)
- `safety-gate` — intercepts destructive suggested actions, requests approval
