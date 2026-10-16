# SPDX-License-Identifier: MIT
import json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import run_scopeproof as r
import scopeproof_bridge as b
import scopeproof_guard as g
class RunnerTests(unittest.TestCase):
 def test_preflight_never_prints_values(self):
  with patch.dict(os.environ,{'PAYPAL_SANDBOX_CLIENT_ID':'DONT-PRINT-ME'},clear=True):
   out=r.preflight();self.assertNotIn('DONT-PRINT-ME',json.dumps(out));self.assertFalse(out['provider_authentication_verified'])
 def test_preflight_missing_is_blocked(self):
  with patch.dict(os.environ,{},clear=True):self.assertEqual(r.preflight()['status'],'BLOCKED_CONFIGURATION')
 def test_cli_default_has_no_remote_action(self):
  env={'PATH':os.environ['PATH']}
  out=subprocess.run([sys.executable,str(Path(r.__file__))],env=env,capture_output=True,text=True,timeout=10)
  self.assertEqual(out.returncode,2);self.assertEqual(json.loads(out.stdout)['status'],'BLOCKED_CONFIGURATION')
 def test_sandbox_requires_confirmation(self):
  with tempfile.TemporaryDirectory() as td,self.assertRaises(b.Blocked):r.sandbox_draft(Path(td),False)
 def test_no_implicit_ai_spend(self):
  with tempfile.TemporaryDirectory() as td,self.assertRaises(b.Blocked):r.ai_check(Path(td),False)
 def test_local_signing_key_persists_privately(self):
  with tempfile.TemporaryDirectory() as td:
   path=Path(td)/'key';a=r.local_signing_key(path);self.assertEqual(a,r.local_signing_key(path));self.assertEqual(len(a),32)
   if os.name=='posix':self.assertEqual(path.stat().st_mode&0o777,0o600)
 def test_symlink_signing_key_refused(self):
  with tempfile.TemporaryDirectory() as td:
   target=Path(td)/'private';target.write_bytes(b'x'*32);link=Path(td)/'link';link.symlink_to(target)
   with self.assertRaises(b.Blocked):r.local_signing_key(link)
 def test_cli_project_identity_is_stable_and_workspace_specific(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);one=root/'one';two=root/'two';one.mkdir();two.mkdir()
   key=r.local_signing_key(one/'approval.key')
   first=r.sandbox_project_id(one,key)
   again=r.sandbox_project_id(one,r.local_signing_key(one/'approval.key'))
   other=r.sandbox_project_id(two,r.local_signing_key(two/'approval.key'))
   self.assertEqual(first,again);self.assertNotEqual(first,other)
   self.assertRegex(first,r'^sp-[a-f0-9]{32}$')
 def test_legacy_cli_ledger_keeps_old_project_identity(self):
  with tempfile.TemporaryDirectory() as td:
   root=Path(td);scope,artifacts,approval=g.example()
   draft=b.safe_draft(scope,'homepage',artifacts,approval)
   b.Ledger(root/'sandbox-ledger.db').claim(draft,'fixture','INJECTED_TEST_TRANSPORT')
   self.assertEqual(r.sandbox_project_id(root,b'x'*32),'demo-web-project')
 def test_missing_cli_key_with_existing_ledger_blocks_before_provider_call(self):
  with tempfile.TemporaryDirectory() as td,patch.dict(os.environ,{
    'PAYPAL_SANDBOX_CLIENT_ID':'fake-client','PAYPAL_SANDBOX_CLIENT_SECRET':'fake-secret',
    'PAYPAL_SANDBOX_SELLER_EMAIL':'seller@business.example.com',
    'PAYPAL_SANDBOX_BUYER_EMAIL':'buyer@personal.example.com'},clear=True):
   root=Path(td);b.Ledger(root/'sandbox-ledger.db')
   with patch.object(b.SandboxPayPal,'authenticate') as authenticate:
    with self.assertRaisesRegex(b.Blocked,'SIGNING_KEY_MISSING_WITH_EXISTING_LEDGER'):
     r.sandbox_draft(root,True)
    authenticate.assert_not_called()
if __name__=='__main__':unittest.main()
