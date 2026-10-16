#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Connection-gated CLI. No default remote requests, payments or uploads.

No credentials are accepted as CLI arguments, written in receipts or printed.
Configure the environment using your operating system's secret handling.
"""
import argparse
from contextlib import closing
from dataclasses import replace
from datetime import datetime
import getpass
import hashlib
import json
import os
from pathlib import Path
import socket
import sqlite3
import stat
import sys
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

import scopeproof_guard as g
import scopeproof_bridge as b


def preflight(probe_network=False):
    present={name:bool(os.environ.get(name)) for name in (
        'PAYPAL_SANDBOX_CLIENT_ID','PAYPAL_SANDBOX_CLIENT_SECRET',
        'PAYPAL_SANDBOX_SELLER_EMAIL','PAYPAL_SANDBOX_BUYER_EMAIL',
        'OPENAI_API_KEY','SCOPEPROOF_AI_MODEL')}
    network={}
    if probe_network:
        for host in ('api-m.sandbox.paypal.com','api.openai.com'):
            try:
                socket.getaddrinfo(host,443)
                network[host]='DNS_RESOLVED_NOT_AUTHENTICATED'
            except OSError:
                network[host]='DNS_FAILED'
    paypal_ok=all(present[k] for k in present if k.startswith('PAYPAL_'))
    ai_ok=present['OPENAI_API_KEY'] and present['SCOPEPROOF_AI_MODEL']
    return {'time_madrid':datetime.now(ZoneInfo('Europe/Madrid')).isoformat(),
        'credentials_present_no_values':present,'network':network,
        'paypal_config_complete':paypal_ok,'ai_config_complete':ai_ok,
        'provider_authentication_verified':False,'external_model_inference_verified':False,
        'real_paypal_draft_verified':False,'real_money_actions_implemented':False,
        'status':'CONFIGURED_NOT_AUTHENTICATED' if paypal_ok and ai_ok else 'BLOCKED_CONFIGURATION',
        'new_spending_authorized':False}


def safe_directory(path: Path):
    if path.exists():
        b.require(not path.is_symlink() and path.is_dir(),'UNSAFE_WORKSPACE')
    else:path.mkdir(parents=True,mode=0o700)
    # Private by default on POSIX; Windows users must review folder ACLs.
    if os.name=='posix':path.chmod(0o700)


def local_signing_key(path: Path):
    if path.exists():
        b.require(not path.is_symlink() and path.is_file(),'UNSAFE_SIGNING_FILE')
        if os.name=='posix':b.require(stat.S_IMODE(path.stat().st_mode)&0o077==0,'SIGNING_FILE_PERMISSIONS')
        key=path.read_bytes();b.require(len(key)==32,'BAD_SIGNING_KEY');return key
    key=os.urandom(32)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'wb') as out:out.write(key)
    return key


def sandbox_draft(workspace, confirm):
    b.require(confirm is True,'CONFIRM_SANDBOX_DRAFT_REQUIRED')
    client=b.SandboxPayPal.from_env()
    seller=os.environ.get('PAYPAL_SANDBOX_SELLER_EMAIL','')
    buyer=os.environ.get('PAYPAL_SANDBOX_BUYER_EMAIL','')
    b.require(bool(seller) and bool(buyer),'SANDBOX_TEST_EMAILS_REQUIRED')
    safe_directory(workspace)
    b.require((workspace/'approval.key').exists() or not (workspace/'sandbox-ledger.db').exists(),
              'SIGNING_KEY_MISSING_WITH_EXISTING_LEDGER')
    key=local_signing_key(workspace/'approval.key')
    project_id=sandbox_project_id(workspace,key)
    # Demo-only synthetic artifact. This is not a real client's delivery approval.
    scope,artifacts,approval=g.example()
    scope=replace(scope,project_id=project_id,recipient=buyer,sender=seller)
    scope.validate()
    approval=replace(approval,scope_sha256=scope.fingerprint(),approved_by='local-demo-review')
    draft=b.safe_draft(scope,'homepage',artifacts,approval)
    signer=b.LocalSigner(key)
    envelope=signer.issue(draft,reviewer=getpass.getuser(),accepted=True)
    ledger=b.Ledger(workspace/'sandbox-ledger.db')
    result=b.execute(scope,'homepage',artifacts,approval,envelope,signer,ledger,client)
    result.update(time_madrid=datetime.now(ZoneInfo('Europe/Madrid')).isoformat(),
                  synthetic_demo_evidence=True,amount='125.00',currency='EUR')
    # Local only. Do not publish these files unreviewed; may include sandbox IDs.
    receipt=workspace/('sandbox-receipt-'+datetime.now().strftime('%Y%m%dT%H%M%S%f')+'.json')
    receipt.write_text(json.dumps(result,indent=2)+'\n')
    if os.name=='posix':receipt.chmod(0o600)
    return result


def sandbox_project_id(workspace, signing_key):
    """Stable per private CLI workspace; retain any existing legacy intent.

    The signing key is generated once with exclusive creation. Only its hash
    contributes to the public project ID; the private key never leaves disk.
    Old ledgers must not acquire a new billing identity during an upgrade.
    """
    database=workspace/'sandbox-ledger.db'
    b.require(not database.is_symlink(),'UNSAFE_LEDGER')
    if database.exists():
        legacy=b.sha(['demo-web-project','homepage'])
        with closing(sqlite3.connect(database)) as db:
            row=db.execute('SELECT 1 FROM intents WHERE key=?',(legacy,)).fetchone()
        if row is not None:return 'demo-web-project'
    return 'sp-'+hashlib.sha256(b'scopeproof-cli-project-v1\0'+signing_key).hexdigest()[:32]


def ai_check(workspace, allow_metered):
    a=b.OpenAIAnalyzer(os.environ.get('OPENAI_API_KEY',''),os.environ.get('SCOPEPROOF_AI_MODEL',''),
                       spending_authorized=allow_metered)
    criteria={'mobile':'The homepage must work on a mobile phone.',
              'form':'The contact form must successfully deliver messages.'}
    evidence={'review':'The layout was reviewed on a mobile device. The contact form does not send emails yet.'}
    out=a.analyze(criteria,evidence)
    safe_directory(workspace)
    out.update(synthetic_test_evidence=True,ready_to_invoice=False)
    (workspace/'ai-review.json').write_text(json.dumps(out,indent=2)+'\n')
    return out


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=['preflight','sandbox-draft','ai-check','reconcile'],nargs='?',default='preflight')
    p.add_argument('--workspace',type=Path,default=Path('.scopeproof-private'))
    p.add_argument('--probe-network',action='store_true')
    p.add_argument('--confirm-sandbox-draft',action='store_true')
    p.add_argument('--allow-metered-ai-call',action='store_true')
    p.add_argument('--billing-key');p.add_argument('--invoice-id')
    args=p.parse_args()
    try:
        if args.mode=='preflight':out=preflight(args.probe_network)
        elif args.mode=='sandbox-draft':out=sandbox_draft(args.workspace,args.confirm_sandbox_draft)
        elif args.mode=='ai-check':out=ai_check(args.workspace,args.allow_metered_ai_call)
        else:
            b.require(args.billing_key is not None,'BILLING_KEY_REQUIRED')
            database=args.workspace/'sandbox-ledger.db'
            b.require(database.is_file() and not database.is_symlink(),'LEDGER_REQUIRED')
            out=b.reconcile(b.Ledger(database),b.SandboxPayPal.from_env(),args.billing_key,args.invoice_id)
        print(json.dumps(out,indent=2))
        return 0 if out.get('status') not in ('BLOCKED_CONFIGURATION','UNKNOWN','IN_FLIGHT',
            'CREATED_UNVERIFIED','CREATE_REJECTED','REVIEW_REQUIRED','READBACK_UNAVAILABLE') else 2
    except (b.Blocked,g.Refused) as ex:
        print(json.dumps({'status':'BLOCKED','reason':str(ex),'not_a_payment':True}));return 2
    except Exception:
        # Do not echo raw provider exceptions or local secret paths.
        print(json.dumps({'status':'FAILED_CLOSED','reason':'UNEXPECTED_ERROR_REVIEW_LOCALLY'}));return 2

if __name__=='__main__':raise SystemExit(main())
