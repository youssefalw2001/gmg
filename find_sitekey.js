const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const FRESH_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiJhMWQ2ZGZlNC1iODhmLTRjNTgtOThkYi00MmU0MmFhMjRmZDYiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ0NDA3LCJpYXQiOjE3ODQxNTI0MDcsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiMDYyNTVmMTAtNmVkZi00YmRiLWFiNjAtZGEzZDQwNmQ4YTgzIiwibmJmIjoxNzg0MTUyNDA3LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiYTFkNmRmZTQtYjg4Zi00YzU4LTk4ZGItNDJlNDJhYTI0ZmQ2IiwidmVyIjoiMS4wIn0.uCsdhElzc2R3WZhvzcnHx3ZsvBRmzVA7dKT5J2fK92PDsg5troyv9_4ndY3yaLpgXwrEPsSyS66dsKrKebghmQ';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&client_id=gmgn_web_20260715-2161-18d5b10&app_ver=20260715-2161-18d5b10&from_app=gmgn';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';

(async () => {
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    
    // Patch turnstile BEFORE page loads
    await page.evaluateOnNewDocument(() => {
        window.__turnstile_calls = [];
        window.__turnstile_tokens = [];
        
        const checkInterval = setInterval(() => {
            if (window.turnstile && !window.turnstile.__patched) {
                window.turnstile.__patched = true;
                const origRender = window.turnstile.render;
                window.turnstile.render = function(el, opts) {
                    window.__turnstile_calls.push({sitekey: opts.sitekey, action: opts.action});
                    const origCb = opts.callback;
                    opts.callback = (token) => {
                        window.__turnstile_tokens.push(token);
                        if (origCb) origCb(token);
                    };
                    return origRender.apply(this, arguments);
                };
            }
        }, 50);
    });
    
    await page.goto('https://gmgn.ai/settings/wallet', {waitUntil: 'networkidle2', timeout: 20000});
    await new Promise(r => setTimeout(r, 3000));
    
    // Login
    await page.evaluate(async (refresh) => {
        let r = await fetch('/account/account/refresh_access_token', {
            method: 'POST', headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({refresh_token: refresh})
        });
        let data = await r.json();
        if (data.code === 0) {
            const token = data.data.data.token;
            localStorage.setItem('access_token', token);
            localStorage.setItem('token_info', JSON.stringify({access_token: token, refresh_token: refresh}));
        }
    }, FRESH_REFRESH);
    
    // Reload after login
    await page.reload({waitUntil: 'networkidle2', timeout: 15000});
    await new Promise(r => setTimeout(r, 5000));
    
    // Look for bind/connect buttons and click them
    const clicked = await page.evaluate(() => {
        const allEls = document.querySelectorAll('button, a, [role=button], span');
        const found = [];
        for (const el of allEls) {
            const text = (el.textContent || '').toLowerCase().trim();
            if (text.includes('bind') || text.includes('connect external') || text === 'connect wallet') {
                found.push(text.substring(0, 40));
                el.click();
            }
        }
        return found;
    });
    
    console.log('Clicked:', clicked);
    await new Promise(r => setTimeout(r, 5000));
    
    // Check turnstile renders
    const result = await page.evaluate(() => ({
        calls: window.__turnstile_calls,
        tokens: window.__turnstile_tokens,
        pageUrl: location.href
    }));
    
    console.log('Result:', JSON.stringify(result, null, 2));
    
    if (result.calls.length > 0) {
        console.log('\n💀💀💀 SITEKEY FOUND: ' + result.calls[0].sitekey);
    }
    if (result.tokens.length > 0) {
        console.log('\n💀💀💀 TOKEN OBTAINED: ' + result.tokens[0]);
    }
    
    await browser.close();
})();
