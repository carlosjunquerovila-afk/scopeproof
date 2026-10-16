from unittest import TestCase,main
from contextlib import closing
import http.client,json,tempfile,threading
from pathlib import Path
from app import create_server,ProcessLock
from workflow import Workspace,FULL_REPORT

class HTTPTests(TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
  self.w=Workspace(self.root);self.server=create_server(self.w);self.origin=self.server.origin
  self.thread=threading.Thread(target=self.server.serve_forever,daemon=True);self.thread.start()
 def tearDown(self):
  self.server.shutdown();self.server.server_close();self.thread.join(3);self.temp.cleanup()
 def req(self,path,body=None,headers=None,token=True,method=None):
  h={'Authorization':'Bearer '+self.w.owner_token} if token else {}
  if body is not None:
   h.update({'Origin':self.origin,'X-ScopeProof-Request':'1','Content-Type':'application/json'})
   raw=body if isinstance(body,str) else json.dumps(body)
  else:raw=None
  h.update(headers or {})
  with closing(http.client.HTTPConnection('127.0.0.1',self.server.server_port,timeout=4)) as con:
   con.request(method or ('POST' if raw is not None else 'GET'),path,body=raw,headers=h)
   r=con.getresponse();return r.status,dict(r.getheaders()),r.read()
 def test_health_public(self):
  code,h,raw=self.req('/health',token=False);self.assertEqual(code,200);self.assertEqual(json.loads(raw)['mode'],'demo')
 def test_state_requires_auth(self):self.assertEqual(self.req('/api/state',token=False)[0],403)
 def test_no_auth_post_has_no_side_effect(self):
  self.assertEqual(self.req('/api/invite',{},token=False)[0],400);self.assertFalse(self.w.review_tokens)
 def test_foreign_origin_rejected(self):
  self.assertEqual(self.req('/api/invite',{},headers={'Origin':'https://evil.example'})[0],400);self.assertFalse(self.w.review_tokens)
 def test_null_origin_rejected(self):self.assertEqual(self.req('/api/invite',{},headers={'Origin':'null'})[0],400)
 def test_rebinding_host_rejected(self):self.assertEqual(self.req('/health',headers={'Host':'attacker.example'})[0],403)
 def test_csrf_header_required(self):self.assertEqual(self.req('/api/invite',{},headers={'X-ScopeProof-Request':'0'})[0],400)
 def test_no_cors(self):
  status,h,_=self.req('/api/state',method='OPTIONS');self.assertEqual(status,403);self.assertNotIn('Access-Control-Allow-Origin',h)
 def test_oversized_request_rejected(self):self.assertEqual(self.req('/api/evidence',{'x':'A'*130000})[0],400)
 def test_duplicate_json_keys_rejected(self):self.assertEqual(self.req('/api/evidence','{"revision":1,"revision":2,"artifacts":{}}')[0],400)
 def test_unexpected_fields_rejected(self):self.assertEqual(self.req('/api/draft',{'snapshot':'x','confirm':True,'amount':999})[0],400)
 def test_no_payment_or_send_endpoints(self):
  for path in ['/api/pay','/api/send','/api/refund','/api/capture']:
   with self.subTest(path=path):self.assertEqual(self.req(path,{})[0],404)
 def test_path_traversal_not_served(self):self.assertEqual(self.req('/../workflow.py')[0],404)
 def test_query_tokens_refused(self):self.assertEqual(self.req('/api/state?token=x')[0],403)
 def test_html_security_headers(self):
  status,h,raw=self.req('/',token=False);self.assertEqual(status,200)
  self.assertIn("frame-ancestors 'none'",h['Content-Security-Policy']);self.assertEqual(h['Referrer-Policy'],'no-referrer')
  self.assertNotIn(self.w.owner_token.encode(),raw)
 def test_evidence_update_real_http(self):
  code,_,raw=self.req('/api/evidence',{'revision':1,'artifacts':{'acceptance-report':FULL_REPORT}})
  self.assertEqual(code,200);self.assertEqual(json.loads(raw)['revision'],2)
 def test_export_has_no_private_key(self):
  code,_,raw=self.req('/api/export');self.assertEqual(code,200)
  self.assertNotIn(self.w.owner_token.encode(),raw);self.assertNotIn((self.root/'signing.key').read_bytes(),raw)
 def test_imported_review_validates_via_http(self):
  s=self.w.state(self.w.owner_token)
  package={'snapshot':s['snapshot'],'analysis':{'criteria':[dict(criterion_id=k,status='unclear',evidence_id=None,quote=None,reason='Needs actual review') for k in s['criteria']]}}
  code,_,raw=self.req('/api/import-analysis',{'package_text':json.dumps(package)})
  self.assertEqual(code,200);state=json.loads(raw)
  self.assertFalse(state['approved_current']);self.assertFalse(state['analysis']['live_inference'])
 def test_prompt_endpoint_returns_current_snapshot_without_contacts(self):
  code,_,raw=self.req('/api/review-prompt');self.assertEqual(code,200)
  self.assertEqual(json.loads(raw)['snapshot'],self.w.state(self.w.owner_token)['snapshot'])
  self.assertNotIn(b'buyer@example.com',raw)
 def test_workspace_lock_prevents_two_processes(self):
  with ProcessLock(self.root/'one.lock'):
   with self.assertRaises(RuntimeError):
    with ProcessLock(self.root/'one.lock'):pass
if __name__=='__main__':main(verbosity=2)
