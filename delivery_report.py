"""Portable, inert delivery records made from the saved ScopeProof workspace.

The record is a readable handover, not an invoice or an authenticated signature.
No network, AI, provider mutation, file access or third-party assets are used.
"""
from __future__ import annotations

import base64
import hashlib
import json
from html import escape
from html.parser import HTMLParser


FORMAT = 'scopeproof-delivery/1'


def canonical(value):
    return json.dumps(value, ensure_ascii=True, allow_nan=False,
                      sort_keys=True, separators=(',', ':')).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def money(cents, currency):
    # Integer arithmetic preserves the exact agreed amount.
    return f'{cents // 100:,}.{cents % 100:02d} {currency}'


def esc(value):
    return escape(str(value), quote=True)


def make_record(state, *, generated_at):
    """Copy only the fields needed for a handover from Workspace.export()."""
    scope = state['scope']
    approval = state.get('approval')
    current_snapshot = state['snapshot']
    accepted = bool(state.get('approved_current'))
    review_status = 'accepted_current' if accepted else (
        'expired' if approval and approval.get('snapshot') == current_snapshot else 'pending')
    last_acceptance = next((e['at'] for e in reversed(state['events'])
                            if e['type'] == 'CURRENT_VERSION_EXPLICITLY_ACCEPTED'
                            and e['revision'] == state['revision']), None)
    analysis = state.get('analysis')
    findings = {f['criterion_id']: f for f in (analysis or {}).get('criteria', [])}
    criteria = []
    for criterion_id, requirement in state['criteria'].items():
        finding = findings.get(criterion_id)
        criteria.append({
            'id': criterion_id,
            'requirement': requirement,
            'analysis': ({k: finding.get(k) for k in
                          ('status', 'reason', 'evidence_id', 'quote')} if finding else None),
            'human_decision': 'accepted' if accepted else 'pending',
        })
    outcome = state.get('outcome')
    billing_snapshot = state.get('outcome_snapshot')
    original = None
    if outcome:
        original = next((v['content'] for v in state.get('version_history', [])
                         if v['snapshot'] == billing_snapshot), None)
    draft = None
    if outcome:
        # Do not copy raw provider error payloads, actor capabilities or envelopes.
        reason = outcome.get('reason', '')
        allowed_rejections = {f'PAYPAL_DRAFT_HTTP_{s}' for s in
                              (400, 401, 403, 404, 405, 406, 415, 422)}
        draft = {
            'status': outcome['status'],
            'invoice_id': outcome.get('invoice_id'),
            'snapshot': billing_snapshot,
            'current_version': billing_snapshot == current_snapshot,
            'fresh_read_this_session': bool(state.get('provider_record_fresh_for_session')),
            'rejection': reason if reason in allowed_rejections else None,
            'recorded_scope': original['scope'] if original else None,
            'recorded_revision': original['revision'] if original else None,
        }
    record = {
        'format': FORMAT,
        'generated_at': generated_at,
        'runtime_version': state['version'],
        'mode': state['mode'],
        'provider_provenance': state['provider_provenance'],
        'current': {
            'snapshot': current_snapshot,
            'revision': state['revision'],
            'scope': scope,
            'criteria': criteria,
            'evidence': state['artifacts'],
        },
        'analysis_source': ({k: analysis.get(k) for k in
                             ('provenance', 'model', 'live_inference')} if analysis else None),
        'review': {
            'status': review_status,
            'accepted_at': last_acceptance,
            'accepted_snapshot': approval.get('snapshot') if approval else None,
            'expires_epoch': approval.get('expires') if approval else None,
            'identity_verified': False,
        },
        'draft': draft,
        'events': [{'type': e['type'], 'revision': e['revision'], 'at': e['at']}
                   for e in state['events']],
        'integrity': {
            'local_ledger_events_checked': state['verified_local_event_count'],
            'independent_notarization': False,
        },
    }
    # Detach nested objects. This function cannot mutate the saved workspace.
    return json.loads(canonical(record))


CSS = '''
:root{color-scheme:light;--ink:#182027;--muted:#59656f;--line:#dfe4e8;--blue:#1657d5;--soft:#f5f7fa}
*{box-sizing:border-box}body{margin:0;background:#f4f5f7;color:var(--ink);font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
main{max-width:1020px;margin:40px auto;background:#fff;border:1px solid var(--line);border-radius:24px;padding:52px 58px}
header{display:flex;justify-content:space-between;gap:20px;align-items:center;border-bottom:1px solid var(--line);padding-bottom:23px;margin-bottom:34px}
.brand{font-size:22px;font-weight:750;letter-spacing:-.7px}.brand span{color:var(--blue)}.tag{background:var(--soft);font-size:11px;font-weight:700;border:1px solid var(--line);padding:6px 11px;border-radius:40px}
.eyebrow{font-size:11px;font-weight:750;letter-spacing:.13em;color:var(--blue);text-transform:uppercase;margin:0 0 8px}
h1{font-size:37px;line-height:1.16;letter-spacing:-1.2px;margin:0 0 15px;overflow-wrap:anywhere}h2{font-size:23px;line-height:1.25;letter-spacing:-.5px;margin:0 0 16px}h3{font-size:15px;line-height:1.45;margin:0 0 12px}
.muted,.meta{color:var(--muted)}.meta{font-size:12px;overflow-wrap:anywhere}.summary{display:grid;grid-template-columns:1.25fr 1fr 1fr;gap:12px;margin:28px 0}.metric{border:1px solid var(--line);border-radius:14px;padding:17px}.metric span{display:block;color:var(--muted);font-size:11px}.metric b{display:block;font-size:20px;line-height:1.3;margin-top:8px}.metric .small{font-size:15px}
.notice{padding:15px 18px;border:1px solid #e5d4b1;background:#fff9ec;border-radius:12px;font-size:13px;margin:24px 0}.notice p{margin:0}.section{border-top:1px solid var(--line);padding-top:30px;margin-top:32px}.criterion{border:1px solid var(--line);border-radius:14px;padding:21px;margin:12px 0;break-inside:avoid}.labels{display:flex;gap:8px;flex-wrap:wrap}.label{font-size:11px;font-weight:650;background:var(--soft);border-radius:6px;padding:4px 8px}.good{background:#e9f5ef;color:#165b3c}.pending{background:#fff3de;color:#755210}.quote{font-size:14px;line-height:1.55;margin:14px 0 8px;padding:13px 16px;border-left:3px solid #bccdea;background:#f7f9fd;white-space:pre-wrap;overflow-wrap:anywhere}.pre{font:13px/1.65 ui-monospace,SFMono-Regular,Consolas,monospace;background:var(--soft);border:1px solid var(--line);border-radius:12px;padding:20px;white-space:pre-wrap;overflow-wrap:anywhere}.hash{font:11px/1.6 ui-monospace,SFMono-Regular,Consolas,monospace;overflow-wrap:anywhere}dl{display:grid;grid-template-columns:150px 1fr;gap:8px 16px;font-size:13px}dt{color:var(--muted)}dd{margin:0;overflow-wrap:anywhere}.timeline{padding-left:20px;font-size:12px;color:var(--muted)}.timeline li{margin:7px 0}.print-note{font-size:12px;color:var(--muted);margin-top:26px}footer{border-top:1px solid var(--line);margin-top:32px;padding-top:20px;font-size:11px;color:var(--muted)}footer p{margin:7px 0}[hidden]{display:none!important}
@media(max-width:720px){main{margin:0;border:0;border-radius:0;padding:26px 22px}header{align-items:flex-start}.summary{grid-template-columns:1fr}h1{font-size:31px}dl{grid-template-columns:1fr;gap:3px}dd{margin-bottom:12px}.tag{max-width:170px;text-align:center}}
@media print{@page{size:A4;margin:17mm 15mm}body{background:white;font-size:10pt}main{margin:0;max-width:none;padding:0;border:0;border-radius:0}header{margin-bottom:20px;padding-bottom:14px}h1{font-size:25pt}h2{font-size:16pt;break-after:avoid}.summary{margin:20px 0}.section{padding-top:18px;margin-top:22px}.print-note{display:none}.criterion{padding:14px}.pre{font-size:9pt}.notice{break-inside:avoid}footer{break-inside:avoid}a{text-decoration:none}}
'''


EVENT_NAMES = {
    'EVIDENCE_UPDATED_APPROVAL_REVOKED': 'Delivery report saved; earlier acceptance revoked',
    'AGREED_SCOPE_REVISED_REVIEW_REQUIRED': 'Agreed scope revised; new acceptance required',
    'EVIDENCE_REFERENCES_GENERATED_NOT_APPROVED': 'Candidate evidence passages located; human acceptance unchanged',
    'IMPORTED_REVIEW_VALIDATED_NOT_APPROVED': 'Imported analysis matched the saved version; human acceptance unchanged',
    'SANDBOX_OAUTH_SUCCEEDED_NO_INVOICE_CREATED': 'Sandbox connection authenticated; no invoice created',
    'CURRENT_VERSION_EXPLICITLY_ACCEPTED': 'Reviewer explicitly accepted the saved version',
    'DRAFT_ATTEMPT_VERIFIED_DRAFT': 'Draft creation/read-back verified in the stated environment',
    'DRAFT_ATTEMPT_UNKNOWN': 'Draft outcome unknown; another creation is blocked',
    'DRAFT_ATTEMPT_CREATE_REJECTED': 'Provider rejected the draft request',
    'RECONCILED_VERIFIED_DRAFT': 'Existing draft reconciled by read-back',
    'LOCAL_LEDGER_RECOVERED_NO_PROVIDER_CALL': 'Earlier local intent recovered without provider contact',
}


def render_record(record):
    if record.get('format') != FORMAT:
        raise ValueError('UNSUPPORTED_DELIVERY_FORMAT')
    current = record['current']
    scope = current['scope']
    milestone = scope['milestones'][0]
    demo = record['mode'] == 'demo'
    environment = 'LOCAL SIMULATOR · NOT PAYPAL' if demo else 'PAYPAL SANDBOX · NO LIVE MONEY'
    review_status = record['review']['status']
    accepted = review_status == 'accepted_current'
    review_label = {'accepted_current': 'Accepted for this version', 'expired': 'Acceptance expired',
                    'pending': 'Awaiting explicit review'}[review_status]
    findings = {'evidence_found': ('Supporting text found', 'good'),
                'missing': ('Evidence missing', 'pending'),
                'unclear': ('Needs clarification', 'pending')}
    cards = []
    for criterion in current['criteria']:
        finding = criterion['analysis']
        label, css_class = findings.get((finding or {}).get('status'), ('Not analysed', 'pending'))
        content = '<p class="meta">No analysis has been recorded for this criterion.</p>'
        if finding:
            content = f'<p class="meta">{esc(finding.get("reason") or "")}</p>'
            if finding.get('quote'):
                content += f'<blockquote class="quote">{esc(finding["quote"])}</blockquote><p class="meta">Source: {esc(finding["evidence_id"])}</p>'
        cards.append(f'''<article class="criterion"><h3>{esc(criterion['requirement'])}</h3>
<div class="labels"><span class="label {css_class}">{label}</span><span class="label {'good' if accepted else 'pending'}">Human review: {'accepted' if accepted else 'pending'}</span></div>{content}</article>''')
    source = record['analysis_source']
    analysis_source = 'No analysis recorded'
    if source:
        analysis_source = {
            'LOCAL_LEXICAL_RETRIEVAL_NOT_LLM': 'Local passage search; no generative model',
            'IMPORTED_REVIEW_UNVERIFIED_AUTHOR': 'Imported AI review; author unverified; no model call during import',
            'OLLAMA_LOOPBACK': 'Local installed model',
        }.get(source.get('provenance'), str(source.get('provenance')))
    draft = record['draft']
    draft_html = '<p class="muted">No draft creation has been attempted.</p>'
    draft_label = 'Not prepared'
    if draft:
        status = draft['status']
        draft_label = {
            'VERIFIED_DRAFT': 'Simulated draft verified' if demo else 'Sandbox draft verified',
            'UNKNOWN': 'Outcome unknown', 'IN_FLIGHT': 'Outcome unresolved',
            'CREATED_UNVERIFIED': 'Created; not verified', 'REVIEW_REQUIRED': 'Manual investigation required',
            'CREATE_REJECTED': 'Draft request rejected',
        }.get(status, str(status))
        warnings = []
        if not draft['current_version']:
            warnings.append('This draft belongs to an earlier saved version. It does not accept or invoice the current delivery.')
        if status == 'VERIFIED_DRAFT' and not draft['fresh_read_this_session']:
            warnings.append('Historical local verification. This running session has not re-read the provider record.')
        if status in ('UNKNOWN', 'IN_FLIGHT', 'CREATED_UNVERIFIED'):
            warnings.append('The provider outcome is not established. Keep the existing record and reconcile; do not create another draft.')
        old_scope = draft.get('recorded_scope')
        original_amount = money(old_scope['milestones'][0]['amount_cents'], old_scope['currency']) if old_scope else 'Original amount unavailable'
        draft_html = f'''<dl><dt>Status</dt><dd>{esc(draft_label)}</dd><dt>Draft identifier</dt><dd>{esc(draft.get('invoice_id') or 'No confirmed identifier')}</dd><dt>Bound evidence</dt><dd>v{esc(draft.get('recorded_revision') or '?')} · {'current version' if draft['current_version'] else 'earlier version'}</dd><dt>Original amount</dt><dd>{esc(original_amount)}</dd><dt>Version fingerprint</dt><dd class="hash">{esc(draft.get('snapshot') or 'Unavailable')}</dd></dl>'''
        for warning in warnings:
            draft_html += f'<div class="notice"><p>{esc(warning)}</p></div>'
    event_html = ''.join(f'<li>{esc(e["at"])} · v{esc(e["revision"])} · {esc(EVENT_NAMES.get(e["type"], e["type"]))}</li>' for e in record['events']) or '<li>No workflow actions recorded.</li>'
    evidence_html = ''.join(f'<h3>{esc(name)}</h3><pre class="pre">{esc(content)}</pre>' for name, content in current['evidence'].items())
    payload_hash = digest(record)
    payload = base64.b64encode(canonical(record)).decode('ascii')
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>ScopeProof delivery · {esc(milestone['name'])} · v{esc(current['revision'])}</title><style>{CSS}</style></head>
<body><main><header><div class="brand"><span>S</span> ScopeProof</div><span class="tag">{environment}</span></header>
<p class="eyebrow">Delivery record</p><h1>{esc(milestone['name'])}</h1>
<p class="muted">Agreed scope, supporting text, explicit review and the recorded draft in one saved handover.</p>
<div class="summary"><div class="metric"><span>AGREED MILESTONE</span><b>{esc(money(milestone['amount_cents'],scope['currency']))}</b></div><div class="metric"><span>SAVED EVIDENCE</span><b>Version {esc(current['revision'])}</b></div><div class="metric"><span>HUMAN REVIEW</span><b class="small">{esc(review_label)}</b></div></div>
<dl><dt>Studio / seller</dt><dd>{esc(scope['sender'])}</dd><dt>Recipient</dt><dd>{esc(scope['recipient'])}</dd><dt>Project</dt><dd>{esc(scope['project_id'])}</dd><dt>Exported at</dt><dd>{esc(record['generated_at'])}</dd></dl>
<div class="notice"><p>{'This record uses a local provider simulator. Any draft identifier is simulated.' if demo else 'This record uses PayPal Sandbox test accounts. Any draft is unsent and unpaid.'} This is a delivery record, not an invoice or proof of payment.</p></div>
<section class="section"><p class="eyebrow">01 / Agreed criteria</p><h2>What was reviewed</h2><p class="meta">{esc(analysis_source)}. Supporting text and human acceptance are separate decisions.</p>{''.join(cards)}</section>
<section class="section"><p class="eyebrow">02 / Saved evidence</p><h2>The report behind this version</h2><p class="meta">The following is supplied report text. ScopeProof does not independently verify that the described work occurred.</p>{evidence_html}</section>
<section class="section"><p class="eyebrow">03 / Recorded outcome</p><h2>{esc(draft_label)}</h2>{draft_html}</section>
<section class="section"><p class="eyebrow">04 / Traceability</p><h2>Version and action history</h2><p class="meta">Current saved-version fingerprint</p><p class="hash">{esc(current['snapshot'])}</p><ol class="timeline">{event_html}</ol></section>
<p class="print-note">Open this file in an ordinary browser. Use Print → Save as PDF to produce a copy for your project record. No connection or login is needed to read it.</p>
<footer><p>Prepared with ScopeProof {esc(record['runtime_version'])}. Review access proves possession of a temporary local link; it does not authenticate a customer or create a legal signature.</p><p>Payload SHA-256: <span class="hash">{payload_hash}</span></p><p>The checksum detects accidental changes when compared with this record. It is not independent notarization; a person with editing access can replace a record.</p></footer>
<pre id="scopeproof-delivery-data" hidden>{payload}</pre></main></body></html>
'''


def create_export(state, *, generated_at):
    record = make_record(state, generated_at=generated_at)
    html = render_record(record)
    filename = f'scopeproof-delivery-v{record["current"]["revision"]}-{record["current"]["snapshot"][:12]}.html'
    return {'filename': filename, 'html': html, 'snapshot': record['current']['snapshot'],
            'record_sha256': digest(record), 'html_sha256': hashlib.sha256(html.encode()).hexdigest()}


class _RecordParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.payloads = []
        self.active = False
    def handle_starttag(self, tag, attrs):
        if tag == 'pre' and dict(attrs).get('id') == 'scopeproof-delivery-data':
            if self.active:
                raise ValueError('NESTED_DELIVERY_RECORD')
            self.active = True
            self.payloads.append('')
    def handle_data(self, data):
        if self.active:
            self.payloads[-1] += data
    def handle_endtag(self, tag):
        if tag == 'pre' and self.active:
            self.active = False


def verify_export(html):
    """Check deterministic visible content, not just an embedded checksum.

    This proves internal byte consistency only, never an independent signature.
    """
    if not isinstance(html, str) or len(html.encode()) > 2_000_000:
        raise ValueError('DELIVERY_FILE_LIMIT')
    parser = _RecordParser()
    parser.feed(html)
    if len(parser.payloads) != 1 or parser.active:
        raise ValueError('ONE_DELIVERY_RECORD_REQUIRED')
    record = json.loads(base64.b64decode(parser.payloads[0], validate=True))
    if render_record(record) != html:
        raise ValueError('VISIBLE_CONTENT_DOES_NOT_MATCH_SAVED_RECORD')
    return {'verified': True, 'format': FORMAT, 'record_sha256': digest(record),
            'snapshot': record['current']['snapshot'], 'revision': record['current']['revision'],
            'mode': record['mode'], 'independent_authentication': False}
