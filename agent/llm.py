from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Iterable

import httpx
import ollama

from .config import Config

log = logging.getLogger("agent.llm")


@dataclass(frozen=True)
class ChatMessage:
    role: str
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None

    def to_openai(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            payload["tool_calls"] = self.tool_calls
        if self.tool_call_id:
            payload["tool_call_id"] = self.tool_call_id
        if self.name:
            payload["name"] = self.name
        return payload


@dataclass(frozen=True)
class ChatResponse:
    content: str
    tool_calls: list[dict[str, Any]]
    raw: dict[str, Any]


class OllamaClient:
    def __init__(self, cfg: Config) -> None:
        self._client = ollama.Client(host=cfg.llm.base_url)
        self._model = cfg.llm.model
        self._temperature = cfg.llm.temperature
        self._max_tokens = cfg.llm.max_tokens
        self._embed_model = cfg.embeddings.model
        self._embed_dim = cfg.embeddings.dimensions

    def chat(self, messages: Iterable[ChatMessage], tools: list[dict[str, Any]] | None = None) -> ChatResponse:
        payload_messages = [m.to_openai() for m in messages]
        result = self._client.chat(
            model=self._model,
            messages=payload_messages,
            tools=tools,
            options={"temperature": self._temperature, "num_predict": self._max_tokens},
        )
        message = result.get("message", {})
        content = message.get("content", "") or ""
        raw_tool_calls = message.get("tool_calls") or []
        normalized_calls = []
        for idx, call in enumerate(raw_tool_calls):
            fn = call.get("function") or {}
            args = fn.get("arguments") or {}
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"_raw": args}
            normalized_calls.append(
                {
                    "id": call.get("id") or f"call_{idx}",
                    "type": "function",
                    "function": {"name": fn.get("name"), "arguments": args},
                }
            )
        return ChatResponse(content=content, tool_calls=normalized_calls, raw=result)

    def embed(self, text: str) -> list[float]:
        result = self._client.embeddings(model=self._embed_model, prompt=text)
        vec = result.get("embedding") or []
        if len(vec) != self._embed_dim:
            log.warning("embedding_dim_mismatch", extra={"got": len(vec), "want": self._embed_dim})
        return list(vec)


class AnthropicClient:
    """Client for Anthropic's native Messages API. Supports Opus 4.8 and Sonnet 4.6."""

    API_VERSION = "2023-06-01"

    def __init__(self, cfg: Config) -> None:
        api_key = cfg.anthropic.api_key
        if not api_key:
            raise RuntimeError(f"missing env var {cfg.anthropic.api_key_env}")
        self._model = cfg.anthropic.model
        self._temperature = cfg.llm.temperature
        self._max_tokens = cfg.llm.max_tokens
        
        # Support custom base_url (e.g., for Nara router)
        base_url = getattr(cfg.anthropic, 'base_url', None) or "https://api.anthropic.com/v1"
        
        self._client = httpx.Client(
            base_url=base_url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": self.API_VERSION,
                "content-type": "application/json",
            },
            timeout=httpx.Timeout(connect=5.0, read=120.0, write=10.0, pool=5.0),
        )

    @staticmethod
    def _translate_messages(messages: Iterable[ChatMessage]) -> tuple[str, list[dict[str, Any]]]:
        system_prompt = ""
        translated: list[dict[str, Any]] = []
        for msg in messages:
            if msg.role == "system":
                system_prompt = msg.content
                continue
            if msg.role == "tool":
                translated.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": msg.tool_call_id or "",
                        "content": msg.content,
                    }],
                })
                continue
            if msg.role == "assistant" and msg.tool_calls:
                blocks: list[dict[str, Any]] = []
                if msg.content:
                    blocks.append({"type": "text", "text": msg.content})
                for call in msg.tool_calls:
                    blocks.append({
                        "type": "tool_use",
                        "id": call["id"],
                        "name": call["function"]["name"],
                        "input": call["function"]["arguments"] or {},
                    })
                translated.append({"role": "assistant", "content": blocks})
                continue
            translated.append({"role": msg.role, "content": msg.content})
        return system_prompt, translated

    @staticmethod
    def _translate_tools(tools: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        if not tools:
            return None
        translated = []
        for spec in tools:
            fn = spec["function"]
            translated.append({
                "name": fn["name"],
                "description": fn["description"],
                "input_schema": fn["parameters"],
            })
        return translated

    def chat(self, messages: Iterable[ChatMessage], tools: list[dict[str, Any]] | None = None) -> ChatResponse:
        system_prompt, translated_msgs = self._translate_messages(messages)
        body: dict[str, Any] = {
            "model": self._model,
            "max_tokens": self._max_tokens,
            "temperature": self._temperature,
            "messages": translated_msgs,
        }
        if system_prompt:
            body["system"] = system_prompt
        translated_tools = self._translate_tools(tools)
        if translated_tools:
            body["tools"] = translated_tools

        response = self._client.post("/messages", json=body)
        if response.status_code >= 400:
            raise RuntimeError(f"anthropic api error {response.status_code}: {response.text[:512]}")
        data = response.json()

        content_text = ""
        tool_calls: list[dict[str, Any]] = []
        for block in data.get("content", []):
            block_type = block.get("type")
            if block_type == "text":
                content_text += block.get("text", "")
            elif block_type == "tool_use":
                tool_calls.append({
                    "id": block.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": block.get("name", ""),
                        "arguments": block.get("input") or {},
                    },
                })
        return ChatResponse(content=content_text, tool_calls=tool_calls, raw=data)

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Anthropic does not expose embeddings; keep Ollama for nomic-embed-text")

    def close(self) -> None:
        self._client.close()


class GroqClient:
    """Fallback client for Groq's free tier. OpenAI-compatible API."""

    BASE_URL = "https://router.bynara.id/v1"

    def __init__(self, cfg: Config) -> None:
        api_key = cfg.groq.api_key
        if not api_key:
            raise RuntimeError(f"missing env var {cfg.groq.api_key_env}")
        self._model = cfg.groq.model
        self._temperature = cfg.llm.temperature
        self._max_tokens = cfg.llm.max_tokens
        self._client = httpx.Client(
            base_url=self.BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=httpx.Timeout(connect=5.0, read=60.0, write=10.0, pool=5.0),
        )

    def chat(self, messages: Iterable[ChatMessage], tools: list[dict[str, Any]] | None = None) -> ChatResponse:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [m.to_openai() for m in messages],
            "temperature": self._temperature,
            "max_tokens": self._max_tokens,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
        response = self._client.post("/chat/completions", json=body)
        response.raise_for_status()
        data = response.json()
        choice = data["choices"][0]["message"]
        content = choice.get("content") or ""
        raw_calls = choice.get("tool_calls") or []
        normalized = []
        for call in raw_calls:
            fn = call["function"]
            args = fn.get("arguments") or "{}"
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {"_raw": args}
            normalized.append(
                {
                    "id": call["id"],
                    "type": "function",
                    "function": {"name": fn["name"], "arguments": args},
                }
            )
        return ChatResponse(content=content, tool_calls=normalized, raw=data)

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError("Groq does not expose embeddings; use Ollama nomic-embed-text")

    def close(self) -> None:
        self._client.close()


def build_llm(cfg: Config) -> OllamaClient | GroqClient | AnthropicClient:
    if cfg.anthropic.enabled:
        log.info("llm_selected", extra={"provider": "anthropic", "model": cfg.anthropic.model})
        return AnthropicClient(cfg)
    if cfg.groq.enabled:
        log.info("llm_selected", extra={"provider": "groq", "model": cfg.groq.model})
        return GroqClient(cfg)
    log.info("llm_selected", extra={"provider": "ollama", "model": cfg.llm.model})
    return OllamaClient(cfg)
