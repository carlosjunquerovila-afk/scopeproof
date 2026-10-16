import json,tempfile,unittest
from unittest.mock import patch
from workflow import Workspace,FULL_REPORT
from scopeproof_bridge import Blocked
class ImportTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.w=Workspace(self.tmp.name);self.t=self.w.owner_token
 def package(self):
  s=self.w.state(self.t)
  return {'snapshot':s['snapshot'],'analysis':{'criteria':[{'criterion_id':k,'status':'unclear','evidence_id':None,'quote':None,'reason':'Insufficient evidence to decide.'} for k in s['criteria']]}}
 def test_import_never_approves(self):
  s=self.w.import_review(self.t,json.dumps(self.package()))
  self.assertFalse(s['approved_current']);self.assertFalse(s['analysis']['live_inference']);self.assertFalse(s['analysis']['author_verified'])
 def test_extra_financial_fields_refused(self):
  p=self.package();p['analysis']['amount']=999
  with self.assertRaises(Blocked):self.w.import_review(self.t,json.dumps(p))
 def test_stale_ai_review_refused(self):
  p=self.package();self.w.update_evidence(self.t,1,{'acceptance-report':FULL_REPORT})
  with self.assertRaises(Blocked):self.w.import_review(self.t,json.dumps(p))
 def test_invented_quote_refused(self):
  p=self.package();p['analysis']['criteria'][0].update(status='evidence_found',evidence_id='acceptance-report',quote='I invented this')
  with self.assertRaises(Blocked):self.w.import_review(self.t,json.dumps(p))
 def test_duplicate_keys_in_import_refused(self):
  p=json.dumps(self.package()).replace('"analysis":','"analysis": {}, "analysis":',1)
  with self.assertRaises(Blocked):self.w.import_review(self.t,p)
 def test_prompt_omits_money_and_recipient(self):
  p=self.w.review_prompt(self.t)['prompt']
  self.assertNotIn('12500',p);self.assertNotIn('buyer@example.com',p);self.assertNotIn('seller@example.com',p)
 def test_import_uses_no_network(self):
  with patch('socket.socket',side_effect=AssertionError('network')):self.w.import_review(self.t,json.dumps(self.package()))
 def test_reviewer_cannot_import_analysis(self):
  t=self.w.invite(self.t)['token']
  with self.assertRaises(Blocked):self.w.import_review(t,json.dumps(self.package()))
if __name__=='__main__':unittest.main(verbosity=2)
