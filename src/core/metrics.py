"""Utilities for exporting simple metrics (Prometheus exposition format)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

try:
    from pydantic import BaseModel
except Exception:  # pragma: no cover
    BaseModel = None  # type: ignore[assignment]


class PrometheusExporter:
    """Write execution metrics in the Prometheus text exposition format."""

    @staticmethod
    def write_metrics(path: Path, agent: str, duration: float, result: Any) -> None:
        """
        Persist metrics for a single agent execution.

        Parameters
        ----------
        path:
            Output file path; parent directories will be created if missing.
        agent:
            Agent class name.
        duration:
            Total execution duration in seconds.
        result:
            Raw result object returned by the agent (dict/Pydantic supported).
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        # Normalise result to a JSON-like dictionary when possible.
        payload: Dict[str, Any] = {}
        if isinstance(result, dict):
            payload = result
        elif BaseModel is not None and isinstance(result, BaseModel):  # type: ignore[arg-type]
            payload = result.model_dump()
        elif hasattr(result, "dict"):  # fallback for other libraries
            try:
                payload = result.dict()  # type: ignore[assignment]
            except Exception:  # pragma: no cover
                payload = {}

        lines: list[str] = []
        lines.append("# HELP ftsystem_run_duration_seconds Agent execution duration.")
        lines.append("# TYPE ftsystem_run_duration_seconds gauge")
        lines.append(f'ftsystem_run_duration_seconds{{agent="{agent}"}} {duration:.6f}')

        rounds = payload.get("rounds")
        if isinstance(rounds, (int, float)):
            lines.append("# HELP ftsystem_rounds_total Number of orchestration rounds.")
            lines.append("# TYPE ftsystem_rounds_total gauge")
            lines.append(f'ftsystem_rounds_total{{agent="{agent}"}} {rounds}')

        metrics = payload.get("metrics") if isinstance(payload, dict) else None
        if isinstance(metrics, dict):
            latency = metrics.get("latency")
            if isinstance(latency, dict):
                lines.append("# HELP ftsystem_subagent_latency_seconds Sub-agent latency in seconds.")
                lines.append("# TYPE ftsystem_subagent_latency_seconds gauge")
                for subagent, value in latency.items():
                    if isinstance(value, (int, float)):
                        lines.append(
                            f'ftsystem_subagent_latency_seconds{{agent="{agent}",subagent="{subagent}"}} {value}'
                        )
            success = metrics.get("success")
            if isinstance(success, dict):
                lines.append("# HELP ftsystem_subagent_success_total Sub-agent success flag (1 successful, 0 otherwise).")
                lines.append("# TYPE ftsystem_subagent_success_total gauge")
                for subagent, value in success.items():
                    if isinstance(value, (int, float)):
                        lines.append(
                            f'ftsystem_subagent_success_total{{agent="{agent}",subagent="{subagent}"}} {value}'
                        )

        lines.append("")  # ensure trailing newline
        path.write_text("\n".join(lines), encoding="utf-8")

