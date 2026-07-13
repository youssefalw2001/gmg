from __future__ import annotations

import logging
import os
import socket
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import httpx

from .config import Config

log = logging.getLogger("agent.preflight")


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str = ""
    critical: bool = True


@dataclass
class PreflightReport:
    checks: list[CheckResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(c.ok for c in self.checks if c.critical)

    def add(self, check: CheckResult) -> None:
        self.checks.append(check)

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "checks": [
                {"name": c.name, "ok": c.ok, "detail": c.detail, "critical": c.critical}
                for c in self.checks
            ],
        }


def _check_env_vars(cfg: Config) -> list[CheckResult]:
    results = []
    for actor in cfg.target.actors:
        value = os.environ.get(actor.token_env)
        if not value:
            results.append(CheckResult(
                name=f"env:{actor.token_env}",
                ok=False,
                detail=f"actor {actor.id} needs env var {actor.token_env}",
            ))
        elif len(value) < 16:
            results.append(CheckResult(
                name=f"env:{actor.token_env}",
                ok=False,
                detail=f"token for {actor.id} is suspiciously short ({len(value)} chars)",
                critical=False,
            ))
        else:
            results.append(CheckResult(
                name=f"env:{actor.token_env}",
                ok=True,
                detail=f"present ({len(value)} chars)",
            ))
    if cfg.groq.enabled and not cfg.groq.api_key:
        results.append(CheckResult(
            name=f"env:{cfg.groq.api_key_env}",
            ok=False,
            detail="groq enabled but api key env var not set",
        ))
    if cfg.anthropic.enabled and not cfg.anthropic.api_key:
        results.append(CheckResult(
            name=f"env:{cfg.anthropic.api_key_env}",
            ok=False,
            detail="anthropic enabled but api key env var not set",
        ))
    if cfg.anthropic.enabled and cfg.groq.enabled:
        results.append(CheckResult(
            name="provider:conflict",
            ok=False,
            detail="both anthropic and groq are enabled; anthropic wins but disable one for clarity",
            critical=False,
        ))
    return results


def _check_ollama(cfg: Config) -> list[CheckResult]:
    if cfg.groq.enabled or cfg.anthropic.enabled:
        try:
            httpx.get(f"{cfg.llm.base_url}/api/tags", timeout=3.0)
            return [CheckResult(
                name="ollama:embeddings",
                ok=True,
                detail=f"reachable for {cfg.embeddings.model}",
                critical=False,
            )]
        except httpx.HTTPError:
            return [CheckResult(
                name="ollama:embeddings",
                ok=False,
                detail=(
                    f"ollama unreachable but needed for embeddings ({cfg.embeddings.model}). "
                    "recall tool will fail. either start ollama or disable recall in prompts."
                ),
                critical=False,
            )]
    results = []
    try:
        response = httpx.get(f"{cfg.llm.base_url}/api/tags", timeout=5.0)
        response.raise_for_status()
        installed = {m.get("name", "") for m in response.json().get("models", [])}
        results.append(CheckResult(
            name="ollama:reachable",
            ok=True,
            detail=f"{cfg.llm.base_url} responded, {len(installed)} models",
        ))
        needed = {cfg.llm.model, cfg.embeddings.model}
        for model in needed:
            found = any(model == name or name.startswith(model + ":") or model.startswith(name.split(":")[0]) for name in installed)
            results.append(CheckResult(
                name=f"ollama:model:{model}",
                ok=found,
                detail="installed" if found else f"run: ollama pull {model}",
            ))
    except httpx.HTTPError as exc:
        results.append(CheckResult(
            name="ollama:reachable",
            ok=False,
            detail=f"cannot reach {cfg.llm.base_url}: {type(exc).__name__}: {exc}",
        ))
    return results


def _check_anthropic(cfg: Config) -> list[CheckResult]:
    if not cfg.anthropic.enabled:
        return []
    if not cfg.anthropic.api_key:
        return [CheckResult(name="anthropic:auth", ok=False, detail="no api key")]
    try:
        response = httpx.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": cfg.anthropic.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": cfg.anthropic.model,
                "max_tokens": 8,
                "messages": [{"role": "user", "content": "ping"}],
            },
            timeout=15.0,
        )
        if response.status_code == 200:
            return [CheckResult(
                name=f"anthropic:model:{cfg.anthropic.model}",
                ok=True,
                detail=f"round-trip ok, {response.json().get('usage', {}).get('output_tokens', 0)} tokens",
            )]
        if response.status_code == 401:
            return [CheckResult(name="anthropic:auth", ok=False, detail="401 invalid key")]
        if response.status_code == 404:
            return [CheckResult(
                name=f"anthropic:model:{cfg.anthropic.model}",
                ok=False,
                detail=f"model id not found; check https://docs.claude.com/en/docs/about-claude/models/overview",
            )]
        return [CheckResult(
            name="anthropic:auth",
            ok=False,
            detail=f"status {response.status_code}: {response.text[:200]}",
        )]
    except httpx.HTTPError as exc:
        return [CheckResult(name="anthropic:auth", ok=False, detail=f"{type(exc).__name__}: {exc}")]


def _check_groq(cfg: Config) -> list[CheckResult]:
    if not cfg.groq.enabled:
        return []
    if not cfg.groq.api_key:
        return [CheckResult(name="groq:auth", ok=False, detail="no api key")]
    try:
        response = httpx.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {cfg.groq.api_key}"},
            timeout=10.0,
        )
        if response.status_code == 200:
            model_ids = {m["id"] for m in response.json().get("data", [])}
            found = cfg.groq.model in model_ids
            return [
                CheckResult(name="groq:auth", ok=True, detail=f"{len(model_ids)} models available"),
                CheckResult(
                    name=f"groq:model:{cfg.groq.model}",
                    ok=found,
                    detail="available" if found else f"not in list; check https://console.groq.com/docs/models",
                ),
            ]
        return [CheckResult(name="groq:auth", ok=False, detail=f"status {response.status_code}")]
    except httpx.HTTPError as exc:
        return [CheckResult(name="groq:auth", ok=False, detail=f"{type(exc).__name__}: {exc}")]


def _check_target_reachable(cfg: Config) -> list[CheckResult]:
    parsed = urlparse(cfg.target.base_url)
    host = parsed.hostname or ""
    if not host:
        return [CheckResult(name="target:base_url", ok=False, detail="cannot parse hostname")]
    try:
        socket.gethostbyname(host)
        dns_ok = CheckResult(name=f"target:dns:{host}", ok=True, detail="resolves")
    except socket.gaierror as exc:
        return [CheckResult(name=f"target:dns:{host}", ok=False, detail=f"cannot resolve: {exc}")]
    if host not in cfg.safety.allow_hosts and not any(host.endswith("." + h) for h in cfg.safety.allow_hosts):
        return [
            dns_ok,
            CheckResult(
                name="target:allowlist",
                ok=False,
                detail=f"{host} not in safety.allow_hosts {cfg.safety.allow_hosts}",
            ),
        ]
    try:
        response = httpx.head(cfg.target.base_url, timeout=10.0, follow_redirects=False)
        return [
            dns_ok,
            CheckResult(
                name="target:reachable",
                ok=True,
                detail=f"HEAD returned {response.status_code}",
            ),
        ]
    except httpx.HTTPError as exc:
        return [
            dns_ok,
            CheckResult(
                name="target:reachable",
                ok=False,
                detail=f"{type(exc).__name__}: {exc}",
                critical=False,
            ),
        ]


def _check_auth_probe(cfg: Config, probe_path: str | None) -> list[CheckResult]:
    if not probe_path:
        return [CheckResult(
            name="auth:probe",
            ok=True,
            detail="skipped (no --auth-probe path given)",
            critical=False,
        )]
    results = []
    for actor in cfg.target.actors:
        try:
            token = actor.token
        except RuntimeError as exc:
            results.append(CheckResult(name=f"auth:{actor.id}", ok=False, detail=str(exc)))
            continue
        url = f"{cfg.target.base_url}{probe_path if probe_path.startswith('/') else '/' + probe_path}"
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = httpx.get(url, headers=headers, timeout=10.0, follow_redirects=False)
            authed = response.status_code < 400
            results.append(CheckResult(
                name=f"auth:{actor.id}",
                ok=authed,
                detail=f"{probe_path} -> {response.status_code}",
                critical=False,
            ))
        except httpx.HTTPError as exc:
            results.append(CheckResult(
                name=f"auth:{actor.id}",
                ok=False,
                detail=f"{type(exc).__name__}: {exc}",
                critical=False,
            ))
    return results


def _check_config_sanity(cfg: Config) -> list[CheckResult]:
    results = []
    placeholder_markers = ("example.internal", "example.com", "your-domain", "localhost")
    if any(m in cfg.target.base_url for m in placeholder_markers):
        results.append(CheckResult(
            name="config:base_url",
            ok=False,
            detail=f"base_url looks like a placeholder: {cfg.target.base_url}",
            critical=False,
        ))
    if len(cfg.target.actors) < 2:
        results.append(CheckResult(
            name="config:actors",
            ok=False,
            detail="IDOR testing requires at least 2 actors",
        ))
    tenants = {a.tenant_id for a in cfg.target.actors}
    if len(tenants) < 2 and len(cfg.target.actors) >= 2:
        results.append(CheckResult(
            name="config:tenants",
            ok=False,
            detail="all actors share the same tenant_id — cross-tenant tests will not work",
            critical=False,
        ))
    if cfg.safety.max_requests_per_task > 5000:
        results.append(CheckResult(
            name="config:budget",
            ok=False,
            detail=f"max_requests_per_task={cfg.safety.max_requests_per_task} is very high",
            critical=False,
        ))
    return results


def run_preflight(cfg: Config, auth_probe_path: str | None = None) -> PreflightReport:
    report = PreflightReport()
    for check in _check_config_sanity(cfg):
        report.add(check)
    for check in _check_env_vars(cfg):
        report.add(check)
    for check in _check_ollama(cfg):
        report.add(check)
    for check in _check_anthropic(cfg):
        report.add(check)
    for check in _check_groq(cfg):
        report.add(check)
    for check in _check_target_reachable(cfg):
        report.add(check)
    for check in _check_auth_probe(cfg, auth_probe_path):
        report.add(check)
    return report
