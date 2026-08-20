# Backend Documentation: Flow & API Reference

This document explains how `backend-orchestration` works end-to-end - the
full lifecycle of a diagnosis job, how it fits together with
`diagnostics-engine` and `ai-reasoning`, and every API endpoint it exposes.

Everything described here was verified by actually running the stack
(Postgres + Redis + all three services) and exercising it with `curl`, not
just written from the diagram.

---

## 1. The three services and what each one owns

```
┌─────────────────────┐      ┌──────────────────────┐      ┌──────────────────────┐
│ backend-orchestration│      │  diagnostics-engine   │      │     ai-reasoning     │
│      (FastAPI)       │      │  (probe execution)    │      │  (LangGraph agents)  │
├──────────────────────┤      ├───────────────────────┤      ├──────────────────────┤
│ REST API              │      │ Runs probes (ping,    │      │ Consumes evidence     │
│ JWT auth               │──▶  │ dns, port, http, ssl, │──▶   │ from Redis Streams    │
│ Job lifecycle           │  invokes as  │ cpu, memory,    │  publishes   │ Multi-agent           │
│ Approval safety gate     │  subprocess  │ disk, service)   │  evidence to │ reasoning (network/    │
│ WebSocket status push     │             │                 │  Redis       │ system/application/    │
│                            │             │                 │              │ evidence/final-diag)   │
└──────────┬───────────────┘             └─────────────────┘              └──────────┬─────────────┘
           │                                                                          │
           │  writes: users, targets,                             writes: hypotheses,│
           │  diagnosis_jobs (create + evidence),                 hypothesis_evidence,│
           │  approval_decisions                                  diagnosis_jobs      │
           │                                                       (status/confidence/│
           ▼                                                        root_cause)       ▼
                              ┌───────────────────────────┐
                              │        PostgreSQL          │
                              │  (shared by both services) │
                              └───────────────────────────┘
```

Only `backend-orchestration` and `ai-reasoning` talk to Postgres directly.
`diagnostics-engine` is stateless - it runs probes and either prints JSON
(consumed by the backend, which triggers it as a subprocess) or publishes
to Redis (consumed by `ai-reasoning`), and doesn't touch the database
itself.

---

## 2. The full request flow, step by step

### Step 1 — Auth

A user registers and logs in. The backend hashes passwords with bcrypt and
issues a JWT (`POST /api/auth/register`, `POST /api/auth/login`). Every
other endpoint requires `Authorization: Bearer <token>`.

### Step 2 — Register a Target

Before diagnosing anything, a `Target` row must exist (`POST
/api/targets`) - it's just the domain/IP/hostname and a type label
(`SERVER` / `APPLICATION` / `NETWORK`).

### Step 3 — Create a DiagnosisJob

`POST /api/diagnosis-jobs` with a `target_id`. This is where the class
diagram's `User.createDiagnosisJob(target)` lives (see
`services/job_service.py::create_diagnosis_job`). What happens:

1. A `DiagnosisJob` row is inserted immediately with `status=QUEUED` and a
   freshly generated UUID `job_id`.
2. The response returns **immediately** (HTTP 202) with that `job_id` -
   the client doesn't wait for probes to finish.
3. In the background (`FastAPI BackgroundTasks`), the backend:
   - flips the job to `RUNNING`,
   - invokes `diagnostics-engine` as a subprocess:
     `python -m src.main --target <identifier> --job-id <job_id> --publish [--probes ...] [--ports ...] [--http-url ...]`,
   - the diagnostics engine runs each probe, **publishes each Evidence
     event to Redis Streams** (for `ai-reasoning` to consume) *and* prints
     the full evidence list as JSON to stdout,
   - the backend parses that stdout JSON and inserts one `Evidence` row
     per probe result,
   - the job moves to `AWAITING_DIAGNOSIS`.
4. A WebSocket notification is pushed to any client connected to
   `/ws/jobs/{job_id}` at each of these transitions.

At this point the backend's job is done. It doesn't know the diagnosis yet
- that's `ai-reasoning`'s job, running as a completely separate,
independently-deployed process.

### Step 4 — AI Reasoning picks it up

Separately, `ai-reasoning`'s Redis consumer has been accumulating the
evidence events for this `job_id` as they were published in step 3. Once
it's seen evidence for all expected probes (or an idle timeout elapses),
it runs the LangGraph workflow:

```
supervisor_agent → {network_agent, system_agent, application_agent} → evidence_agent → final_diagnosis_agent
```

The Final Diagnosis Agent ranks problem findings, picks a root cause,
computes a confidence score, and generates recommendations - see
`ai-reasoning/README.md` for the full agent-by-agent breakdown. It also
builds the standardized LLM input payload (the Cloud LLM call itself isn't
wired up yet - that's the next phase).

### Step 5 — Diagnosis is written back to Postgres

`ai-reasoning/src/persistence/repository.py::save_diagnosis()` then:
- updates the `DiagnosisJob` row: `status=COMPLETED`,
  `aggregate_confidence`, `root_cause`, `recommendations`,
- inserts one `Hypothesis` row per ranked problem finding,
- inserts a `HypothesisEvidence` row (`relation=SUPPORTS`) linking each
  hypothesis back to the specific `Evidence` row that produced it.

This is the same Postgres database the backend uses, so from this point
on `GET /api/diagnosis-jobs/{job_id}` returns the full result - root
cause, confidence, recommendations, evidence, and ranked hypotheses with
their evidence links - with no further backend involvement required.

### Step 6 — Human review (the safety gate)

An admin reviews the job (`GET /api/diagnosis-jobs/{job_id}`) and its
recommendations, then records a decision: `POST
/api/diagnosis-jobs/{job_id}/approval` with `decision=APPROVED` or
`REJECTED` and a `remediation_action` description. This is the class
diagram's `User.makeApprovalDecision()`. Nothing in this codebase actually
*executes* remediation - recording the decision is the full scope of the
safety gate at this stage.

### Job status state machine

```
QUEUED ──▶ RUNNING ──▶ AWAITING_DIAGNOSIS ──▶ COMPLETED
              │
              ▼
            FAILED   (probe execution crashed - e.g. diagnostics engine
                       timeout or bad output; individual probe
                       failures/degradations are normal diagnostic
                       *findings*, not this kind of failure)
```

A job can sit in `AWAITING_DIAGNOSIS` indefinitely if the `ai-reasoning`
consumer isn't running - that's expected and matches the "if Redis Streams
is unavailable, diagnosis job remains pending" note in the architecture
diagram.

---

## 3. Authentication

JWT bearer tokens, `HS256`, 60-minute expiry by default (`JWT_EXPIRE_MINUTES`).

```
POST /api/auth/login  {email, password}
        │
        ▼
   access_token (JWT: sub=user_id, role=USER|ADMIN, exp=...)
        │
        ▼
Authorization: Bearer <token>  on every subsequent request
```

Two roles:
- **USER** — can create targets, create/view their own diagnosis jobs.
- **ADMIN** — everything a USER can do, plus sees *all* jobs (not just
  their own) and is the only role that can post approval decisions.

---

## 4. API Reference

Base URL: `http://localhost:8000`. Interactive docs at `/docs` (Swagger)
and `/redoc`.

### Auth

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/auth/register` | none | Create a user. Body: `{name, email, password, role?}`. `role` defaults to `USER`. |
| POST | `/api/auth/login` | none | Body: `{email, password}` → `{access_token, token_type}`. |
| GET | `/api/auth/me` | any | Returns the current user's profile. |

### Targets

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/targets` | any | Body: `{name, identifier, type}`. `type` ∈ `SERVER \| APPLICATION \| NETWORK`. |
| GET | `/api/targets` | any | List all targets. |
| GET | `/api/targets/{target_id}` | any | Get one target. |

### Diagnosis Jobs

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/diagnosis-jobs` | any | Body: `{target_id, probes?, ports?, http_url?}`. Returns **202** immediately with `status=QUEUED`; probes run in the background. |
| GET | `/api/diagnosis-jobs` | any | List jobs. Regular users see only their own; admins see all. |
| GET | `/api/diagnosis-jobs/{job_id}` | any | Full job detail: status, root cause, confidence, recommendations, evidence, and ranked hypotheses (with their supporting evidence links). |
| GET | `/api/diagnosis-jobs/{job_id}/evidence` | any | Just the evidence list for a job. |
| GET | `/api/diagnosis-jobs/{job_id}/hypotheses` | any | Just the ranked hypotheses (each with `evidence_links`), sorted by `rank`. |

**Create request example:**
```json
POST /api/diagnosis-jobs
{
  "target_id": 1,
  "probes": ["dns", "http", "cpu", "memory"],
  "ports": [80, 443],
  "http_url": null
}
```
All three optional fields can be omitted to run the diagnostics engine's
full default probe suite.

**Job detail response example** (a completed job):
```json
{
  "job_id": "70718ecf-b648-4daf-bff2-626980a6cdbd",
  "user_id": 1,
  "target_id": 1,
  "status": "COMPLETED",
  "created_at": "2026-08-19T05:52:36.704206Z",
  "aggregate_confidence": 0.3,
  "root_cause": "Expected status 200, got 403",
  "recommendations": ["Inspect the application/service logs for the failing HTTP endpoint."],
  "error_message": null,
  "evidence": [ { "evidence_id": "...", "probe_type": "http", "result_status": "failed", "...": "..." } ],
  "hypotheses": [
    {
      "hypothesis_id": 1,
      "rank": 1,
      "description": "Expected status 200, got 403",
      "explanation": "The application agent's http probe reported: ... (severity=high, evidence confidence=60%).",
      "hypothesis_confidence": 0.3,
      "evidence_links": [ { "evidence_id": "...", "relation": "SUPPORTS" } ]
    }
  ]
}
```

### Approvals (admin-only)

| Method | Path | Auth | Description |
|---|---|---|---|
| POST | `/api/diagnosis-jobs/{job_id}/approval` | ADMIN | Body: `{decision, remediation_action}`. `decision` ∈ `APPROVED \| REJECTED`. |
| GET | `/api/diagnosis-jobs/{job_id}/approval` | ADMIN | List all approval decisions recorded for a job, newest first. |

Non-admins get `403 Forbidden` on both. Missing/invalid token gets `401
Unauthorized`.

### WebSocket

| Path | Description |
|---|---|
| `/ws/jobs/{job_id}` | Connects and immediately receives the job's current status as JSON, then a new message each time the status changes (RUNNING → AWAITING_DIAGNOSIS → COMPLETED/FAILED). Push-only; the server doesn't expect messages back. No auth on this endpoint yet (see backend README's "Known simplifications"). |

### Health

| Method | Path | Description |
|---|---|---|
| GET | `/health` | `{"status": "ok"}` - liveness check. |

---

## 5. Deviations from the class diagram (and why)

| Diagram says | Implemented as | Why |
|---|---|---|
| `jobId : Long`, `evidenceId : Long` | UUID (string) | Both IDs have to be generated *before* any Postgres row exists, and stay consistent across three independent services communicating over Redis Streams - a DB auto-increment integer can't be known that early. `diagnostics-engine` already generates a UUID per run/probe; the backend and `ai-reasoning` reuse those same values rather than translating between ID schemes. |
| `Evidence.observedResult` | `observed_result` (the probe's human-readable message) | Matches the diagram field. An *additional* `raw_data` (JSONB) column was added beyond the diagram to preserve the probe's full structured output for debugging - never required by any endpoint. |
| Behavior methods (`start()`, `addEvidence()`, `calculateAggregateConfidence()`, `approve()`, etc.) | Functions in `services/*.py` operating on the ORM model | Keeps persistence (models) and business logic (services) independently testable, standard FastAPI practice. |

---

## 6. Known simplifications (see also `backend-orchestration/README.md`)

- Schema is bootstrapped with `Base.metadata.create_all()`, not Alembic
  migrations - fine for this stage, would need real migrations before any
  production use.
- The WebSocket endpoint has no authentication.
- `/api/auth/login` takes a JSON body rather than the OAuth2
  form-encoded body FastAPI's built-in Swagger "Authorize" button
  expects, so that button doesn't work out of the box in `/docs` - use
  "Try it out" on the login endpoint and paste the token in manually.
