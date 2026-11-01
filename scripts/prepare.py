#!/usr/bin/env python3
"""Download and verify the locked official ImageBuilder, then extract it."""
import hashlib
import json
from pathlib import Path
import subprocess

project = Path(__file__).resolve().parents[1]
lock = json.loads((project / 'build.lock.json').read_text())
item = lock['imagebuilder']
archive = project / 'downloads' / item['filename']
archive.parent.mkdir(parents=True, exist_ok=True)
if not archive.exists():
    partial = archive.with_name(archive.name + '.part')
    subprocess.run(['curl', '--fail', '--location', '--retry', '3',
                    '--connect-timeout', '15', '--output', str(partial),
                    item['url']], check=True)
    archive_to_check = partial
else:
    archive_to_check = archive
h = hashlib.sha256()
with archive_to_check.open('rb') as source:
    for chunk in iter(lambda: source.read(1024 * 1024), b''):
        h.update(chunk)
digest = h.hexdigest()
if digest != item['sha256']:
    raise SystemExit('ImageBuilder SHA-256 mismatch; refusing extraction')
if archive_to_check != archive:
    archive_to_check.rename(archive)
work = project / 'work'
work.mkdir(exist_ok=True)
builder = work / item['filename'].removesuffix('.tar.zst')
if not (builder / 'Makefile').exists():
    subprocess.run(['tar', '--zstd', '-xf', str(archive), '-C', str(work)], check=True)
print(builder)
