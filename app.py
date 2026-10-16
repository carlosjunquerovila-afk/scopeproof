#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""ScopeProof local review application. Run python app.py; only localhost is bound.
Default: simulator, not PayPal. Add --sandbox for deliberate sandbox configuration.
No invoice send/capture/refund routes. No automatic model or dependency downloads.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import threading
import webbrowser
import scopeproof_bridge as bridge
import scopeproof_guard as guard
from workflow import Workspace

ROOT=Path(__file__).resolve().parent
BODY_LIMIT=120_000
class ProcessLock:
    def __init__(self,path):self.path=path;self.file=None
    def __enter__(self):
        if self.path.is_symlink():raise RuntimeError('Lock symlink refused')
        self.file=self.path.open('a+b');os.chmod(self.path,0o600)
        self.file.seek(0);self.file.write(b'0');self.file.flush();self.file.seek(0)
        try:
            if os.name=='nt':
                import msvcrt;msvcrt.locking(self.file.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl;fcntl.flock(self.file,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:
            self.file.close();raise RuntimeError('Workspace already running; use its existing session') from None
        return self
    def __exit__(self,*args):self.file.close()

def exact_fields(data,*keys):
    bridge.require(type(data) is dict and set(data)==set(keys),'REQUEST_FIELDS')

class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'
    def log_message(self,*args):pass # Never log URLs/tokens, credentials or evidence.
    @property
    def ws(self):return self.server.workspace
    def send_data(self,status,data,content_type='application/json; charset=utf-8'):
        raw=bridge.canonical(data) if not isinstance(data,bytes) else data
        self.send_response(status)
        headers={'Content-Type':content_type,'Content-Length':str(len(raw)),
                 'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',
                 'Referrer-Policy':'no-referrer','Connection':'close',
                 'Content-Security-Policy':"default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'none'",
                 'Permissions-Policy':'camera=(), microphone=(), geolocation=()'}
        for k,v in headers.items():self.send_header(k,v)
        self.end_headers();self.wfile.write(raw);self.close_connection=True
    def check_host(self):
        bridge.require(self.headers.get_all('Host')==[self.server.expected_host], 'HOST_REFUSED')
        bridge.require(not self.headers.get('Transfer-Encoding'),'TRANSFER_ENCODING_REFUSED')
        bridge.require('?' not in self.path and '#' not in self.path,'URL_PARAMETERS_REFUSED')
    def token(self):
        values=self.headers.get_all('Authorization') or []
        bridge.require(len(values)==1 and values[0].startswith('Bearer '),'AUTH_REQUIRED')
        t=values[0][7:];self.ws.role(t);return t
    def do_GET(self):
        try:
            self.check_host()
            if self.path=='/health':return self.send_data(200,{'service':'ScopeProof','mode':self.ws.mode,'up':True})
            if self.path=='/favicon.ico':return self.send_data(204,b'','image/x-icon')
            static={'/':('index.html','text/html; charset=utf-8'), '/app.css':('app.css','text/css; charset=utf-8'), '/app.js':('app.js','text/javascript; charset=utf-8')}
            if self.path in static:
                name,kind=static[self.path];return self.send_data(200,(ROOT/'static'/name).read_bytes(),kind)
            if self.path=='/api/state':return self.send_data(200,self.ws.state(self.token()))
            if self.path=='/api/export':return self.send_data(200,self.ws.export(self.token()))
            if self.path=='/api/review-prompt':return self.send_data(200,self.ws.review_prompt(self.token()))
            self.send_data(404,{'error':'NOT_FOUND'})
        except bridge.Blocked as e:self.send_data(403,{'error':str(e)})
        except Exception:self.send_data(500,{'error':'INTERNAL_ERROR'})
    def do_POST(self):
        try:
            self.check_host();t=self.token()
            bridge.require(self.headers.get_all('Origin')==[self.server.origin],'ORIGIN_REFUSED')
            bridge.require(self.headers.get('X-ScopeProof-Request')=='1','CSRF_HEADER_REQUIRED')
            bridge.require(self.headers.get_content_type()=='application/json','JSON_REQUIRED')
            lengths=self.headers.get_all('Content-Length') or []
            bridge.require(len(lengths)==1 and re.fullmatch(r'[0-9]{1,6}',lengths[0]),'CONTENT_LENGTH_REQUIRED')
            n=int(lengths[0]);bridge.require(0<n<=BODY_LIMIT,'BODY_LIMIT')
            self.connection.settimeout(8)
            raw=self.rfile.read(n);bridge.require(len(raw)==n,'TRUNCATED_BODY')
            data=bridge.parse_json(raw)
            if self.path=='/api/evidence':
                exact_fields(data,'revision','artifacts');out=self.ws.update_evidence(t,data['revision'],data['artifacts'])
            elif self.path=='/api/scope':
                exact_fields(data,'revision','name','amount_cents','currency','criteria')
                out=self.ws.update_scope(t,data['revision'],data['name'],data['amount_cents'],data['currency'],data['criteria'])
            elif self.path=='/api/analyze':
                exact_fields(data,'engine','model');out=self.ws.review(t,data['engine'],data['model'])
            elif self.path=='/api/import-analysis':
                exact_fields(data,'package_text');out=self.ws.import_review(t,data['package_text'])
            elif self.path=='/api/invite':
                exact_fields(data);out=self.ws.invite(t);out['url']=self.server.origin+'/#token='+out.pop('token')
            elif self.path=='/api/approve':
                exact_fields(data,'snapshot','decisions','acknowledgement')
                out=self.ws.approve(t,data['snapshot'],data['decisions'],data['acknowledgement'])
            elif self.path=='/api/draft':
                exact_fields(data,'snapshot','confirm');out=self.ws.draft(t,data['snapshot'],data['confirm'])
            elif self.path=='/api/reconcile':
                exact_fields(data,'invoice_id');out=self.ws.reconcile(t,data['invoice_id'])
            elif self.path=='/api/fault':
                exact_fields(data,'fault');out=self.ws.fault(t,data['fault'])
            elif self.path=='/api/connect-paypal':
                exact_fields(data,'client_id','secret','seller','buyer','confirm')
                out=self.ws.connect_paypal(t,data['client_id'],data['secret'],data['seller'],data['buyer'],data['confirm'])
                data.clear()
            else:return self.send_data(404,{'error':'NOT_FOUND'})
            self.send_data(200,out)
        except (bridge.Blocked,guard.Refused) as e:self.send_data(400,{'error':str(e)})
        except Exception:self.send_data(500,{'error':'INTERNAL_ERROR'})
    def do_OPTIONS(self):self.send_data(403,{'error':'CROSS_ORIGIN_DISABLED'})

def create_server(workspace,port=0):
    server=ThreadingHTTPServer(('127.0.0.1',port),Handler)
    server.daemon_threads=True;server.workspace=workspace
    server.expected_host='127.0.0.1:'+str(server.server_port)
    server.origin='http://'+server.expected_host
    return server

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--sandbox',action='store_true')
    p.add_argument('--workspace',type=Path,default=Path.home()/'.scopeproof-local')
    p.add_argument('--port',type=int,default=8765)
    p.add_argument('--no-browser',action='store_true')
    a=p.parse_args();a.workspace.mkdir(mode=0o700,parents=True,exist_ok=True)
    with ProcessLock(a.workspace/'app.lock'):
        w=Workspace(a.workspace,mode='sandbox' if a.sandbox else 'demo')
        with create_server(w,a.port) as server:
            url=server.origin+'/#token='+w.owner_token
            print('ScopeProof mode:',w.mode,flush=True)
            print('Private local session — do not publish this link:',url,flush=True)
            print('Ctrl+C stops the application. No background service is installed.',flush=True)
            if not a.no_browser:webbrowser.open(url)
            try:server.serve_forever()
            except KeyboardInterrupt:pass
if __name__=='__main__':main()
