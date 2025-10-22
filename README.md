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
- New agent generator: `new-agent <Name> [--target-dir src/agents] [--config-out cfg.json] [--force]`
  - Example: `python -m src.main new-agent Report --config-out report_config.json`
- Config formats: JSON and YAML (`--config file.yaml`)

### RAG (Local Retrieval)

- Build index: `python -m src.main rag index --src <folder|file> [--index-dir data/index]`
- Query index: `python -m src.main rag query --q "<text>" [--top-k 5] [--index-dir data/index]`
- Supported sources: `.txt`, `.md`. Index stored as JSONL in `data/index/chunks.jsonl`.


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
  - Filters: `--agent HelloAgent`, `--contains Hello`
- Replay a transcript file: `python -m src.main history replay logs/sessions/<file>.jsonl`

## Testing

- Run tests: `python -m pytest -q`
- Coverage: `pytest -q --cov=src --cov-report=term-missing --cov-fail-under=85`

## Project Structure

- CLI: `src/main.py` (Typer commands)
- Agents base: `src/agents/base.py`, dynamic registry: `src/agents/__init__.py`
- Example agent: `src/agents/hello_agent.py`
- Tests: `tests/`
- Plugins guide: `docs/plugins.md`

## Design Guide

- Primary (ApplyIntelligently): `docs/ftSystem_core.md`

## Voice Setup (Vosk)

- Download a PL model from the Vosk models page and unpack (e.g., `D:\\models\\vosk-pl`).
- Install deps: `pip install vosk sounddevice pyttsx3` (TTS optional on Windows).
- Run interactive with voice: `python -m src.main interactive --agent HelloAgent --voice-in vosk --stt-model-dir D:\\models\\vosk-pl --beep --silence-timeout-sec 1.5`

## Redaction Levels

- Global option: `--redact-level {normal|strict}` (or ENV `FTSYSTEM_REDACT_LEVEL`).
- Normal masks API keys (e.g., `sk-...`) and emails.
- Strict additionally masks bearer tokens, AWS keys, IPv4 addresses, and long numeric sequences (e.g., credit cards).
