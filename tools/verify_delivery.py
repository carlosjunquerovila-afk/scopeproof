#!/usr/bin/env python3
"""Verify the visible content of a ScopeProof delivery HTML record, offline."""
from pathlib import Path
import argparse
import json
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from delivery_report import verify_export


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    try:
        if args.report.stat().st_size > 2_000_000:
            raise ValueError('DELIVERY_FILE_LIMIT')
        result = verify_export(args.report.read_text(encoding='utf-8'))
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(json.dumps({'verified': False, 'reason': str(error)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
