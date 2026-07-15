const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_web_20260715-2161-18d5b10&app_ver=20260715-2161-18d5b10&from_app=gmgn';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const SITEKEY = '6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T';

(async () => {
    console.log('🔥 HUNTING REQUEST_ID');
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 3000));
    
    const result = await page.evaluate(async (refresh, params, target, sitekey) => {
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
        
        // Generate txn_id
        r = await fetch('/account/account/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
        });
        data = await r.json();
        const txnId = data.data.data.txn_id;
        log.push('txn_id: ' + txnId);
        
        // IDEA: Maybe there's a "request_captcha" or "init_captcha" endpoint
        // that returns the request_id BEFORE we solve it
        const initEndpoints = [
            {url: '/account/mfa/txn/v1/request_captcha', body: {txn_id: txnId, usage: 'bind_wallet'}},
            {url: '/account/mfa/txn/v1/init_captcha', body: {txn_id: txnId, usage: 'bind_wallet'}},
            {url: '/account/mfa/txn/v1/get_captcha', body: {txn_id: txnId, usage: 'bind_wallet'}},
            {url: '/account/mfa/txn/v1/captcha_request', body: {txn_id: txnId, usage: 'bind_wallet'}},
            {url: '/account/mfa/txn/v1/send_captcha', body: {txn_id: txnId, usage: 'bind_wallet'}},
            {url: '/account/mfa/txn/v1/start', body: {txn_id: txnId, usage: 'bind_wallet', verify_type: 'captcha'}},
            {url: '/account/mfa/txn/v1/request', body: {txn_id: txnId, usage: 'bind_wallet', verify_type: 'captcha'}},
        ];
        
        for (const ep of initEndpoints) {
            r = await fetch(ep.url + '?' + params, {method: 'POST', headers: h, body: JSON.stringify(ep.body)});
            if (r.status === 404) continue;
            try {
                data = await r.json();
                if (data.code === 0 || (data.data && data.data.request_id)) {
                    log.push('FOUND: ' + ep.url + ' → ' + JSON.stringify(data).substring(0, 300));
                    return {log, found: true, endpoint: ep.url, data};
                }
                if (data.message && !data.message.includes('not found')) {
                    log.push(ep.url.split('/').pop() + ': ' + data.code + ' ' + (data.message || '').substring(0, 60));
                }
            } catch(e) {}
        }
        
        // IDEA 2: Maybe request_id comes from the generate_mfa_params response
        // and we missed it? Check the FULL response
        r = await fetch('/account/account/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
        });
        data = await r.json();
        log.push('Full generate_mfa response: ' + JSON.stringify(data));
        
        // Check if there's a request_id in the response somewhere
        const fullStr = JSON.stringify(data);
        if (fullStr.includes('request_id') || fullStr.includes('requestId')) {
            log.push('FOUND request_id in response!');
        }
        
        // IDEA 3: Maybe the request_id IS part of the captcha widget rendering
        // In reCAPTCHA Enterprise, the "action" parameter might be used
        // Or maybe it's the grecaptcha widgetId
        
        // Load reCAPTCHA
        await new Promise(resolve => {
            const script = document.createElement('script');
            script.src = 'https://www.recaptcha.net/recaptcha/enterprise.js?render=' + sitekey;
            script.onload = () => setTimeout(resolve, 2000);
            document.head.appendChild(script);
            setTimeout(resolve, 8000);
        });
        
        if (window.grecaptcha && window.grecaptcha.enterprise) {
            let captchaToken = null;
            try {
                captchaToken = await new Promise((resolve, reject) => {
                    grecaptcha.enterprise.ready(async () => {
                        const t = await grecaptcha.enterprise.execute(sitekey, {action: 'bind_wallet'});
                        resolve(t);
                    });
                    setTimeout(() => reject('timeout'), 10000);
                });
            } catch(e) { log.push('captcha error: ' + e); }
            
            if (captchaToken) {
                log.push('Got captcha token: ' + captchaToken.substring(0, 40));
                
                // Try MANY different request_id values
                const attempts = [
                    txnId,
                    captchaToken.substring(0, 36),
                    captchaToken,  // Full token AS request_id
                    '0',
                    '1',
                    '',
                    'bind_wallet',
                    txnId + ':captcha',
                ];
                
                for (const reqId of attempts) {
                    r = await fetch('/account/mfa/txn/v1/verify_captcha?' + params, {
                        method: 'POST', headers: h,
                        body: JSON.stringify({txn_id: txnId, usage: 'bind_wallet', captcha_data: captchaToken, request_id: reqId})
                    });
                    data = await r.json();
                    
                    if (data.code === 0) {
                        log.push('SUCCESS with request_id: ' + reqId.substring(0, 30));
                        return {log, success: true, requestId: reqId.substring(0, 30)};
                    }
                    if (!data.message.includes('mismatch')) {
                        log.push('DIFFERENT ERROR with reqId=' + reqId.substring(0, 20) + ': ' + data.code + ' ' + data.message);
                    }
                }
                
                // Maybe request_id needs specific format — check verify_items for clues
                log.push('All request_id attempts failed with mismatch');
            }
        }
        
        return {log, txnId};
    }, FRESH_REFRESH, PARAMS, TARGET, SITEKEY);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
