#!/usr/bin/env python3
"""Restore pinned public assets and reproduce the candidate with APK offline."""
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

project = Path(__file__).resolve().parents[3]
device = project / 'devices/tr1200'
release = json.loads((device / 'release-assets.lock.json').read_text())
for relative, expected in release['input_files_sha256'].items():
    if hashlib.sha256((device / relative).read_bytes()).hexdigest() != expected:
        raise SystemExit(f'Candidate input was modified: {relative}')
assets = project / 'release-assets' / release['tag'].removesuffix('-candidate')
assets.mkdir(parents=True, exist_ok=True)
for item in release['assets']:
    folder = project / 'downloads' if item['role'] == 'imagebuilder' else assets
    folder.mkdir(exist_ok=True)
    path = folder / item['filename']
    if not path.exists():
        partial = path.with_name(path.name + '.part')
        subprocess.run(['curl', '--fail', '--location', '--retry', '3',
                        '--connect-timeout', '15', '--output', str(partial),
                        item['url']], check=True)
        to_check = partial
    else:
        to_check = path
    digest = hashlib.sha256()
    with to_check.open('rb') as source:
        for chunk in iter(lambda: source.read(4 * 1024 * 1024), b''):
            digest.update(chunk)
    if digest.hexdigest() != item['sha256'] or to_check.stat().st_size != item['bytes']:
        raise SystemExit(f'Asset checksum/size mismatch: {path.name}')
    if to_check != path:
        to_check.rename(path)

subprocess.run(['python3', str(device / 'scripts/prepare.py')], check=True)
build_lock = json.loads((device / 'build.lock.json').read_text())
builder = project / build_lock['workspace']
cache = assets / release['package_cache']
cache_dir = builder / 'dl'
makefile = builder / 'Makefile'
original = makefile.read_bytes()
needle = b'--cache-dir $(DL_DIR)\n'
if original.count(needle) != 1:
    raise SystemExit('Unexpected official Makefile; refusing to patch APK invocation')
# ImageBuilder recursive make clears MAKEFLAGS. Apply the same temporary
# host-side APK --no-network override while restoring the pinned package cache.
with tempfile.TemporaryDirectory(prefix='tr1200-cache-', dir=project / 'work') as temporary:
    saved = Path(temporary)
    cache_backup = saved / 'original-dl'
    if cache_dir.exists():
        cache_dir.rename(cache_backup)
    try:
        subprocess.run(['tar', '--zstd', '-xf', str(cache), '-C', str(builder)], check=True)
        makefile.write_bytes(original.replace(needle, b'--cache-dir $(DL_DIR) --no-network\n'))
        subprocess.run(['bash', str(device / 'scripts/build.sh')], check=True)
    finally:
        makefile.write_bytes(original)
        if cache_dir.exists():
            cache_dir.rename(saved / 'reproduced-dl')
        if cache_backup.exists():
            cache_backup.rename(cache_dir)
subprocess.run(['python3', str(device / 'scripts/verify-image.py')], check=True)
report = json.loads((project / build_lock['output_directory'] / 'tr1200-verification.json').read_text())
if report['sha256'] != release['expected_image_sha256']:
    raise SystemExit('Rebuilt image differs from the archived candidate')
print('TR1200 candidate reproduced with identical SHA-256 and APK network disabled.')
