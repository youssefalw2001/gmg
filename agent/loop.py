from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any

from rich.console import Console
from rich.panel import Panel

from .config import Config
from .llm import ChatMessage, GroqClient, OllamaClient
from .memory import MemoryStore
from .prompts import build_system_prompt, reflection_prompt
from .tools import ToolError, ToolRegistry

log = logging.getLogger("agent.loop")
console = Console()


@dataclass
class LoopResult:
    completed: bool
    iterations: int
    findings: list[dict[str, Any]]
    reason: str


class AgentLoop:
    """Observe -> plan -> act -> reflect. Terminates on finish() or budget exhaustion."""

    REFLECT_EVERY = 5

    def __init__(
        self,
        cfg: Config,
        llm: OllamaClient | GroqClient,
        memory: MemoryStore,
        registry: ToolRegistry,
    ) -> None:
        self._cfg = cfg
        self._llm = llm
        self._memory = memory
        self._registry = registry
        self._messages: list[ChatMessage] = []

    def run(self, task: str) -> LoopResult:
        self._messages = [
            ChatMessage(role="system", content=build_system_prompt(self._cfg)),
            ChatMessage(role="user", content=task),
        ]
        tools = self._registry.specs()
        finished = False
        reason = ""

        for iteration in range(1, self._cfg.safety.max_loop_iterations + 1):
            if iteration % self.REFLECT_EVERY == 0:
                self._messages.append(
                    ChatMessage(role="user", content=reflection_prompt(iteration))
                )

            log.info("iteration_start", extra={"iteration": iteration})
            try:
                response = self._llm.chat(self._messages, tools=tools)
            except Exception as exc:
                log.exception("llm_call_failed")
                reason = f"llm_error: {type(exc).__name__}: {exc}"
                break

            self._messages.append(
                ChatMessage(
                    role="assistant",
                    content=response.content or "",
                    tool_calls=response.tool_calls or None,
                )
            )

            if response.content:
                console.print(Panel(response.content, title=f"iter {iteration} · reasoning", border_style="cyan"))

            if not response.tool_calls:
                if response.content and "finish" in response.content.lower():
                    finished = True
                    reason = "assistant_signaled_finish_without_tool"
                    break
                self._messages.append(
                    ChatMessage(
                        role="user",
                        content="You must call a tool or call finish. Try again.",
                    )
                )
                continue

            for call in response.tool_calls:
                fn_name = call["function"]["name"]
                args = call["function"]["arguments"] or {}
                console.print(
                    Panel(
                        json.dumps(args, indent=2, default=str),
                        title=f"iter {iteration} · call {fn_name}",
                        border_style="yellow",
                    )
                )
                try:
                    result = self._registry.call(fn_name, args)
                    log.info("tool_ok", extra={"tool": fn_name, "iteration": iteration})
                except ToolError as exc:
                    result = {"error": str(exc)}
                    log.warning("tool_error", extra={"tool": fn_name, "iteration": iteration, "err": str(exc)})

                self._messages.append(
                    ChatMessage(
                        role="tool",
                        content=json.dumps(result, default=str)[:8000],
                        tool_call_id=call["id"],
                        name=fn_name,
                    )
                )
                console.print(
                    Panel(
                        json.dumps(result, indent=2, default=str)[:2000],
                        title=f"iter {iteration} · result {fn_name}",
                        border_style="green" if "error" not in result else "red",
                    )
                )
                if fn_name == "finish":
                    finished = True
                    reason = "finish_tool_called"
                    break

            if finished:
                break

        if not finished and not reason:
            reason = "max_iterations_reached"

        findings = self._memory.list_findings()
        return LoopResult(
            completed=finished,
            iterations=iteration,
            findings=findings,
            reason=reason,
        )
