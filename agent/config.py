from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Actor:
    id: str
    token_env: str
    tenant_id: str

    @property
    def token(self) -> str:
        value = os.environ.get(self.token_env)
        if not value:
            raise RuntimeError(f"missing env var {self.token_env} for actor {self.id}")
        return value


@dataclass(frozen=True)
class LLMConfig:
    provider: str
    model: str
    base_url: str
    temperature: float
    max_tokens: int


@dataclass(frozen=True)
class GroqConfig:
    enabled: bool
    model: str
    api_key_env: str

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)


@dataclass(frozen=True)
class AnthropicConfig:
    enabled: bool
    model: str
    api_key_env: str

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)


@dataclass(frozen=True)
class EmbeddingsConfig:
    provider: str
    model: str
    dimensions: int


@dataclass(frozen=True)
class MemoryConfig:
    db_path: Path
    episodic_ttl_days: int


@dataclass(frozen=True)
class TargetConfig:
    name: str
    base_url: str
    auth_type: str
    actors: tuple[Actor, ...]


@dataclass(frozen=True)
class SafetyConfig:
    rate_limit_rps: int
    max_requests_per_task: int
    max_loop_iterations: int
    passive_only: bool
    allow_hosts: tuple[str, ...]


@dataclass(frozen=True)
class LoggingConfig:
    level: str
    json: bool
    path: Path


@dataclass(frozen=True)
class Config:
    llm: LLMConfig
    groq: GroqConfig
    anthropic: AnthropicConfig
    embeddings: EmbeddingsConfig
    memory: MemoryConfig
    target: TargetConfig
    safety: SafetyConfig
    logging: LoggingConfig
    raw: dict[str, Any] = field(default_factory=dict)


def load_config(path: str | Path = "config.yaml") -> Config:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    llm = LLMConfig(**raw["llm"])
    groq = GroqConfig(**raw["groq"])
    anthropic = AnthropicConfig(**raw["anthropic"])
    embeddings = EmbeddingsConfig(**raw["embeddings"])
    mem = raw["memory"]
    memory = MemoryConfig(db_path=Path(mem["db_path"]), episodic_ttl_days=int(mem["episodic_ttl_days"]))
    tgt = raw["target"]
    actors = tuple(Actor(**a) for a in tgt["actors"])
    target = TargetConfig(
        name=tgt["name"],
        base_url=tgt["base_url"].rstrip("/"),
        auth_type=tgt["auth_type"],
        actors=actors,
    )
    safety_raw = raw["safety"]
    safety = SafetyConfig(
        rate_limit_rps=int(safety_raw["rate_limit_rps"]),
        max_requests_per_task=int(safety_raw["max_requests_per_task"]),
        max_loop_iterations=int(safety_raw["max_loop_iterations"]),
        passive_only=bool(safety_raw["passive_only"]),
        allow_hosts=tuple(safety_raw["allow_hosts"]),
    )
    log_raw = raw["logging"]
    logging_cfg = LoggingConfig(
        level=log_raw["level"],
        json=bool(log_raw["json"]),
        path=Path(log_raw["path"]),
    )
    return Config(
        llm=llm,
        groq=groq,
        anthropic=anthropic,
        embeddings=embeddings,
        memory=memory,
        target=target,
        safety=safety,
        logging=logging_cfg,
        raw=raw,
    )
