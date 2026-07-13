# HANDOFF — Operator's Manual for the Executing Agent

You are the AI that will run this tool. Read this once. Follow it in order.

## What this tool does

Autonomous IDOR/BOLA testing against an authorized web application target.
Two actors, both with valid credentials to the same platform but different
tenants. The tool discovers endpoints, probes each one with both actors,
and confirms cross-tenant access by comparing responses.

## What you (the executing agent) must do before invoking

1. **Verify authorization.** The human operating this must have written
   permission to test the target. This tool is passive-safe by default
   (`safety.passive_only: true` in config), meaning only GET/HEAD/OPTIONS.
   Do not flip this to false without confirming write authorization.

2. **Populate config.yaml.** Edit these fields:
   - `target.name` — friendly name for the target
   - `target.base_url` — HTTPS base URL, no trailing slash
   - `target.auth_type` — one of `bearer`, `cookie`, `header`
   - `target.actors` — at least two actors with different `tenant_id`
   - `safety.allow_hosts` — must include the target hostname

3. **Populate environment variables.** Copy `.env.example` to `.env` and fill:
   - `USER_A_TOKEN` — bearer token / session cookie for actor `user_a`
   - `USER_B_TOKEN` — bearer token / session cookie for actor `user_b`
   - `GROQ_API_KEY` — only if you set `groq.enabled: true` in config

4. **Choose LLM backend.** Priority order in `build_llm`:
   `anthropic > groq > ollama`. Enable exactly one API-based provider.

   | Provider | Config key | Model default | Cost | When to use |
   |---|---|---|---|---|
   | Ollama | `llm` (always active) | `qwen2.5-coder:32b` | Free (local) | Default; no internet dep |
   | Groq | `groq.enabled: true` | `llama-3.3-70b-versatile` | Free tier | Cloud speed, no local GPU |
   | Anthropic | `anthropic.enabled: true` | `claude-opus-4-8` | Paid, per-token | Highest capability |

   For Opus 4.8: set `anthropic.enabled: true` and put your key in
   `ANTHROPIC_API_KEY`. Preflight runs a real ping against `/v1/messages`
   so an invalid key is caught before the loop starts.

   **Embeddings still use Ollama's `nomic-embed-text` regardless of the chat
   provider.** Anthropic and Groq don't expose embedding endpoints. If you
   don't want Ollama, edit `prompts.py` to remove references to `recall` —
   the agent will fall back on plain context.

## Preflight — always run first

```
python run.py preflight --auth-probe /api/me
```

The `--auth-probe` path should be an endpoint that returns 200 for a valid
token and 401 for an invalid one. If you don't know one, omit the flag —
that check will be skipped but the rest still runs.

Preflight checks: config sanity, env vars, LLM reachability, model availability,
DNS resolution, target reachability, allowlist consistency, per-actor auth.

**Do not proceed to `run` if preflight critical checks fail.** Fix the reported
issues first. Warnings (yellow) are acceptable but should be noted.

## Running against the target

Two invocation styles:

### Task templates (preferred for autonomous execution)

```
python run.py list-tasks
```

Shows every template with its required parameters. Then:

```
python run.py run --template spec_sweep --param spec_path=/workspace/openapi.yaml
python run.py run --template single_endpoint --param endpoint=/api/v1/orders/{id}
python run.py run --template id_enumeration --param endpoint=/api/v1/documents/{id}
```

### Free-form task

```
python run.py run --task "Discover IDOR issues on /api/v1/orders/{id} and /api/v1/invoices/{id}"
```

## What the tool will NOT do

- Test hosts not in `safety.allow_hosts` — hard block
- Exceed `safety.max_requests_per_task` — request budget enforced
- Perform writes when `safety.passive_only: true` — schema-level block
- Retry the same failing request indefinitely — the loop detects stagnation

## What you must monitor while it runs

- `data/agent.log` — structured JSON logs (`level`, `msg`, extras per event)
- `data/agent.db` — SQLite with tables: `semantic`, `episodic`, `findings`, `http_log`
- Rich console output — per-iteration reasoning + tool calls

## Interpreting findings

Findings are written to `data/findings.json` at the end of a run. Each has:

- `endpoint` — the path template (e.g. `/api/v1/orders/{id}`)
- `severity` — critical / high / medium / low / info
- `title` — one-line summary
- `evidence` — includes `owner_request_id` and `intruder_request_id`
- `repro` — a curl script that reproduces the finding

**Verify each finding manually** before reporting it upstream. The agent's
verdict is high-confidence but not infallible. For each finding, pull the
raw request/response with:

```
sqlite3 data/agent.db "SELECT * FROM http_log WHERE id = <request_id>"
```

## Kill switch

If the agent is misbehaving:

- Ctrl-C — the loop catches SIGINT via the outer try/except in `run.py`
- Docker: `docker compose down agent`
- The loop hard-caps at `safety.max_loop_iterations` iterations regardless

## Handoff back to the human

At end of run, the console prints:
- Completion status
- Iteration count
- Reason for termination (`finish_tool_called`, `max_iterations_reached`, etc.)
- Findings table

Attach `data/findings.json` and `data/agent.log` to the handoff report.
Do not commit `data/` to version control — it contains bearer tokens
in log headers if redaction ever misses (unlikely; headers are redacted
before storage, but treat the DB as sensitive anyway).

## Common failure modes and fixes

| Symptom | Cause | Fix |
|---|---|---|
| `ollama:reachable FAIL` | Ollama not running | `ollama serve` in another terminal |
| `ollama:model:X FAIL` | Model not pulled | `ollama pull qwen2.5-coder:32b` |
| `env:USER_A_TOKEN FAIL` | Missing env var | Set it in `.env`, `export $(cat .env \| xargs)` |
| `target:allowlist FAIL` | Host not in allow_hosts | Add to `config.yaml → safety.allow_hosts` |
| `auth:user_a FAIL` (401) | Expired token | Refresh the token; update `.env` |
| Agent loops without progress | Model too small | Switch to `qwen2.5-coder:32b` or enable Groq |
| `max_iterations_reached` | Task too broad | Use a narrower template or scope the endpoint list |

## When the tool is NOT the right choice

- The target uses signed request bodies (HMAC) — the tool doesn't sign
- The target requires MFA per request — no re-auth flow
- The target is production without change control — use staging
- You lack written authorization — stop
