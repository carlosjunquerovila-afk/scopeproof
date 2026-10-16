#!/usr/bin/env python3
"""Render a standalone factual report from saved run evidence. No AI inference."""
from html import escape
import argparse
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--replay-result', type=Path, default=root / 'replay_run.json',
                    help='Recorded replay JSON, including an external --output result.')
args = parser.parse_args()
fresh = json.loads((root / 'fresh_run.json').read_text())
replay_bytes = args.replay_result.read_bytes()
replay = json.loads(replay_bytes)
assert fresh['mode'] == 'FRESH_EXTERNAL_CHATGPT_IMPORT'
assert replay['mode'] == 'FROZEN_EXTERNAL_RESPONSE_REPLAY'
assert fresh['all_passed'] is True and replay['all_passed'] is True, 'Do not render failed run as success'
assert fresh['prompt_sha256'] == replay['prompt_sha256']
assert fresh['response_sha256'] == replay['response_sha256']
before = json.loads((root / 'incomplete_review.json').read_text())['analysis']['criteria']
after = json.loads((root / 'complete_review.json').read_text())['analysis']['criteria']
rows = []
for cid in ('responsive', 'contact', 'accessibility'):
    a = next(x for x in before if x['criterion_id'] == cid)
    b = next(x for x in after if x['criterion_id'] == cid)
    rows.append(f'<tr><th>{escape(cid.title())}</th><td><b>{escape(a["status"])}</b><blockquote>{escape(a["quote"] or "No quotation")}</blockquote></td><td><b>{escape(b["status"])}</b><blockquote>{escape(b["quote"] or "No quotation")}</blockquote></td></tr>')
request_rows = ''.join('<tr><td>'+str(n)+'</td><td>'+escape(r['method']+' '+r['path'])+'</td><td>'+str(r['http_status'])+'</td><td>'+escape(r['error'] or r['outcome_status'] or 'OK')+'</td></tr>' for n,r in enumerate(fresh['http_requests'],1))
fresh_prompts = [r for r in fresh['http_requests'] if r['path'] == '/api/review-prompt']
replay_prompts = [r for r in replay['http_requests'] if r['path'] == '/api/review-prompt']
fresh_evidence = [r for r in fresh['http_requests'] if r['path'] == '/api/evidence']
replay_evidence = [r for r in replay['http_requests'] if r['path'] == '/api/evidence']
assert len(fresh_prompts) == len(replay_prompts) == 2
snapshot_rows = []
for i, label in enumerate(('Incomplete report', 'Corrected report')):
    snap = fresh_prompts[i]['snapshot']
    assert snap == replay_prompts[i]['snapshot']
    assert fresh_evidence[i]['revision'] == replay_evidence[i]['revision']
    snapshot_rows.append('<tr><th>'+label+'</th><td>'+str(fresh_evidence[i]['revision'])+
                         '</td><td><code>'+escape(snap)+'</code></td><td>Identical</td></tr>')
replay_record = ('<h2>Recorded versions and snapshots</h2><p>Original fresh runtime: <code>'+
    escape(fresh['app_version'])+'</code>. Latest recorded replay runtime: <code>'+
    escape(replay['app_version'])+'</code>. These are separate runs; replay uses saved model responses.</p>'+
    '<p class="muted">Replay recorded: '+escape(replay['started_at'])+' → '+escape(replay['completed_at'])+
    '</p><table><thead><tr><th>Evidence stage</th><th>Revision</th><th>Exported snapshot</th><th>Replay binding</th>'+
    '</tr></thead><tbody>'+''.join(snapshot_rows)+'</tbody></table>')
html = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ScopeProof — fresh AI import evidence</title><style>
:root{color:#172130;background:#f6f8fb;font:16px/1.55 system-ui,sans-serif}body{max-width:1100px;margin:0 auto;padding:48px 24px 64px}main{background:white;border:1px solid #dce3ec;border-radius:20px;padding:44px}h1{font-size:40px;line-height:1.1;letter-spacing:-1px;margin:16px 0}h2{font-size:23px;margin:38px 0 14px}.eyebrow{color:#3261be;font-weight:700;letter-spacing:.12em;font-size:12px}.lede{font-size:19px;color:#46556b;max-width:780px}.badges{display:flex;gap:8px;flex-wrap:wrap;margin:24px 0}.badge{border:1px solid #cbd8ef;border-radius:30px;padding:5px 12px;font-size:13px;color:#234e97;background:#f5f8ff}.facts{display:grid;grid-template-columns:repeat(4,1fr);gap:12px}.fact{border:1px solid #dce3ec;border-radius:12px;padding:18px}.fact b{display:block;font-size:30px}.fact span{font-size:13px;color:#58677c}table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid #dce3ec;padding:15px;text-align:left;vertical-align:top}thead{background:#f6f8fb}blockquote{margin:9px 0 0;color:#526176;font-size:13px}li{margin:9px 0}.note{border-left:3px solid #416db7;background:#f5f8ff;padding:16px 20px}.muted{color:#617087;font-size:13px}code{overflow-wrap:anywhere;font-size:12px}details{margin-top:26px}summary{cursor:pointer;font-weight:600}@media(max-width:650px){body{padding:12px}main{padding:24px}h1{font-size:30px}.facts{grid-template-columns:repeat(2,1fr)}td,th{padding:8px}table{font-size:12px}}@media print{body{padding:0;background:white}main{border:0;padding:0}details{display:none}h2{break-after:avoid}tr,.note{break-inside:avoid}}
</style><main><div class="eyebrow">SCOPEPROOF / RECORDED DEMONSTRATION</div><h1>Fresh model output.<br>Version-bound review.</h1><p class="lede">Two newly generated external ChatGPT analyses were imported into the real local application through HTTP. The full synthetic workflow passed, including stale-version rejection and one-invoice retry behavior.</p><div class="badges"><span class="badge">Actual loopback HTTP</span><span class="badge">Fresh external AI generation</span><span class="badge">Synthetic evidence</span><span class="badge">Billing simulator</span></div><div class="facts"><div class="fact"><b>2</b><span>fresh external model responses</span></div><div class="fact"><b>16</b><span>application HTTP requests</span></div><div class="fact"><b>1</b><span>simulated draft across two attempts</span></div><div class="fact"><b>0</b><span>real PayPal calls or payments</span></div></div><h2>What the model returned</h2><p>The text deliberately paraphrases the acceptance criteria. The first report includes explicit missing tests and a vendor instruction to mark everything passed. The model treated that instruction as evidence text, and left the outstanding checks missing.</p><table><thead><tr><th>Criterion</th><th>Before remaining checks</th><th>After corrected report</th></tr></thead><tbody>'''+''.join(rows)+'''</tbody></table><h2>What the application enforced</h2><ol><li>Imported analysis never approved the evidence or set a price.</li><li>Draft creation before explicit review returned <code>CURRENT_REVIEW_REQUIRED</code>.</li><li>A simulated local operator accepted each criterion for the current snapshot.</li><li>Two draft attempts produced exactly one simulator invoice, <code>INV2-MOCK-0001</code>, with a verified read-back.</li><li>Editing the evidence revoked approval and cleared the imported analysis.</li><li>The previous model response returned <code>AI_REVIEW_STALE</code>; the old review link was refused; another billing attempt required a new review.</li></ol><div class="note"><b>What this proves — and its limits</b><p>This is a reproducible functional check of this synthetic case. The app did not call a model API: a separate ChatGPT agent generated responses to exported prompts. The app correctly labels the import <code>IMPORTED_REVIEW_UNVERIFIED_AUTHOR</code>. Approval was an explicit simulated operator action, not a customer identity check. Billing was the local simulator, not PayPal Sandbox. This is not an independent audit, a model accuracy estimate, or proof that the reported delivery happened.</p></div><h2>Reproduce the run</h2><p>Run <code>python3 run_demo.py --replay --app /path/to/ScopeProof_app</code> alongside the saved prompts and responses. Replay performs no new inference. It checks prompt equality, reimports the frozen responses, and executes the HTTP workflow in a temporary workspace.</p><p class="muted">Fresh run: '''+escape(fresh['started_at'])+' → '+escape(fresh['completed_at'])+'''<br>Runtime version: '''+escape(fresh['app_version'])+'''<br>Fresh run: PASS. Saved-response replay: '''+('PASS' if replay['all_passed'] else 'FAIL')+'''.</p><details><summary>Sanitized application request trace</summary><table><thead><tr><th>#</th><th>Request</th><th>HTTP</th><th>Result</th></tr></thead><tbody>'''+request_rows+'''</tbody></table></details></main></html>'''
html = html.replace('<br>Runtime version: ', '<br>Fresh runtime version: ')
html = html.replace('<details><summary>Sanitized application request trace</summary>',
                    replay_record + '<details><summary>Sanitized application request trace</summary>')
(root / 'ScopeProof_fresh_AI_evidence.html').write_text(html, encoding='utf-8')
manifest = {'provenance': 'EXTERNAL_CHATGPT_AGENT_OUTPUTS_IMPORTED_THROUGH_APP_HTTP',
            'generation_agent': '/root/fresh_ai_demo/blind_prompt_generation',
            'generation_context': 'Only the exported prompt was provided for each turn; the second turn retained prior prompt context.',
            'model_identifier': 'Not exposed; no model-version claim',
            'external_model_invocations': 2, 'app_model_api_calls': 0,
            'model_outputs_edited_by_harness': False, 'independent_audit': False,
            'report_replay_result': {'basename': args.replay_result.name,
                'sha256': hashlib.sha256(replay_bytes).hexdigest(),
                'app_version': replay['app_version'], 'completed_at': replay['completed_at']},
            'files': {path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in sorted(root.iterdir()) if path.is_file() and path.name != 'manifest.json'}}
(root / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print('Report and manifest written; no external service called.')
