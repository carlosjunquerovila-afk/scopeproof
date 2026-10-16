#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Executable fault demo over LOOPBACK HTTP; NOT PayPal and NOT live AI."""
import copy
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import socket
import tempfile
import threading
import urllib.error
import urllib.request

import scopeproof_guard as g
import scopeproof_bridge as b
from test_scopeproof_bridge import FakePayPal

@contextmanager
def mock_http():
    fake = FakePayPal()
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self): self.respond()
        def do_GET(self): self.respond()
        def respond(self):
            n = int(self.headers.get('Content-Length','0'))
            body = self.rfile.read(n) if n else None
            try:
                reply = fake(self.command,b.PAYPAL+self.path,dict(self.headers),body)
            except TimeoutError:
                # Deliberately lose the response after the mock has stored an invoice.
                self.close_connection = True
                self.connection.shutdown(socket.SHUT_RDWR)
                return
            data = json.dumps(reply.body).encode()
            self.send_response(reply.status);self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    port=server.server_address[1]
    def transport(method,url,headers,body):
        assert url.startswith(b.PAYPAL+'/')
        target=f'http://127.0.0.1:{port}'+url[len(b.PAYPAL):]
        req=urllib.request.Request(target,headers=headers,data=body,method=method)
        try:
            response=urllib.request.urlopen(req,timeout=3)
        except urllib.error.HTTPError as ex:return b.Reply(ex.code,{})
        with response:return b.Reply(response.status,b.parse_json(response.read(b.MAX_RESPONSE+1)))
    try:yield fake,transport
    finally:server.shutdown();server.server_close();thread.join(3)

def main():
    scenarios=[]
    for scenario in ('happy_path','lost_response','remote_amount_changed','parallel_clicks','stale_evidence'):
        with tempfile.TemporaryDirectory() as td,mock_http() as (fake,http):
            scope,art,approval=g.example()
            signer=b.LocalSigner(b'DEMO-LOCAL-SIGNER-NOT-A-REAL-SECRET')
            draft=b.safe_draft(scope,'homepage',art,approval)
            envelope=signer.issue(draft,reviewer='DEMO_LOCAL_REVIEWER',accepted=True)
            ledger=b.Ledger(Path(td)/'ledger.db')
            paypal=b.SandboxPayPal('MOCK-CLIENT','MOCK-SECRET',transport=http)
            def execute():return b.execute(scope,'homepage',art,approval,envelope,signer,ledger,paypal)
            if scenario=='lost_response':fake.failure='after_create'
            if scenario=='remote_amount_changed':fake.mutate=lambda x:x['amount'].update(value='999.99')
            if scenario=='stale_evidence':art['acceptance-report']=b'not the approved bytes'
            if scenario=='parallel_clicks':
                barrier=threading.Barrier(6);out=[]
                def worker():barrier.wait(5);out.append(execute()['status'])
                threads=[threading.Thread(target=worker) for _ in range(6)]
                for t in threads:t.start()
                for t in threads:t.join(10)
                assert len(out)==6 and not any(t.is_alive() for t in threads)
                statuses=sorted(out)
            else:
                try:statuses=[execute()['status']]
                except g.Refused:statuses=['BLOCKED_STALE_EVIDENCE']
                if scenario=='lost_response':
                    fake.failure=None
                    statuses.append(execute()['status'])
                    key=draft['billing_key']
                    statuses.append(b.reconcile(ledger,paypal,key,next(iter(fake.invoices)))['status'])
                if scenario=='happy_path':statuses.append(execute()['status'])
            checks={
                'happy_path':lambda:statuses==['VERIFIED_DRAFT','VERIFIED_DRAFT'] and fake.creates==1,
                'lost_response':lambda:statuses==['UNKNOWN','UNKNOWN','VERIFIED_DRAFT'] and fake.creates==1,
                'remote_amount_changed':lambda:statuses==['REVIEW_REQUIRED'] and fake.creates==1,
                'parallel_clicks':lambda:fake.creates==1 and 'VERIFIED_DRAFT' in statuses,
                'stale_evidence':lambda:statuses==['BLOCKED_STALE_EVIDENCE'] and len(fake.calls)==0,
            }
            assert checks[scenario](),(scenario,statuses,fake.calls)
            scenarios.append({'scenario':scenario,'states':statuses,'http_requests':[list(x) for x in fake.calls],
                'mock_create_requests':fake.creates,'mock_invoice_count':len(fake.invoices),
                'events_verified':ledger.check_events(),'passed':True})
    result={'provenance':'LOOPBACK_HTTP_MOCK_NOT_PAYPAL','real_paypal_calls':0,'model_inferences':0,
            'real_payments':0,'scenarios':scenarios,'all_passed':True}
    print(json.dumps(result,indent=2))
    return result
if __name__=='__main__':main()
