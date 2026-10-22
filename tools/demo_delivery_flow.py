#!/usr/bin/env python3
"""Run a fresh project through real local HTTP and export usable delivery files.

The reviewer is a scripted local operator and the provider is the simulator.
There is no browser, PayPal request, model API call, outreach or charge here.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import http.client
import json
from pathlib import Path
import sys
import tempfile
import threading

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app import create_server
from delivery_report import verify_export
from workflow import Workspace


def now():
    return datetime.now(timezone.utc).isoformat()


def run(output):
    output.mkdir(parents=True, exist_ok=True)
    transcript, files = [], []
    started = now()
    with tempfile.TemporaryDirectory(prefix='scopeproof-fresh-project-') as tmp:
        workspace = Workspace(Path(tmp))
        owner = workspace.owner_token
        server = create_server(workspace)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        def request(path, body=None, *, actor=None, expected=200):
            headers = {'Authorization': 'Bearer ' + (actor or owner)}
            raw = None
            if body is not None:
                headers.update({'Origin': server.origin, 'X-ScopeProof-Request': '1',
                                'Content-Type': 'application/json'})
                raw = json.dumps(body)
            with closing(http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=8)) as conn:
                conn.request('POST' if body is not None else 'GET', path, body=raw, headers=headers)
                response = conn.getresponse()
                data = json.loads(response.read())
                transcript.append({'at': now(), 'method': 'POST' if body is not None else 'GET',
                                   'path': path, 'status': response.status,
                                   'revision': data.get('revision'), 'snapshot': data.get('snapshot'),
                                   'error': data.get('error')})
                if response.status != expected:
                    raise AssertionError(f'{path}: expected {expected}, received {response.status}')
                return data

        def download(name):
            result = request('/api/delivery-report')
            checked = verify_export(result['html'])
            destination = output / name
            destination.write_text(result['html'], encoding='utf-8')
            files.append({'path': name, 'bytes': destination.stat().st_size,
                          'sha256': hashlib.sha256(destination.read_bytes()).hexdigest(),
                          'snapshot': checked['snapshot'], 'revision': checked['revision'],
                          'internal_consistency': checked['verified']})
            return result

        try:
            s = request('/api/state')
            project_id = s['scope']['project_id']
            criteria = {
                'responsive': 'Booking page checked at 390 and 1440 pixels.',
                'contact': 'Reservation form submitted successfully in staging.',
                'accessibility': 'Keyboard navigation checked with no blocked controls.',
            }
            s = request('/api/scope', {'revision': s['revision'],
                                      'name': 'Booking portal — October delivery',
                                      'amount_cents': 29900, 'currency': 'EUR', 'criteria': criteria})
            incomplete = ('Booking page checked at 390 and 1440 pixels.\n'
                          'Reservation form has not been tested.\n'
                          'Keyboard navigation assessment is pending.')
            s = request('/api/evidence', {'revision': s['revision'],
                                         'artifacts': {'acceptance-report': incomplete}})
            s = request('/api/analyze', {'engine': 'local_search', 'model': None})
            rejected = request('/api/draft', {'snapshot': s['snapshot'], 'confirm': True}, expected=400)
            assert rejected['error'] == 'CURRENT_REVIEW_REQUIRED'
            assert workspace.paypal.count() == 0
            download('01-review-pending.html')

            complete = '\n'.join(criteria.values())
            s = request('/api/evidence', {'revision': s['revision'],
                                         'artifacts': {'acceptance-report': complete}})
            s = request('/api/analyze', {'engine': 'local_search', 'model': None})
            assert not s['approved_current']
            invite = request('/api/invite', {})
            reviewer = invite['url'].split('#token=', 1)[1]
            s = request('/api/approve', {'snapshot': s['snapshot'],
                                        'decisions': {k: True for k in criteria},
                                        'acknowledgement': True}, actor=reviewer)
            accepted_snapshot = s['snapshot']
            s = request('/api/draft', {'snapshot': accepted_snapshot, 'confirm': True})
            assert s['outcome']['status'] == 'VERIFIED_DRAFT'
            assert s['outcome']['provenance'] == 'LOCAL_SIMULATOR_NOT_PAYPAL'
            s = request('/api/draft', {'snapshot': accepted_snapshot, 'confirm': True})
            assert workspace.paypal.post_count == 1
            accepted_report = download('02-delivery-accepted.html')
            assert '299.00 EUR' in accepted_report['html']

            changed = complete + '\nNew request: add calendar availability. Not included in the accepted version.'
            s = request('/api/evidence', {'revision': s['revision'],
                                         'artifacts': {'acceptance-report': changed}})
            assert not s['approved_current']
            assert s['outcome_snapshot'] == accepted_snapshot
            request('/api/approve', {'snapshot': accepted_snapshot,
                                     'decisions': {k: True for k in criteria},
                                     'acknowledgement': True}, actor=reviewer, expected=400)
            revised_report = download('03-new-version-needs-review.html')
            assert 'It does not accept or invoice the current delivery' in revised_report['html']
            assert workspace.paypal.post_count == 1
            receipt = {
                'started_at': started, 'completed_at': now(),
                'project_created_this_run': project_id,
                'workflow': 'fresh scope → incomplete report → refused premature draft → corrected evidence → explicit local review → one simulated draft → downloadable record → changed version loses approval',
                'transport': 'actual loopback HTTP against app.py',
                'runtime_version': s['version'],
                'http_requests': len(transcript), 'provider_create_count': workspace.paypal.post_count,
                'accepted_snapshot': accepted_snapshot, 'current_snapshot': s['snapshot'],
                'all_checks_passed': True,
                'boundaries': {'provider': 'LOCAL_SIMULATOR_NOT_PAYPAL', 'external_requests': 0,
                               'model_calls': 0, 'reviewer': 'scripted local operator',
                               'browser_rendering_tested': False, 'customer_participation': False,
                               'invoices_sent': 0, 'payments_or_revenue': 0},
                'files': files, 'requests': transcript,
            }
            (output / 'flow_receipt.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
            return receipt
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    receipt = run(args.output.resolve())
    print(json.dumps({k: receipt[k] for k in ('all_checks_passed', 'http_requests',
                     'provider_create_count', 'accepted_snapshot', 'current_snapshot', 'boundaries')}, indent=2))


if __name__ == '__main__':
    main()
