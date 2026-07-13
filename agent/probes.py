from __future__ import annotations

import base64
import json
import re
import statistics
import time
from dataclasses import dataclass
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

import httpx

SECRET_PATTERNS: dict[str, re.Pattern[str]] = {
    "aws_access_key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "aws_secret_key": re.compile(r"(?i)aws_secret_access_key['\"\s:=]+[A-Za-z0-9/+=]{40}"),
    "github_pat": re.compile(r"\bghp_[A-Za-z0-9]{36}\b"),
    "github_oauth": re.compile(r"\bgho_[A-Za-z0-9]{36}\b"),
    "github_fine_grained": re.compile(r"\bgithub_pat_[A-Za-z0-9_]{82}\b"),
    "stripe_live_sk": re.compile(r"\bsk_live_[0-9a-zA-Z]{24,}\b"),
    "stripe_live_pk": re.compile(r"\bpk_live_[0-9a-zA-Z]{24,}\b"),
    "stripe_restricted": re.compile(r"\brk_live_[0-9a-zA-Z]{24,}\b"),
    "slack_token": re.compile(r"\bxox[abpors]-[0-9]{10,}-[0-9]{10,}-[0-9a-zA-Z]{24,}\b"),
    "slack_webhook": re.compile(r"https://hooks\.slack\.com/services/T[A-Z0-9]+/B[A-Z0-9]+/[A-Za-z0-9]+"),
    "twilio_sid": re.compile(r"\bAC[a-f0-9]{32}\b"),
    "twilio_token": re.compile(r"\bSK[a-f0-9]{32}\b"),
    "sendgrid": re.compile(r"\bSG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}\b"),
    "google_api_key": re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b"),
    "private_key_rsa": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED |DSA )?PRIVATE KEY-----"),
    "jwt": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
    "bearer_hardcoded": re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.=]{20,}"),
    "generic_api_key": re.compile(r"(?i)(?:api[_-]?key|apikey|access[_-]?token|secret[_-]?key)['\"\s:=]+['\"]?[A-Za-z0-9_\-]{20,}['\"]?"),
    "postgres_url": re.compile(r"postgres(?:ql)?://[^:]+:[^@]+@[^/\s]+"),
    "mongodb_url": re.compile(r"mongodb(?:\+srv)?://[^:]+:[^@]+@[^/\s]+"),
    "mysql_url": re.compile(r"mysql://[^:]+:[^@]+@[^/\s]+"),
}

SENSITIVE_PATHS: tuple[str, ...] = (
    "/.env", "/.env.local", "/.env.production", "/.env.development",
    "/.git/config", "/.git/HEAD",
    "/.aws/credentials", "/.aws/config",
    "/robots.txt", "/sitemap.xml", "/sitemap_index.xml",
    "/.well-known/security.txt", "/.well-known/openid-configuration",
    "/api-docs", "/api-docs.json", "/swagger.json", "/swagger-ui.html",
    "/openapi.json", "/openapi.yaml", "/v2/api-docs", "/v3/api-docs",
    "/debug/vars", "/debug/pprof",
    "/actuator", "/actuator/env", "/actuator/heapdump", "/actuator/mappings",
    "/wp-config.php.bak", "/config.json", "/config.yml", "/config.yaml",
    "/backup.sql", "/dump.sql", "/database.sql",
    "/.DS_Store", "/Thumbs.db",
    "/server-status", "/server-info",
    "/console", "/graphql", "/graphiql", "/altair",
    "/phpinfo.php", "/info.php", "/test.php",
    "/admin", "/administrator", "/management",
    "/.svn/entries", "/.hg/store",
)

JS_URL_PATTERN = re.compile(
    r"""["'`](?:/api/|/v\d+/|https?://[^"'`\s]+/api/)[^"'`\s]*["'`]""",
    re.IGNORECASE,
)


@dataclass
class ProbeContext:
    request_fn: Callable[[dict[str, Any]], dict[str, Any]]
    memory_get_http: Callable[[int], dict[str, Any] | None]
    memory_record_event: Callable[..., int]
    embed_fn: Callable[[str], list[float]]


def scan_for_secrets(text: str) -> list[dict[str, str]]:
    if not isinstance(text, str):
        text = str(text)
    findings = []
    for name, pattern in SECRET_PATTERNS.items():
        for match in pattern.finditer(text):
            snippet = match.group(0)
            findings.append({
                "type": name,
                "match": snippet[:80] + ("..." if len(snippet) > 80 else ""),
                "offset": match.start(),
            })
    return findings


def extract_js_urls(text: str) -> list[str]:
    if not isinstance(text, str):
        return []
    seen: set[str] = set()
    urls: list[str] = []
    for match in JS_URL_PATTERN.finditer(text):
        url = match.group(0).strip("\"'`")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    return urls


def _body_text(request_record: dict[str, Any] | None) -> str:
    if not request_record:
        return ""
    body = request_record.get("response_body")
    if isinstance(body, (dict, list)):
        return json.dumps(body, default=str)
    return str(body or "")


def probe_secret_leak(ctx: ProbeContext, args: dict[str, Any]) -> dict[str, Any]:
    """Fetch a set of common paths as user_a (or specified actor) and scan responses for secrets."""
    actor_id = args.get("actor_id", "user_a")
    extra_paths: list[str] = args.get("extra_paths") or []
    scan_js_bundles: bool = bool(args.get("scan_js_bundles", True))
    all_paths = list(SENSITIVE_PATHS) + extra_paths

    findings: list[dict[str, Any]] = []
    scanned: list[dict[str, Any]] = []
    js_bundle_urls: list[str] = []

    for path in all_paths:
        try:
            result = ctx.request_fn({"method": "GET", "path": path, "actor_id": actor_id})
        except Exception as exc:
            scanned.append({"path": path, "error": str(exc)[:200]})
            continue
        status = result["status"]
        record = ctx.memory_get_http(int(result["request_id"]))
        body_text = _body_text(record)
        secrets = scan_for_secrets(body_text)
        entry = {
            "path": path,
            "status": status,
            "size": len(body_text),
            "request_id": result["request_id"],
            "secrets_found": len(secrets),
        }
        scanned.append(entry)
        if status < 400 and secrets:
            findings.append({
                "path": path,
                "status": status,
                "request_id": result["request_id"],
                "secrets": secrets,
                "severity": "critical",
                "verdict": "confirmed_secret_exposure",
            })
        if status < 400 and scan_js_bundles and body_text:
            js_bundle_urls.extend(extract_js_urls(body_text))

    if scan_js_bundles:
        seen_bundles: set[str] = set()
        for url in js_bundle_urls[:20]:
            path = urlparse(url).path if url.startswith("http") else url
            if not path or path in seen_bundles:
                continue
            seen_bundles.add(path)
            try:
                result = ctx.request_fn({"method": "GET", "path": path, "actor_id": actor_id})
            except Exception:
                continue
            record = ctx.memory_get_http(int(result["request_id"]))
            body_text = _body_text(record)
            secrets = scan_for_secrets(body_text)
            if secrets and result["status"] < 400:
                findings.append({
                    "path": path,
                    "status": result["status"],
                    "request_id": result["request_id"],
                    "secrets": secrets,
                    "severity": "critical",
                    "verdict": "confirmed_secret_in_js",
                })

    ctx.memory_record_event(
        kind="probe",
        key="secret_leak_sweep",
        value={"scanned": len(scanned), "findings": len(findings)},
        embedding=ctx.embed_fn(f"secret leak scan; {len(findings)} findings"),
    )
    return {"findings": findings, "scanned_count": len(scanned), "scanned": scanned[:50]}


def probe_auth_weakness(ctx: ProbeContext, args: dict[str, Any]) -> dict[str, Any]:
    """Test a login endpoint for rate limiting, user enumeration, verbose errors, and JWT weaknesses."""
    endpoint = args["login_endpoint"]
    username_field = args.get("username_field", "email")
    password_field = args.get("password_field", "password")
    valid_username = args["valid_username"]
    invalid_username = args.get("invalid_username", f"nonexistent_{int(time.time())}@example.invalid")
    actor_id = args.get("actor_id", "user_a")
    method = args.get("method", "POST").upper()

    findings: list[dict[str, Any]] = []

    invalid_response = ctx.request_fn({
        "method": method, "path": endpoint, "actor_id": actor_id,
        "body": {username_field: valid_username, password_field: "wrong_password_test_only_xxxxxxx"},
    })
    invalid_user_response = ctx.request_fn({
        "method": method, "path": endpoint, "actor_id": actor_id,
        "body": {username_field: invalid_username, password_field: "wrong_password_test_only_xxxxxxx"},
    })

    valid_rec = ctx.memory_get_http(int(invalid_response["request_id"]))
    invalid_rec = ctx.memory_get_http(int(invalid_user_response["request_id"]))
    valid_body = _body_text(valid_rec)[:2048]
    invalid_body = _body_text(invalid_rec)[:2048]

    if invalid_response["status"] != invalid_user_response["status"]:
        findings.append({
            "type": "user_enumeration_via_status",
            "severity": "medium",
            "detail": f"valid user -> {invalid_response['status']}, invalid user -> {invalid_user_response['status']}",
            "request_ids": [invalid_response["request_id"], invalid_user_response["request_id"]],
        })
    elif valid_body and invalid_body and abs(len(valid_body) - len(invalid_body)) > 32:
        findings.append({
            "type": "user_enumeration_via_response_size",
            "severity": "medium",
            "detail": f"body size differs: valid={len(valid_body)} invalid={len(invalid_body)}",
            "request_ids": [invalid_response["request_id"], invalid_user_response["request_id"]],
        })

    verbose_markers = ["stack trace", "traceback", "SQLSTATE", "at java.", "at org.", "line ", "syntax error", "duplicate key", "user does not exist", "invalid password", "wrong password"]
    for marker in verbose_markers:
        if marker.lower() in valid_body.lower() or marker.lower() in invalid_body.lower():
            findings.append({
                "type": "verbose_error_disclosure",
                "severity": "low",
                "detail": f"response contains diagnostic marker: {marker!r}",
                "request_ids": [invalid_response["request_id"], invalid_user_response["request_id"]],
            })
            break

    timings: list[float] = []
    for _ in range(3):
        started = time.monotonic()
        ctx.request_fn({
            "method": method, "path": endpoint, "actor_id": actor_id,
            "body": {username_field: valid_username, password_field: "wrong"},
        })
        timings.append(time.monotonic() - started)
    valid_median = statistics.median(timings)

    timings_invalid: list[float] = []
    for _ in range(3):
        started = time.monotonic()
        ctx.request_fn({
            "method": method, "path": endpoint, "actor_id": actor_id,
            "body": {username_field: invalid_username, password_field: "wrong"},
        })
        timings_invalid.append(time.monotonic() - started)
    invalid_median = statistics.median(timings_invalid)

    ratio = valid_median / max(invalid_median, 0.001)
    if ratio > 1.5 or ratio < 0.5:
        findings.append({
            "type": "user_enumeration_via_timing",
            "severity": "medium",
            "detail": f"valid user median {valid_median*1000:.1f}ms vs invalid {invalid_median*1000:.1f}ms (ratio {ratio:.2f})",
        })

    rate_limit_burst_count = 8
    statuses: list[int] = []
    for _ in range(rate_limit_burst_count):
        r = ctx.request_fn({
            "method": method, "path": endpoint, "actor_id": actor_id,
            "body": {username_field: valid_username, password_field: "wrong"},
        })
        statuses.append(r["status"])
    got_rate_limited = any(s == 429 for s in statuses)
    if not got_rate_limited:
        findings.append({
            "type": "missing_login_rate_limit",
            "severity": "high",
            "detail": f"{rate_limit_burst_count} failed logins accepted, no 429; statuses={statuses}",
        })

    for record in (valid_rec, invalid_rec):
        body = _body_text(record)
        jwt_match = SECRET_PATTERNS["jwt"].search(body)
        if jwt_match:
            jwt_findings = analyze_jwt(jwt_match.group(0))
            if jwt_findings:
                findings.append({
                    "type": "jwt_weakness",
                    "severity": "high",
                    "detail": jwt_findings,
                    "request_ids": [record.get("id") if record else None],
                })

    ctx.memory_record_event(
        kind="probe",
        key=f"auth_weakness {endpoint}",
        value={"endpoint": endpoint, "finding_count": len(findings)},
        embedding=ctx.embed_fn(f"auth weakness probe {endpoint}; {len(findings)} findings"),
    )
    return {
        "endpoint": endpoint,
        "findings": findings,
        "confirmed_weaknesses": [f for f in findings if f.get("severity") in {"high", "critical"}],
    }


def analyze_jwt(token: str) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    parts = token.split(".")
    if len(parts) != 3:
        return findings
    try:
        header_bytes = base64.urlsafe_b64decode(parts[0] + "=" * (-len(parts[0]) % 4))
        payload_bytes = base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4))
        header = json.loads(header_bytes)
        payload = json.loads(payload_bytes)
    except (ValueError, json.JSONDecodeError):
        return findings

    alg = str(header.get("alg", "")).lower()
    if alg in {"none", ""}:
        findings.append({"issue": "alg_none", "severity": "critical", "detail": "JWT alg is none or empty"})
    if alg.startswith("hs") and len(parts[2]) < 22:
        findings.append({"issue": "weak_signature_length", "severity": "high", "detail": f"HMAC signature only {len(parts[2])} chars"})
    for claim in ("role", "roles", "is_admin", "isAdmin", "admin", "permissions", "scopes", "tenant_id", "user_id", "uid", "sub"):
        if claim in payload:
            findings.append({
                "issue": "sensitive_claim_present",
                "severity": "info",
                "detail": f"claim {claim} = {payload[claim]!r} — tamper-test this claim",
            })
    if "exp" not in payload:
        findings.append({"issue": "no_expiration", "severity": "high", "detail": "JWT has no exp claim"})
    return findings


def probe_business_logic(ctx: ProbeContext, args: dict[str, Any]) -> dict[str, Any]:
    """Test a transactional endpoint for negative amounts, mass assignment, replay, and race conditions."""
    endpoint = args["endpoint"]
    method = args.get("method", "POST").upper()
    actor_id = args.get("actor_id", "user_a")
    baseline_payload: dict[str, Any] = dict(args["baseline_payload"])
    amount_field = args.get("amount_field", "amount")
    protected_fields: list[str] = args.get("protected_fields") or ["role", "is_admin", "verified", "tenant_id", "balance", "credit"]

    findings: list[dict[str, Any]] = []

    tampered_payloads: dict[str, Any] = {
        "negative_amount": {**baseline_payload, amount_field: -100},
        "zero_amount": {**baseline_payload, amount_field: 0},
        "extreme_large": {**baseline_payload, amount_field: 10**15},
        "decimal_underflow": {**baseline_payload, amount_field: 0.00001},
        "scientific_notation": {**baseline_payload, amount_field: "1e-10"},
        "string_amount": {**baseline_payload, amount_field: "-100"},
        "null_amount": {**baseline_payload, amount_field: None},
    }
    for label, payload in tampered_payloads.items():
        try:
            result = ctx.request_fn({"method": method, "path": endpoint, "actor_id": actor_id, "body": payload})
        except Exception as exc:
            continue
        if 200 <= result["status"] < 300:
            findings.append({
                "type": f"accepted_invalid_amount:{label}",
                "severity": "critical" if label in {"negative_amount", "string_amount", "null_amount"} else "high",
                "detail": f"{method} {endpoint} accepted {label} with status {result['status']}",
                "request_id": result["request_id"],
                "payload_used": payload,
            })

    mass_assignment_payload = dict(baseline_payload)
    for field in protected_fields:
        mass_assignment_payload[field] = "attacker_controlled"
    try:
        result = ctx.request_fn({"method": method, "path": endpoint, "actor_id": actor_id, "body": mass_assignment_payload})
        if 200 <= result["status"] < 300:
            record = ctx.memory_get_http(int(result["request_id"]))
            body_text = _body_text(record)
            reflected = [f for f in protected_fields if f in body_text and "attacker_controlled" in body_text]
            if reflected:
                findings.append({
                    "type": "mass_assignment",
                    "severity": "critical",
                    "detail": f"protected fields reflected in response: {reflected}",
                    "request_id": result["request_id"],
                })
            else:
                findings.append({
                    "type": "mass_assignment_suspect",
                    "severity": "high",
                    "detail": f"endpoint accepted extra fields {protected_fields}; verify server-side effect manually",
                    "request_id": result["request_id"],
                })
    except Exception:
        pass

    replay_ids: list[int] = []
    for _ in range(3):
        try:
            r = ctx.request_fn({"method": method, "path": endpoint, "actor_id": actor_id, "body": baseline_payload})
            replay_ids.append(r["request_id"])
        except Exception:
            break
    if len(replay_ids) == 3:
        recs = [ctx.memory_get_http(rid) for rid in replay_ids]
        successes = [r for r in recs if r and 200 <= r["status"] < 300]
        if len(successes) >= 2:
            findings.append({
                "type": "no_idempotency",
                "severity": "high",
                "detail": f"identical {method} {endpoint} accepted {len(successes)} times without idempotency key check",
                "request_ids": replay_ids,
            })

    ctx.memory_record_event(
        kind="probe",
        key=f"business_logic {endpoint}",
        value={"endpoint": endpoint, "finding_count": len(findings)},
        embedding=ctx.embed_fn(f"business logic probe {endpoint}; {len(findings)} findings"),
    )
    return {
        "endpoint": endpoint,
        "findings": findings,
        "critical_count": sum(1 for f in findings if f.get("severity") == "critical"),
    }


def discover_endpoints(ctx: ProbeContext, args: dict[str, Any]) -> dict[str, Any]:
    """Discover endpoints from robots.txt, sitemap.xml, OpenAPI docs, and JS bundles."""
    actor_id = args.get("actor_id", "user_a")
    include_js_scan = bool(args.get("include_js_scan", True))

    discovery_paths = [
        "/robots.txt",
        "/sitemap.xml",
        "/sitemap_index.xml",
        "/.well-known/openid-configuration",
        "/.well-known/security.txt",
        "/api-docs",
        "/api-docs.json",
        "/swagger.json",
        "/openapi.json",
        "/openapi.yaml",
        "/v2/api-docs",
        "/v3/api-docs",
        "/graphql",
    ]

    discovered_paths: set[str] = set()
    sources: dict[str, list[str]] = {}

    for path in discovery_paths:
        try:
            result = ctx.request_fn({"method": "GET", "path": path, "actor_id": actor_id})
        except Exception:
            continue
        if result["status"] >= 400:
            continue
        record = ctx.memory_get_http(int(result["request_id"]))
        body_text = _body_text(record)
        found_here: list[str] = []

        if path == "/robots.txt":
            for line in body_text.splitlines():
                line = line.strip()
                if line.lower().startswith(("allow:", "disallow:")):
                    _, _, target = line.partition(":")
                    target = target.strip()
                    if target and target not in {"/", "*"}:
                        found_here.append(target)
        elif path.startswith("/sitemap"):
            for match in re.finditer(r"<loc>([^<]+)</loc>", body_text):
                url = match.group(1)
                parsed_path = urlparse(url).path
                if parsed_path and parsed_path != "/":
                    found_here.append(parsed_path)
        elif path.endswith((".json", "/api-docs", "/v2/api-docs", "/v3/api-docs")):
            try:
                spec = json.loads(body_text)
                for spec_path in (spec.get("paths") or {}):
                    found_here.append(spec_path)
            except json.JSONDecodeError:
                pass
        elif path == "/.well-known/openid-configuration":
            try:
                oidc = json.loads(body_text)
                for key in ("authorization_endpoint", "token_endpoint", "userinfo_endpoint", "jwks_uri", "revocation_endpoint"):
                    if key in oidc:
                        parsed_path = urlparse(oidc[key]).path
                        if parsed_path:
                            found_here.append(parsed_path)
            except json.JSONDecodeError:
                pass

        if found_here:
            sources[path] = found_here
            discovered_paths.update(found_here)

    js_urls_found: list[str] = []
    if include_js_scan:
        try:
            root_result = ctx.request_fn({"method": "GET", "path": "/", "actor_id": actor_id})
        except Exception:
            root_result = None
        if root_result and root_result["status"] < 400:
            record = ctx.memory_get_http(int(root_result["request_id"]))
            body_text = _body_text(record)
            js_srcs = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', body_text, re.IGNORECASE)
            for js_src in js_srcs[:10]:
                js_path = urlparse(js_src).path if js_src.startswith("http") else js_src
                if not js_path.startswith("/"):
                    js_path = "/" + js_path
                try:
                    js_result = ctx.request_fn({"method": "GET", "path": js_path, "actor_id": actor_id})
                except Exception:
                    continue
                if js_result["status"] >= 400:
                    continue
                js_record = ctx.memory_get_http(int(js_result["request_id"]))
                js_body = _body_text(js_record)
                urls_in_js = extract_js_urls(js_body)
                js_urls_found.extend(urls_in_js)
                for url in urls_in_js:
                    parsed_path = urlparse(url).path if url.startswith("http") else url
                    if parsed_path and parsed_path.startswith("/"):
                        discovered_paths.add(parsed_path)
        if js_urls_found:
            sources["js_bundles"] = js_urls_found[:50]

    id_pattern = re.compile(r"[/:](?:id|[a-z]+Id|uuid|slug)\b|\{[^}]*(?:id|Id|uuid|slug)[^}]*\}")
    idor_candidates = [p for p in discovered_paths if id_pattern.search(p)]

    ctx.memory_record_event(
        kind="discovery",
        key="endpoint_discovery",
        value={"discovered": len(discovered_paths), "idor_candidates": len(idor_candidates)},
        embedding=ctx.embed_fn(f"endpoint discovery; {len(discovered_paths)} paths, {len(idor_candidates)} idor candidates"),
    )

    return {
        "discovered_count": len(discovered_paths),
        "discovered_paths": sorted(discovered_paths)[:200],
        "idor_candidates": sorted(idor_candidates),
        "sources": sources,
    }
