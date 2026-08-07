# Backend Orchestration (FastAPI) - Phase 3

Owns the diagnostic job lifecycle (`queued → running → complete/failed`),
REST API endpoints, real-time status updates to the React frontend,
JWT-based authentication and authorization, and the human-in-the-loop
safety gate for destructive remediation actions.

Not started yet - build after the diagnostics engine works standalone.

## Planned Modules

- `auth` - User authentication, password verification, JWT access-token
  generation, and authentication dependencies.

- `job` - Job model, status enum, and JobService for managing the diagnostic
  lifecycle.

- `api` - FastAPI REST endpoints for creating jobs, checking job status,
  retrieving diagnostic results, and managing protected resources.

- `websocket` - FastAPI WebSocket connections for real-time job-status and
  diagnostic-result updates to the React frontend.

- `probe-trigger` - Starts or communicates with the Python diagnostics
  engine to execute diagnostic jobs.

- `safety-gate` — Intercepts destructive remediation suggestions and requires
  explicit administrator approval before any action is performed.

## Security

The backend will use stateless JWT authentication for protected API
endpoints.

```text
React Frontend
      │
      │ Login
      ▼
FastAPI Backend
      │
      ├── Authenticate user
      ├── Issue JWT
      │
      ▼
Protected API / WebSocket
      │
      ├── Verify JWT
      ├── Check user role
      │
      ▼
Diagnostic Operations