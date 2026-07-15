const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_web_20260715-2161-18d5b10&app_ver=20260715-2161-18d5b10&from_app=gmgn';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const SITEKEY = '6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T';

(async () => {
    console.log('🔥 FINAL ATTEMPT — ONE FLOW, NO GAPS');
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 3000));
    
    const result = await page.evaluate(async (refresh, params, target, sitekey) => {
        const log = [];
        
        // Step 1: Token
        let r = await fetch('/account/account/refresh_access_token', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refresh})
        });
        let data = await r.json();
        if (data.code !== 0) return {error: 'token fail'};
        const token = data.data.data.token;
        const h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token};
        log.push('1. Token OK');
        
        // Step 2: Load reCAPTCHA FIRST (takes time)
        await new Promise(resolve => {
            if (window.grecaptcha && window.grecaptcha.enterprise) { resolve(); return; }
            const s = document.createElement('script');
            s.src = 'https://www.recaptcha.net/recaptcha/enterprise.js?render=' + sitekey;
            s.onload = () => setTimeout(resolve, 2000);
            document.head.appendChild(s);
            setTimeout(resolve, 8000);
        });
        log.push('2. reCAPTCHA loaded');
        
        // Step 3: Get captcha token FIRST
        let captchaToken = null;
        try {
            captchaToken = await new Promise((resolve, reject) => {
                grecaptcha.enterprise.ready(async () => {
                    const t = await grecaptcha.enterprise.execute(sitekey, {action: 'bind_wallet'});
                    resolve(t);
                });
                setTimeout(() => reject('timeout'), 12000);
            });
        } catch(e) { return {error: 'captcha fail: ' + e}; }
        log.push('3. Captcha token: ' + captchaToken.substring(0, 40));
        
        // Step 4: Generate txn_id IMMEDIATELY before verify (minimize time gap)
        r = await fetch('/account/account/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
        });
        data = await r.json();
        if (data.code !== 0) return {error: 'mfa fail', data};
        const txnId = data.data.data.txn_id;
        log.push('4. txn_id: ' + txnId);
        
        // Step 5: IMMEDIATELY verify captcha (same txn_id, no gap)
        // The request_id — maybe it needs to be the JTI from our access token?
        // Decode token to get jti
        const tokenPayload = JSON.parse(atob(token.split('.')[1]));
        const jti = tokenPayload.jti;
        const fatherId = tokenPayload.data?.father_id;
        log.push('5. Token jti: ' + jti + ', father_id: ' + fatherId);
        
        // Try multiple request_id values FAST
        const requestIds = [
            crypto.randomUUID(),
            jti,
            fatherId,
            txnId,
        ];
        
        for (const reqId of requestIds) {
            if (!reqId) continue;
            r = await fetch('/account/mfa/txn/v1/verify_captcha?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({txn_id: txnId, usage: 'bind_wallet', captcha_data: captchaToken, request_id: reqId})
            });
            data = await r.json();
            
            if (data.code === 0) {
                log.push('💀💀💀 CAPTCHA VERIFIED with request_id: ' + reqId);
                
                // BIND!
                r = await fetch('/account/bind_wallet?' + params, {
                    method: 'POST', headers: h,
                    body: JSON.stringify({address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId})
                });
                data = await r.json();
                log.push('BIND: ' + JSON.stringify(data));
                return {log, success: true, bindResult: data};
            }
            
            log.push('reqId=' + reqId.substring(0, 12) + ': ' + data.code + ' ' + (data.message || '').substring(0, 40));
        }
        
        return {log, txnId, captchaToken: captchaToken.substring(0, 50)};
    }, FRESH_REFRESH, PARAMS, TARGET, SITEKEY);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
