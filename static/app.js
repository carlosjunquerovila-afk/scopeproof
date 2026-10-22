'use strict';
const $=id=>document.getElementById(id);
let token=new URLSearchParams(location.hash.slice(1)).get('token')||sessionStorage.getItem('scopeproof-session');
if(token){sessionStorage.setItem('scopeproof-session',token);history.replaceState(null,'',location.pathname);}
let state=null,busy=false;
const savedActions=['analyze','exportPrompt','importReview','invite','createDraft','refresh','reconcile','connectPayPal','export','deliveryReport','setFault','approve'];
function scopeEditor(){const criteria={};document.querySelectorAll('[data-scope-criterion]').forEach(e=>criteria[e.dataset.scopeCriterion]=e.value);return {name:$('scopeName').value,cents:String($('scopeCents').value),currency:$('scopeCurrency').value,criteria};}
function savedScope(s){const m=s.scope.milestones[0];return {name:m.name,cents:String(m.amount_cents),currency:s.scope.currency,criteria:s.criteria};}
function sameScope(a,b){return a.name===b.name&&a.cents===b.cents&&a.currency===b.currency&&Object.keys(a.criteria).length===Object.keys(b.criteria).length&&Object.keys(a.criteria).every(k=>a.criteria[k]===b.criteria[k]);}
function hasUnsavedEvidence(){return !!state&&state.role==='merchant'&&$('evidence').value!==state.artifacts['acceptance-report'];}
function hasUnsavedScope(){return !!state&&state.role==='merchant'&&!sameScope(scopeEditor(),savedScope(state));}
function updateEditing(){
 const evidenceDirty=hasUnsavedEvidence(),scopeDirty=hasUnsavedScope(),merchant=!!state&&state.role==='merchant';
 $('unsavedEvidence').hidden=!evidenceDirty;
 $('unsavedEvidenceText').textContent=evidenceDirty?'Unsaved report changes. Save the report or discard these edits to continue. Reviews and drafts still refer to saved version v'+state.revision+'.':'';
 $('unsavedScope').hidden=!scopeDirty;
 $('unsavedScopeText').textContent=scopeDirty?'Unsaved scope changes. Save the scope or discard these edits before review or billing. The displayed milestone amount still refers to the saved scope.':'';
 $('operationStatus').hidden=!busy;
 $('operationStatus').textContent=state?'Request in progress. You can keep editing; other actions will resume when it finishes.':'Loading the saved workspace. Editing will become available when it is ready.';
 savedActions.forEach(id=>$(id).disabled=!state||busy||evidenceDirty||scopeDirty);
 if(state?.outcome?.status==='CREATE_REJECTED')$('createDraft').disabled=true;
 ['saveEvidence','saveScope'].forEach(id=>$(id).disabled=!merchant||busy);
 ['discardEvidence','discardScope','loadComplete'].forEach(id=>$(id).disabled=!merchant);
 ['evidence','scopeName','scopeCents'].forEach(id=>$(id).readOnly=!merchant);
 $('scopeCurrency').disabled=!merchant;
 document.querySelectorAll('[data-scope-criterion]').forEach(e=>e.readOnly=!merchant);
}
function requireSavedEditors(){if(hasUnsavedEvidence()||hasUnsavedScope())throw new Error('Save or discard your report and scope edits before continuing. Your unsaved text has been kept.');}
$('evidence').oninput=updateEditing;
['scopeName','scopeCents'].forEach(id=>$(id).oninput=updateEditing);
$('scopeCurrency').onchange=updateEditing;
$('discardEvidence').onclick=()=>{if(!state)return;$('evidence').value=state.artifacts['acceptance-report'];updateEditing();notice('Restored saved report version v'+state.revision+'.',true);};
$('discardScope').onclick=()=>{if(!state)return;renderScope(savedScope(state));updateEditing();notice('Restored the saved scope.',true);};
window.addEventListener('beforeunload',event=>{if(hasUnsavedEvidence()||hasUnsavedScope()){event.preventDefault();event.returnValue='';}});
function renderScope(editor){
 $('scopeName').value=editor.name;$('scopeCents').value=editor.cents;$('scopeCurrency').value=editor.currency;
 $('scopeCriteria').replaceChildren();Object.entries(editor.criteria).forEach(([id,v])=>{const l=document.createElement('label');l.textContent=id;const i=document.createElement('input');i.dataset.scopeCriterion=id;i.value=v;i.oninput=updateEditing;l.append(i);$('scopeCriteria').append(l);});
}
function notice(text,ok=false){$('alert').textContent=text;$('alert').hidden=false;$('alert').className=ok?'success':'';}
async function api(path,data){
 if(!state&&path!=='/api/state')throw new Error('Wait for the workspace to finish loading.');
 if(!['/api/evidence','/api/scope'].includes(path))requireSavedEditors();
 const opts={headers:{Authorization:'Bearer '+(token||''),'X-ScopeProof-Request':'1'}};
 if(data!==undefined){opts.method='POST';opts.headers['Content-Type']='application/json';opts.body=JSON.stringify(data);}
 const response=await fetch(path,opts);const result=await response.json();
 if(!response.ok)throw new Error(result.error==='ARTIFACT_LIMIT'?'Report exceeds 20,000 characters or 50,000 UTF-8 bytes. The saved version was not changed.':result.error||'REQUEST_FAILED');return result;
}
function text(tag,value,cls){const e=document.createElement(tag);e.textContent=value;if(cls)e.className=cls;return e;}
function renderReview(s,merchant){
 const findings=new Map((s.analysis?.criteria||[]).map(c=>[c.criterion_id,c]));
 const names={evidence_found:'Supporting text found',missing:'Evidence missing',unclear:'Needs clarification'};
 const classes={evidence_found:'finding-supported',missing:'finding-missing',unclear:'finding-unclear'};
 $('analysis').replaceChildren();
 if(s.analysis){
  const provenance=s.analysis.provenance==='LOCAL_LEXICAL_RETRIEVAL_NOT_LLM'?'Local text search · no generative model used':s.analysis.provenance==='IMPORTED_REVIEW_UNVERIFIED_AUTHOR'?'Imported AI review · author unverified · no inference during import':'Analysis source: '+s.analysis.provenance+(s.analysis.model?' · '+s.analysis.model:'');
  $('analysis').append(text('p',provenance,'small'));
  const summary=document.createElement('div');summary.className='finding-summary';
  for(const [status,label] of [['evidence_found','with supporting text'],['missing','missing evidence'],['unclear','needing clarification']]){
   const count=Object.keys(s.criteria).filter(id=>findings.get(id)?.status===status).length;
   const item=document.createElement('div');item.className='finding-count';item.append(text('strong',String(count)),text('span',label));summary.append(item);
  }
  $('analysis').append(summary,text('p','Analysis findings only. Accepting the work is a separate human decision.','small'));
 }else $('analysis').append(text('p','No analysis for this saved version. Inspect the report against each agreed criterion.','small'));
 $('criteria').replaceChildren();
 Object.entries(s.criteria).forEach(([id,value])=>{
  const row=document.createElement('div');row.className='criterion';
  row.append(text('h3',value,'criterion-title'));
  const finding=findings.get(id);
  if(finding){
   row.append(text('span',names[finding.status]||'Needs clarification','finding-label '+(classes[finding.status]||'finding-unclear')));
   row.append(text('p',finding.reason,'finding-reason'));
   if(finding.quote){
    row.append(text('p',finding.evidence_id==='acceptance-report'?'Quoted from the delivery report':'Quoted from '+finding.evidence_id,'quote-source'));
    row.append(text('blockquote',finding.quote,'finding-quote'));
   }
  }else row.append(text('p','No finding for this criterion yet.','small'));
  const label=document.createElement('label');label.className='check criterion-decision';
  const checkbox=document.createElement('input');checkbox.type='checkbox';checkbox.dataset.criterion=id;checkbox.disabled=merchant;checkbox.checked=s.approved_current;
  label.append(checkbox,text('span',merchant?(s.approved_current?'Accepted by the reviewer for this version':'Awaiting the reviewer’s acceptance'):'I inspected the work and accept this criterion.'));
  row.append(label);$('criteria').append(row);
 });
}
function show(s,editors={}){
 const pendingText=Object.hasOwn(editors,'evidence')?editors.evidence:(hasUnsavedEvidence()?$('evidence').value:null);
 const pendingScope=Object.hasOwn(editors,'scope')?editors.scope:(hasUnsavedScope()?scopeEditor():null);
 state=s;const merchant=s.role==='merchant',demo=s.mode==='demo';
 document.querySelectorAll('.merchant-only').forEach(e=>e.hidden=!merchant);
 $('environment').textContent=demo?'LOCAL SIMULATOR · NOT PAYPAL':'PAYPAL SANDBOX · NO LIVE MONEY';
 $('role').textContent=merchant?'Merchant session':'Review session';
 const m=s.scope.milestones[0];$('milestone').textContent=m.name;
 renderScope(pendingScope===null?savedScope(s):pendingScope);
 $('amount').textContent=new Intl.NumberFormat('en-IE',{style:'currency',currency:s.scope.currency}).format(m.amount_cents/100);
 $('recipient').textContent='Recipient: '+s.scope.recipient;$('revision').textContent='Scope revision '+s.scope.revision+' · Evidence version '+s.revision;
 $('evidenceVersion').textContent='v'+s.revision;$('evidence').value=pendingText===null?s.artifacts['acceptance-report']:pendingText;$('evidence').readOnly=!merchant;
 $('modeNotice').textContent=demo?'SIMULATOR: the browser talks to the real local application; provider responses are deliberately simulated. No PayPal connection, customer notification or LLM inference is implied.':'SANDBOX: draft-only integration. No invoice is sent and no payment is captured. Credentials must be configured locally; provider success is not assumed.';
 renderReview(s,merchant);
 $('reviewerActions').hidden=merchant;$('snapshot').textContent='Version fingerprint: '+s.snapshot;
 $('approvalStatus').textContent=s.approved_current?'Current version explicitly accepted':'Current version has no valid acceptance';
 const outcome=s.outcome, status=outcome?.status;const priorVersion=!!outcome&&s.outcome_snapshot!==s.snapshot;
 const historical=status==='VERIFIED_DRAFT'&&!s.provider_record_fresh_for_session;
 const rejected=status==='CREATE_REJECTED';
 const rejectedHttp=/^PAYPAL_DRAFT_HTTP_(400|401|403|404|405|406|415|422)$/.exec(outcome?.reason||'')?.[1];
 $('draftTitle').textContent=rejected?(priorVersion?'Previous version draft request rejected':'Draft request rejected'):priorVersion?'Previous version draft · '+status:status==='VERIFIED_DRAFT'?(historical?'Previously verified draft · refresh required':demo?'Simulated draft verified':'Sandbox draft verified'):status||'Not invoiced';
 $('invoiceId').textContent=outcome?.invoice_id||'';
 $('draftDescription').textContent=rejected?'PayPal Sandbox rejected the create request'+(rejectedHttp?' (HTTP '+rejectedHttp+')':'')+'. Review the request and account setup manually. This attempt is closed and cannot be retried or reconciled here.':priorVersion?'This provider record belongs to earlier evidence. It is not acceptance of the current version; review is required.':status==='UNKNOWN'||status==='IN_FLIGHT'?'Outcome unknown. Another creation is blocked; reconcile the existing intent first.':status==='REVIEW_REQUIRED'?'Provider fields differ from the approved scope. Manual investigation required; no automatic retry.':status==='VERIFIED_DRAFT'?(historical?'Recovered from the local record. This process has not re-read the provider; connect and refresh explicitly. Not sent or paid.':'Read-back matched the agreed amount, recipient and line. Draft only — not sent or paid.'):'Approval is required before a draft can be created.';
 $('draftConsentText').textContent=demo?'Create a simulated draft. Do not send a payment request.':'Create one PayPal SANDBOX draft. Do not send it or move money.';
 $('createDraft').textContent=rejected?'Draft request rejected':priorVersion?'Review current version before proceeding':status==='VERIFIED_DRAFT'?'Re-read existing draft':'Prepare draft';
 $('reconcileBox').hidden=!merchant||!['UNKNOWN','IN_FLIGHT','CREATED_UNVERIFIED'].includes(status);
 $('invoiceCandidate').hidden=demo;$('faultPanel').hidden=!merchant||!demo;
 $('connectionPanel').hidden=!merchant||demo;
 $('connectionStatus').textContent=s.paypal_connected?'Sandbox authentication succeeded in this process. No invoice created by connecting.':'Not connected. Authentication has not been validated.';
 $('mockCount').textContent=demo?'Persistent simulated drafts: '+s.demo_invoice_count:'';
 $('events').replaceChildren(...s.events.slice().reverse().map(e=>text('p',new Date(e.at).toLocaleString()+' · v'+e.revision+' · '+e.type)));
 updateEditing();
}
async function action(f,initial=false){
 if(busy)return;
 if(!state&&!initial){notice('Wait for the workspace to finish loading.');return;}
 busy=true;updateEditing();
 try{$('alert').hidden=true;await f();}catch(e){notice(e.message);}finally{busy=false;updateEditing();}
}
$('saveScope').onclick=()=>action(async()=>{const submitted=scopeEditor();const cents=Number(submitted.cents);if(!Number.isSafeInteger(cents))throw new Error('Integer cents required');const next=await api('/api/scope',{revision:state.revision,name:submitted.name,amount_cents:cents,currency:submitted.currency,criteria:submitted.criteria});const current=scopeEditor();show(next,{scope:sameScope(current,submitted)?null:current});notice(hasUnsavedScope()?'Saved the submitted scope. Newer scope edits are still unsaved and have been kept.':'Scope revised. New acceptance is required.',true);});
$('saveEvidence').onclick=()=>action(async()=>{const submitted=$('evidence').value;const next=await api('/api/evidence',{revision:state.revision,artifacts:{'acceptance-report':submitted}});show(next,{evidence:$('evidence').value!==submitted?$('evidence').value:null});notice(hasUnsavedEvidence()?'Saved the submitted report. Newer edits are still unsaved and have been kept.':'Saved a new version. All previous approval is invalidated.',true);});
$('loadComplete').onclick=()=>{if(!state||state.role!=='merchant')return;$('evidence').value='Responsive layout verified at 375, 768 and 1440 pixels.\nContact form submission tested successfully in the staging environment.\nAccessibility review has no critical issues in the supplied report.';updateEditing();notice('Synthetic complete sample loaded into the editor. Save it as a new version before review.',true);};
$('engine').onchange=()=>{$('modelRow').hidden=$('engine').value!=='ollama';$('importPanel').hidden=$('engine').value!=='imported';$('analyze').hidden=$('engine').value==='imported';};
$('exportPrompt').onclick=()=>action(async()=>{const out=await api('/api/review-prompt');$('promptText').value=out.prompt;$('promptText').hidden=false;$('promptText').select();});
$('importReview').onclick=()=>action(async()=>{show(await api('/api/import-analysis',{package_text:$('reviewJson').value}));notice('Version and quotations validated. Human review is still required.',true);});
$('analyze').onclick=()=>action(async()=>{show(await api('/api/analyze',{engine:$('engine').value,model:$('model').value||null}));});
$('invite').onclick=()=>action(async()=>{requireSavedEditors();const win=window.open('about:blank','_blank');const data=await api('/api/invite',{});if(win){win.opener=null;win.location.href=data.url;}else notice('Your browser blocked the new review window. Allow popups for this local application.');});
$('approve').onclick=()=>action(async()=>{const decisions={};document.querySelectorAll('[data-criterion]').forEach(e=>decisions[e.dataset.criterion]=e.checked);show(await api('/api/approve',{snapshot:state.snapshot,decisions,acknowledgement:$('ack').checked}));notice('Accepted this version only. You have not created or sent an invoice.',true);});
$('createDraft').onclick=()=>action(async()=>{if(state.outcome?.status==='CREATE_REJECTED')throw new Error('The provider rejected this draft request. This attempt cannot be retried; review its request and account setup manually.');show(await api('/api/draft',{snapshot:state.snapshot,confirm:$('draftConsent').checked}));});
$('refresh').onclick=()=>action(async()=>show(await api('/api/state')));
$('reconcile').onclick=()=>action(async()=>show(await api('/api/reconcile',{invoice_id:$('invoiceCandidate').value||null})));
$('setFault').onclick=()=>action(async()=>{await api('/api/fault',{fault:$('fault').value});notice('Simulator condition selected: '+$('fault').value,true);});
$('connectPayPal').onclick=()=>action(async()=>{
 const payload={client_id:$('clientId').value,secret:$('clientSecret').value,seller:$('sellerEmail').value,buyer:$('buyerEmail').value,confirm:$('connectConsent').checked};
 try{show(await api('/api/connect-paypal',payload));notice('Sandbox authentication checked. Review the updated recipient before creating a draft.',true);}finally{$('clientId').value='';$('clientSecret').value='';payload.secret='';payload.client_id='';}
});
$('export').onclick=()=>action(async()=>{const data=await api('/api/export');const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='scopeproof-local-record.json';a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
$('deliveryReport').onclick=()=>action(async()=>{
 const data=await api('/api/delivery-report');
 // Only the local authenticated server creates the escaped, script-free document.
 const blob=new Blob([data.html],{type:'text/html;charset=utf-8'});
 const url=URL.createObjectURL(blob),a=document.createElement('a');a.href=url;a.download=data.filename;a.click();
 setTimeout(()=>URL.revokeObjectURL(url),1000);
 notice('Downloaded the saved-version delivery record. Open it in your browser to read or print to PDF. Review its environment and version before sharing.',true);
});
updateEditing();
action(async()=>show(await api('/api/state')),true);
