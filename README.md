# InfraPilot

<<<<<<< HEAD
> **An Agentic NOC for Explainable Network and System Diagnosis**
=======
> **An Explainable Agentic Network Operations Center (NOC) for AI-Assisted Infrastructure Diagnosis**
>>>>>>> 45cbca2e225971de09c4b74b9e8ba2c0cb0e87a5

InfraPilot is a lightweight implementation of an Agentic Network Operations Center (NOC) that automates infrastructure diagnostics using evidence-driven AI reasoning. Instead of presenting raw probe results, the system collects diagnostic evidence, analyzes it using specialized AI agents, and produces transparent root-cause explanations with evidence-based confidence scores and remediation recommendations.

---

## Architecture

```text
                    ┌────────────────────┐
                    │     React UI       │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │     Fast API       │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ Python Diagnostics │
                    │      Engine        │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │   Redis Streams    │
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │ LangGraph AI Agents│
                    └─────────┬──────────┘
                              │
                              ▼
                    ┌────────────────────┐
                    │   PostgreSQL DB    │
                    └────────────────────┘
```

---

## Workflow

```text
Run Diagnosis
      │
      ▼
Python Diagnostics Engine
      │
Collect Structured Evidence
      │
      ▼
Redis Streams
      │
      ▼
LangGraph AI Agents
      │
      ▼
FastAPI Orchestrator
      │
      ▼
React Dashboard
```

The AI agents reason over collected evidence rather than executing diagnostics directly, making every diagnosis transparent, traceable, and explainable.

---

## Features

- Modular Python diagnostics engine for network, application, system, and observability monitoring.
- Standardized structured evidence model shared across all probes.
- Asynchronous event-driven architecture using Redis Streams.
- Multi-agent AI reasoning with LangGraph.
- Explainable diagnosis with evidence-backed confidence scoring.
- Multiple ranked diagnostic hypotheses.
- Human-in-the-loop approval workflow for sensitive remediation actions.
- Real-time dashboard using React, Spring Boot, and WebSockets.
- Dockerized development environment.

---

## Technology Stack

| Layer | Technology |
|--------|------------|
| Frontend | React |
| Backend | FastAPI |
| Diagnostics Engine | Python (`asyncio`) |
| AI Reasoning | LangGraph |
| Messaging | Redis Streams |
| Database | PostgreSQL |
| Real-Time Communication | WebSocket (STOMP) |
| Containerization | Docker |

---

## Repository Structure

```text
<<<<<<< HEAD
InfraPilot/
│
├── ai-reasoning/                  # AI reasoning service
│   ├── src/
│   │   ├── graph/
│   │   │   ├── workflow.py        # LangGraph workflow
│   │   │   ├── state.py           # Shared graph state
│   │   │   └── nodes/
│   │   │       ├── network_agent.py
│   │   │       ├── system_agent.py
│   │   │       ├── application_agent.py
│   │   │       ├── evidence_agent.py
│   │   │       └── supervisor_agent.py
│   │   │
│   │   ├── llm/
│   │   │   └── client.py          # Cloud LLM API connection
│   │   │
│   │   ├── consumers/
│   │   │   └── redis_consumer.py  # Reads evidence from Redis Streams
│   │   │
│   │   └── main.py
│   │
│   ├── tests/
│   ├── consumer_demo.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── backend-orchestration/         # FastAPI backend
│   ├── src/
│   │   ├── main.py
│   │   ├── routes/
│   │   │   ├── diagnosis.py
│   │   │   └── results.py
│   │   ├── services/
│   │   │   ├── diagnosis_service.py
│   │   │   └── redis_service.py
│   │   └── models/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── README.md
│
├── diagnostics-engine/
│   ├── src/
=======
agentic-noc/
├── diagnostics-engine/
│   ├── src/
>>>>>>> 45cbca2e225971de09c4b74b9e8ba2c0cb0e87a5
│   │   ├── probes/
│   │   │   ├── network/
│   │   │   ├── application/
│   │   │   ├── system/
│   │   │   └── observability/
│   │   └── core/
<<<<<<< HEAD
│   │
│   ├── tests/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── frontend/                      # React dashboard
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   └── App.jsx
│   └── ...
│
├── docs/
│   ├── architecture/
│   ├── workflow/
│   └── research-paper/
│
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
=======
│   └── tests/
│
├── backend-orchestration/
│
├── ai-reasoning/
│   └── consumer_demo.py
│
├── frontend/
│
└── docs/
>>>>>>> 45cbca2e225971de09c4b74b9e8ba2c0cb0e87a5
```

---

## Development Roadmap

Current implementation status:

- ✅ Repository structure
- ✅ Python diagnostics engine
- ✅ Redis Streams integration
- 🚧 FastAPI orchestration
- 🚧 LangGraph multi-agent reasoning
- 🚧 PostgreSQL persistence
- 🚧 React dashboard
- 🚧 Human approval workflow

---

## Current Diagnostic Coverage

### Network
- Ping
- DNS Resolution
- TCP Port Connectivity

### Application
- HTTP Health Check
- SSL Certificate Validation

### System
- CPU Usage
- Memory Usage
- Disk Usage

### Observability
- Service Health
- Log Monitoring

---

## Planned AI Capabilities

The AI reasoning layer will provide:

- Root cause analysis
- Multiple diagnostic hypotheses
- Evidence-based confidence scoring
- Explainable reasoning
- Operator learning mode
- Remediation recommendations
- Human-in-the-loop approval

---

## Quick Start

### 1. Start Redis

```bash
docker compose up -d redis
```

---

### 2. Setup the Diagnostics Engine

```bash
cd diagnostics-engine

python3 -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

pip install -r requirements.txt
```

---

### 3. Run Diagnostics

```bash
python -m src.main --target example.com --publish

# Windows
py -m src.main --target example.com --publish
```

---

### 4. Watch Evidence on Redis Streams

```bash
cd ../ai-reasoning

pip install -r requirements.txt

python consumer_demo.py
```

---

### 5. Run Tests

```bash
cd ../diagnostics-engine

pytest tests/ -v
```

---

## Project Scope

<<<<<<< HEAD
InfraPilot is **not intended to replace enterprise Network Operations Centers (NOCs)**.  
Instead, it provides a lightweight and reproducible prototype for studying
evidence-driven, AI-assisted infrastructure diagnosis.

The project focuses on:

- Automated network, application, and system diagnostics
- Structured infrastructure evidence collection
- Evidence-driven multi-agent AI reasoning
- Explainable root-cause hypothesis generation
- Confidence-based diagnostic assessment
- Human-in-the-loop validation of AI-generated diagnoses
- Event-driven communication between diagnostic and reasoning components
- Transparent and reproducible AI-assisted diagnostic workflows
=======
InfraPilot is **not** intended to replace enterprise Network Operations Centers.

Instead, it provides a lightweight, reproducible implementation of the core architectural principles behind modern Agentic NOCs, focusing on:

- Automated infrastructure diagnostics
- Evidence-driven AI reasoning
- Explainable diagnosis
- Human-assisted operational decisions
- Transparent and trustworthy AI workflows
>>>>>>> 45cbca2e225971de09c4b74b9e8ba2c0cb0e87a5

---

## Future Enhancements

<<<<<<< HEAD
- Expanded specialized AI agents for additional infrastructure domains
- Explainable evidence graphs for tracing relationships between observations and hypotheses
- Persistent incident history and audit trails
- Operator learning and interactive diagnostic assistance
- Real-time infrastructure and topology visualization
- Quantitative evaluation of diagnosis accuracy, latency, and scalability
- Approval-based automated remediation workflows
- Support for larger-scale and distributed infrastructure environments
=======
- Infrastructure, Database, and Network AI agents
- Explainable evidence graph
- Incident history and audit trail
- Operator learning mode
- Real-time topology visualization
- Approval workflow for automated remediation
>>>>>>> 45cbca2e225971de09c4b74b9e8ba2c0cb0e87a5

---

For implementation details of each module, refer to the individual README files within each project directory.
