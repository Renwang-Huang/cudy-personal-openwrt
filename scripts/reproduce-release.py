#!/usr/bin/env python3
"""Rebuild a published candidate with its archived APK cache, offline."""
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
# Preserve OpenWrt package signature checking and the original repository URLs.
# APK resolves the signed indexes and packages from the archived cache.
apk = ('APK=$(STAGING_DIR_HOST)/bin/apk --root $(TARGET_DIR) '
       '--keys-dir $(TOPDIR)/keys --repositories-file $(TOPDIR)/repositories '
       '--repository $(PACKAGE_DIR)/packages.adb --cache-dir $(DL_DIR) --no-network')
with tempfile.TemporaryDirectory(prefix='tr3000-apk-cache-', dir=project / 'work') as temporary:
    temp = Path(temporary)
    subprocess.run(['tar', '--zstd', '-xf', str(cache), '-C', str(temp)], check=True)
    subprocess.run(['bash', str(project / 'scripts/build.sh'),
                    f'DL_DIR={temp / "dl"}', apk], check=True)
subprocess.run(['python3', str(project / 'scripts/verify-image.py')], check=True)
report = json.loads((project / 'output/verification.json').read_text())
if report['sha256'] != release['expected_image_sha256']:
    raise SystemExit('Image differs from the archived candidate; inspect output/verification.json')
print('Candidate image reproduced with identical SHA-256.')
