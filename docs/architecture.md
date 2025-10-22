# ftSystem Architecture Overview

This document captures a high-level view of the ftSystem platform after the 2025‑10‑22 refresh (docstrings, typing, logging).

## Component Diagram

```mermaid
flowchart LR
    CLI["Typer CLI (`src/main.py`)"]
    Registry["Agent Registry (`agents/__init__.py`)"]
    Master["MasterAgent (`agents/master_agent.py`)"]
    Agents["Helper Agents (`agents/*.py`)"]
    Core["Core Services (`src/core/*`)"]
    Storage["History & Logs (`logs/`, JSONL)"]

    CLI -->|discover| Registry
    CLI -->|run/list/etc.| Master
    Master -->|delegates| Agents
    Master -->|forum & redaction| Core
    Agents -->|results| Master
    Master -->|session summary| Storage
    Core -->|policies/redaction| Master
```

## Orchestration Sequence

```mermaid
sequenceDiagram
    participant User
    participant CLI as Typer CLI
    participant Master as MasterAgent
    participant Registry as Agent Registry
    participant Helper as Helper Agent
    participant Core as Core Services
    participant History as History Store

    User->>CLI: `ftsystem run --agent MasterAgent`
    CLI->>Registry: resolve MasterAgent class
    CLI->>Master: instantiate with AgentConfig
    Master->>Core: fetch security policy / redaction
    Master->>Registry: select sub-agents
    Master->>Helper: run sub-agent (async thread)
    Helper-->>Master: result / error
    Master->>Core: redact transcript entry
    Master->>History: persist session summary JSONL
    Master-->>CLI: rounds + metrics + transcript
    CLI-->>User: render output / save JSON
```

## Notes

- Critical paths now emit debug-level logging around agent selection, rounds, and configuration overlays.
- Policies (`SecurityPolicy`) derived from environment variables are evaluated on each run, so tests can safely modify `FTSYSTEM_ALLOWED_AGENTS`.
- All diagrams are intentionally lightweight (Mermaid) to keep them versionable and easy to modify.
- Optional metrics export via `--metrics-path` uses Prometheus format and captures per-subagent latency/success for monitoring.
- Performance profiling (`perf profile`) offers quick benchmarking of orchestrations; combine with CLI `--lang` (en/pl) for localized output during demos.
