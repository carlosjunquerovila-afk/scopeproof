"""Regression tests: scoped review reads and real process-interruption recovery.
The process exits are real; the provider is explicitly a local SQLite simulator.
"""
from contextlib import closing
from pathlib import Path
import http.client
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

import scopeproof_bridge as b
from workflow import Workspace,FULL_REPORT,fingerprint
from app import create_server

WORKER=r'''
import os,sys
from workflow import Workspace,FULL_REPORT
w=Workspace(sys.argv[1]); phase=sys.argv[2]; t=w.owner_token
w.update_evidence(t,1,{'acceptance-report':FULL_REPORT})
s=w.state(t);r=w.invite(t)['token']
w.approve(r,s['snapshot'],{k:True for k in s['criteria']},True)
create=w.paypal.create_draft;get=w.paypal.get_invoice;transition=w.ledger.transition
if phase in ('after_intent','after_provider'):
 def cut(payload):
  if phase=='after_provider':create(payload)
  os._exit(73)
 w.paypal.create_draft=cut
elif phase=='after_id':
 w.paypal.get_invoice=lambda iid:os._exit(73)
else:
 def cut(key,state,**kwargs):
  if phase=='before_verified' and state=='VERIFIED_DRAFT':os._exit(73)
  result=transition(key,state,**kwargs)
  if phase=='after_verified' and state=='VERIFIED_DRAFT':os._exit(73)
  return result
 w.ledger.transition=cut
w.draft(t,w.state(t)['snapshot'],True)
raise RuntimeError('Cut was not reached')
'''

class ReviewRecoveryTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.w=Workspace(self.root);self.t=self.w.owner_token
 def change(self):
  return self.w.update_evidence(self.t,self.w.state(self.t)['revision'],{'acceptance-report':'SYNTHETIC_NEW_VERSION_PRIVATE'})
 def approve(self):
  s=self.w.state(self.t);r=self.w.invite(self.t)['token']
  self.w.approve(r,s['snapshot'],{k:True for k in s['criteria']},True)
 def crash(self,phase):
  # Separate fresh workspace per worker, not one already used by this test's self.w.
  root=self.root/phase
  env={**os.environ,'PYTHONPATH':str(Path(__file__).resolve().parent)}
  p=subprocess.run([sys.executable,'-c',WORKER,str(root),phase],cwd=Path(__file__).parent,env=env,capture_output=True,text=True,timeout=12)
  self.assertEqual(p.returncode,73,p.stderr)
  w=Workspace(root);s=w.state(w.owner_token)
  self.assertIsNotNone(s['outcome']);self.assertFalse(s['provider_record_fresh_for_session'])
  return w,s
 def test_old_link_cannot_read_new_evidence(self):
  old=self.w.invite(self.t)['token'];self.change()
  with self.assertRaisesRegex(b.Blocked,'REVIEW_LINK_STALE'):self.w.state(old)
 def test_old_link_cannot_read_new_scope(self):
  old=self.w.invite(self.t)['token'];s=self.w.state(self.t)
  self.w.update_scope(self.t,s['revision'],'Updated milestone',15000,'USD',s['criteria'])
  with self.assertRaisesRegex(b.Blocked,'REVIEW_LINK_STALE'):self.w.state(old)
 def test_old_link_invalid_even_if_bytes_same_new_revision(self):
  old=self.w.invite(self.t)['token'];s=self.w.state(self.t)
  self.w.update_evidence(self.t,s['revision'],s['artifacts'])
  with self.assertRaisesRegex(b.Blocked,'REVIEW_LINK_STALE'):self.w.state(old)
 def test_new_link_reads_current_version(self):
  self.change();r=self.w.invite(self.t)['token']
  self.assertEqual(self.w.state(r)['artifacts']['acceptance-report'],'SYNTHETIC_NEW_VERSION_PRIVATE')
 def test_restart_revokes_old_capabilities(self):
  r=self.w.invite(self.t)['token'];other=Workspace(self.root)
  for t in (self.t,r):
   with self.assertRaises(b.Blocked):other.state(t)
 def test_normal_workflow_has_fresh_readback(self):
  self.w.update_evidence(self.t,1,{'acceptance-report':FULL_REPORT});self.approve()
  s=self.w.draft(self.t,self.w.state(self.t)['snapshot'],True)
  self.assertEqual(s['outcome']['status'],'VERIFIED_DRAFT');self.assertTrue(s['provider_record_fresh_for_session'])
 def test_verified_restart_is_historical_until_refresh(self):
  self.w.update_evidence(self.t,1,{'acceptance-report':FULL_REPORT});self.approve()
  self.w.draft(self.t,self.w.state(self.t)['snapshot'],True)
  other=Workspace(self.root);s=other.state(other.owner_token)
  self.assertFalse(s['provider_record_fresh_for_session']);self.assertEqual(s['outcome']['status'],'VERIFIED_DRAFT')
  s=other.draft(other.owner_token,s['snapshot'],True)
  self.assertTrue(s['provider_record_fresh_for_session']);self.assertEqual(other.paypal.count(),1);self.assertEqual(other.paypal.post_count,0)
 def test_failed_authentication_clears_freshness(self):
  self.w.update_evidence(self.t,1,{'acceptance-report':FULL_REPORT});self.approve()
  self.w.draft(self.t,self.w.state(self.t)['snapshot'],True)
  with patch.object(self.w.paypal,'authenticate',side_effect=b.Blocked('AUTH_FAILED')):
   with self.assertRaises(b.Blocked):self.w.draft(self.t,self.w.state(self.t)['snapshot'],True)
  self.assertFalse(self.w.state(self.t)['provider_record_fresh_for_session'])
  self.assertEqual(self.w.paypal.count(),1)
 def test_failed_refresh_clears_freshness(self):
  self.w.update_evidence(self.t,1,{'acceptance-report':FULL_REPORT});self.approve()
  self.w.draft(self.t,self.w.state(self.t)['snapshot'],True)
  with patch.object(self.w.paypal,'get_invoice',side_effect=b.Blocked('READ_FAILED')):
   state=self.w.draft(self.t,self.w.state(self.t)['snapshot'],True)
  self.assertFalse(state['provider_record_fresh_for_session'])
  self.assertEqual(state['outcome']['status'],'READBACK_UNAVAILABLE')
  self.assertEqual(self.w.paypal.count(),1)
 def test_cut_before_provider_does_not_unlock_blind_retry(self):
  w,s=self.crash('after_intent');self.assertEqual(w.paypal.count(),0)
  s=w.draft(w.owner_token,s['snapshot'],True)
  self.assertEqual(s['outcome']['status'],'IN_FLIGHT');self.assertEqual(w.paypal.count(),0)
 def test_cut_after_provider_recovered_without_creation(self):
  w,s=self.crash('after_provider');self.assertEqual(s['outcome']['status'],'IN_FLIGHT');self.assertEqual(w.paypal.count(),1)
  s=w.reconcile(w.owner_token);self.assertEqual(s['outcome']['status'],'VERIFIED_DRAFT')
  self.assertEqual(w.paypal.count(),1);self.assertEqual(w.paypal.post_count,0)
 def test_cut_after_id_restores_id_and_reconciles(self):
  w,s=self.crash('after_id');self.assertEqual(s['outcome']['status'],'CREATED_UNVERIFIED')
  self.assertIsNotNone(s['outcome']['invoice_id']);s=w.reconcile(w.owner_token)
  self.assertEqual(s['outcome']['status'],'VERIFIED_DRAFT');self.assertEqual(w.paypal.count(),1);self.assertEqual(w.paypal.post_count,0)
 def test_cut_before_verified_reconciles_read_only(self):
  w,s=self.crash('before_verified');self.assertEqual(s['outcome']['status'],'CREATED_UNVERIFIED')
  s=w.reconcile(w.owner_token);self.assertTrue(s['provider_record_fresh_for_session']);self.assertEqual(w.paypal.post_count,0)
 def test_cut_after_verified_is_historical(self):
  w,s=self.crash('after_verified');self.assertEqual(s['outcome']['status'],'VERIFIED_DRAFT')
  self.assertFalse(s['provider_record_fresh_for_session']);self.assertEqual(w.paypal.count(),1)
 def test_restart_does_not_contact_provider(self):
  with patch('socket.socket',side_effect=AssertionError('No network')):Workspace(self.root)
 def test_missing_snapshot_refused_not_replaced(self):
  w,s=self.crash('after_id')
  with closing(w.connect()) as db:db.execute('DELETE FROM billing_versions');db.commit()
  with self.assertRaisesRegex(b.Blocked,'BILLING_SNAPSHOT_MISSING'):Workspace(w.root)
  self.assertEqual(w.paypal.count(),1)
 def test_corrupted_snapshot_refused(self):
  w,s=self.crash('after_id')
  with closing(w.connect()) as db:
   row=db.execute('SELECT snapshot FROM billing_versions').fetchone()[0]
   body=json.loads(db.execute('SELECT body FROM snapshots WHERE sha=?',(row,)).fetchone()[0]);body['revision']+=99
   db.execute('UPDATE snapshots SET body=? WHERE sha=?',(json.dumps(body),row));db.commit()
  with self.assertRaisesRegex(b.Blocked,'BILLING_SNAPSHOT_CORRUPTED'):Workspace(w.root)
 def test_recovery_preserves_original_billing_version_after_edit(self):
  w,s=self.crash('after_id');original=s['outcome_snapshot']
  w.update_evidence(w.owner_token,s['revision'],{'acceptance-report':'changed after attempted billing'})
  next_w=Workspace(w.root);state=next_w.state(next_w.owner_token)
  self.assertEqual(state['outcome_snapshot'],original);self.assertNotEqual(state['snapshot'],original)
 def test_stale_link_rejected_over_actual_http(self):
  r=self.w.invite(self.t)['token'];self.change();server=create_server(self.w)
  th=threading.Thread(target=server.serve_forever,daemon=True);th.start()
  try:
   with closing(http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=4)) as c:
    c.request('GET','/api/state',headers={'Authorization':'Bearer '+r})
    response=c.getresponse();body=response.read()
    self.assertEqual(response.status,403);self.assertNotIn(b'SYNTHETIC_NEW_VERSION_PRIVATE',body)
    self.assertIn(b'REVIEW_LINK_STALE',body)
  finally:server.shutdown();server.server_close();th.join(3)
 def test_new_link_allowed_over_actual_http(self):
  self.change();r=self.w.invite(self.t)['token'];server=create_server(self.w)
  th=threading.Thread(target=server.serve_forever,daemon=True);th.start()
  try:
   with closing(http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=4)) as c:
    c.request('GET','/api/state',headers={'Authorization':'Bearer '+r})
    response=c.getresponse();body=response.read();self.assertEqual(response.status,200)
    self.assertIn(b'SYNTHETIC_NEW_VERSION_PRIVATE',body)
  finally:server.shutdown();server.server_close();th.join(3)

if __name__=='__main__':unittest.main(verbosity=2)
