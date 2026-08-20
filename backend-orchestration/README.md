# Backend Orchestration (FastAPI) — Phase 3

Owns the diagnostic job lifecycle (`QUEUED → RUNNING → AWAITING_DIAGNOSIS →
COMPLETED/FAILED`), the REST API, real-time job-status updates over
WebSocket, JWT-based authentication and authorization, and the
human-in-the-loop safety gate for remediation actions.

**Status: implemented and tested end-to-end** against a live PostgreSQL +
Redis + diagnostics-engine + ai-reasoning stack. See `/mnt/user-data/outputs/docs/backend.md`
(also included in this zip at `docs/backend.md`) for the full request flow
and API reference.

## Modules

- `core/` — `config.py` (env-driven settings), `database.py` (SQLAlchemy
  engine/session), `security.py` (bcrypt password hashing + JWT).
- `models/` — SQLAlchemy ORM models for all 7 entities in the class
  diagram: `User`, `Target`, `DiagnosisJob`, `Evidence`, `Hypothesis`,
  `HypothesisEvidence`, `ApprovalDecision`.
- `schemas/` — Pydantic request/response models.
- `services/` — business logic: `auth_service`, `job_service` (the
  DiagnosisJob lifecycle), `approval_service` (the safety gate),
  `probe_trigger` (invokes diagnostics-engine as a subprocess).
- `api/` — REST routers: `auth`, `targets`, `diagnosis_jobs`, `approvals`.
- `websocket/` — `/ws/jobs/{job_id}` for real-time status push.

## Quickstart (local, without Docker)

```bash
cd backend-orchestration
pip install -r requirements.txt

# Postgres must be running and reachable at DATABASE_URL (see .env.example
# at the repo root). Tables are created automatically on startup.
export DATABASE_URL=postgresql+psycopg2://infrapilot:infrapilot@localhost:5432/infrapilot
export JWT_SECRET_KEY=dev-secret
export DIAGNOSTICS_ENGINE_DIR=../diagnostics-engine
export DIAGNOSTICS_ENGINE_PYTHON=python3   # or the diagnostics-engine venv's python

uvicorn src.main:app --reload
```

Then open `http://localhost:8000/docs` for interactive Swagger docs.

## Quickstart (Docker Compose)

From the repo root:

```bash
docker compose up --build
```

This starts Redis, Postgres, and this backend (which bundles the
diagnostics engine's dependencies into its own image so the subprocess
invocation works inside the container - see `Dockerfile`). The
`ai-reasoning` consumer still runs separately (`python -m src.main` in
that directory) since it isn't containerized yet.

## Known simplifications (prototype-stage, documented deliberately)

- **`job_id`/`evidence_id` are UUIDs, not `Long`s**, deviating from the
  class diagram - see `src/models/diagnosis_job.py` for why.
- **Schema bootstrap via `Base.metadata.create_all()`**, not Alembic
  migrations - fine for a prototype, would need real migrations before
  any production use.
- **No auth on the WebSocket endpoint** - a production version should
  validate a JWT passed as a query param before accepting the connection.
- **Swagger's built-in "Authorize" button won't authenticate** since
  `/api/auth/login` takes a JSON body (matching the frontend's expected
  contract) rather than the OAuth2 form-encoded body FastAPI's
  `OAuth2PasswordBearer` assumes. Use "Try it out" on `/api/auth/login`
  and paste the returned token into Authorize manually.
