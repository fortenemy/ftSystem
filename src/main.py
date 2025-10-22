import asyncio
import inspect
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import typer
from pydantic import BaseModel

from agents import AGENT_REGISTRY, AGENT_IMPORT_ERRORS  # dynamiczny rejestr agentów
from agents.base import AgentConfig, SessionSummary
from core.i18n import I18N, t
from core.metrics import PrometheusExporter
from core.security import Redactor

app = typer.Typer(help="ftSystem - Multi-Agent AI CLI")
history_app = typer.Typer(help="Session history utilities")
app.add_typer(history_app, name="history")
voice_app = typer.Typer(help="Voice utilities")
app.add_typer(voice_app, name="voice")
security_app = typer.Typer(help="Security utilities")
app.add_typer(security_app, name="security")
perf_app = typer.Typer(help="Performance utilities")
app.add_typer(perf_app, name="perf")

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
    lang: str = typer.Option(
        os.environ.get("FTSYSTEM_LANG", "en"),
        "--lang",
        help="CLI language (en or pl)",
        show_default=False,
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
    I18N.set_language(lang)
    logging.debug("ftsystem language set to %s", I18N.get_language())


def complete_agent(incomplete: str) -> list[str]:
    """Return agent names that match the provided prefix (case-insensitive)."""
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
    metrics_path: Optional[Path] = typer.Option(
        None, "--metrics-path", help="Write Prometheus metrics to this file"
    ),
    tag: list[str] = typer.Option(None, "--tag", help="Add session tag (repeatable)"),
):
    """
    Run selected agent with optional configuration.
    """
    logging.debug(
        "[cli] run command invoked (agent=%s, config=%s, params=%s, output=%s, tags=%s)",
        agent,
        config,
        bool(param),
        output,
        tag,
    )
    if agent not in AGENT_REGISTRY:
        typer.echo(t("agent_not_found", agent=agent, available=list(AGENT_REGISTRY.keys())), err=True)
        raise typer.Exit(code=1)

    agent_cls = AGENT_REGISTRY[agent]

    # Build config (file -> env -> CLI params)
    try:
        agent_config = _build_agent_config(agent, config, param)
    except Exception as e:
        typer.echo(
            f"Failed to build config for '{agent}': {type(e).__name__}: {e}",
            err=True,
        )
        raise typer.Exit(code=1)

    # Instantiate and run agent
    agent_instance = agent_cls(agent_config)
    logging.debug(
        "[cli] instantiated agent %s (config_name=%s, has_params=%s)",
        agent,
        getattr(agent_config, "name", None),
        bool(getattr(agent_config, "params", None)),
    )
    _set_current_tags(tag)
    start_t = time.perf_counter()
    result = agent_instance.run()
    duration = time.perf_counter() - start_t
    logging.debug("[cli] agent %s completed run (type=%s)", agent, type(result).__name__)
    typer.echo(f"{agent}.run() result: {result}")
    if metrics_path is not None:
        PrometheusExporter.write_metrics(metrics_path, agent, duration, result)
    if output is not None:
        try:
            # Support Pydantic models (v2)
            to_dump = result.model_dump() if isinstance(result, BaseModel) else result
            with open(output, "w", encoding="utf-8") as f:
                json.dump(to_dump, f, ensure_ascii=False, indent=2)
            typer.echo(f"Saved result JSON to: {output}")
        except TypeError as e:
            typer.echo(
                f"Failed to serialise result for '{agent}' to {output}: {type(e).__name__}: {e}",
                err=True,
            )
            raise typer.Exit(code=1)
    _persist_session_summary(agent, status="ok", message=None, data=result)


@perf_app.command("profile")
def perf_profile(
    agent: str = typer.Option(
        "MasterAgent", "--agent", help="Agent class name to profile", autocompletion=complete_agent
    ),
    subagent: list[str] = typer.Option(
        None,
        "--subagent",
        help="Subagent to include (repeatable, defaults to a sample set for MasterAgent)",
        autocompletion=complete_agent,
    ),
    rounds: int = typer.Option(1, "--rounds", help="Rounds parameter when profiling MasterAgent"),
    repeat: int = typer.Option(3, "--repeat", help="Number of times to run the agent"),
    json_out: bool = typer.Option(False, "--json", help="Return results as JSON"),
):
    """Profile execution time for the selected agent across multiple runs."""
    if agent not in AGENT_REGISTRY:
        typer.echo(t("agent_not_found", agent=agent, available=list(AGENT_REGISTRY.keys())), err=True)
        raise typer.Exit(code=1)
    if repeat < 1:
        raise typer.BadParameter("--repeat must be >= 1")
    agent_cls = AGENT_REGISTRY[agent]

    chosen_subagents = subagent or []
    if agent == "MasterAgent" and not chosen_subagents:
        chosen_subagents = [name for name in AGENT_REGISTRY.keys() if name != "MasterAgent"][:3]

    durations: list[float] = []
    results: list[Any] = []
    for idx in range(repeat):
        params: dict[str, Any] | None = None
        if agent == "MasterAgent":
            params = {"subagents": chosen_subagents, "rounds": rounds}
        elif chosen_subagents:
            params = {"subagents": chosen_subagents}
        cfg = AgentConfig(
            name=f"{agent}-profile",
            description="Performance profiling run",
            params=params,
        )
        logging.debug(
            "[perf] run #%s agent=%s params=%s",
            idx + 1,
            agent,
            params,
        )
        start = time.perf_counter()
        res = agent_cls(cfg).run()
        duration = time.perf_counter() - start
        durations.append(duration)
        results.append(res)

    summary = {
        "agent": agent,
        "runs": repeat,
        "durations": durations,
        "avg_duration": sum(durations) / repeat if durations else 0.0,
        "min_duration": min(durations) if durations else 0.0,
        "max_duration": max(durations) if durations else 0.0,
    }
    if agent == "MasterAgent":
        summary["rounds"] = rounds
        summary["subagents"] = chosen_subagents

    if json_out:
        typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        typer.echo(f"Agent: {agent}")
        if agent == "MasterAgent":
            typer.echo(f" Subagents: {chosen_subagents or '[]'}")
            typer.echo(f" Rounds: {rounds}")
        typer.echo(f" Runs: {repeat}")
        typer.echo(f" Avg duration: {summary['avg_duration']:.6f}s")
        typer.echo(f" Min duration: {summary['min_duration']:.6f}s")
        typer.echo(f" Max duration: {summary['max_duration']:.6f}s")
@app.command("list-agents")
def list_agents(
    verbose: bool = typer.Option(False, "--verbose", help="Show docstring and module path"),
    show_errors: bool = typer.Option(False, "--show-errors", help="Show agent import errors"),
    format: str = typer.Option("text", "--format", help="Output format: text|json"),
):
    """Display the list of available agents."""
    fmt = (format or "text").lower()
    if fmt not in {"text", "json"}:
        raise typer.BadParameter("--format must be 'text' or 'json'")
    if fmt == "json":
        agents = []
        for name, cls in AGENT_REGISTRY.items():
            item = {"name": name}
            if verbose:
                item["module"] = cls.__module__
                doc = inspect.getdoc(cls) or ""
                if doc:
                    item["doc"] = doc
            agents.append(item)
        out = {"agents": agents}
        if show_errors and AGENT_IMPORT_ERRORS:
            out["errors"] = {k: str(v) for k, v in AGENT_IMPORT_ERRORS.items()}
        typer.echo(json.dumps(out, ensure_ascii=False))
        return
    # text output
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
    """Convert a class-style name into snake_case for filenames."""
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
            typer.echo(
                f"Failed to write config JSON to {config_out}: {type(e).__name__}: {e}",
                err=True,
            )



# ---------------------
# History helpers/CLI
# ---------------------

def _history_dir() -> Path:
    """Return the directory that stores JSONL history files."""
    base = os.environ.get("FTSYSTEM_HISTORY_DIR")
    return Path(base) if base else Path("logs")


def _history_path_for(date: Optional[datetime] = None) -> Path:
    """Compute the JSONL history path for the given date (defaults to today)."""
    d = (date or datetime.now(timezone.utc)).strftime("%Y-%m-%d")
    p = _history_dir()
    p.mkdir(parents=True, exist_ok=True)
    return p / f"history_{d}.jsonl"


def _persist_session_summary(agent: str, status: str, message: Optional[str], data: object) -> None:
    """Persist a one-line JSON summary of the latest session run."""
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
            tags=_current_tags(),
        )
        path = _history_path_for()
        with open(path, "a", encoding="utf-8") as f:
            f.write(summary.model_dump_json())
            f.write("\n")
        logging.debug("Saved session summary to %s", path)
    except Exception as e:
        logging.debug(
            "Could not persist session summary for %s at %s: %s",
            agent,
            path if "path" in locals() else _history_path_for(),
            e,
            exc_info=e,
        )


@history_app.command("show")
def history_show(
    date: Optional[str] = typer.Option(None, "--date", help="Date YYYY-MM-DD to show (default today)"),
    limit: int = typer.Option(20, "--limit", help="Max lines to show"),
    offset: int = typer.Option(0, "--offset", help="Skip first N matching entries (newest-first)"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Filter by agent name"),
    contains: Optional[str] = typer.Option(None, "--contains", help="Filter by substring in message or data preview"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag"),
    json_out: bool = typer.Option(False, "--json", help="Output as a JSON array instead of JSONL lines"),
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
        typer.echo(
            t(
                "no_history",
                date=date or datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            )
        )
        raise typer.Exit(code=0)
    lines = path.read_text(encoding="utf-8").splitlines()
    # newest-first
    filtered: list[tuple[str, dict]] = []
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
        if tag and not (obj.get("tags") and tag in obj.get("tags", [])):
            continue
        filtered.append((line, obj))
    start = max(0, int(offset))
    end = start + int(limit) if limit else None
    page = filtered[start:end]
    if json_out:
        typer.echo(json.dumps([obj for _, obj in page], ensure_ascii=False))
    else:
        for line, _ in page:
            typer.echo(line)


# ---------------------
# Config helpers
# ---------------------

def _deep_merge(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    """Recursively merge mapping ``b`` into ``a`` without mutating inputs."""
    out: dict[str, Any] = dict(a)
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def _parse_params(params: Optional[list[str]]) -> dict[str, Any]:
    """Parse CLI ``key=value`` overrides into JSON-compatible types."""
    result: dict[str, Any] = {}
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
    """Assemble an AgentConfig from file, environment, and CLI overrides."""
    data: dict[str, Any] = {}
    logging.debug(
        "[config] building config for agent=%s (config_path=%s, cli_params=%s)",
        agent,
        config_path,
        bool(cli_params),
    )
    if config_path is not None:
        suffix = config_path.suffix.lower()
        try:
            if suffix in {".yml", ".yaml"}:
                try:
                    import yaml  # type: ignore
                except Exception as e:  # pragma: no cover
                    raise RuntimeError(
                        f"YAML support is required to load {config_path}: {type(e).__name__}: {e}"
                    ) from e
                with open(config_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f) or {}
            else:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except FileNotFoundError as e:
            raise RuntimeError(f"Config file not found: {config_path}") from e
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Invalid JSON in config file {config_path}: {e}") from e
        except Exception as e:
            raise RuntimeError(
                f"Failed to load config file {config_path}: {type(e).__name__}: {e}"
            ) from e
        logging.debug("[config] loaded config file %s (keys=%s)", config_path, list(data.keys()))
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
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Environment variable FTSYSTEM_PARAMS must be valid JSON: {e}") from e
        existing_params = data.get("params") or {}
        if existing_params and not isinstance(existing_params, dict):
            raise RuntimeError(
                f"Expected 'params' to be a mapping in config for {agent}, got {type(existing_params).__name__}"
            )
        data["params"] = _deep_merge(existing_params or {}, penv)
        logging.debug("[config] merged params from environment (keys=%s)", list((data.get("params") or {}).keys()))
    # CLI overlays
    pcli = _parse_params(cli_params)
    if pcli:
        existing_params_cli = data.get("params") or {}
        if existing_params_cli and not isinstance(existing_params_cli, dict):
            raise RuntimeError(
                f"Expected 'params' to be a mapping before applying CLI overrides for {agent}, "
                f"got {type(existing_params_cli).__name__}"
            )
        data["params"] = _deep_merge(existing_params_cli or {}, pcli)
        logging.debug("[config] merged params from CLI (keys=%s)", list((data.get("params") or {}).keys()))
    config_obj = AgentConfig(**data)
    logging.debug(
        "[config] final AgentConfig(name=%s, has_params=%s)",
        config_obj.name,
        bool(config_obj.params),
    )
    return config_obj


# ---------------------
# Config dir & profiles
# ---------------------

def _config_dir() -> Path:
    """Directory for auxiliary CLI configuration artifacts."""
    base = os.environ.get("FTSYSTEM_CONFIG_DIR")
    return Path(base) if base else Path("logs") / "config"


def _voice_profile_path() -> Path:
    """Return the file path that stores the persistent voice profile."""
    d = _config_dir()
    d.mkdir(parents=True, exist_ok=True)
    return d / "voice_profile.json"


def _load_voice_profile() -> dict[str, Any]:
    """Load the persisted voice profile JSON into a dictionary."""
    p = _voice_profile_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def _save_voice_profile(data: dict[str, Any]) -> None:
    """Write the voice profile dictionary back to disk."""
    p = _voice_profile_path()
    p.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# Tags context (process-local)
_TAGS: list[str] = []


def _set_current_tags(tags: Optional[list[str]]) -> None:
    """Store the current tag list for subsequent summary persistence."""
    global _TAGS
    _TAGS = [t for t in (tags or []) if isinstance(t, str) and t.strip()]


def _current_tags() -> list[str]:
    """Return the most recently set tags."""
    return list(_TAGS)


@history_app.command("find")
def history_find(
    contains: str = typer.Option(..., "--contains", help="Substring to search in message/data"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Filter by agent name"),
    since: Optional[str] = typer.Option(None, "--since", help="Start date YYYY-MM-DD (inclusive)"),
    days: Optional[int] = typer.Option(None, "--days", help="Search from last N days (inclusive)"),
    limit: Optional[int] = typer.Option(None, "--limit", help="Limit number of results (after ordering)"),
    reverse: bool = typer.Option(False, "--reverse", help="Newest-first ordering (default oldest-first)"),
    offset: int = typer.Option(0, "--offset", help="Skip first N results after ordering"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON array"),
):
    """Search across multiple history files by substring and optional filters."""
    if since and days is not None:
        raise typer.BadParameter("Use either --since or --days, not both")
    from datetime import date as _date, timedelta as _timedelta

    pdir = _history_dir()
    files = list(pdir.glob("history_*.jsonl")) if pdir.exists() else []
    date_from: Optional[_date] = None
    if since:
        try:
            date_from = _date.fromisoformat(since)
        except Exception:
            raise typer.BadParameter("--since must be YYYY-MM-DD")
    elif days is not None:
        today = _date.today()
        d = max(0, int(days))
        date_from = _date.fromordinal(today.toordinal() - max(0, d - 1))
    # Filter files by date
    selected: list[tuple[_date, Path]] = []
    for f in files:
        try:
            dstr = f.stem.split("_")[1]
            fd = _date.fromisoformat(dstr)
        except Exception:
            continue
        if date_from is None or fd >= date_from:
            selected.append((fd, f))
    selected.sort(key=lambda t: t[0], reverse=bool(reverse))
    hits: list[dict] = []
    needle = contains
    for _, path in selected:
        try:
            lines = path.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in lines:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            if agent and obj.get("agent") != agent:
                continue
            if not (
                (obj.get("message") and needle in obj.get("message", ""))
                or (obj.get("data_preview") and needle in obj.get("data_preview", ""))
            ):
                continue
            obj_with_src = dict(obj)
            obj_with_src["_file"] = str(path)
            hits.append(obj_with_src)
    total = len(hits)
    # apply offset + limit
    start = max(0, int(offset))
    end = start + int(limit) if limit else None
    items = hits[start:end]
    if json_out:
        typer.echo(json.dumps({"total": total, "items": items}, ensure_ascii=False))
    else:
        for obj in items:
            typer.echo(json.dumps(obj, ensure_ascii=False))


@history_app.command("stats")
def history_stats(
    since: Optional[str] = typer.Option(None, "--since", help="Start date YYYY-MM-DD (inclusive)"),
    days: Optional[int] = typer.Option(None, "--days", help="From last N days (inclusive)"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Restrict counts to a specific agent"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON"),
):
    """Aggregate counts per agent and status across history files."""
    if since and days is not None:
        raise typer.BadParameter("Use either --since or --days, not both")
    from datetime import date as _date

    pdir = _history_dir()
    files = list(pdir.glob("history_*.jsonl")) if pdir.exists() else []
    date_from: Optional[_date] = None
    if since:
        try:
            date_from = _date.fromisoformat(since)
        except Exception:
            raise typer.BadParameter("--since must be YYYY-MM-DD")
    elif days is not None:
        today = _date.today()
        d = max(0, int(days))
        date_from = _date.fromordinal(today.toordinal() - max(0, d - 1))
    # Aggregate
    by_agent: dict[str, int] = {}
    by_status: dict[str, int] = {}
    total = 0
    for f in files:
        try:
            dstr = f.stem.split("_")[1]
            fd = _date.fromisoformat(dstr)
        except Exception:
            continue
        if date_from is not None and fd < date_from:
            continue
        try:
            lines = f.read_text(encoding="utf-8").splitlines()
        except Exception:
            continue
        for line in lines:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            ag = str(obj.get("agent", ""))
            if agent and ag != agent:
                continue
            total += 1
            st = str(obj.get("status", ""))
            by_agent[ag] = by_agent.get(ag, 0) + 1
            by_status[st] = by_status.get(st, 0) + 1
    if json_out:
        typer.echo(json.dumps({"total": total, "by_agent": by_agent, "by_status": by_status}, ensure_ascii=False))
        return
    typer.echo(f"Total: {total}")
    typer.echo("By agent:")
    for k, v in sorted(by_agent.items()):
        typer.echo(f" - {k}: {v}")
    typer.echo("By status:")
    for k, v in sorted(by_status.items()):
        typer.echo(f" - {k}: {v}")


@security_app.command("redact")
def security_redact(
    inp: Path = typer.Option(..., "--in", help="Input text file"),
    out: Path = typer.Option(..., "--out", help="Output text file"),
    level: Optional[str] = typer.Option(None, "--level", help="Redaction level: strict|normal"),
):
    """Apply redaction to a text file using configured (or overridden) level."""
    if level:
        Redactor.set_level(level)
    if not inp.exists():
        typer.echo(f"Input not found: {inp}", err=True)
        raise typer.Exit(code=1)
    text = inp.read_text(encoding="utf-8", errors="ignore")
    red = Redactor.redact(text) or ""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(red, encoding="utf-8")
    typer.echo(f"Wrote redacted text to {out}")


@history_app.command("export")
def history_export(
    out: Path = typer.Option(..., "--out", help="Output file path (JSONL)"),
    date: Optional[str] = typer.Option(None, "--date", help="Date YYYY-MM-DD (default today)"),
    limit: int = typer.Option(None, "--limit", help="Limit number of entries (from newest)"),
    agent: Optional[str] = typer.Option(None, "--agent", help="Filter by agent name"),
    contains: Optional[str] = typer.Option(None, "--contains", help="Filter by substring in message/data"),
    tag: Optional[str] = typer.Option(None, "--tag", help="Filter by tag name"),
):
    """Export filtered history to a JSONL file."""
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
    out.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with out.open("w", encoding="utf-8") as f:
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
            if tag and not (obj.get("tags") and tag in obj.get("tags", [])):
                continue
            f.write(json.dumps(obj, ensure_ascii=False))
            f.write("\n")
            count += 1
            if limit and count >= limit:
                break
    typer.echo(f"Exported {count} entries to {out}")


@history_app.command("clear")
def history_clear(
    date: Optional[str] = typer.Option(None, "--date", help="Date YYYY-MM-DD (default today)"),
    all_files: bool = typer.Option(False, "--all", help="Clear all history files in the history dir"),
    yes: bool = typer.Option(False, "--yes", help="Do not prompt for confirmation"),
):
    """Delete history file(s). Safe by default; requires --yes."""
    if not yes:
        typer.echo(t("clearing_refused"))
        raise typer.Exit(code=1)
    pdir = _history_dir()
    if all_files:
        if not pdir.exists():
            typer.echo("Nothing to clear")
            raise typer.Exit(code=0)
        removed = 0
        for p in pdir.glob("history_*.jsonl"):
            try:
                p.unlink()
                removed += 1
            except Exception:
                pass
        typer.echo(f"Removed {removed} files from {pdir}")
        raise typer.Exit(code=0)
    dt = None
    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise typer.BadParameter("--date must be in YYYY-MM-DD format")
    p = _history_path_for(dt)
    if p.exists():
        p.unlink()
        typer.echo(f"Removed {p}")
    else:
        typer.echo("Nothing to clear")


@history_app.command("prune")
def history_prune(
    keep: Optional[int] = typer.Option(None, "--keep", help="Keep last N entries for a given date"),
    date: Optional[str] = typer.Option(None, "--date", help="Date YYYY-MM-DD (default today)"),
    days: Optional[int] = typer.Option(None, "--days", help="Remove history files older than N days"),
    yes: bool = typer.Option(False, "--yes", help="Confirm pruning operation"),
):
    """Prune history: keep last N entries or remove files older than N days."""
    if not yes:
        typer.echo(t("pruning_refused"))
        raise typer.Exit(code=1)
    # Files aging mode
    if days is not None:
        from datetime import date as _date

        today = _date.today()
        try:
            ndays = int(days)
        except Exception:
            raise typer.BadParameter("--days must be an integer")
        cutoff = _date.fromordinal(today.toordinal() - max(0, ndays))
        pdir = _history_dir()
        removed = 0
        if pdir.exists():
            for p in pdir.glob("history_*.jsonl"):
                try:
                    dstr = p.stem.split("_")[1]
                    pd = _date.fromisoformat(dstr)
                except Exception:
                    continue
                if pd < cutoff:
                    try:
                        p.unlink()
                        removed += 1
                    except Exception:
                        pass
        typer.echo(f"Removed {removed} old file(s)")
        return
    # Line prune mode
    if keep is None:
        raise typer.BadParameter("Specify --keep N or --days N")
    if date:
        try:
            dt = datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            raise typer.BadParameter("--date must be in YYYY-MM-DD format")
    else:
        dt = None
    p = _history_path_for(dt)
    if not p.exists():
        typer.echo("No history file to prune")
        raise typer.Exit(code=0)
    lines = p.read_text(encoding="utf-8").splitlines()
    k = max(0, int(keep))
    new_lines = lines[-k:] if k > 0 else []
    p.write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")
    typer.echo(f"Pruned to {len(new_lines)} entrie(s) in {p}")


@history_app.command("replay")
def history_replay(
    file: Path = typer.Argument(..., help="Path to a session transcript JSONL file"),
    limit: int = typer.Option(None, "--limit", help="Max turns to show (from start)"),
    out: Path = typer.Option(None, "--out", help="If set, save pretty output to this file"),
):
    """Replay a transcript file (JSONL) with pretty formatting."""
    if not file.exists():
        typer.echo(f"Transcript not found: {file}", err=True)
        raise typer.Exit(code=1)
    lines = file.read_text(encoding="utf-8").splitlines()
    count = 0
    pretty: list[str] = []
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
            pretty.append(f"[{tdisp}] {role}({ag}): {text}")
        else:
            pretty.append(f"[{tdisp}] {role}: {text}")
        count += 1
        if limit and count >= limit:
            break
    if out is not None:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("\n".join(pretty) + ("\n" if pretty else ""), encoding="utf-8")
        typer.echo(f"Saved replay to {out}")
    else:
        for l in pretty:
            typer.echo(l)


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
    tag: list[str] = typer.Option(None, "--tag", help="Add session tag (repeatable)"),
    dry_run_tts: bool = typer.Option(False, "--dry-run-tts", help="Log TTS text instead of speaking (for tests)"),
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
            typer.echo(
                f"Failed to load config from {config}: {type(e).__name__}: {e}",
                err=True,
            )
            raise typer.Exit(code=1)
    else:
        agent_config = AgentConfig(name=agent, description=f"Interactive config for {agent}")

    agent_instance = AGENT_REGISTRY[agent](agent_config)
    # Tags
    _set_current_tags(tag)
    typer.echo("Interactive mode. Type /exit to quit, /help for help.")
    # Voice setup (lazy, only when requested)
    stt = None
    tts = None
    last_reply: Optional[str] = None
    # Apply voice profile defaults if not explicitly provided
    prof = _load_voice_profile()
    voice_lang_eff = voice_lang or prof.get("voice_lang", voice_lang)
    mic_index_eff = mic_index if mic_index is not None else prof.get("mic_index")
    beep_eff = beep if ("beep" not in prof) else bool(prof.get("beep"))

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
                    lang=voice_lang_eff,
                    samplerate=16000,
                    max_seconds=max_utterance_sec,
                    device_index=mic_index_eff,
                    beep=bool(beep_eff),
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
                return SapiTTS(lang=voice_lang_eff)
            raise typer.BadParameter(f"Unsupported --voice-out: {voice_out}")
        tts = _make_tts()
        typer.echo("Voice output enabled.")
    # Prepare session transcript file and helpers
    def _session_dir() -> Path:
        """Return directory for interactive session transcripts."""
        base = os.environ.get("FTSYSTEM_SESSION_DIR")
        return Path(base) if base else (Path("logs") / "sessions")

    def _session_file_path(agent_name: str) -> Path:
        """Compute a timestamped session transcript path for the agent."""
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%SZ")
        safe = re.sub(r"[^a-zA-Z0-9_-]", "_", agent_name)
        d = _session_dir()
        d.mkdir(parents=True, exist_ok=True)
        return d / f"session_{safe}_{stamp}.jsonl"

    def _append_session_turn(path: Path, role: str, agent_name: str, text: str) -> None:
        """Append a serialised turn to the session transcript file."""
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
                typer.echo(f"Commands: /exit, /help, /history /last /tags{extra}")
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
            if cmd == "/last":
                typer.echo(last_reply or "(no reply yet)")
                continue
            if cmd == "/tags":
                tags = _current_tags()
                typer.echo(", ".join(tags) if tags else "(no tags)")
                continue
            if cmd.startswith("/save"):
                parts = cmd.split(maxsplit=1)
                if len(parts) == 1:
                    typer.echo("Usage: /save <file>")
                    continue
                if not last_reply:
                    typer.echo("Nothing to save (no last reply).")
                    continue
                dest = Path(parts[1]).expanduser()
                try:
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_text(last_reply, encoding="utf-8")
                    typer.echo(f"Saved to: {dest}")
                except Exception as e:
                    typer.echo(f"Save error: {e}", err=True)
                continue
            if cmd == "/clear":
                # Try ANSI clear; also print a confirmation line for testability
                try:
                    typer.echo("\x1b[2J\x1b[H", nl=False)
                except Exception:
                    pass
                typer.echo("Screen cleared.")
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
                last_reply = str(res)
                if tts:
                    try:
                        if dry_run_tts:
                            typer.echo(f"[TTS] {str(res)}")
                        else:
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


@voice_app.command("profile")
def voice_profile(
    show: bool = typer.Option(False, "--show", help="Show current voice profile as JSON"),
    set_: bool = typer.Option(False, "--set", help="Set fields from provided options"),
    voice_lang: Optional[str] = typer.Option(None, "--voice-lang"),
    mic_index: Optional[int] = typer.Option(None, "--mic-index"),
    beep: Optional[bool] = typer.Option(None, "--beep/--no-beep"),
):
    """Manage voice defaults used by interactive mode."""
    prof = _load_voice_profile()
    if set_:
        if voice_lang is not None:
            prof["voice_lang"] = voice_lang
        if mic_index is not None:
            prof["mic_index"] = mic_index
        if beep is not None:
            prof["beep"] = bool(beep)
        _save_voice_profile(prof)
    if show or not set_:
        typer.echo(json.dumps(prof, ensure_ascii=False))


@voice_app.command("devices")
def voice_devices(
    list_voices: bool = typer.Option(False, "--list-voices", help="Also list TTS voices (pyttsx3)"),
    json_out: bool = typer.Option(False, "--json", help="Output JSON instead of text"),
):
    """List available input audio devices and optionally TTS voices."""
    result: dict = {}
    # Microphones via sounddevice
    try:
        import sounddevice as sd  # type: ignore

        devices = sd.query_devices()
        mics = []
        for idx, dev in enumerate(devices):
            if (dev.get("max_input_channels") or 0) > 0:
                mics.append(
                    {
                        "index": idx,
                        "name": dev.get("name"),
                        "samplerate": dev.get("default_samplerate"),
                        "hostapi": dev.get("hostapi"),
                    }
                )
        result["microphones"] = mics
    except Exception:
        result["microphones"] = []
        result["note_microphones"] = "sounddevice not installed or unavailable"

    if list_voices:
        try:
            import pyttsx3  # type: ignore

            eng = pyttsx3.init()
            voices = []
            for v in eng.getProperty("voices"):
                voices.append(
                    {
                        "id": getattr(v, "id", None),
                        "name": getattr(v, "name", None),
                        "languages": [str(x) for x in (getattr(v, "languages", []) or [])],
                    }
                )
            result["voices"] = voices
        except Exception:
            result["voices"] = []
            result["note_voices"] = "pyttsx3 not installed or unavailable"

    if json_out:
        typer.echo(json.dumps(result, ensure_ascii=False))
        return
    # Text output
    typer.echo("Microphones:")
    if result.get("microphones"):
        for m in result["microphones"]:
            typer.echo(
                f" - #{m['index']}: {m['name']} (sr={m['samplerate']}, hostapi={m['hostapi']})"
            )
    else:
        typer.echo(
            " - (none)" + (" - sounddevice not installed" if result.get("note_microphones") else "")
        )
    if list_voices:
        typer.echo("TTS Voices:")
        if result.get("voices"):
            for v in result["voices"]:
                typer.echo(f" - {v['name']} ({','.join(v['languages'])})")
        else:
            typer.echo(
                " - (none)" + (" - pyttsx3 not installed" if result.get("note_voices") else "")
            )

