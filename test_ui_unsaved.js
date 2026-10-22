'use strict';
// Controller integration: execute unmodified app.js with a DOM/transport test adapter.
// This checks behavior, not browser rendering, accessibility or browser-to-HTTP wiring.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const {spawnSync}=require('node:child_process');
const source=fs.readFileSync(__dirname+'/static/app.js','utf8');
const html=fs.readFileSync(__dirname+'/static/index.html','utf8');
const init=spawnSync('python3',['-c',"import json,tempfile; from workflow import Workspace; t=tempfile.TemporaryDirectory(); w=Workspace(t.name); print(json.dumps(w.state(w.owner_token)))"],{cwd:__dirname,encoding:'utf8'});
assert.equal(init.status,0,init.stderr);const initial=JSON.parse(init.stdout);
const copy=x=>JSON.parse(JSON.stringify(x));
const tick=()=>new Promise(r=>setImmediate(r));
async function setup(options={}){
 const nodes=new Map(),all=[],calls=[],listeners={},blobs=[],downloads=[];let server=copy(initial),nextResponse=null,popups=0,releaseInitial=null;
 class El{constructor(tag='div'){this.tag=tag;this.children=[];this.value='';this.dataset={};this.hidden=false;this.disabled=false;this.textContent='';all.push(this);}append(...v){this.children.push(...v);}replaceChildren(...v){this.children=v;}select(){}click(){if(this.tag==='a')downloads.push({href:this.href,filename:this.download});return this.onclick?.();}}
 for(const match of html.matchAll(/<[^>]*\bid="([^"]+)"[^>]*>/g)){const e=new El();e.disabled=/\bdisabled\b/.test(match[0]);e.readOnly=/\breadonly\b/.test(match[0]);nodes.set(match[1],e);}
 nodes.get('engine').value='local_search';
 const env={URLSearchParams,URL:{createObjectURL(blob){blobs.push(blob);return 'blob:controller-test-'+blobs.length;},revokeObjectURL(){}},Intl,Date,JSON,Number,Error,Blob,setTimeout,location:{hash:'#token=test',pathname:'/'},history:{replaceState(){}},sessionStorage:{getItem(){return null;},setItem(){}},document:{getElementById(id){assert(nodes.has(id),'Unknown DOM node '+id);return nodes.get(id);},createElement(tag){return new El(tag);},querySelectorAll(selector){const key=selector==='[data-criterion]'?'criterion':selector==='[data-scope-criterion]'?'scopeCriterion':null;const connected=new Set();const walk=e=>{if(!e||typeof e!=='object'||connected.has(e))return;connected.add(e);e.children.forEach(walk);};nodes.forEach(walk);return key?[...connected].filter(x=>x.dataset[key]!==undefined):[];}},window:{addEventListener(name,cb){listeners[name]=cb;},open(){popups++;return {opener:null,location:{}};}},fetch:async(path,opts)=>{
  calls.push({path,body:opts.body?JSON.parse(opts.body):null});
  if(options.deferInitial&&calls.length===1)return new Promise(r=>{releaseInitial=()=>r({ok:true,json:async()=>copy(server)});});
  if(nextResponse){const fn=nextResponse;nextResponse=null;return fn(path,opts);}
  if(path==='/api/evidence'){server.artifacts=JSON.parse(opts.body).artifacts;server.revision++;server.approved_current=false;}
  if(path==='/api/scope'){const d=JSON.parse(opts.body);server.scope.milestones[0].name=d.name;server.scope.milestones[0].amount_cents=d.amount_cents;server.scope.currency=d.currency;server.criteria=d.criteria;server.revision++;server.scope.revision++;server.approved_current=false;}
  return {ok:true,json:async()=>copy(server)};
 }};
 vm.createContext(env);vm.runInContext(source,env,{filename:'static/app.js'});await tick();
 return {nodes,calls,listeners,blobs,downloads,edit(value){nodes.get('evidence').value=value;nodes.get('evidence').oninput();},setResponse(fn){nextResponse=fn;},getServer:()=>copy(server),popups:()=>popups,releaseInitial:async()=>{releaseInitial();await tick();},editScope(id,value){nodes.get(id).value=value;(nodes.get(id).oninput||nodes.get(id).onchange)();},scopeCriteria:()=>env.document.querySelectorAll('[data-scope-criterion]')};
}
(async()=>{
 const results=[];
 {
  const t=await setup();t.edit('Unsaved customer report');assert.equal(t.nodes.get('unsavedEvidence').hidden,false);assert.match(t.nodes.get('unsavedEvidenceText').textContent,/saved version v1/);
  for(const id of ['analyze','exportPrompt','importReview','invite','createDraft','refresh','connectPayPal','export'])assert.equal(t.nodes.get(id).disabled,true,id);
  assert.equal(t.nodes.get('saveEvidence').disabled,false);results.push('unsaved_edits_visible_and_stale_actions_disabled');
  const count=t.calls.length;await t.nodes.get('analyze').onclick();assert.equal(t.calls.length,count);assert.equal(t.nodes.get('evidence').value,'Unsaved customer report');results.push('direct_stale_analysis_cannot_bypass_guard');
  await t.nodes.get('invite').onclick();assert.equal(t.popups(),0);assert.equal(t.calls.length,count);results.push('unsaved_review_does_not_open_empty_window');
  let prevented=false;const event={preventDefault(){prevented=true;}};t.listeners.beforeunload(event);assert.equal(prevented,true);assert.equal(event.returnValue,'');results.push('navigation_warns_about_unsaved_report');
  await t.nodes.get('saveEvidence').onclick();assert.equal(t.nodes.get('evidence').value,'Unsaved customer report');assert.equal(t.getServer().artifacts['acceptance-report'],'Unsaved customer report');assert.equal(t.nodes.get('unsavedEvidence').hidden,true);assert.equal(t.nodes.get('analyze').disabled,false);assert.equal(t.nodes.get('evidenceVersion').textContent,'v2');results.push('saving_keeps_text_and_enables_current_version_actions');
  t.edit('Changed again');t.nodes.get('discardEvidence').onclick();assert.equal(t.nodes.get('evidence').value,'Unsaved customer report');assert.equal(t.nodes.get('unsavedEvidence').hidden,true);results.push('explicit_discard_restores_last_saved_report');
 }
 {
  const t=await setup();t.nodes.get('loadComplete').onclick();assert.equal(t.nodes.get('unsavedEvidence').hidden,false);assert.equal(t.nodes.get('analyze').disabled,true);assert.match(t.nodes.get('evidence').value,/Responsive layout/);results.push('sample_loading_requires_save_before_review');
  const text=t.nodes.get('evidence').value;t.setResponse(async()=>({ok:false,json:async()=>({error:'ARTIFACT_LIMIT'})}));await t.nodes.get('saveEvidence').onclick();assert.equal(t.nodes.get('evidence').value,text);assert.equal(t.nodes.get('unsavedEvidence').hidden,false);results.push('failed_save_preserves_unsaved_text');
 }
 {
  const t=await setup();let release;t.setResponse(()=>new Promise(r=>{release=r;}));const action=t.nodes.get('analyze').onclick();await tick();t.edit('Typed while analysis was pending');release({ok:true,json:async()=>t.getServer()});await action;assert.equal(t.nodes.get('evidence').value,'Typed while analysis was pending');assert.equal(t.nodes.get('unsavedEvidence').hidden,false);results.push('late_analysis_response_does_not_erase_new_edits');
 }
 {
  const t=await setup();t.edit('First submitted text');let release;t.setResponse(()=>new Promise(r=>{release=r;}));const action=t.nodes.get('saveEvidence').onclick();await tick();t.edit('Newer draft during save');const saved=t.getServer();saved.artifacts['acceptance-report']='First submitted text';saved.revision=2;release({ok:true,json:async()=>saved});await action;assert.equal(t.nodes.get('evidence').value,'Newer draft during save');assert.equal(t.nodes.get('evidenceVersion').textContent,'v2');assert.equal(t.nodes.get('unsavedEvidence').hidden,false);assert.match(t.nodes.get('alert').textContent,/Newer edits/);results.push('late_save_response_keeps_more_recent_edits');
 }
 {
  const t=await setup();const original=t.nodes.get('evidence').value;t.edit('Submitted new version');let release;t.setResponse(()=>new Promise(r=>{release=r;}));const action=t.nodes.get('saveEvidence').onclick();await tick();t.edit(original);const saved=t.getServer();saved.artifacts['acceptance-report']='Submitted new version';saved.revision=2;release({ok:true,json:async()=>saved});await action;assert.equal(t.nodes.get('evidence').value,original);assert.equal(t.nodes.get('unsavedEvidence').hidden,false);results.push('reverting_to_old_text_during_save_is_preserved_as_new_unsaved_edit');
 }
 {
  const t=await setup({deferInitial:true});assert.equal(t.nodes.get('evidence').readOnly,true);assert.equal(t.nodes.get('scopeName').readOnly,true);assert.equal(t.nodes.get('scopeCents').readOnly,true);assert.equal(t.nodes.get('scopeCurrency').disabled,true);assert.equal(t.nodes.get('saveEvidence').disabled,true);assert.equal(t.nodes.get('loadComplete').disabled,true);await t.nodes.get('saveEvidence').onclick();assert.equal(t.calls.length,1);await t.releaseInitial();assert.equal(t.nodes.get('evidence').readOnly,false);assert.equal(t.nodes.get('scopeCurrency').disabled,false);assert.equal(t.nodes.get('saveEvidence').disabled,false);results.push('editors_locked_until_initial_state_has_loaded');
 }
 {
  const t=await setup();let release;t.setResponse(()=>new Promise(r=>{release=r;}));const staleRead=t.nodes.get('analyze').onclick();await tick();t.edit('Version two typed while v1 request is pending');assert.equal(t.nodes.get('evidence').readOnly,false);assert.equal(t.nodes.get('saveEvidence').disabled,true);assert.equal(t.nodes.get('saveScope').disabled,true);assert.equal(t.nodes.get('refresh').disabled,true);const calls=t.calls.length;await t.nodes.get('saveEvidence').onclick();await t.nodes.get('refresh').onclick();assert.equal(t.calls.length,calls);release({ok:true,json:async()=>t.getServer()});await staleRead;assert.equal(t.nodes.get('evidence').value,'Version two typed while v1 request is pending');assert.equal(t.nodes.get('saveEvidence').disabled,false);await t.nodes.get('saveEvidence').onclick();assert.equal(t.nodes.get('evidenceVersion').textContent,'v2');assert.equal(t.nodes.get('evidence').value,'Version two typed while v1 request is pending');results.push('pending_v1_request_cannot_overlap_and_roll_back_v2_save');
 }
 {
  for(const [id,value] of [['scopeName','Revised milestone'],['scopeCents','19900'],['scopeCurrency','USD']]){
   const t=await setup();t.editScope(id,value);assert.equal(t.nodes.get('unsavedScope').hidden,false,id);assert.equal(t.nodes.get('createDraft').disabled,true);assert.equal(t.nodes.get('analyze').disabled,true);assert.equal(t.nodes.get('refresh').disabled,true);const calls=t.calls.length;await t.nodes.get('createDraft').onclick();await t.nodes.get('analyze').onclick();await t.nodes.get('refresh').onclick();assert.equal(t.calls.length,calls);assert.equal(t.nodes.get(id).value,value);t.nodes.get('discardScope').onclick();assert.equal(t.nodes.get('unsavedScope').hidden,true);assert.equal(t.nodes.get('createDraft').disabled,false);
  }
  results.push('unsaved_name_amount_and_currency_block_stale_review_and_draft_until_explicit_discard');
 }
 {
  const t=await setup();const criterion=t.scopeCriteria()[0];criterion.value='Revised criterion';criterion.oninput();assert.equal(t.nodes.get('unsavedScope').hidden,false);assert.equal(t.nodes.get('invite').disabled,true);await t.nodes.get('saveScope').onclick();assert.equal(t.nodes.get('unsavedScope').hidden,true);assert.equal(t.getServer().criteria[criterion.dataset.scopeCriterion],'Revised criterion');assert.equal(t.nodes.get('evidenceVersion').textContent,'v2');results.push('criterion_edits_are_saved_explicitly_before_review');
 }
 {
  const t=await setup();t.editScope('scopeCents','19900');t.edit('Pending report text');assert.equal(t.nodes.get('saveScope').disabled,false);assert.equal(t.nodes.get('saveEvidence').disabled,false);await t.nodes.get('saveScope').onclick();assert.equal(t.nodes.get('scopeCents').value,'19900');assert.equal(t.nodes.get('evidence').value,'Pending report text');assert.equal(t.nodes.get('unsavedScope').hidden,true);assert.equal(t.nodes.get('unsavedEvidence').hidden,false);assert.equal(t.nodes.get('createDraft').disabled,true);await t.nodes.get('saveEvidence').onclick();assert.equal(t.nodes.get('unsavedEvidence').hidden,true);assert.equal(t.nodes.get('scopeCents').value,'19900');assert.equal(t.getServer().scope.milestones[0].amount_cents,19900);assert.equal(t.nodes.get('evidenceVersion').textContent,'v3');results.push('both_editors_can_be_saved_sequentially_without_losing_the_other');
 }
 {
  const t=await setup();t.editScope('scopeCents','19900');let release;t.setResponse(()=>new Promise(r=>{release=r;}));const action=t.nodes.get('saveScope').onclick();await tick();t.editScope('scopeCents','29900');const saved=t.getServer();saved.scope.milestones[0].amount_cents=19900;saved.revision=2;release({ok:true,json:async()=>saved});await action;assert.equal(t.nodes.get('scopeCents').value,'29900');assert.equal(t.nodes.get('unsavedScope').hidden,false);assert.equal(t.nodes.get('createDraft').disabled,true);assert.match(t.nodes.get('alert').textContent,/Newer scope edits/);results.push('late_scope_save_preserves_newer_amount_edit');
 }
 {
  const t=await setup();let release;t.setResponse(()=>new Promise(r=>{release=r;}));const action=t.nodes.get('refresh').onclick();await tick();t.editScope('scopeName','Edited during refresh');t.editScope('scopeCurrency','USD');const criterion=t.scopeCriteria()[0];criterion.value='Edited criterion during refresh';criterion.oninput();release({ok:true,json:async()=>t.getServer()});await action;assert.equal(t.nodes.get('scopeName').value,'Edited during refresh');assert.equal(t.nodes.get('scopeCurrency').value,'USD');assert.equal(t.scopeCriteria()[0].value,'Edited criterion during refresh');assert.equal(t.nodes.get('unsavedScope').hidden,false);results.push('late_refresh_preserves_name_currency_and_criterion_edits');
 }
 {
  const t=await setup();t.editScope('scopeCents','19900');t.setResponse(async()=>({ok:false,json:async()=>({error:'SCOPE_FORMAT'})}));await t.nodes.get('saveScope').onclick();assert.equal(t.nodes.get('scopeCents').value,'19900');assert.equal(t.nodes.get('unsavedScope').hidden,false);assert.equal(t.nodes.get('saveScope').disabled,false);assert.equal(t.nodes.get('operationStatus').hidden,true);results.push('failed_scope_save_retains_edits_and_releases_busy_lock');
 }
 {
  const t=await setup(),review=t.getServer();review.role='reviewer';review.approved_current=false;
  review.analysis={provenance:'IMPORTED_REVIEW_UNVERIFIED_AUTHOR',criteria:Object.keys(review.criteria).map((id,i)=>({criterion_id:id,status:['evidence_found','missing','unclear'][i],reason:'Review finding '+id,evidence_id:'acceptance-report',quote:'Quoted passage '+id}))};
  t.setResponse(async()=>({ok:true,json:async()=>review}));await t.nodes.get('refresh').onclick();
  const flatten=e=>[e.textContent,...e.children.map(flatten)].join(' ');
  const inputs=e=>[...(e.tag==='input'?[e]:[]),...e.children.flatMap(inputs)];
  t.nodes.get('criteria').children.forEach((row,i)=>{const id=Object.keys(review.criteria)[i],content=flatten(row);assert(content.includes(review.criteria[id]));assert(content.includes('Quoted passage '+id));assert(content.includes(['Supporting text found','Evidence missing','Needs clarification'][i]));const check=inputs(row)[0];assert.equal(check.checked,false);assert.equal(check.disabled,false);});
  assert.match(flatten(t.nodes.get('analysis')),/Accepting the work is a separate human decision/);assert.equal(t.nodes.get('approvalStatus').textContent,'Current version has no valid acceptance');
  results.push('criterion_findings_and_quotes_are_paired_without_accepting_the_work');
 }
 {
  const t=await setup(),rejected=t.getServer();rejected.outcome={status:'CREATE_REJECTED',reason:'PAYPAL_DRAFT_HTTP_422'};rejected.outcome_snapshot=rejected.snapshot;
  t.setResponse(async()=>({ok:true,json:async()=>rejected}));await t.nodes.get('refresh').onclick();
  assert.equal(t.nodes.get('draftTitle').textContent,'Draft request rejected');assert.match(t.nodes.get('draftDescription').textContent,/HTTP 422/);assert.equal(t.nodes.get('createDraft').disabled,true);assert.equal(t.nodes.get('reconcileBox').hidden,true);
  const calls=t.calls.length;await t.nodes.get('createDraft').onclick();assert.equal(t.calls.length,calls);assert.equal(t.nodes.get('createDraft').disabled,true);
  rejected.outcome.reason='private-unexpected-provider-body';t.setResponse(async()=>({ok:true,json:async()=>rejected}));await t.nodes.get('refresh').onclick();assert(!t.nodes.get('draftDescription').textContent.includes('private-unexpected-provider-body'));
  results.push('confirmed_provider_rejection_blocks_creation_and_reconciliation_without_exposing_raw_reason');
 }
 {
  const t=await setup();t.edit('Unsaved handover text');const calls=t.calls.length;assert.equal(t.nodes.get('deliveryReport').disabled,true);await t.nodes.get('deliveryReport').onclick();assert.equal(t.calls.length,calls);assert.equal(t.downloads.length,0);results.push('delivery_report_cannot_export_stale_saved_text_while_editor_is_dirty');
 }
 {
  const t=await setup();const report={filename:'scopeproof-delivery-v1-test.html',html:'<!doctype html><title>Saved delivery</title>',snapshot:initial.snapshot};t.setResponse(async()=>({ok:true,json:async()=>report}));await t.nodes.get('deliveryReport').onclick();assert.equal(t.calls.at(-1).path,'/api/delivery-report');assert.equal(t.downloads[0].filename,report.filename);assert.equal(await t.blobs[0].text(),report.html);assert.match(t.nodes.get('alert').textContent,/saved-version delivery record/);results.push('delivery_download_uses_server_document_and_filename_without_rendering_it_in_the_app');
 }
 {
  const t=await setup();t.setResponse(async()=>({ok:false,json:async()=>({error:'AUTH_REQUIRED_OR_EXPIRED'})}));await t.nodes.get('deliveryReport').onclick();assert.equal(t.downloads.length,0);assert.equal(t.nodes.get('deliveryReport').disabled,false);results.push('failed_delivery_export_does_not_download_a_partial_record');
 }
 console.log(JSON.stringify({passed:true,checks:results,check_count:results.length,transport:'DOM/HTTP adapters; actual app.js; initial state from actual Python Workspace',browser_rendering_tested:false,external_calls:0},null,2));
})().catch(e=>{console.error(e);process.exitCode=1;});
