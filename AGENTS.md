# Repository Guidelines

## Project Structure & Module Organization

Core CLI code lives in `src/`, with entry points in `src/main.py` and agent implementations in `src/agents/`. Shared utilities (logging, orchestration, redaction) sit under `src/core/`. Tests mirror the source tree inside `tests/`, while reusable scripts land in `scripts/`. Documentation and design notes are in `docs/`; session artifacts and logs should remain under `logs/`. Keep configuration examples (such as `hello_config.json`) at the repository root for quick reuse.

## Build, Test, and Development Commands

- `python -m pip install -r requirements.txt -r requirements-dev.txt` sets up runtime and dev tooling.
- `python -m pytest -q` runs the unit suite; add `--cov=src --cov-report=term-missing` to check coverage before merging.
- `python -m src.main list-agents` confirms registry health; `python -m src.main run --agent HelloAgent` is the smoke test for agent wiring.
- `python -m src.main new-agent Report --config-out report_config.json` scaffolds a new agent and emits a starter config.

## Coding Style & Naming Conventions

Use 4-space indentation and keep lines under 100 characters, matching the `black` and `ruff` configuration in `pyproject.toml`. Run `ruff check .` to catch lint issues and import order problems, and `black .` for formatting. Classes stay in `CamelCase`, functions and variables in `snake_case`, constants in `UPPER_SNAKE_CASE`. Provide concise docstrings for public agent methods and explain non-obvious orchestration logic with short comments.

## Testing Guidelines

Write tests in `tests/` using `pytest`, naming files `test_*.py` and functions `test_*`. Target ≥85% coverage (`pytest -q --cov=src --cov-fail-under=85`). When validating new agents, add scenario-based tests that exercise their decision paths and ensure registry discovery via `AGENT_REGISTRY`. Prefer fixtures over ad-hoc setup for repeatable transcripts or config payloads.

## Commit & Pull Request Guidelines

Follow the existing history by using descriptive English subjects; Conventional Commit prefixes (`feat:`, `fix:`) are preferred when they clarify intent. Break work into logical commits and keep messages in the imperative mood (e.g., `feat: add reporting agent`). Pull requests should include: a succinct summary of behavior changes, references to Jira/ticket IDs or GitHub issues, test results (`pytest` output or coverage), and screenshots or transcript snippets if UI or conversational output changes.

## Agent Development Tips

Place new agent modules under `src/agents/` and ensure they subclass the shared base in `src/agents/base.py`. Register agents via the module-level `register_agent` helper so `list-agents --verbose` reports them correctly. When adding configuration knobs, document them in the agent docstring and provide defaults through the generated config file. Respect security settings (`FTSYSTEM_ALLOWED_AGENTS`, `FTSYSTEM_MAX_ROUNDS`) and reuse the redaction utilities when handling sensitive payloads.
