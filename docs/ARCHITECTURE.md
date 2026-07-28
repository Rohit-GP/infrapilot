# Architecture Reference

## Data flow

```
React UI --(1)--> Spring Boot --(2)--> Python probing engine
                       ^                        |
                       |                      (3) publish
                     (6) push               structured evidence
                    status/result                |
                       |                          v
                  PostgreSQL <--(5)-- LangGraph agents <--(4)-- Redis Stream
                                    (Network/DB/Infra +
                                       Coordinator)
```

1. User clicks "Run Diagnosis" → Spring Boot creates a job (`queued`), opens
   a STOMP WebSocket channel to the frontend.
2. Spring Boot triggers the Python diagnostics engine for the target.
3. Diagnostics engine runs probes concurrently, publishes each `Evidence` to
   a Redis Stream (`diagnostics:evidence`) as it completes — doesn't block
   waiting for all probes.
4. LangGraph agents (consumer group on the stream) pick up evidence:
   Network agent reasons over ping/dns/port, DB/Infra agents over their
   respective evidence, Coordinator merges into one verdict.
5. Coordinator's output (root cause, confidence, suggested fix) + all raw
   evidence get persisted to PostgreSQL against the job ID.
6. Spring Boot pushes status updates to the UI as they happen. If the
   suggested fix is destructive, it stops here and asks the dashboard for
   approval instead of marking the job complete.

## Why Redis Streams, not Pub/Sub

Pub/Sub has no delivery guarantee — if the LangGraph service is down when
evidence is published, that evidence is lost silently. Streams persist
messages; a consumer group picks up where it left off after a restart.
This matters here because probing and reasoning are separate processes
that can restart independently.

## Job status states

`queued` → `running` → (`awaiting_approval` →) `complete` | `failed`

`awaiting_approval` only applies when the AI-suggested fix is destructive
(restart a service, flush iptables, kill a process) — the safety gate
lives in Spring Boot, reusing the same job-status/WebSocket machinery
rather than being a separate system.

## Probe evidence contract

Every probe returns the same shape (`src/core/models.py::Evidence` in the
diagnostics engine) regardless of probe type:

```json
{
  "probe_type": "port",
  "target": "example.com",
  "status": "ok | degraded | failed | error",
  "latency_ms": 12.4,
  "message": "human-readable summary",
  "raw": { "...probe-specific detail..." },
  "error": null,
  "job_id": "uuid",
  "evidence_id": "uuid",
  "timestamp": 1234567890.12
}
```

LangGraph agents should only ever need this shape — never parse raw
probe/tool output directly. Keep this contract stable; it's the seam
between the Python side and everything downstream.
