# ftSystem

![coverage](https://img.shields.io/badge/coverage-%E2%89%A585%25-brightgreen)

ftSystem is an open-source Python CLI that coordinates a team of AI agents, managed by a single master agent, to deliver accurate, format-controlled answers.

## Installation

- Create venv (optional):
  - Windows: `python -m venv .venv && .venv\\Scripts\\activate`
  - Unix: `python -m venv .venv && source .venv/bin/activate`
- Install deps: `python -m pip install -r requirements.txt -r requirements-dev.txt`
- Optional (package): `pip install -e .` then use `ftsystem` command

## Quick Start

- List agents: `python -m src.main list-agents`
- Run agent: `python -m src.main run --agent HelloAgent`
- Use config: `python -m src.main run --agent HelloAgent --config hello_config.json`
- Save result: `python -m src.main run --agent HelloAgent --output out.json`

## CLI Features

- Logging level: `--log-level {CRITICAL|ERROR|WARNING|INFO|DEBUG}`
  - Example: `python -m src.main --log-level DEBUG list-agents`
- Verbose agents list: `list-agents --verbose` (shows docstrings and module paths)
- Import errors: `list-agents --show-errors` (diagnostics for failed agent imports)
- JSON output: `list-agents --format json [--verbose --show-errors]`
- New agent generator: `new-agent <Name> [--target-dir src/agents] [--config-out cfg.json] [--force]`
  - Example: `python -m src.main new-agent Report --config-out report_config.json`
- Config formats: JSON and YAML (`--config file.yaml`)
- Metrics export: `--metrics-path metrics.prom` writes Prometheus-format metrics for completed runs.
- Language: global `--lang {en|pl}` switch for CLI prompts/errors.

### Orchestration

- Master orchestration: `--agent MasterAgent` with params in config or CLI:
  - `params.subagents: [HelloAgent, ...]`, `params.rounds: 1..N`, `params.timeout_seconds: <float>`
  - Returns JSON with `rounds`, `results`, `metrics` (latency/success), and `transcript` (forum messages)
- Example: `python -m src.main run --agent MasterAgent --param rounds=2 --param subagents='["HelloAgent"]' --output out.json`

### Security

- Redaction: sensitive patterns (e.g., `sk-...` keys, emails) are masked in transcripts and history previews.
- Policies (ENV):
  - `FTSYSTEM_ALLOWED_AGENTS=HelloAgent,ConfigEchoAgent`
  - `FTSYSTEM_MAX_ROUNDS=3`
  - History/session dirs: `FTSYSTEM_HISTORY_DIR`, `FTSYSTEM_SESSION_DIR`

### Voice (S2S)

- Enable voice in interactive mode:
  - STT: `--voice-in vosk` (offline) or `mock` (tests)
  - TTS: `--voice-out sapi5` (Windows) or `mock`
  - Model path: `--stt-model-dir <vosk_model_dir>` or ENV `FTSYSTEM_VOSK_MODEL`
  - Language and mic: `--voice-lang pl-PL`, `--mic-index <int>`, `--max-utterance-sec 8`
  - UX options: `--beep/--no-beep` (start/stop beeps), `--silence-timeout-sec <float>` to auto-stop after silence
- Use `/rec` command inside interactive to record one utterance; by default audio is NOT saved (text only, redacted).
- Example: `python -m src.main interactive --agent HelloAgent --voice-in vosk --stt-model-dir d:\models\vosk-pl --voice-out sapi5`

### Interactive & History

- Interactive mode: `python -m src.main interactive --agent HelloAgent`
  - Stores transcript in `logs/sessions/session_<agent>_<timestamp>.jsonl`
  - Env overrides: `FTSYSTEM_SESSION_DIR`
- Session history (JSONL summaries): `python -m src.main history show --limit 10`
  - JSON array output: `--json`
  - Filter by tag: `--tag mytag`
  - Filters: `--agent HelloAgent`, `--contains Hello`
  - Paging: `--offset N` plus `--limit N` (newest-first)
- Replay a transcript file: `python -m src.main history replay logs/sessions/<file>.jsonl`
  - Save replay to file: `--out replay.txt`
- Export history: `python -m src.main history export --out export.jsonl [--limit 50]`
- Clear history: `python -m src.main history clear --yes [--all]`
- Prune history: `python -m src.main history prune --keep 100 --yes` or remove old files: `--days 7 --yes`
- Find across days: `python -m src.main history find --contains "Hello" --days 7 --json`
  - Pagination: `--offset N`, `--limit N` and `--reverse` (newest-first)
  - JSON result: `{ "total": <int>, "items": [ ... ] }`
  - Example: `python -m src.main history find --contains "Hello" --days 30 --offset 20 --limit 10 --reverse --json`
  - Ordering: `--reverse` (newest-first), limit: `--limit N`
- Stats: `python -m src.main history stats --days 7 --json`
  - Filter by agent: `--agent MasterAgent`

### Voice Utilities

- List input devices (microphones): `python -m src.main voice devices`
- Include TTS voices: `python -m src.main voice devices --list-voices`
- JSON output: `--json`
- Profiles: `python -m src.main voice profile --set --voice-lang en-US --mic-index 2 --no-beep` and `--show`
- Interactive extras: inside interactive, use `/last` (show last agent reply), `/tags`, `/clear` (wipe screen)
- TTS dry-run (tests/dev): `--dry-run-tts` logs TTS text instead of speaking

### Security Tools

- Redact file content: `python -m src.main security redact --in in.txt --out out.txt [--level strict|normal]`
  - Strict masks: bearer tokens, AWS keys, IPv4, long numbers, PL IBAN/PESEL
  - Also masks PL NIP (10 digits, with separators) and EU VAT `PL` + 10 digits
  - Policy: default redaction level is `normal`; use `--redact-level strict` for broader masking. We do not bypass redaction in CLI commands unless explicitly configured.

### Tags

- Add tags to sessions: `--tag <name>` in `run` or `interactive` (repeatable)
- Filter by tag in `history show --tag <name>`

## Testing

- Run tests: `python -m pytest -q`
- Coverage: `pytest -q --cov=src --cov-report=term-missing --cov-fail-under=85`

## Developer Guide

- Docstrings: add concise, PEP 257-style docstrings to all public functions and methods. Start with a one-line summary; document parameters, return types, and raised exceptions where useful.
- Type hints: use precise typing (PEP 484/PEP 561). Prefer concrete types (`dict[str, Any]`, `list[str]`) over bare `dict`/`list`. Keep `Any` only when unavoidable.
- Error messages: include exception type and helpful context (file paths, agent name). Avoid bare `except`. Surface validation problems without leaking secrets.
- Logging: use `logging` (not prints). Add debug-level logs in critical paths. Do not log sensitive content; rely on `Redactor`.
- Style/tooling: keep ruff/black/mypy passing. Follow existing module structure and naming.
- Metrics: expose optional Prometheus files via `--metrics-path`; ensure new metrics include HELP and TYPE lines.
- Profiling: use `python -m src.main perf profile --repeat 5 --json` to benchmark orchestrations with many agents.
- I18N: CLI supports English/Polish strings via `--lang` global option and `FTSYSTEM_LANG` env override.

## Performance & Metrics

- Profile orchestrations: `python -m src.main perf profile --agent MasterAgent --repeat 5 --json` provides min/max/avg durations and subagent counts.
- Metrics export: add `--metrics-path metrics.prom` to any `run` execution to emit Prometheus exposition data (duration, per-subagent latency/success).
- Language: use global `--lang {en|pl}` or env `FTSYSTEM_LANG` to switch CLI messages between English and Polish.

## Project Structure

- CLI: `src/main.py` (Typer commands)
- Agents base: `src/agents/base.py`, dynamic registry: `src/agents/__init__.py`
- Example agent: `src/agents/hello_agent.py`
- Tests: `tests/`
- Plugins guide: `docs/plugins.md`

## Design Guide

- Primary (ApplyIntelligently): `docs/ftSystem_core.md`
- Architecture diagrams: `docs/architecture.md`

## Contributor Guide (Codex)

- Repository guidelines for Codex: [AGENTS.md](AGENTS.md)

## Voice Setup (Vosk)

- Download a PL model from the Vosk models page and unpack (e.g., `D:\\models\\vosk-pl`).
- Install deps: `pip install vosk sounddevice pyttsx3` (TTS optional on Windows).
- Run interactive with voice: `python -m src.main interactive --agent HelloAgent --voice-in vosk --stt-model-dir D:\\models\\vosk-pl --beep --silence-timeout-sec 1.5`

## Redaction Levels

- Global option: `--redact-level {normal|strict}` (or ENV `FTSYSTEM_REDACT_LEVEL`).
- Normal masks API keys (e.g., `sk-...`) and emails.
- Strict additionally masks bearer tokens, AWS keys, IPv4 addresses, and long numeric sequences (e.g., credit cards).

## Code Review Summary

A comprehensive code review was conducted on 2025-10-22 covering functionality, code quality, and security:

### Functionality & Logic ✅

- **CLI & Agent System**: Dynamic agent discovery (`AGENT_REGISTRY`) and registration work correctly. CLI commands (`run`, `list-agents`, `interactive`) handle edge cases and errors appropriately.
- **Orchestration**: `MasterAgent` implements async orchestration with configurable rounds, timeouts, and sub-agent selection.
- **Error Handling**: Proper validation for missing agents, config issues, and import errors with clear user feedback.

### Code Quality ✅

- **Tooling**: Pre-commit hooks with `ruff`, `black`, and `mypy` ensure consistent formatting and type safety.
- **Structure**: Modular design with clear separation (`src/agents/`, `src/core/`, `src/main.py`). Naming conventions follow Python standards (`CamelCase` for classes, `snake_case` for functions/variables).
- **Readability**: Code is well-commented in English, functions are focused, and minimal duplication exists.
- **Extensibility**: Abstract `Agent` base class and `AgentConfig` Pydantic model support easy agent creation.

### Security ✅

- **Input Validation**: CLI arguments validated by `Typer`, agent configs by `Pydantic`. Layered config system (env/file/CLI) with proper precedence.
- **Redaction**: `Redactor` class masks sensitive data (API keys, emails, tokens, IPs, credit cards, Polish IBAN/PESEL/NIP) at two levels (`normal`, `strict`).
- **Security Policy**: `SecurityPolicy` class implements agent allowlists and round limits via environment variables.
- **No Hardcoded Secrets**: All sensitive values loaded from environment or config files.

### Recommendations

1. Documentation: add inline docstrings to all public methods for better IDE support. [Done 2025-10-22]
2. Testing: current coverage is ≥85%. Consider adding more edge case tests for complex orchestration scenarios. [Open]
3. Type Hints: ensure all new code includes comprehensive type hints. [Done 2025-10-22]
4. Error Messages: make selected errors more descriptive with context. [Done 2025-10-22]
5. Logging: consider adding more debug‑level logs in critical paths for troubleshooting. [Open]

### Updates (2025-10-22)

- Added comprehensive docstrings to public APIs across src/agents, src/core, and CLI helpers.
- Completed type hints for helper utilities and refined function signatures.
- Improved error messages with exception types and actionable context (invalid config JSON/YAML, env JSON parse errors, serialization failures).

Overall, ftSystem demonstrates solid engineering practices with good security foundations and maintainable architecture.
