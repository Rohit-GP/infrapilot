# Diagnostics Engine (Python socket probing engine)

Phase 1 of Agentic NOC. Runs various probes against
a target and returns normalized `Evidence` objects as JSON. Fully standalone
— no Redis, Spring Boot, or LangGraph required to run it.

```
Diagnostics Engine
│
├── Network Layer
│   ├── DNS Probe
│   ├── Ping Probe
│   └── Port Probe
│
├── Application Layer
│   ├── HTTP Health Probe
│   └── SSL Probe
│
├── System Layer
│   ├── CPU Probe
│   ├── Memory Probe
│   └── Disk Probe
│
└── Observability Layer
    └── Log Probe
```

## Setup

```bash
cd diagnostics-engine
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

```bash
# Basic run - ping, dns, port(80,443), service (skipped, no url/log configured)
py -m src.main --target example.com

# Custom ports
py -m src.main --target example.com --ports 22,80,443,8080

# Only specific probes
py -m src.main --target example.com --probes dns,port

# Use a specific DNS server (diagnose resolver-specific issues)
py -m src.main --target example.com --dns-server 8.8.8.8

# Include an HTTP health check and log scan
# py -m src.main `
#   --target localhost `
#   --service-url http://localhost:8080/health `
#   --log-path "C:\logs\myapp\app.log"

# Publish evidence to Redis Stream (requires Redis running, Phase 2)
py -m src.main --target example.com --publish
```

Exit code is `1` if any probe reports `failed` or `error`, `0` otherwise —
useful for scripting/CI.

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

Tests for `port` and `dns` probes run against loopback/localhost, so they
don't require external network access. `ping` isn't unit-tested directly
since it shells out to a system binary that varies by OS/container.

## Design notes

- **Probes never raise** - every probe function catches its own exceptions
  and returns an `Evidence(status=ERROR, ...)` instead. The runner and CLI
  never need try/except around a probe call.
- **`connect_ex` over `connect`** for the port probe - avoids a raised
  exception in the hot path and lets refused-vs-timeout be read directly
  from the return code / exception path, which matters diagnostically
  (refused = something is listening but not on that port; timeout = likely
  firewalled).
- **`ping` shells out** rather than using raw ICMP sockets, because raw
  sockets need root/`CAP_NET_RAW`. This keeps the probe runnable
  unprivileged everywhere except minimal containers that lack the `ping`
  binary (see `Dockerfile`, which installs `iputils-ping`).
- **Extending with DB/Infra probes**: per the design doc, add new modules
  under `src/probes/` (e.g. `db_probe.py`, `infra_probe.py`) and register
  them in `PROBE_REGISTRY` in `src/core/runner.py`. Nothing else needs to
  change - the CLI, runner, and publisher are probe-agnostic.
