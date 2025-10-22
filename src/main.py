import typer
import json
import logging
import sys
import os
import asyncio
import inspect
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel
from agents import AGENT_REGISTRY, AGENT_IMPORT_ERRORS  # dynamiczny rejestr agentów
from agents.base import AgentConfig, SessionSummary
from core.security import Redactor
from rag.simple import build_index as rag_build_index, query_index as rag_query_index

app = typer.Typer(help="ftSystem - Multi-Agent AI CLI")
history_app = typer.Typer(help="Session history utilities")
app.add_typer(history_app, name="history")
rag_app = typer.Typer(help="Local retrieval (RAG) utilities")
app.add_typer(rag_app, name="rag")

# Global profile setting (dev/prod)
PROFILE: str = os.environ.get("FTSYSTEM_PROFILE", "dev")


@app.callback()
def _configure(
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        help="Logging level (CRITICAL, ERROR, WARNING, INFO, DEBUG)",
        show_default=True,
    ),
    profile: str = typer.Option(None, "--profile", help="Config profile: dev or prod"),
    redact_level: Optional[str] = typer.Option(
        None,
        "--redact-level",
        help="Redaction level: strict|normal (default: env FTSYSTEM_REDACT_LEVEL or normal)",
    ),
):
    """Global CLI configuration (logging, etc.)."""
    level_name = str(log_level).upper()
    valid = {"CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"}
    if level_name not in valid:
        raise typer.BadParameter(f"Invalid log level: {log_level}")
    level = getattr(logging, level_name, logging.INFO)
    try:
        from rich.logging import RichHandler  # type: ignore

        logging.basicConfig(
            level=level,
            format="%(message)s",
            handlers=[RichHandler(rich_tracebacks=True, markup=True)],
            force=True,
        )
    except Exception:
        logging.basicConfig(
            level=level,
            format="%(levelname)s: %(message)s",
            handlers=[logging.StreamHandler(sys.stdout)],
            force=True,
        )
    global PROFILE
    if profile:
        PROFILE = profile
    logging.debug("ftsystem logger initialized (level=%s, profile=%s)", level_name, PROFILE)
    # Configure redaction level (normal|strict)
    rlevel = (redact_level or os.environ.get("FTSYSTEM_REDACT_LEVEL") or "normal").lower()
    if rlevel not in {"normal", "strict"}:
        rlevel = "normal"
    Redactor.set_level(rlevel)


def complete_agent(incomplete: str):
    """Autocomplete for agent names based on the registry."""
    text = (incomplete or "").lower()
    return [name for name in AGENT_REGISTRY.keys() if name.lower().startswith(text)]


@app.command()
def run(
    agent: str = typer.Option(
        ..., "--agent", help="Agent class name (e.g. HelloAgent)", autocompletion=complete_agent
    ),
    config: Path = typer.Option(None, "--config", help="Path to agent config file (JSON or YAML)"),
    param: list[str] = typer.Option(None, "--param", help="Override config params key=value (repeatable)"),
    output: Path = typer.Option(None, "--output", help="If set, save run() result to JSON at this path"),
):
    """
    Run selected agent with optional configuration.
    """
    if agent not in AGENT_REGISTRY:
        typer.echo(
            f"Agent '{agent}' not found. Available: {list(AGENT_REGISTRY.keys())}",
            err=True,
        )
        raise typer.Exit(code=1)

    agent_cls = AGENT_REGISTRY[agent]

    # Build config (file -> env -> CLI params)
    try:
        agent_config = _build_agent_config(agent, config, param)
    except Exception as e:
        typer.echo(f"Error building config: {e}", err=True)
        raise typer.Exit(code=1)

    # Instantiate and run agent
    agent_instance = agent_cls(agent_config)
    result = agent_instance.run()
    typer.echo(f"{agent}.run() result: {result}")
    if output is not None:
        try:
            # Support Pydantic models (v2)
            to_dump = result.model_dump() if isinstance(result, BaseModel) else result
            with open(output, "w", encoding="utf-8") as f:
                json.dump(to_dump, f, ensure_ascii=False, indent=2)
            typer.echo(f"Saved result JSON to: {output}")
        except TypeError as e:
            typer.echo(f"Serialization error: {e}", err=True)
            raise typer.Exit(code=1)
    _persist_session_summary(agent, status="ok", message=None, data=result)


@app.command("list-agents")
def list_agents(
    verbose: bool = typer.Option(False, "--verbose", help="Show docstring and module path"),
    show_errors: bool = typer.Option(False, "--show-errors", help="Show agent import errors"),
):
    """Display the list of available agents."""
    typer.echo("Available agents:")
    for name, cls in AGENT_REGISTRY.items():
        if verbose:
            doc = inspect.getdoc(cls) or ""
            module = cls.__module__
            typer.echo(f" - {name} ({module})")
            if doc:
                typer.echo(f"   doc: {doc}")
        else:
            typer.echo(f" - {name}")
    if show_errors:
        if AGENT_IMPORT_ERRORS:
            typer.echo("Import errors:")
            for mod, err in AGENT_IMPORT_ERRORS.items():
                typer.echo(f" - {mod}: {err}")
        else:
            typer.echo("No import errors.")


def _to_snake(name: str) -> str:
    name = name.strip()
    name = re.sub(r"\W+", " ", name)
    name = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return "_".join(part.lower() for part in name.split())


@app.command("new-agent")
def new_agent(
    name: str = typer.Argument(..., help="Agent class name, e.g., Report or ReportAgent"),
    target_dir: Path = typer.Option(Path("src/agents"), "--target-dir", help="Directory to create the agent in"),
    config_out: Path = typer.Option(None, "--config-out", help="Optional path to write example JSON config"),
    force: bool = typer.Option(False, "--force", help="Overwrite files if they exist"),
):
    """Generate a new agent class file (and optional config)."""
    class_name = name if name.endswith("Agent") else f"{name}Agent"
    snake = _to_snake(class_name.replace("Agent", ""))
    filename = f"{snake}_agent.py"
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / filename

    if file_path.exists() and not force:
        typer.echo(f"File already exists: {file_path}. Use --force to overwrite.")
        raise typer.Exit(code=1)

    content = f'''
from .base import Agent, AgentConfig
from typing import Any
import logging


class {class_name}(Agent):
    """Example agent generated by CLI."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)

    def run(self, **kwargs: Any) -> Any:
        logging.info("{class_name} is running")
        return {{"message": "Hello from {class_name}"}}
'''.lstrip()

    file_path.write_text(content, encoding="utf-8")
    typer.echo(f"Created agent: {file_path}")

    if config_out is not None:
        cfg = {"name": snake, "description": f"Auto config for {class_name}"}
        try:
            with open(config_out, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            typer.echo(f"Wrote config JSON: {config_out}")
        except Exception as e:
            typer.echo(f"Could not write config: {e}", err=True)



# ---------------------
# History helpers/CLI
# ---------------------

def _history_dir() -> Path:
    base = os.environ.get("FTSYSTEM_HISTORY_DIR")
    return Path(base) if base else Path("logs")


def _history_path_for(date: Optional[datetime] = None) -> Path:
    d = (date or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    p = _history_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p / f"history_{d}.jsonl"


def _persist_session_summary(agent: str, status: str, message: Optional[str], data: object) -> None:
    try:
        preview = None
        if data is not None:
            s = str(data)
            preview = s[:200]
            preview = Redactor.redact(preview)
        summary = SessionSummary(
            timestamp=datetime.now(timezone.utc),
            agent=agent,
            status=status,
            message=message,
            data_preview=preview,
        )
        path = _history_path_for()
        with open(path, "a", encoding="utf-8") as f:
            f.write(summary.model_dump_json())
            f.write("\n")
        logging.debug("Saved session summary to %s", path)
    except Exception as e:
        logging.debug("Could not persist session summary: %s", e)


@history_app.command("show")
def history_show(
    date: Optional[str] = typer.Option(None, "--date", help="Date YYYY-MM-DD to show (default today)"),
    limit: int = typer.Option(20, "--limit", help="Max lines to show"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Filter by agent name"),
    contains: Optional[str] = typer.Option(None, "--contains", help="Filter by substring in message or data preview"),
):
    """Show recent session summaries from JSONL files (with optional filters)."""
    dt = None
    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise typer.BadParameter("--date must be in YYYY-MM-DD format")
    path = _history_path_for(dt)
    if not path.exists():
        typer.echo(f"No history for date: {date or datetime.now(timezone.utc).strftime('%Y-%m-%d')}")
        raise typer.Exit(code=0)
    lines = path.read_text(encoding="utf-8").splitlines()
    emitted = 0
    for line in reversed(lines):
        try:
            obj = json.loads(line)
        except Exception:
            continue
        if agent and obj.get("agent") != agent:
            continue
        if contains and not (
            (obj.get("message") and contains in obj.get("message", ""))
            or (obj.get("data_preview") and contains in obj.get("data_preview", ""))
        ):
            continue
        typer.echo(line)
        emitted += 1
        if emitted >= limit:
            break


# ---------------------
# Config helpers
# ---------------------

def _deep_merge(a: dict, b: dict) -> dict:
    out = dict(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _parse_params(params: Optional[list[str]]) -> dict:
    result: dict = {}
    if not params:
        return result
    for item in params:
        if "=" not in item:
            continue
        k, v = item.split("=", 1)
        try:
            result[k] = json.loads(v)
        except Exception:
            result[k] = v
    return result


def _build_agent_config(agent: str, config_path: Optional[Path], cli_params: Optional[list[str]]) -> AgentConfig:
    data: dict = {}
    if config_path is not None:
        suffix = config_path.suffix.lower()
        if suffix in {".yml", ".yaml"}:
            try:
                import yaml  # type: ignore
            except Exception as e:  # pragma: no cover
                raise RuntimeError(f"YAML not available: {e}")
            with open(config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            with open(config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
    if not data:
        data = {"name": agent, "description": f"Auto config for {agent}"}
    # Env overlays
    name_env = os.environ.get("FTSYSTEM_AGENT_NAME")
    desc_env = os.environ.get("FTSYSTEM_AGENT_DESCRIPTION")
    params_env = os.environ.get("FTSYSTEM_PARAMS")
    if name_env:
        data["name"] = name_env
    if desc_env:
        data["description"] = desc_env
    if params_env:
        try:
            penv = json.loads(params_env)
            data["params"] = _deep_merge(data.get("params", {}) or {}, penv)
        except Exception:
            pass
    # CLI overlays
    pcli = _parse_params(cli_params)
    if pcli:
        data["params"] = _deep_merge(data.get("params", {}) or {}, pcli)
    return AgentConfig(**data)


@history_app.command("replay")
def history_replay(
    file: Path = typer.Argument(..., help="Path to a session transcript JSONL file"),
    limit: int = typer.Option(None, "--limit", help="Max turns to show (from start)"),
):
    """Replay a transcript file (JSONL) with pretty formatting."""
    if not file.exists():
        typer.echo(f"Transcript not found: {file}", err=True)
        raise typer.Exit(code=1)
    lines = file.read_text(encoding="utf-8").splitlines()
    count = 0
    for line in lines:
        try:
            obj = json.loads(line)
        except Exception:
            continue
        ts = str(obj.get("timestamp", ""))
        # Print only time for brevity
        try:
            tdisp = datetime.fromisoformat(ts.replace("Z", "+00:00")).strftime("%H:%M:%S")
        except Exception:
            tdisp = ts
        role = obj.get("role", "?")
        ag = obj.get("agent", "?")
        text = obj.get("text", "")
        if role == "agent":
            typer.echo(f"[{tdisp}] {role}({ag}): {text}")
        else:
            typer.echo(f"[{tdisp}] {role}: {text}")
        count += 1
        if limit and count >= limit:
            break


@app.command("interactive")
def interactive(
    agent: str = typer.Option(
        ..., "--agent", help="Agent class name (e.g. HelloAgent)", autocompletion=complete_agent
    ),
    config: Path = typer.Option(None, "--config", help="Path to agent config file (JSON or YAML)"),
    voice_in: Optional[str] = typer.Option(None, "--voice-in", help="STT provider: vosk|mock"),
    voice_out: Optional[str] = typer.Option(None, "--voice-out", help="TTS provider: sapi5|mock"),
    stt_model_dir: Optional[Path] = typer.Option(None, "--stt-model-dir", help="Path to Vosk model directory (for --voice-in vosk)"),
    voice_lang: str = typer.Option("pl-PL", "--voice-lang", help="Language code for voice (e.g., pl-PL)"),
    max_utterance_sec: int = typer.Option(8, "--max-utterance-sec", help="Max seconds per utterance"),
    mic_index: Optional[int] = typer.Option(None, "--mic-index", help="Microphone device index"),
    silence_timeout_sec: Optional[float] = typer.Option(
        None, "--silence-timeout-sec", help="Auto-stop after this many seconds of silence (when using --voice-in vosk)"
    ),
    beep: bool = typer.Option(True, "--beep/--no-beep", help="Play beeps on start/stop recording"),
):
    """Interactive loop that maintains session and writes summaries."""
    if agent not in AGENT_REGISTRY:
        typer.echo(
            f"Agent '{agent}' not found. Available: {list(AGENT_REGISTRY.keys())}",
            err=True,
        )
        raise typer.Exit(code=1)

    # Load config (reuse logic from run)
    if config is not None:
        try:
            suffix = config.suffix.lower()
            if suffix in {".yml", ".yaml"}:
                import yaml  # type: ignore

                with open(config, "r", encoding="utf-8") as f:
                    config_data = yaml.safe_load(f) or {}
            else:
                with open(config, "r", encoding="utf-8") as f:
                    config_data = json.load(f)
            agent_config = AgentConfig(**config_data)
        except Exception as e:
            typer.echo(f"Error loading config: {e}", err=True)
            raise typer.Exit(code=1)
    else:
        agent_config = AgentConfig(name=agent, description=f"Interactive config for {agent}")

    agent_instance = AGENT_REGISTRY[agent](agent_config)
    typer.echo("Interactive mode. Type /exit to quit, /help for help.")
    # Voice setup (lazy, only when requested)
    stt = None
    tts = None
    if voice_in:
        def _make_stt():
            if voice_in == "mock":
                class _MockSTT:
                    def listen_once(self_inner):
                        import os
                        return os.environ.get("FTSYSTEM_MOCK_STT_TEXT", "")
                return _MockSTT()
            if voice_in == "vosk":
                from core.voice import VoskSTT, STTConfig
                model_dir_eff = stt_model_dir or Path(os.environ.get("FTSYSTEM_VOSK_MODEL", ""))
                cfg = STTConfig(
                    model_dir=model_dir_eff,
                    lang=voice_lang,
                    samplerate=16000,
                    max_seconds=max_utterance_sec,
                    device_index=mic_index,
                    beep=bool(beep),
                    silence_timeout_sec=silence_timeout_sec,
                )
                return VoskSTT(cfg)
            raise typer.BadParameter(f"Unsupported --voice-in: {voice_in}")
        stt = _make_stt()
        typer.echo("Voice input enabled. Use /rec to record an utterance.")
    if voice_out:
        def _make_tts():
            if voice_out == "mock":
                class _MockTTS:
                    def speak(self_inner, text: str):
                        return None
                return _MockTTS()
            if voice_out == "sapi5":
                from core.voice import SapiTTS
                return SapiTTS(lang=voice_lang)
            raise typer.BadParameter(f"Unsupported --voice-out: {voice_out}")
        tts = _make_tts()
        typer.echo("Voice output enabled.")
    # Prepare session transcript file and helpers
    def _session_dir() -> Path:
        base = os.environ.get("FTSYSTEM_SESSION_DIR")
        return Path(base) if base else (Path("logs") / "sessions")

    def _session_file_path(agent_name: str) -> Path:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", agent_name)
        d = _session_dir()
        d.mkdir(parents=True, exist_ok=True)
        return d / f"session_{safe}_{stamp}.jsonl"

    def _append_session_turn(path: Path, role: str, agent_name: str, text: str) -> None:
        rec = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "role": role,
            "agent": agent_name,
            "text": text,
        }
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False))
            f.write("\n")

    session_path = _session_file_path(agent)
    typer.echo(f"Session file: {session_path}")
    while True:
        try:
            text = typer.prompt("»")
        except typer.Abort:
            break
        if not text:
            continue
        cmd = text.strip()
        if cmd.startswith("/"):
            if cmd in {"/exit", "/quit", "/q"}:
                break
            if cmd == "/help":
                extra = " /rec" if stt else ""
                typer.echo(f"Commands: /exit, /help, /history{extra}")
                continue
            if cmd == "/history":
                # Show last 10 items
                history_show.callback  # no-op to keep linter happy
                # Call underlying function with defaults
                _ = None
                path = _history_path_for()
                lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
                for line in lines[-10:]:
                    typer.echo(line)
                continue
            if cmd == "/rec":
                if not stt:
                    typer.echo("Voice input not enabled. Use --voice-in.")
                    continue
                try:
                    utter = stt.listen_once()
                except Exception as e:
                    typer.echo(f"STT error: {e}", err=True)
                    continue
                from core.security import Redactor
                utter_red = Redactor.redact(utter) or ""
                typer.echo(f"Transcribed: {utter_red}")
                if not utter_red.strip():
                    continue
                _append_session_turn(session_path, role="user", agent_name=agent, text=utter_red)
                res = agent_instance.run(input=utter_red)
                typer.echo(f"-> {res}")
                if tts:
                    try:
                        tts.speak(str(res))
                    except Exception:
                        pass
                _persist_session_summary(agent, status="ok", message=f"input:{utter_red}", data=res)
                continue
        # Execute agent turn (pass input as kwarg if agent uses it)
        _append_session_turn(session_path, role="user", agent_name=agent, text=text)
        res = agent_instance.run(input=text)
        typer.echo(f"→ {res}")
        _append_session_turn(session_path, role="agent", agent_name=agent, text=str(res))
        _persist_session_summary(agent, status="ok", message=f"input:{text}", data=res)

if __name__ == "__main__":
    app()


# =========================
# RAG subcommands
# =========================

@rag_app.command("index")
def rag_index(
    src: Path = typer.Option(..., "--src", help="Source folder or file with .txt/.md content"),
    index_dir: Path = typer.Option(Path("data") / "index", "--index-dir", help="Index output directory"),
):
    """Build/refresh a simple local text index from files."""
    if not src.exists():
        typer.echo(f"Source not found: {src}", err=True)
        raise typer.Exit(code=1)
    out = rag_build_index(src, index_dir)
    typer.echo(f"Index written: {out}")


@rag_app.command("query")
def rag_query(
    q: str = typer.Option(..., "--q", help="Query text"),
    index_dir: Path = typer.Option(Path("data") / "index", "--index-dir", help="Index directory"),
    top_k: int = typer.Option(5, "--top-k", help="Number of results to return"),
):
    """Query the local index and print top-k results."""
    try:
        results = rag_query_index(index_dir, q, top_k=top_k)
    except FileNotFoundError as e:
        typer.echo(str(e), err=True)
        raise typer.Exit(code=1)
    for rank, (score, rec) in enumerate(results, start=1):
        snippet = str(rec.get("text", "")).strip().replace("\n", " ")
        if len(snippet) > 160:
            snippet = snippet[:157] + "..."
        typer.echo(f"{rank}. [{score:.2f}] {rec.get('doc_path')}#{rec.get('chunk_idx')}: {snippet}")

