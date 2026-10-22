from contextlib import closing
from html.parser import HTMLParser
from pathlib import Path
import http.client
import json
import tempfile
import threading
import unittest
from unittest.mock import patch

import scopeproof_bridge as bridge
from app import create_server
from delivery_report import create_export, make_record, render_record, verify_export
from workflow import Workspace, FULL_REPORT


class DeliveryReportTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.w = Workspace(Path(self.temp.name))
        self.owner = self.w.owner_token

    def complete(self):
        s = self.w.state(self.owner)
        self.w.update_evidence(self.owner, s['revision'], {'acceptance-report': FULL_REPORT})
        s = self.w.state(self.owner)
        reviewer = self.w.invite(self.owner)['token']
        self.w.approve(reviewer, s['snapshot'], {k: True for k in s['criteria']}, True)
        return self.w.state(self.owner)

    def record(self):
        return make_record(self.w.export(self.owner), generated_at='2026-10-19T18:45:00+00:00')

    def test_pending_report_keeps_evidence_and_human_acceptance_separate(self):
        self.w.review(self.owner, 'local_search', None)
        r = self.record()
        self.assertEqual(r['review']['status'], 'pending')
        self.assertTrue(all(c['human_decision'] == 'pending' for c in r['current']['criteria']))
        self.assertIsNone(r['draft'])
        self.assertIn('Awaiting explicit review', render_record(r))

    def test_completed_report_matches_current_accepted_version_and_amount(self):
        s = self.complete()
        self.w.draft(self.owner, s['snapshot'], True)
        out = self.w.delivery_report(self.owner)
        check = verify_export(out['html'])
        self.assertTrue(check['verified'])
        self.assertEqual(check['snapshot'], s['snapshot'])
        self.assertEqual(check['record_sha256'], out['record_sha256'])
        self.assertIn('125.00 EUR', out['html'])
        self.assertIn('LOCAL SIMULATOR · NOT PAYPAL', out['html'])
        self.assertIn('INV2-MOCK-0001', out['html'])
        self.assertFalse(check['independent_authentication'])

    def test_new_evidence_never_inherits_acceptance_or_existing_draft(self):
        s = self.complete()
        self.w.draft(self.owner, s['snapshot'], True)
        self.w.update_evidence(self.owner, s['revision'], {'acceptance-report': FULL_REPORT + '\nNew change pending review.'})
        r = self.record()
        self.assertEqual(r['review']['status'], 'pending')
        self.assertFalse(r['draft']['current_version'])
        self.assertEqual(r['draft']['recorded_revision'], s['revision'])
        self.assertIn('It does not accept or invoice the current delivery', render_record(r))

    def test_preflight_failure_does_not_bind_future_draft_to_old_evidence(self):
        for failure in ('approval', 'authentication'):
            for restart in (False, True):
                with self.subTest(failure=failure, restart=restart):
                    w = Workspace(Path(self.temp.name) / (failure + str(restart)))
                    owner = w.owner_token
                    def accept():
                        state = w.state(owner)
                        reviewer = w.invite(owner)['token']
                        w.approve(reviewer, state['snapshot'],
                                  {k: True for k in state['criteria']}, True)
                        return state
                    before = accept()
                    target = w.signer if failure == 'approval' else w.paypal
                    method = 'check' if failure == 'approval' else 'authenticate'
                    with patch.object(target, method, side_effect=bridge.Blocked('PREFLIGHT_FAILED')):
                        with self.assertRaises(bridge.Blocked):
                            w.draft(owner, before['snapshot'], True)
                    self.assertEqual(w.paypal.count(), 0)
                    if restart:
                        w = Workspace(w.root)
                        owner = w.owner_token
                    w.update_evidence(owner, before['revision'], {'acceptance-report': FULL_REPORT})
                    current = accept()
                    result = w.draft(owner, current['snapshot'], True)
                    self.assertEqual(result['outcome']['status'], 'VERIFIED_DRAFT')
                    self.assertEqual(result['outcome_snapshot'], current['snapshot'])
                    record = make_record(w.export(owner), generated_at='audit')
                    self.assertTrue(record['draft']['current_version'])
                    self.assertEqual(record['draft']['recorded_revision'], current['revision'])
                    self.assertEqual(w.paypal.count(), 1)
                    restored = Workspace(w.root)
                    self.assertEqual(restored.state(restored.owner_token)['outcome_snapshot'], current['snapshot'])

    def test_restarted_session_labels_provider_verification_historical(self):
        s = self.complete()
        self.w.draft(self.owner, s['snapshot'], True)
        restored = Workspace(Path(self.temp.name))
        out = restored.delivery_report(restored.owner_token)
        self.assertIn('This running session has not re-read the provider record', out['html'])
        self.assertTrue(verify_export(out['html'])['verified'])

    def test_unknown_provider_outcome_is_not_presented_as_verified(self):
        s = self.complete()
        self.w.fault(self.owner, 'lost_reply')
        self.w.draft(self.owner, s['snapshot'], True)
        r = self.record()
        self.assertEqual(r['draft']['status'], 'UNKNOWN')
        html = render_record(r)
        self.assertIn('Outcome unknown', html)
        self.assertNotIn('<h2>Simulated draft verified</h2>', html)
        self.assertIn('do not create another draft', html)

    def test_expired_approval_is_not_displayed_as_current_acceptance(self):
        self.complete()
        with patch('workflow.time.time', return_value=10**12):
            r = self.record()
        self.assertEqual(r['review']['status'], 'expired')
        self.assertTrue(all(c['human_decision'] == 'pending' for c in r['current']['criteria']))

    def test_report_never_executes_supplied_html(self):
        attack = '<script>alert("data")</script><img src="https://example.invalid/beacon" onerror="alert(1)"><form action="https://example.invalid/"></form>'
        s = self.w.state(self.owner)
        self.w.update_evidence(self.owner, s['revision'], {'acceptance-report': attack})
        out = self.w.delivery_report(self.owner)
        tags = []
        class Tags(HTMLParser):
            def handle_starttag(self, tag, attrs):
                tags.append(tag)
        Tags().feed(out['html'])
        self.assertNotIn('script', tags)
        self.assertNotIn('img', tags)
        self.assertNotIn('form', tags)
        self.assertIn('&lt;script&gt;', out['html'])
        self.assertIn("default-src 'none'", out['html'])
        self.assertTrue(verify_export(out['html'])['verified'])

    def test_visible_amount_tampering_is_detected_even_with_unchanged_embedded_record(self):
        out = self.w.delivery_report(self.owner)
        modified = out['html'].replace('125.00 EUR', '925.00 EUR', 1)
        with self.assertRaisesRegex(ValueError, 'VISIBLE_CONTENT_DOES_NOT_MATCH'):
            verify_export(modified)

    def test_export_has_no_capabilities_private_keys_or_provider_mutation(self):
        s = self.complete()
        self.w.draft(self.owner, s['snapshot'], True)
        before = self.w.export(self.owner)
        count = self.w.paypal.post_count
        out = self.w.delivery_report(self.owner)
        after = self.w.export(self.owner)
        self.assertEqual(before, after)
        self.assertEqual(count, self.w.paypal.post_count)
        self.assertNotIn(self.owner, out['html'])
        record = self.record()
        self.assertNotIn('envelope', json.dumps(record))
        self.assertNotIn('signing.key', json.dumps(record))
        self.assertNotIn('review-link:', json.dumps(record))

    def test_reviewer_cannot_export_merchant_delivery_record(self):
        token = self.w.invite(self.owner)['token']
        with self.assertRaisesRegex(bridge.Blocked, 'MERCHANT_ROLE_REQUIRED'):
            self.w.delivery_report(token)

    def test_duplicate_or_oversized_embedded_records_are_rejected(self):
        out = self.w.delivery_report(self.owner)
        with self.assertRaisesRegex(ValueError, 'ONE_DELIVERY_RECORD_REQUIRED'):
            verify_export(out['html'] + out['html'])
        with self.assertRaisesRegex(ValueError, 'DELIVERY_FILE_LIMIT'):
            verify_export('x' * 2_000_001)

    def test_authenticated_real_http_returns_report_without_mutating_workspace(self):
        server = create_server(self.w)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with closing(http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=4)) as conn:
                conn.request('GET', '/api/delivery-report', headers={'Authorization': 'Bearer ' + self.owner})
                response = conn.getresponse()
                self.assertEqual(response.status, 200)
                out = json.loads(response.read())
                self.assertTrue(verify_export(out['html'])['verified'])
            with closing(http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=4)) as conn:
                conn.request('GET', '/api/delivery-report')
                response = conn.getresponse()
                self.assertEqual(response.status, 403)
                response.read()
            self.assertEqual(self.w.state(self.owner)['revision'], 1)
            self.assertEqual(self.w.paypal.post_count, 0)
        finally:
            server.shutdown()
            server.server_close()
            thread.join(3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
