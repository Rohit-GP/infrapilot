````markdown
# AI Reasoning Layer (LangGraph)

The AI Reasoning Layer is the reasoning component of **InfraPilot**. It consumes
structured infrastructure evidence from Redis Streams, processes it through
specialized LangGraph agents, validates and correlates their findings, and
produces an explainable diagnostic result.

The reasoning pipeline is currently deterministic and evidence-backed.
Cloud LLM integration will be added as the next phase to provide deeper
natural-language reasoning and explanation.

## Architecture

```text
Diagnostics Engine
       │
       ▼
 Redis Streams
       │
       ▼
 Redis Consumer
       │
       ▼
 LangGraph Workflow
       │
       ├── Network Agent
       ├── System Agent
       ├── Application Agent
       └── Evidence Agent
               │
               ▼
        Validated Findings
               │
               ▼
     Final Diagnosis Agent
               │
               ▼
      Structured Diagnosis
               │
               ▼
          Cloud LLM
        (next phase)
               │
               ▼
    Explainable Diagnostic Report
````

The specialized agents analyze evidence from different infrastructure
domains. The Evidence Agent validates and correlates their observations.
The Final Diagnosis Agent ranks validated problems, determines the current
root-cause candidate, calculates diagnosis confidence, and generates
evidence-backed recommendations.

The Cloud LLM is planned as a reasoning and explanation layer on top of the
validated findings. It is not currently responsible for the deterministic
diagnosis.

## Current Status

Redis Streams communication has been verified using the production Redis
consumer.

Run the AI reasoning service:

```bash
pip install -r requirements.txt
python -m src.main
```

Then, in another terminal, run the diagnostics engine:

```bash
cd ../diagnostics-engine
python -m src.main --target example.com --publish
```

The Redis consumer receives the individual evidence events and accumulates
them by job. The reasoning workflow is executed after the diagnostics job
has completed, allowing the complete evidence set to be analyzed together.

Example:

```text
[redis] evidence received job=<job-id> probe=cpu status=ok
[redis] evidence received job=<job-id> probe=disk status=ok
[redis] evidence received job=<job-id> probe=dns status=ok
[redis] evidence received job=<job-id> probe=http status=ok
...
```

The final reasoning result is produced only after the complete diagnostic
evidence for the job has been collected.

## Agents

### Network Agent

Analyzes network-related evidence:

* DNS
* Ping
* TCP ports

Produces structured findings describing network reachability and
connectivity.

### System Agent

Analyzes system-resource evidence:

* CPU
* Memory
* Disk
* Process
* Service

Produces structured findings describing system health and resource
conditions.

### Application Agent

Analyzes application and service evidence:

* HTTP
* SSL/TLS
* Application/service health

Produces structured findings describing application-layer health.

### Evidence Agent

Validates specialist findings against the underlying diagnostic evidence
and ensures that findings remain connected to their supporting evidence.

### Final Diagnosis Agent

Consumes the validated specialist findings and produces the deterministic
final diagnosis.

Its responsibilities are:

* Separate healthy findings from problematic findings.
* Rank problematic findings by severity and evidence confidence.
* Select the strongest current root-cause candidate.
* Calculate diagnosis confidence.
* Generate evidence-backed recommendations.
* Produce a structured diagnosis that can later be passed to the Cloud LLM.

The Final Diagnosis Agent does not currently use an LLM.

### Cloud LLM

The Cloud LLM is the planned language-model reasoning layer.

It will consume the structured validated findings rather than the complete
raw diagnostic payload.

Its responsibilities will include:

* Correlating findings across infrastructure domains.
* Explaining the likely root cause.
* Comparing competing root-cause hypotheses.
* Providing an evidence-grounded explanation.
* Producing a human-readable diagnostic report.

The Cloud LLM is not a separate specialist agent.

## Data Flow

```text
Probe Evidence
      │
      ▼
Redis Streams
      │
      ▼
Redis Consumer
      │
      │ collect complete job evidence
      ▼
LangGraph Workflow
      │
      ├── Network Agent
      ├── System Agent
      └── Application Agent
                │
                ▼
        Evidence Agent
                │
                ▼
       Validated Findings
                │
                ▼
      Final Diagnosis Agent
                │
                ▼
       Structured Diagnosis
                │
                ▼
            Cloud LLM
         (next phase)
                │
                ▼
   Explainable Diagnostic Report
```

The reasoning layer keeps the diagnosis connected to the infrastructure
evidence that produced it, supporting transparent and evidence-driven
analysis.

## LLM Input

The planned Cloud LLM input will be a compact representation of the
validated findings rather than the complete raw diagnostic payload.

Example:

```json
{
  "job_id": "4dcfc8cc-299d-4d7e-ad15-e53e97b6bb94",
  "target": "x.com",
  "required_agents": [
    "application",
    "network",
    "system"
  ],
  "findings": [
    {
      "agent": "network",
      "probe": "dns",
      "severity": "low",
      "finding": "DNS resolution completed successfully."
    },
    {
      "agent": "network",
      "probe": "ping",
      "severity": "low",
      "finding": "Host is reachable using ICMP ping."
    },
    {
      "agent": "system",
      "probe": "cpu",
      "severity": "low",
      "finding": "CPU utilization is 24.0%."
    },
    {
      "agent": "system",
      "probe": "memory",
      "severity": "medium",
      "finding": "Memory utilization is elevated at 81.5%."
    },
    {
      "agent": "application",
      "probe": "http",
      "severity": "low",
      "finding": "Application returned HTTP 200."
    }
  ]
}
```

This keeps the LLM input focused on validated observations while preserving
the source agent and probe responsible for each finding.

Raw diagnostic evidence remains available internally for traceability and
evidence inspection.

## Final Diagnosis Output

The deterministic Final Diagnosis Agent currently produces:

```json
{
  "root_cause": "Memory utilization is elevated at 81.5%.",
  "confidence": 0.36,
  "recommendations": [
    "Continue monitoring the target and collect additional evidence if the problem persists."
  ]
}
```

This output represents the current deterministic diagnosis and is not yet
the final LLM-generated explanation.

## Implementation Status

* [x] Redis Streams communication verification
* [x] Production Redis consumer
* [x] LangGraph workflow
* [x] Network Agent
* [x] System Agent
* [x] Application Agent
* [x] Evidence Agent
* [x] Supervisor Agent
* [x] Final Diagnosis Agent
* [ ] Cloud LLM integration
* [ ] LLM-based root-cause reasoning
* [ ] Explainable diagnostic report
* [ ] PostgreSQL persistence
* [ ] React dashboard integration

## Project Structure

```text
ai-reasoning/
│
├── src/
│   ├── graph/
│   │   ├── workflow.py
│   │   ├── state.py
│   │   └── nodes/
│   │       ├── network_agent.py
│   │       ├── system_agent.py
│   │       ├── application_agent.py
│   │       ├── evidence_agent.py
│   │       ├── supervisor_agent.py
│   │       └── final_diagnosis_agent.py
│   │
│   ├── llm/
│   │   └── client.py
│   │
│   ├── consumers/
│   │   └── redis_consumer.py
│   │
│   └── main.py
│
├── tests/
├── consumer_demo.py
├── requirements.txt
├── Dockerfile
└── README.md
```

## Configuration

LLM/API credentials will be provided through environment variables and must
not be committed to the repository.

The AI Reasoning Layer is developed incrementally so that Redis communication,
specialized reasoning agents, evidence validation, deterministic diagnosis,
LLM integration, and diagnostic reporting can each be validated
independently.

