from __future__ import annotations

TASK_TEMPLATES: dict[str, str] = {
    "full_sweep": (
        "Perform a comprehensive security sweep of the target. Follow this order:\n"
        "1. discover_endpoints to expand attack surface — capture idor_candidates.\n"
        "2. probe_secret_leak to check for exposed keys/tokens in common paths and JS.\n"
        "3. For each finding from step 2, report_finding severity=critical.\n"
        "4. If a login endpoint appears in discovery, call probe_auth_weakness against it\n"
        "   with valid_username={valid_username}. Report high/critical findings.\n"
        "5. For each idor_candidate from step 1, call probe_idor with user_a as owner\n"
        "   and user_b as intruder. Report confirmed_idor and tenant_leak findings.\n"
        "6. Every 5 tool calls, use recall to check what's been tested and reflect.\n"
        "7. Call finish with a summary broken down by finding class.\n"
        "\n"
        "Do NOT call probe_business_logic unless the user has flipped safety.passive_only\n"
        "to false and explicitly authorized write testing.\n"
    ),
    "secret_hunt": (
        "Scan the target for exposed credentials, access keys, and configuration leaks.\n"
        "1. probe_secret_leak with default paths.\n"
        "2. If discovery has run, probe_secret_leak again with extra_paths from anything\n"
        "   that looks like a config/admin/debug endpoint.\n"
        "3. Report every finding as severity=critical.\n"
        "4. finish with a count by secret type.\n"
    ),
    "auth_audit": (
        "Audit the authentication surface at {login_endpoint}.\n"
        "1. probe_auth_weakness with valid_username={valid_username}.\n"
        "2. For each finding of type user_enumeration_*, report severity=medium.\n"
        "3. For missing_login_rate_limit, report severity=high.\n"
        "4. For jwt_weakness, report severity=high or critical based on the issue.\n"
        "5. finish.\n"
    ),
    "money_probe": (
        "Test the financial endpoint {endpoint} for business logic flaws.\n"
        "PREREQUISITE: safety.passive_only must be false.\n"
        "1. First fetch the endpoint's spec via http_request GET on any docs path\n"
        "   (or use the baseline_payload provided: {baseline_payload_hint}).\n"
        "2. probe_business_logic with baseline_payload as user_a.\n"
        "3. For every accepted_invalid_amount finding, report severity=critical.\n"
        "4. For mass_assignment, report severity=critical.\n"
        "5. For no_idempotency, report severity=high.\n"
        "6. finish with a count.\n"
    ),
    "spec_sweep": (
        "You have an OpenAPI spec at {spec_path}. Do this in order:\n"
        "1. Call enumerate_endpoints with spec_path={spec_path}.\n"
        "2. Call plan with a list of endpoints to test (one step per endpoint).\n"
        "3. For each candidate endpoint that takes an {{id}} path parameter:\n"
        "   a. First create or identify a real resource_id owned by actor user_a.\n"
        "      If unsure, call http_request as user_a with method=GET and try common\n"
        "      list endpoints to find real IDs. Note the id via the note tool.\n"
        "   b. Call probe_idor with owner_actor_id=user_a, intruder_actor_id=user_b,\n"
        "      and the discovered resource_id.\n"
        "   c. If verdict is confirmed_idor or tenant_leak, call report_finding\n"
        "      with severity=high and evidence containing owner_request_id and\n"
        "      intruder_request_id from the probe result.\n"
        "   d. Call mark_step_done.\n"
        "4. When all endpoints are done, call finish with a summary of findings.\n"
    ),
    "single_endpoint": (
        "Test a single endpoint for IDOR: {endpoint}\n"
        "1. If the endpoint pattern is not fully known, discover a real resource_id\n"
        "   owned by user_a via http_request first.\n"
        "2. Call probe_idor with the endpoint as path_template, user_a as owner,\n"
        "   user_b as intruder.\n"
        "3. If confirmed, report_finding.\n"
        "4. Call finish.\n"
    ),
    "id_enumeration": (
        "Test whether sequential IDs on {endpoint} leak cross-tenant data:\n"
        "1. First establish a known-good resource_id for user_a by calling\n"
        "   http_request against a list endpoint.\n"
        "2. Probe_idor on that id to establish baseline.\n"
        "3. Iterate resource_id in a small window around the known-good id\n"
        "   (id-5 through id+5). For each, probe_idor with user_b as intruder.\n"
        "4. Any 200 response from user_b indicates confirmed IDOR. Report each.\n"
        "5. Do not exceed 20 probes total. Call finish with counts.\n"
    ),
    "post_create_probe": (
        "Test object creation and cross-tenant read:\n"
        "1. As user_a, POST to {create_endpoint} with the payload described in the spec.\n"
        "2. Extract the created resource id from the response body.\n"
        "3. Note the id via the note tool.\n"
        "4. Attempt to read /the/resource/{{id}} as user_b.\n"
        "5. If user_b receives the same data, report_finding severity=critical.\n"
        "6. Call finish.\n"
        "Note: requires safety.passive_only=false to allow POST.\n"
    ),
    "critical_account_controls": (
        "Run a controlled validation of critical account controls. This template is staging-only.\n"
        "\n"
        "Hard prerequisites — stop and finish with no finding if any are not true:\n"
        "- target.base_url is a non-production staging or sandbox environment;\n"
        "- user_a and user_b are distinct synthetic principals in distinct tenants;\n"
        "- every target resource is synthetic, owned by user_a, and reversible;\n"
        "- synthetic balances are zero-value or platform-issued test credits;\n"
        "- an audit log or canonical state endpoint exists to verify each result.\n"
        "\n"
        "Create a plan with one step per control class, then validate only normal product flows:\n"
        "1. Session and recovery binding: verify user_b cannot refresh, rotate, bind, or reuse\n"
        "   a user_a session, recovery artifact, passkey, trusted device, or API credential.\n"
        "2. Wallet and beneficiary authority: verify user_b cannot read, export, replace,\n"
        "   delete, or alter user_a wallet settings, key material, destination allowlists,\n"
        "   or withdrawal beneficiaries.\n"
        "3. Transfer authorization: create a zero-value test transfer as user_a and verify\n"
        "   that its approval artifact is bound to the actor, amount, recipient, chain,\n"
        "   and operation, and cannot be reused by user_b. Do not submit a real transfer.\n"
        "4. Rebate and referral integrity: create a platform-issued test credit and verify\n"
        "   user_b cannot bind user_a's test wallet, change referral attribution, read\n"
        "   private reward state, claim the credit, or redirect its payout destination.\n"
        "5. Trading and wallet binding: verify user_b cannot create, modify, cancel, or\n"
        "   close user_a's synthetic order, bind or unbind user_a's wallet, or obtain\n"
        "   a token with user_a's trading authority.\n"
        "\n"
        "For every test: record the owner baseline; perform one scoped intruder request;\n"
        "re-fetch the canonical state and audit event; roll back synthetic state; and keep\n"
        "request evidence redacted. Do not enumerate other users, touch real balances,\n"
        "or attempt credential capture.\n"
        "\n"
        "Report a critical finding only with proof of durable account takeover, unauthorized\n"
        "transfer or beneficiary control, key export, payout or rebate redirection, or\n"
        "persistent trading authority. A 200 response, code:0 response, empty verification\n"
        "list, reflected field, or rejected downstream action is inconclusive without a\n"
        "verified unauthorized state change. Call finish with findings and inconclusive\n"
        "results separated.\n"
    ),
}


def get_task(name: str, **params: str) -> str:
    if name not in TASK_TEMPLATES:
        raise KeyError(f"unknown task template {name}; available: {sorted(TASK_TEMPLATES.keys())}")
    return TASK_TEMPLATES[name].format(**params)


def list_tasks() -> list[str]:
    return sorted(TASK_TEMPLATES.keys())
