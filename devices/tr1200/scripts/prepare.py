#!/usr/bin/env python3
"""Verify and extract the official TR1200-compatible ImageBuilder."""
import hashlib
import json
from pathlib import Path
import subprocess

project = Path(__file__).resolve().parents[3]
device = project / 'devices/tr1200'
item = json.loads((device / 'build.lock.json').read_text())['imagebuilder']
archive = project / 'downloads' / item['filename']
archive.parent.mkdir(parents=True, exist_ok=True)
if not archive.exists():
    partial = archive.with_name(archive.name + '.part')
    subprocess.run(['curl', '--fail', '--location', '--retry', '3',
                    '--connect-timeout', '15', '--output', str(partial),
                    item['url']], check=True)
    to_check = partial
else:
    to_check = archive
digest = hashlib.sha256()
with to_check.open('rb') as source:
    for chunk in iter(lambda: source.read(4 * 1024 * 1024), b''):
        digest.update(chunk)
if digest.hexdigest() != item['sha256'] or to_check.stat().st_size != item['bytes']:
    raise SystemExit('Official ImageBuilder checksum/size mismatch')
if to_check != archive:
    to_check.rename(archive)
work = project / 'work'
work.mkdir(exist_ok=True)
builder = work / item['filename'].removesuffix('.tar.zst')
if not (builder / 'Makefile').exists():
    subprocess.run(['tar', '--zstd', '-xf', str(archive), '-C', str(work)], check=True)
print(builder)
