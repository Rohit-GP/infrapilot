# AI Reasoning Layer (LangGraph)

The AI Reasoning Layer is the AI component of **InfraPilot**. It consumes
structured infrastructure evidence from Redis Streams, processes it through
specialized LangGraph agents, and produces an explainable diagnostic result
with ranked root-cause hypotheses and confidence information.

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
       Supervisor Agent
               │
               ▼
          Cloud LLM
               │
               ▼
     Diagnostic Report
````

The specialized agents analyze different evidence domains, while the
Supervisor Agent combines their findings into the final diagnostic result.

## Current Status

Redis Streams communication has been verified using `consumer_demo.py`.
This script is a **development verification utility**, not the production
AI reasoning workflow.

Run the verification consumer:

```bash
pip install -r requirements.txt
python consumer_demo.py
```

Then, in another terminal:

```bash
cd ../diagnostics-engine
python -m src.main --target example.com --publish
```

The consumer should receive evidence similar to:

```text
[1234567890-0] probe=port status=ok target=example.com -> All checked ports open: [80, 443]
```

The production Redis consumer will replace this verification script when
the LangGraph reasoning workflow is integrated.

## Agents

* **Network Agent** - analyzes DNS, Ping, and TCP port evidence.
* **System Agent** - analyzes CPU, memory, disk, process, and service evidence.
* **Application Agent** - analyzes HTTP, SSL, and application/service evidence.
* **Evidence Agent** - evaluates and correlates observations from multiple
  evidence sources.
* **Supervisor Agent** - coordinates agent findings and produces the final
  diagnostic assessment.

The **Cloud LLM** provides the language-model reasoning capability used by
the agents; it is not a separate agent.

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
│   │       └── supervisor_agent.py
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
      ▼
LangGraph Agents
      │
      ▼
Evidence Correlation
      │
      ▼
Supervisor Agent
      │
      ▼
Root-Cause Hypotheses
      │
      ▼
Explainable Diagnostic Report
```

The reasoning layer keeps the diagnosis connected to the infrastructure
evidence that produced it, supporting transparent and evidence-driven
analysis.

## Implementation Status

* [x] Redis Streams communication verification
* [ ] Production Redis consumer
* [ ] LangGraph workflow
* [ ] Network Agent
* [ ] System Agent
* [ ] Application Agent
* [ ] Evidence Agent
* [ ] Supervisor Agent
* [ ] Cloud LLM integration
* [ ] Explainable diagnostic report
* [ ] PostgreSQL persistence
* [ ] React dashboard integration

## Configuration

LLM/API credentials should be provided through environment variables and
must not be committed to the repository.

The AI Reasoning Layer is developed incrementally so that Redis communication,
agent workflows, LLM integration, and diagnostic reasoning can each be
validated independently.

