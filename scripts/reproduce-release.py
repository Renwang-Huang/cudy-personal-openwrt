#!/usr/bin/env python3
"""Fetch verified release assets, then rebuild without APK network access."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

project = Path(__file__).resolve().parents[1]
release = json.loads((project / 'release-assets.lock.json').read_text())
assets = project / 'release-assets'
assets.mkdir(exist_ok=True)
for item in release['assets']:
    folder = project / 'downloads' if item['role'] == 'imagebuilder' else assets
    folder.mkdir(exist_ok=True)
    path = folder / item['filename']
    if not path.exists():
        subprocess.run(['curl', '--fail', '--location', '--retry', '3',
                        '--connect-timeout', '15', '--output', str(path),
                        item['url']], check=True)
    digest = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != item['sha256']:
        raise SystemExit(f'Asset checksum mismatch: {path.name}')

subprocess.run(['python3', str(project / 'scripts/prepare.py')], check=True)
build_lock = json.loads((project / 'build.lock.json').read_text())
builder = project / 'work' / build_lock['imagebuilder']['filename'].removesuffix('.tar.zst')
cache = assets / release['package_cache']
# Replace the package cache with the exact release cache. OpenWrt's recursive
# make clears MAKEFLAGS, so an APK= command-line override is insufficient.
# Temporarily amend only the host-side APK invocation in its Makefile instead.
cache_dir = builder / 'dl'
makefile = builder / 'Makefile'
original = makefile.read_bytes()
needle = b'--cache-dir $(DL_DIR)\n'
if original.count(needle) != 1:
    raise SystemExit('Unexpected ImageBuilder Makefile; refusing to patch')
with tempfile.TemporaryDirectory(prefix='tr3000-cache-', dir=project / 'work') as temporary:
    saved = Path(temporary)
    cache_backup = saved / 'original-dl'
    if cache_dir.exists():
        cache_dir.rename(cache_backup)
    try:
        subprocess.run(['tar', '--zstd', '-xf', str(cache), '-C', str(builder)], check=True)
        makefile.write_bytes(original.replace(needle, b'--cache-dir $(DL_DIR) --no-network\n'))
        subprocess.run(['bash', str(project / 'scripts/build.sh')], check=True)
    finally:
        makefile.write_bytes(original)
        if cache_dir.exists():
            cache_dir.rename(saved / 'reproduced-dl')
        if cache_backup.exists():
            cache_backup.rename(cache_dir)
subprocess.run(['python3', str(project / 'scripts/verify-image.py')], check=True)
report = json.loads((project / 'output/verification.json').read_text())
if report['sha256'] != release['expected_image_sha256']:
    raise SystemExit('Image differs from the archived candidate; inspect output/verification.json')
print('Candidate image reproduced with identical SHA-256.')
