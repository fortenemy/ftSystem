import asyncio
import logging
from typing import Any, Dict

from .base import Agent, AgentConfig
from agents import AGENT_REGISTRY
from core.forum import Forum
from core.security import SecurityPolicy, Redactor


class MasterAgent(Agent):
    """
    Minimal async orchestrator that runs available sub-agents in a round-based flow
    and aggregates their outputs. This is a skeleton for future expansion.
    """

    def __init__(self, config: AgentConfig):
        """Store configuration for orchestration rounds and sub-agent selection."""
        super().__init__(config)

    def run(self, **kwargs: Any) -> Any:
        """Execute orchestration cycles and return aggregated results."""
        forum = Forum()
        policy = SecurityPolicy.from_env()
        user_input = kwargs.get("input")
        logging.debug(
            "[master] run start (params=%s, has_input=%s)",
            self.config.params,
            bool(user_input),
        )
        forum.post("system", "MasterAgent starting orchestration", agent="MasterAgent")
        if user_input:
            forum.post("user", Redactor.redact(str(user_input)) or "")
        rounds = 1
        timeout_s = None
        if self.config.params:
            try:
                if isinstance(self.config.params.get("rounds"), int):
                    rounds = int(self.config.params.get("rounds")) or 1
                if self.config.params.get("timeout_seconds") is not None:
                    timeout_s = float(self.config.params.get("timeout_seconds"))
            except Exception:
                pass

        async def _run_round_once() -> Dict[str, Any]:
            results: Dict[str, Any] = {}
            latencies: Dict[str, float] = {}

            async def _run_one(name: str, cls: type[Agent]) -> None:
                try:
                    start = asyncio.get_event_loop().time()
                    logging.debug("[master] starting subagent %s", name)
                    res = await asyncio.to_thread(
                        lambda: cls(AgentConfig(name=name, description=f"Auto for {name}")).run()
                    )
                    results[name] = res
                    forum.post("agent", Redactor.redact(str(res)) or "", agent=name)
                    latencies[name] = asyncio.get_event_loop().time() - start
                    logging.debug("[master] finished subagent %s (latency=%.3fs)", name, latencies[name])
                except Exception as e:  # pragma: no cover
                    err_msg = f"{type(e).__name__} while running {name}: {e}"
                    logging.error(err_msg)
                    results[name] = {"error": err_msg}

            wanted = []
            if self.config.params and isinstance(self.config.params.get("subagents"), list):
                wanted = [str(n) for n in self.config.params.get("subagents")]

            if wanted:
                selected: list[tuple[str, type[Agent]]] = []
                for name in wanted:
                    if name == "MasterAgent":
                        continue
                    cls = AGENT_REGISTRY.get(name)
                    if cls is not None:
                        selected.append((name, cls))
                # If none valid, fall back to default selection
                if not selected:
                    sub = {n: c for n, c in AGENT_REGISTRY.items() if n != "MasterAgent"}
                    selected = list(sub.items())[:2]
                    logging.debug(
                        "[master] requested subagents unavailable, fallback selection=%s",
                        [n for n, _ in selected],
                    )
            else:
                # Default selection (deterministic subset)
                sub = {n: c for n, c in AGENT_REGISTRY.items() if n != "MasterAgent"}
                selected = list(sub.items())[:2]
                logging.debug("[master] default subagent selection=%s", [n for n, _ in selected])
            # Apply allowlist filter
            allowed_names = policy.filter_subagents([n for n, _ in selected])
            selected = [(n, c) for (n, c) in selected if n in allowed_names]
            if not selected:
                logging.debug(
                    "[master] no subagents allowed after policy filter (requested=%s, allowed=%s)",
                    [n for n, _ in selected],
                    allowed_names,
                )
                return {"results": {}, "metrics": {"latency": {}, "success": {}}}
            logging.debug("[master] executing subagents=%s", [n for n, _ in selected])
            tasks = [asyncio.create_task(_run_one(n, c)) for n, c in selected]
            if timeout_s and timeout_s > 0:
                try:
                    await asyncio.wait_for(asyncio.gather(*tasks), timeout=timeout_s)
                except asyncio.TimeoutError:  # pragma: no cover
                    for t in tasks:
                        if not t.done():
                            t.cancel()
                    # mark unfinished as timeout
                    for name, _ in selected:
                        if name not in results:
                            results[name] = {"error": "timeout"}
            else:
                await asyncio.gather(*tasks)
            # Attach metrics
            success: Dict[str, float] = {}
            for n in results:
                success[n] = 0.0 if isinstance(results[n], dict) and results[n].get("error") else 1.0
            logging.debug(
                "[master] round complete (results=%s, latencies=%s)",
                list(results.keys()),
                latencies,
            )
            return {"results": results, "metrics": {"latency": latencies, "success": success}}

        rounds = policy.cap_rounds(rounds)
        logging.debug(
            "[master] executing rounds=%s (timeout=%s, policy_max=%s)",
            rounds,
            timeout_s,
            policy.max_rounds,
        )
        last_results: Dict[str, Any] = {}
        for idx in range(rounds):
            logging.debug("[master] starting round %s/%s", idx + 1, rounds)
            last_results = asyncio.run(_run_round_once())
        forum.post("agent", "Synthesis complete", agent="MasterAgent")
        final_payload = {"rounds": rounds, **last_results, "transcript": forum.to_dict()}
        logging.debug(
            "[master] run finished (rounds=%s, result_keys=%s)",
            rounds,
            list(last_results.get("results", {}).keys()),
        )
        return final_payload
