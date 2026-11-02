#!/usr/bin/env python3
"""Restore the checksummed source cache attached to this candidate release."""
import hashlib
import json
from pathlib import Path
import subprocess

project = Path(__file__).resolve().parents[3]
lock = json.loads((project / 'devices/tr3600/build.lock.json').read_text())
cache = lock['source_cache']
archive = project / 'downloads' / cache['filename']
archive.parent.mkdir(exist_ok=True)
if not archive.exists():
    partial = archive.with_name(archive.name + '.part')
    subprocess.run(['curl', '--fail', '--location', '--retry', '3',
                    '--connect-timeout', '15', '--output', str(partial),
                    cache['url']], check=True)
    to_check = partial
else:
    to_check = archive
digest = hashlib.sha256()
with to_check.open('rb') as source:
    for chunk in iter(lambda: source.read(4 * 1024 * 1024), b''):
        digest.update(chunk)
if digest.hexdigest() != cache['sha256']:
    raise SystemExit('Source cache checksum mismatch')
if to_check != archive:
    to_check.rename(archive)
source_dir = project / 'work/tr3600-source'
if not (source_dir / 'Makefile').exists():
    raise SystemExit('Run devices/tr3600/scripts/prepare.py first')
subprocess.run(['tar', '--zstd', '-xf', str(archive), '-C', str(source_dir)], check=True)
print('Locked source downloads restored.')
