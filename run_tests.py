#!/usr/bin/env python3
"""Run local policy/workflow/HTTP tests. Uses simulator only; no external accounts."""
from pathlib import Path
import subprocess,sys,json
ROOT=Path(__file__).resolve().parent
MODULES=['test_scopeproof_guard','test_scopeproof_bridge','test_runner','test_workflow','test_app_http','test_import_review','test_review_recovery','test_evidence_limits','test_delivery_report','test_unicode_boundary']
def main():
 p=subprocess.run([sys.executable,'-W','error::ResourceWarning','-m','unittest','-v',*MODULES],cwd=ROOT,timeout=75)
 if p.returncode:return p.returncode
 p=subprocess.run([sys.executable,'demo_http.py'],cwd=ROOT,capture_output=True,text=True,timeout=20)
 if p.returncode:print(p.stderr);return p.returncode
 out=json.loads(p.stdout);print('Original five HTTP fault scenarios:',out['all_passed'])
 return 0 if out['all_passed'] else 1
if __name__=='__main__':raise SystemExit(main())
