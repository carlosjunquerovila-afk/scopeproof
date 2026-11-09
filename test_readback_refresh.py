"""Read-only recovery regressions. Real local HTTP, simulated provider only."""
from contextlib import closing
import http.client
import json
import tempfile
import threading
import unittest
from unittest.mock import patch

import scopeproof_bridge as b
from app import create_server
from workflow import Workspace, FULL_REPORT


class ReadbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.w = Workspace(self.tmp.name)
        self.t = self.w.owner_token
        s = self.w.update_evidence(self.t, 1, {'acceptance-report': FULL_REPORT})
        self.reviewer = self.w.invite(self.t)['token']
        self.w.approve(self.reviewer, s['snapshot'], {k: True for k in s['criteria']}, True)
        self.created = self.w.draft(self.t, s['snapshot'], True)
        self.key = self.created['outcome']['billing_key']

    def changed(self):
        return self.w.update_evidence(self.t, self.w.state(self.t)['revision'],
                                      {'acceptance-report': FULL_REPORT + '\nLater change.'})

    def test_changed_version_can_read_old_draft_without_approval_or_create(self):
        before = self.changed()
        with patch.object(self.w.paypal, 'create_draft', side_effect=AssertionError('Must never create')):
            after = self.w.refresh_draft(self.t, True)
        self.assertEqual(after['outcome']['status'], 'VERIFIED_DRAFT')
        self.assertTrue(after['provider_record_fresh_for_session'])
        self.assertFalse(after['approved_current'])
        for field in ('snapshot', 'outcome_snapshot', 'approval', 'scope', 'artifacts', 'analysis'):
            self.assertEqual(after[field], before[field], field)
        self.assertNotEqual(after['snapshot'], after['outcome_snapshot'])
        self.assertEqual(self.w.paypal.count(), 1)

    def test_restart_and_expired_approval_do_not_require_new_acceptance_to_read(self):
        other = Workspace(self.tmp.name)
        with patch('workflow.time.time', return_value=10**12):
            before = other.state(other.owner_token)
            self.assertFalse(before['approved_current'])
            after = other.refresh_draft(other.owner_token, True)
            self.assertFalse(after['approved_current'])
        self.assertEqual(after['approval'], before['approval'])
        self.assertTrue(after['provider_record_fresh_for_session'])
        self.assertEqual(other.paypal.post_count, 0)

    def test_failed_read_clears_freshness_and_allows_read_only_retry(self):
        with patch.object(self.w.paypal, 'get_invoice', side_effect=OSError('private provider detail')):
            failed = self.w.refresh_draft(self.t, True)
        self.assertEqual(failed['outcome']['status'], 'READBACK_UNAVAILABLE')
        self.assertFalse(failed['provider_record_fresh_for_session'])
        self.assertNotIn('private provider detail', json.dumps(failed))
        self.assertEqual(self.w.ledger.get(self.key)['state'], 'VERIFIED_DRAFT')
        self.assertEqual(self.w.refresh_draft(self.t, True)['outcome']['status'], 'VERIFIED_DRAFT')
        self.assertEqual(self.w.paypal.post_count, 1)

    def test_mismatch_closes_refresh_and_never_recreates(self):
        self.w.paypal.fault = 'wrong_total'
        state = self.w.refresh_draft(self.t, True)
        self.assertEqual(state['outcome']['status'], 'REVIEW_REQUIRED')
        self.assertFalse(state['provider_record_fresh_for_session'])
        with self.assertRaisesRegex(b.Blocked, 'VERIFIED_DRAFT_REQUIRED'):
            self.w.refresh_draft(self.t, True)
        self.assertEqual(self.w.paypal.count(), 1)

    def test_original_amount_recipient_status_and_id_are_still_checked(self):
        original = self.w.paypal.get_invoice(self.created['outcome']['invoice_id'])
        mutations = [lambda x: x.update(status='PAID'),
                     lambda x: x.update(id='INV2-OTHER-0001'),
                     lambda x: x['primary_recipients'][0]['billing_info'].update(email_address='other@example.com')]
        for mutate in mutations:
            remote = json.loads(json.dumps(original)); mutate(remote)
            with self.subTest(remote=remote['status']):
                with patch.object(self.w.paypal, 'get_invoice', return_value=remote), \
                     patch.object(self.w.ledger, 'transition', return_value={**self.w.ledger.get(self.key), 'state': 'REVIEW_REQUIRED'}) as transition:
                    result = b.refresh_verified_draft(self.w.ledger, self.w.paypal, self.key)
                    self.assertEqual(result['status'], 'REVIEW_REQUIRED')
                    transition.assert_called_once_with(self.key, 'REVIEW_REQUIRED', reason='READBACK_CHANGED')

    def test_reviewer_cannot_read_provider(self):
        with patch.object(self.w.paypal, 'get_invoice') as read:
            with self.assertRaisesRegex(b.Blocked, 'MERCHANT_ROLE_REQUIRED'):
                self.w.refresh_draft(self.reviewer, True)
            read.assert_not_called()

    def test_explicit_confirmation_required_before_provider_read(self):
        with patch.object(self.w.paypal, 'get_invoice') as read:
            for confirmation in (False, None, 1, 'true'):
                with self.assertRaisesRegex(b.Blocked, 'EXPLICIT_READBACK_REQUIRED'):
                    self.w.refresh_draft(self.t, confirmation)
            read.assert_not_called()

    def test_unknown_or_rejected_intent_cannot_use_verified_refresh(self):
        for state in ('UNKNOWN', 'IN_FLIGHT', 'CREATE_REJECTED', 'REVIEW_REQUIRED', 'CREATED_UNVERIFIED'):
            row = {**self.w.ledger.get(self.key), 'state': state}
            with self.subTest(state=state), patch.object(self.w.ledger, 'get', return_value=row), \
                 patch.object(self.w.paypal, 'get_invoice') as read:
                with self.assertRaisesRegex(b.Blocked, 'VERIFIED_DRAFT_REQUIRED'):
                    self.w.refresh_draft(self.t, True)
                read.assert_not_called()

    def test_provider_provenance_mismatch_blocked_before_read(self):
        with patch.object(self.w.paypal, 'provenance', 'PAYPAL_SANDBOX'), \
             patch.object(self.w.paypal, 'get_invoice') as read:
            with self.assertRaisesRegex(b.Blocked, 'CANNOT_MIX_MOCK_AND_SANDBOX_LEDGER'):
                self.w.refresh_draft(self.t, True)
            read.assert_not_called()

    def test_missing_connection_refused(self):
        self.w.paypal = None
        with self.assertRaisesRegex(b.Blocked, 'PAYPAL_SANDBOX_NOT_CONNECTED'):
            self.w.refresh_draft(self.t, True)

    def test_no_draft_refused(self):
        with tempfile.TemporaryDirectory() as d:
            w = Workspace(d)
            with self.assertRaisesRegex(b.Blocked, 'NO_DRAFT_TO_REFRESH'):
                w.refresh_draft(w.owner_token, True)

    def test_http_route_preserves_auth_origin_fields_and_old_version(self):
        self.changed()
        server = create_server(self.w)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        def request(payload, token=None, origin=None):
            headers = {'Authorization': 'Bearer ' + (token or self.t), 'Origin': origin or server.origin,
                       'Content-Type': 'application/json', 'X-ScopeProof-Request': '1'}
            with closing(http.client.HTTPConnection('127.0.0.1', server.server_port, timeout=4)) as conn:
                conn.request('POST', '/api/refresh-draft', json.dumps(payload), headers)
                response = conn.getresponse()
                return response.status, json.loads(response.read())
        try:
            for payload, token, origin in [({'confirm': True}, 'invalid', None),
                                           ({'confirm': True}, None, 'https://other.example'),
                                           ({'confirm': True, 'invoice_id': 'INV2-OTHER-0001'}, None, None),
                                           ({'confirm': False}, None, None)]:
                with patch.object(self.w.paypal, 'get_invoice') as read:
                    self.assertEqual(request(payload, token, origin)[0], 400)
                    read.assert_not_called()
            code, state = request({'confirm': True})
            self.assertEqual(code, 200)
            self.assertFalse(state['approved_current'])
            self.assertEqual(state['outcome_snapshot'], self.created['snapshot'])
            self.assertTrue(state['provider_record_fresh_for_session'])
            self.assertEqual(self.w.paypal.count(), 1)
        finally:
            server.shutdown(); server.server_close(); thread.join(3)


if __name__ == '__main__':
    unittest.main(verbosity=2)
