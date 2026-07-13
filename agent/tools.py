from __future__ import annotations

import difflib
import hashlib
import json
import logging
import re
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urlparse

import httpx

from .config import Config, Actor
from .memory import MemoryStore
from .rate_limit import TokenBucket

log = logging.getLogger("agent.tools")


class ToolError(RuntimeError):
    pass


@dataclass(frozen=True)
class Tool:
    name: str
    description: str
    schema: dict[str, Any]
    handler: Callable[[dict[str, Any]], dict[str, Any]]

    def to_openai(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.schema,
            },
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        if tool.name in self._tools:
            raise ValueError(f"duplicate tool {tool.name}")
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        if name not in self._tools:
            raise ToolError(f"unknown tool {name}")
        return self._tools[name]

    def specs(self) -> list[dict[str, Any]]:
        return [t.to_openai() for t in self._tools.values()]

    def call(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        tool = self.get(name)
        try:
            return tool.handler(arguments)
        except ToolError:
            raise
        except Exception as exc:
            log.exception("tool_error", extra={"tool": name})
            raise ToolError(f"{name} failed: {type(exc).__name__}: {exc}") from exc


def _validate_host(url: str, allow_hosts: tuple[str, ...]) -> None:
    parsed = urlparse(url)
    if parsed.scheme not in {"http", "https"}:
        raise ToolError(f"scheme not allowed: {parsed.scheme}")
    if not any(parsed.hostname == host or (parsed.hostname or "").endswith("." + host) for host in allow_hosts):
        raise ToolError(f"host not in allowlist: {parsed.hostname}")


def _actor_by_id(cfg: Config, actor_id: str) -> Actor:
    for actor in cfg.target.actors:
        if actor.id == actor_id:
            return actor
    raise ToolError(f"unknown actor {actor_id}")


def _apply_auth(headers: dict[str, str], actor: Actor, auth_type: str) -> dict[str, str]:
    result = dict(headers)
    if auth_type == "bearer":
        result["Authorization"] = f"Bearer {actor.token}"
    elif auth_type == "cookie":
        existing = result.get("Cookie", "")
        result["Cookie"] = f"{existing}; session={actor.token}".strip("; ")
    elif auth_type == "header":
        result["X-Auth-Token"] = actor.token
    else:
        raise ToolError(f"unsupported auth_type {auth_type}")
    return result


def _redact_headers(headers: dict[str, str]) -> dict[str, str]:
    redacted = {}
    for key, value in headers.items():
        lowered = key.lower()
        if lowered in {"authorization", "cookie", "x-auth-token", "x-api-key"}:
            redacted[key] = "***REDACTED***"
        else:
            redacted[key] = value
    return redacted


def _safe_body(response: httpx.Response) -> Any:
    content_type = response.headers.get("content-type", "")
    if "json" in content_type:
        try:
            return response.json()
        except json.JSONDecodeError:
            return response.text[:4096]
    return response.text[:4096]


def _structural_signature(payload: Any, depth: int = 0) -> Any:
    if depth > 8:
        return "<deep>"
    if isinstance(payload, dict):
        return {k: _structural_signature(v, depth + 1) for k, v in sorted(payload.items())}
    if isinstance(payload, list):
        if not payload:
            return []
        return [_structural_signature(payload[0], depth + 1), f"len={len(payload)}"]
    return type(payload).__name__


def _tenant_leak_score(body_a: Any, body_b: Any, tenant_a: str, tenant_b: str) -> dict[str, Any]:
    text_a = json.dumps(body_a, default=str)
    text_b = json.dumps(body_b, default=str)
    similarity = difflib.SequenceMatcher(None, text_a, text_b).ratio()
    contains_b_tenant_in_a = tenant_b in text_a
    contains_a_tenant_in_b = tenant_a in text_b
    return {
        "similarity": round(similarity, 4),
        "a_leaks_b_tenant": contains_b_tenant_in_a,
        "b_leaks_a_tenant": contains_a_tenant_in_b,
        "structurally_identical": _structural_signature(body_a) == _structural_signature(body_b),
    }


def build_registry(cfg: Config, memory: MemoryStore, embed_fn: Callable[[str], list[float]]) -> ToolRegistry:
    from . import probes as _probes

    # Wrap embed_fn to handle Ollama being unreachable gracefully
    def safe_embed_fn(text: str) -> list[float]:
        try:
            return embed_fn(text)
        except Exception:
            # Return zero vector if embeddings unavailable
            return [0.0] * cfg.embeddings.dimensions

    registry = ToolRegistry()
    limiter = TokenBucket(cfg.safety.rate_limit_rps)
    
    # Load cookies for Cloudflare bypass
    import os as _os
    _cookie_jar = {}
    _cookie_path = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "cookies.json")
    if _os.path.exists(_cookie_path):
        import json as _json
        with open(_cookie_path) as _f:
            _cookie_jar = _json.load(_f)
    
    client = httpx.Client(
        timeout=httpx.Timeout(connect=5.0, read=30.0, write=10.0, pool=5.0),
        follow_redirects=False,
        verify=True,
        cookies=_cookie_jar,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Origin": "https://gmgn.ai",
            "Referer": "https://gmgn.ai/",
        },
    )
    request_counter = {"count": 0}

    def _http_request(args: dict[str, Any]) -> dict[str, Any]:
        method = args["method"].upper()
        path = args["path"]
        actor_id = args["actor_id"]
        headers = args.get("headers") or {}
        body = args.get("body")
        params = args.get("params")

        if request_counter["count"] >= cfg.safety.max_requests_per_task:
            raise ToolError("request budget exhausted")

        if cfg.safety.passive_only and method not in {"GET", "HEAD", "OPTIONS"}:
            raise ToolError("passive_only mode forbids non-read methods")

        actor = _actor_by_id(cfg, actor_id)
        url = f"{cfg.target.base_url}{path if path.startswith('/') else '/' + path}"
        _validate_host(url, cfg.safety.allow_hosts)

        auth_headers = _apply_auth(headers, actor, cfg.target.auth_type)
        limiter.acquire()
        request_counter["count"] += 1

        started = time.monotonic()
        try:
            response = client.request(
                method,
                url,
                headers=auth_headers,
                params=params,
                json=body if isinstance(body, (dict, list)) else None,
                content=body if isinstance(body, (str, bytes)) else None,
            )
            elapsed_ms = (time.monotonic() - started) * 1000.0
            resp_body = _safe_body(response)
            request_id = memory.log_http(
                actor_id=actor_id,
                method=method,
                url=url,
                status=response.status_code,
                request_headers=_redact_headers(auth_headers),
                request_body=body,
                response_headers=dict(response.headers),
                response_body=resp_body,
                elapsed_ms=elapsed_ms,
            )
            summary_text = f"{method} {path} as {actor_id} -> {response.status_code}"
            memory.record_event(
                kind="http",
                key=f"{method} {path}",
                value={
                    "request_id": request_id,
                    "actor_id": actor_id,
                    "status": response.status_code,
                    "elapsed_ms": elapsed_ms,
                },
                embedding=safe_embed_fn(summary_text),
            )
            return {
                "request_id": request_id,
                "status": response.status_code,
                "headers": dict(response.headers),
                "body_preview": resp_body if isinstance(resp_body, str) else json.dumps(resp_body)[:2048],
                "elapsed_ms": elapsed_ms,
            }
        except httpx.HTTPError as exc:
            raise ToolError(f"http_error: {type(exc).__name__}: {exc}") from exc

    registry.register(Tool(
        name="http_request",
        description=(
            "Send an authenticated HTTP request to the target platform. "
            "Auth is applied automatically based on actor_id. "
            "Returns request_id for later diffing and status/headers/body_preview."
        ),
        schema={
            "type": "object",
            "properties": {
                "method": {"type": "string", "enum": ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]},
                "path": {"type": "string", "description": "Path starting with /"},
                "actor_id": {"type": "string", "description": "Actor id from config"},
                "headers": {"type": "object", "additionalProperties": {"type": "string"}},
                "params": {"type": "object"},
                "body": {},
            },
            "required": ["method", "path", "actor_id"],
        },
        handler=_http_request,
    ))

    def _get_response(args: dict[str, Any]) -> dict[str, Any]:
        record = memory.get_http(int(args["request_id"]))
        if not record:
            raise ToolError(f"no request with id {args['request_id']}")
        return record

    registry.register(Tool(
        name="get_response",
        description="Fetch the stored request/response by request_id.",
        schema={
            "type": "object",
            "properties": {"request_id": {"type": "integer"}},
            "required": ["request_id"],
        },
        handler=_get_response,
    ))

    def _diff_responses(args: dict[str, Any]) -> dict[str, Any]:
        a = memory.get_http(int(args["request_id_a"]))
        b = memory.get_http(int(args["request_id_b"]))
        if not a or not b:
            raise ToolError("one or both request_ids not found")
        tenant_a = ""
        tenant_b = ""
        for actor in cfg.target.actors:
            if actor.id == a["actor_id"]:
                tenant_a = actor.tenant_id
            if actor.id == b["actor_id"]:
                tenant_b = actor.tenant_id
        score = _tenant_leak_score(a["response_body"], b["response_body"], tenant_a, tenant_b)
        return {
            "status_a": a["status"], "status_b": b["status"],
            "url_a": a["url"], "url_b": b["url"],
            "actor_a": a["actor_id"], "actor_b": b["actor_id"],
            **score,
        }

    registry.register(Tool(
        name="diff_responses",
        description=(
            "Compare two stored responses structurally. "
            "Returns similarity, tenant leak indicators, and whether the shapes match."
        ),
        schema={
            "type": "object",
            "properties": {
                "request_id_a": {"type": "integer"},
                "request_id_b": {"type": "integer"},
            },
            "required": ["request_id_a", "request_id_b"],
        },
        handler=_diff_responses,
    ))

    def _probe_idor(args: dict[str, Any]) -> dict[str, Any]:
        path_template = args["path_template"]
        resource_id = str(args["resource_id"])
        owner_actor_id = args["owner_actor_id"]
        intruder_actor_id = args["intruder_actor_id"]
        method = args.get("method", "GET").upper()

        if "{id}" not in path_template:
            raise ToolError("path_template must contain {id}")

        concrete_path = path_template.replace("{id}", resource_id)

        owner_result = _http_request({
            "method": method, "path": concrete_path, "actor_id": owner_actor_id,
        })
        intruder_result = _http_request({
            "method": method, "path": concrete_path, "actor_id": intruder_actor_id,
        })

        verdict = "safe"
        reason = ""
        owner_status = owner_result["status"]
        intruder_status = intruder_result["status"]

        if owner_status == 200 and intruder_status == 200:
            diff = _diff_responses({
                "request_id_a": owner_result["request_id"],
                "request_id_b": intruder_result["request_id"],
            })
            if diff["structurally_identical"] and diff["similarity"] > 0.90:
                verdict = "confirmed_idor"
                reason = f"intruder received owner's resource (similarity {diff['similarity']})"
            elif diff["b_leaks_a_tenant"] or diff["a_leaks_b_tenant"]:
                verdict = "tenant_leak"
                reason = "cross-tenant identifier appeared in response"
            else:
                verdict = "different_data_same_endpoint"
                reason = "both got 200 with different data; check auth boundary"
        elif owner_status == 200 and intruder_status in {401, 403, 404}:
            verdict = "safe"
            reason = f"intruder correctly blocked ({intruder_status})"
        elif owner_status != 200:
            verdict = "inconclusive"
            reason = f"owner request itself failed ({owner_status})"

        result = {
            "path": concrete_path,
            "method": method,
            "owner_actor_id": owner_actor_id,
            "intruder_actor_id": intruder_actor_id,
            "owner_status": owner_status,
            "intruder_status": intruder_status,
            "verdict": verdict,
            "reason": reason,
            "owner_request_id": owner_result["request_id"],
            "intruder_request_id": intruder_result["request_id"],
        }
        memory.record_event(
            kind="probe",
            key=f"{method} {path_template}",
            value=result,
            embedding=safe_embed_fn(f"IDOR probe {method} {path_template} verdict={verdict}"),
        )
        return result

    registry.register(Tool(
        name="probe_idor",
        description=(
            "Run the two-actor IDOR test on a path template with {id}. "
            "Fetches the resource as owner and as intruder, then compares. "
            "Verdicts: confirmed_idor, tenant_leak, safe, different_data_same_endpoint, inconclusive."
        ),
        schema={
            "type": "object",
            "properties": {
                "path_template": {"type": "string", "description": "e.g. /api/v1/orders/{id}"},
                "resource_id": {"type": "string"},
                "owner_actor_id": {"type": "string"},
                "intruder_actor_id": {"type": "string"},
                "method": {"type": "string", "default": "GET"},
            },
            "required": ["path_template", "resource_id", "owner_actor_id", "intruder_actor_id"],
        },
        handler=_probe_idor,
    ))

    def _enumerate_endpoints(args: dict[str, Any]) -> dict[str, Any]:
        spec_path = args["spec_path"]
        try:
            with open(spec_path, "r", encoding="utf-8") as fh:
                if spec_path.endswith((".yaml", ".yml")):
                    import yaml
                    spec = yaml.safe_load(fh)
                else:
                    spec = json.load(fh)
        except FileNotFoundError as exc:
            raise ToolError(f"spec not found: {spec_path}") from exc

        paths = spec.get("paths", {})
        candidates = []
        id_pattern = re.compile(r"\{[^}]*(id|Id|uuid|slug)[^}]*\}")
        for path, methods in paths.items():
            if not id_pattern.search(path):
                continue
            for method_name in ("get", "put", "patch", "delete"):
                if method_name in methods:
                    candidates.append({"method": method_name.upper(), "path": path})
        memory.note("endpoints.idor_candidates", {"count": len(candidates), "items": candidates})
        return {"count": len(candidates), "candidates": candidates}

    registry.register(Tool(
        name="enumerate_endpoints",
        description=(
            "Parse an OpenAPI spec (YAML or JSON) and return endpoints with path parameters "
            "that look like object identifiers (id, uuid, slug)."
        ),
        schema={
            "type": "object",
            "properties": {"spec_path": {"type": "string"}},
            "required": ["spec_path"],
        },
        handler=_enumerate_endpoints,
    ))

    def _note(args: dict[str, Any]) -> dict[str, Any]:
        memory.note(args["key"], args["value"])
        return {"ok": True, "key": args["key"]}

    registry.register(Tool(
        name="note",
        description="Write a durable fact to semantic memory. Overwrites existing key.",
        schema={
            "type": "object",
            "properties": {
                "key": {"type": "string"},
                "value": {"type": "object"},
            },
            "required": ["key", "value"],
        },
        handler=_note,
    ))

    def _recall(args: dict[str, Any]) -> dict[str, Any]:
        query = args["query"]
        k = int(args.get("k", 5))
        vec = safe_embed_fn(query)
        records = memory.recall(vec, k=k)
        return {
            "matches": [
                {"id": r.id, "kind": r.kind, "key": r.key, "value": r.value, "score": r.score}
                for r in records
            ]
        }

    registry.register(Tool(
        name="recall",
        description="Semantic search across past events. Returns top-k most similar prior actions.",
        schema={
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "k": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
        handler=_recall,
    ))

    def _report_finding(args: dict[str, Any]) -> dict[str, Any]:
        endpoint = args["endpoint"]
        severity = args["severity"]
        title = args["title"]
        evidence = args["evidence"]
        owner_request_id = int(evidence.get("owner_request_id", 0))
        intruder_request_id = int(evidence.get("intruder_request_id", 0))
        owner = memory.get_http(owner_request_id) if owner_request_id else None
        intruder = memory.get_http(intruder_request_id) if intruder_request_id else None
        repro_lines = ["# Reproduction"]
        for label, record in (("owner", owner), ("intruder", intruder)):
            if record:
                repro_lines.append(
                    f"# {label} ({record['actor_id']})\n"
                    f"curl -X {record['method']} '{record['url']}' "
                    f"-H 'Authorization: Bearer $TOKEN_{record['actor_id'].upper()}'"
                )
        repro = "\n".join(repro_lines)
        finding_id = memory.record_finding(endpoint, severity, title, evidence, repro)
        return {"finding_id": finding_id, "endpoint": endpoint, "severity": severity}

    registry.register(Tool(
        name="report_finding",
        description=(
            "Record a confirmed finding with evidence and a generated reproduction script. "
            "Only call after probe_idor returns confirmed_idor or tenant_leak."
        ),
        schema={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string"},
                "severity": {"type": "string", "enum": ["critical", "high", "medium", "low", "info"]},
                "title": {"type": "string"},
                "evidence": {"type": "object"},
            },
            "required": ["endpoint", "severity", "title", "evidence"],
        },
        handler=_report_finding,
    ))

    def _plan(args: dict[str, Any]) -> dict[str, Any]:
        steps = args["steps"]
        memory.note("plan.current", {"steps": steps, "cursor": 0})
        return {"ok": True, "steps_count": len(steps)}

    registry.register(Tool(
        name="plan",
        description="Save a step-by-step plan. Use this before executing multi-step work.",
        schema={
            "type": "object",
            "properties": {
                "steps": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
            },
            "required": ["steps"],
        },
        handler=_plan,
    ))

    def _mark_step_done(args: dict[str, Any]) -> dict[str, Any]:
        plan = memory.get_note("plan.current") or {"steps": [], "cursor": 0}
        cursor = int(plan.get("cursor", 0))
        plan["cursor"] = cursor + 1
        memory.note("plan.current", plan)
        remaining = plan["steps"][plan["cursor"]:] if plan["cursor"] < len(plan["steps"]) else []
        return {"cursor": plan["cursor"], "remaining": remaining}

    registry.register(Tool(
        name="mark_step_done",
        description="Advance the plan cursor by one step. Returns remaining steps.",
        schema={"type": "object", "properties": {}, "required": []},
        handler=_mark_step_done,
    ))

    probe_ctx = _probes.ProbeContext(
        request_fn=_http_request,
        memory_get_http=memory.get_http,
        memory_record_event=memory.record_event,
        embed_fn=safe_embed_fn,
    )

    registry.register(Tool(
        name="probe_secret_leak",
        description=(
            "Scan common sensitive paths (/.env, /.git/config, /api-docs, /swagger, etc.) "
            "and JS bundles for exposed access keys, tokens, and credentials. "
            "Finds AWS keys, Stripe keys, GitHub tokens, JWTs, database URLs, private keys, and 15+ other patterns. "
            "Any secret found with a non-404 status is treated as CRITICAL."
        ),
        schema={
            "type": "object",
            "properties": {
                "actor_id": {"type": "string", "default": "user_a"},
                "extra_paths": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Additional paths to scan beyond the built-in list",
                },
                "scan_js_bundles": {"type": "boolean", "default": True},
            },
        },
        handler=lambda args: _probes.probe_secret_leak(probe_ctx, args),
    ))

    registry.register(Tool(
        name="probe_auth_weakness",
        description=(
            "Test a login/auth endpoint for user enumeration (status, response size, timing), "
            "missing rate limiting on failed logins, verbose error disclosure, and JWT weaknesses "
            "(alg=none, missing exp, weak signature) in any returned tokens."
        ),
        schema={
            "type": "object",
            "properties": {
                "login_endpoint": {"type": "string"},
                "valid_username": {"type": "string", "description": "A username known to exist"},
                "invalid_username": {"type": "string"},
                "username_field": {"type": "string", "default": "email"},
                "password_field": {"type": "string", "default": "password"},
                "method": {"type": "string", "default": "POST"},
                "actor_id": {"type": "string", "default": "user_a"},
            },
            "required": ["login_endpoint", "valid_username"],
        },
        handler=lambda args: _probes.probe_auth_weakness(probe_ctx, args),
    ))

    registry.register(Tool(
        name="probe_business_logic",
        description=(
            "Test a transactional endpoint (payment, transfer, balance change) for critical business "
            "logic flaws: negative amounts, zero amounts, decimal precision tricks, mass assignment "
            "of protected fields (role, balance, is_admin), and missing idempotency (replay). "
            "Requires safety.passive_only=false because it sends POST/PUT."
        ),
        schema={
            "type": "object",
            "properties": {
                "endpoint": {"type": "string"},
                "baseline_payload": {"type": "object", "description": "A payload that would succeed normally"},
                "amount_field": {"type": "string", "default": "amount"},
                "method": {"type": "string", "default": "POST"},
                "actor_id": {"type": "string", "default": "user_a"},
                "protected_fields": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["endpoint", "baseline_payload"],
        },
        handler=lambda args: _probes.probe_business_logic(probe_ctx, args),
    ))

    registry.register(Tool(
        name="discover_endpoints",
        description=(
            "Passively discover endpoints from robots.txt, sitemap.xml, OpenAPI/Swagger specs, "
            "OpenID Connect configuration, and JavaScript bundles. Returns all discovered paths "
            "plus a filtered list of IDOR candidates (paths containing id/uuid/slug parameters). "
            "Run this early to expand the attack surface beyond what you already know."
        ),
        schema={
            "type": "object",
            "properties": {
                "actor_id": {"type": "string", "default": "user_a"},
                "include_js_scan": {"type": "boolean", "default": True},
            },
        },
        handler=lambda args: _probes.discover_endpoints(probe_ctx, args),
    ))

    def _finish(args: dict[str, Any]) -> dict[str, Any]:
        summary = args["summary"]
        findings = memory.list_findings()
        memory.note("run.summary", {"summary": summary, "findings_count": len(findings)})
        return {"ok": True, "summary": summary, "findings_count": len(findings), "findings": findings}

    registry.register(Tool(
        name="finish",
        description="Signal the task is complete. Provides final summary and returns all findings.",
        schema={
            "type": "object",
            "properties": {"summary": {"type": "string"}},
            "required": ["summary"],
        },
        handler=_finish,
    ))

    return registry
