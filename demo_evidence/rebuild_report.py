#!/usr/bin/env python3
"""Compatibility entry point for the report renderer; same CLI as build_report.py."""
from pathlib import Path
import runpy

if __name__ == '__main__':
    runpy.run_path(str(Path(__file__).resolve().with_name('build_report.py')), run_name='__main__')
