#!/usr/bin/env python3
"""Produce a source-bound local verification receipt. No provider/model calls.

Python 3.11+ and an installed Node.js are required for a COMPLETE result.
Uses temporary simulator workspaces. Output must be a new directory outside the
source tree. A replay is recorded as replay, never as fresh AI inference.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

ROOT = Path(__file__).resolve().parents[1]

def stamp():
    try:
        return datetime.now(ZoneInfo('Europe/Madrid')).isoformat()
    except ZoneInfoNotFoundError:
        # Windows without tzdata: still emit an aware timestamp, never fake Madrid.
        from datetime import timezone
        return datetime.now(timezone.utc).isoformat()

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def source_manifest():
    paths = set()
    for pattern in ('*.py', '*.md', 'LICENSE', 'static/*', 'tools/*.py',
                    'test*.js', 'demo_evidence/*.py', 'demo_evidence/*.json',
                    'demo_evidence/*.txt', 'submission/*.md'):
        paths.update(p for p in ROOT.glob(pattern) if p.is_file())
    return {p.relative_to(ROOT).as_posix(): sha(p) for p in sorted(paths)}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output == ROOT or ROOT in output.parents:
        parser.error('Output must be outside the source tree.')
    if output.exists():
        parser.error('Output already exists; choose a new directory. Nothing overwritten.')
    if sys.version_info < (3, 11):
        parser.error('Python 3.11 or later required.')
    output.mkdir(parents=True)
    manifest = source_manifest()
    receipt = {'started_at': stamp(), 'python': sys.version.split()[0],
               'source_sha256': manifest, 'checks': [],
               'boundaries': {'provider': 'LOCAL_SIMULATOR_NOT_PAYPAL',
                              'fresh_model_inference': False, 'browser_rendering_tested': False,
                              'paypal_sandbox_executed': False, 'customer_validation': False,
                              'external_publication': False}}
    try:
        receipt['git_commit'] = subprocess.check_output(
            ['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        receipt['working_tree_changes'] = subprocess.check_output(
            ['git', 'status', '--porcelain'], cwd=ROOT, text=True).splitlines()
    except (OSError, subprocess.CalledProcessError):
        receipt['git_commit'] = None
    env = {**os.environ, 'SCOPEPROOF_PYTHON': sys.executable,
           'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8'}

    def run(name, command, timeout=110):
        started = time.monotonic()
        try:
            p = subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                               text=True, encoding='utf-8', errors='replace', timeout=timeout)
            code, stdout, stderr = p.returncode, p.stdout, p.stderr
        except (OSError, subprocess.TimeoutExpired) as exc:
            code, stdout, stderr = -1, '', type(exc).__name__
        log = output / (name + '.log')
        log.write_text(stdout + '\n' + stderr, encoding='utf-8')
        check = {'name': name, 'exit_code': code, 'passed': code == 0,
                 'seconds': round(time.monotonic() - started, 3),
                 'log': log.name, 'log_sha256': sha(log)}
        receipt['checks'].append(check)
        print(name + ': ' + ('PASS' if code == 0 else 'FAIL'), flush=True)
        return check, stdout, stderr

    suite, stdout, stderr = run('python_and_http_faults', [sys.executable, 'run_tests.py'])
    count = re.search(r'Ran (\d+) tests', stdout + stderr)
    suite['python_test_count'] = int(count.group(1)) if count else None
    suite['five_http_scenarios_passed'] = 'Original five HTTP fault scenarios: True' in stdout
    suite['passed'] = suite['passed'] and count is not None and suite['five_http_scenarios_passed']
    node = shutil.which('node')
    if node:
        run('javascript_syntax', [node, '--check', 'static/app.js'])
        js, stdout, _ = run('javascript_controller', [node, 'test_ui_unsaved.js'], 35)
        try:
            data = json.loads(stdout)
            js['controller_check_count'] = data['check_count']
            js['passed'] = js['passed'] and data['passed'] is True
        except (ValueError, KeyError, TypeError):
            js['passed'] = False
    else:
        receipt['checks'].append({'name': 'javascript_controller', 'passed': False,
                                  'status': 'NOT_RUN_NODE_UNAVAILABLE'})
    replay, _, _ = run('saved_response_replay', [sys.executable, 'demo_evidence/run_demo.py',
                            '--app', '.', '--replay', '--output', str(output / 'replay.json')], 35)
    delivery, _, _ = run('delivery_http_flow', [sys.executable, 'tools/demo_delivery_flow.py',
                                              '--output', str(output / 'delivery')], 35)
    for check, path, flag in [(replay, output / 'replay.json', 'all_passed'),
                              (delivery, output / 'delivery' / 'flow_receipt.json', 'all_checks_passed')]:
        try:
            data = json.loads(path.read_text(encoding='utf-8'))
            check['passed'] = check['passed'] and data[flag] is True
            requests = data.get('http_requests', data.get('http_request_count'))
            check['http_request_count'] = len(requests) if isinstance(requests, list) else requests
        except (OSError, ValueError, KeyError, TypeError):
            check['passed'] = False
    receipt['source_unchanged_during_run'] = source_manifest() == manifest
    receipt['completed_at'] = stamp()
    receipt['all_checks_passed'] = receipt['source_unchanged_during_run'] and all(c['passed'] for c in receipt['checks'])
    receipt['status'] = 'LOCAL_CHECKS_PASSED' if receipt['all_checks_passed'] else 'FAILED_OR_INCOMPLETE'
    (output / 'verification.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(receipt['status'] + ': ' + str(output / 'verification.json'))
    return 0 if receipt['all_checks_passed'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
