"""Regression: saved evidence must be reviewable under the same limits."""
import tempfile
import unittest
from workflow import Workspace
from scopeproof_bridge import Blocked

class EvidenceLimitTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.ws=Workspace(self.tmp.name);self.token=self.ws.owner_token
    def test_ascii_character_boundary_remains_reviewable(self):
        self.ws.update_evidence(self.token,1,{'acceptance-report':'x'*20000})
        out=self.ws.review(self.token,'local_search')
        self.assertEqual(out['analysis']['status'],'NEEDS_HUMAN_REVIEW')
    def test_over_character_limit_preserves_saved_snapshot(self):
        before=self.ws.state(self.token)
        with self.assertRaisesRegex(Blocked,'ARTIFACT_LIMIT'):
            self.ws.update_evidence(self.token,1,{'acceptance-report':'x'*20001})
        after=self.ws.state(self.token)
        self.assertEqual(after['snapshot'],before['snapshot'])
        self.assertEqual(after['artifacts'],before['artifacts'])
    def test_multibyte_utf8_boundary_remains_reviewable(self):
        self.ws.update_evidence(self.token,1,{'acceptance-report':'😀'*12500})
        self.assertEqual(self.ws.review(self.token,'local_search')['analysis']['status'],'NEEDS_HUMAN_REVIEW')
    def test_utf8_overflow_preserves_saved_revision(self):
        before=self.ws.state(self.token)
        with self.assertRaisesRegex(Blocked,'ARTIFACT_LIMIT'):
            self.ws.update_evidence(self.token,1,{'acceptance-report':'😀'*12501})
        self.assertEqual(self.ws.state(self.token)['snapshot'],before['snapshot'])

if __name__=='__main__':unittest.main()
