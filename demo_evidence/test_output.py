#!/usr/bin/env python3
"""One HTTP replay plus CLI guards: external output must not mutate packaged files."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile

HERE = Path(__file__).resolve().parent

def hashes():
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in HERE.iterdir() if p.is_file()}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=HERE.parent / 'ScopeProof_app_candidate')
    args = parser.parse_args()
    original = hashes()
    with tempfile.TemporaryDirectory(prefix='scopeproof-result-test-') as td:
        out = Path(td) / 'replay.json'
        cmd = [sys.executable, str(HERE / 'run_demo.py'), '--app', str(args.app)]
        invalid = subprocess.run(cmd + ['--fresh', '--output', str(out)], capture_output=True, text=True)
        assert invalid.returncode == 2 and '--output is available only with --replay' in invalid.stderr
        protected = subprocess.run(cmd + ['--replay', '--output', str(HERE / 'fresh_run.json')],
                                   capture_output=True, text=True)
        assert protected.returncode == 2 and '--output must not replace' in protected.stderr
        done = subprocess.run(cmd + ['--replay', '--output', str(out)], capture_output=True, text=True)
        assert done.returncode == 0, done.stderr
        result = json.loads(out.read_text())
        assert result['all_passed'] is True
        assert result['mode'] == 'FROZEN_EXTERNAL_RESPONSE_REPLAY'
        assert len(result['http_requests']) == 16
        assert result['checks']['draft_retry']['create_requests'] == 1
        assert hashes() == original, 'Packaged files changed during external-output replay'
    print('PASS: one actual HTTP replay, external result, unchanged packaged files, CLI receipt guards.')

if __name__ == '__main__':
    main()
