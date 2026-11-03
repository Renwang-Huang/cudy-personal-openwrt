#!/usr/bin/env python3
"""Prepare a verified, offline UI kit and local visual fixtures. Never connects to a router."""
import argparse
import hashlib
import json
import shutil
import subprocess
import tarfile
import tempfile
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]


def valid(path, item):
    return path.is_file() and not path.is_symlink() and path.stat().st_size == item['bytes'] and hashlib.blake2b(path.read_bytes(), digest_size=32).hexdigest() == item['content_id']


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=REPO / 'work/tr1200-ui-argon-3.1.2')
    parser.add_argument('--apk', type=Path, default=REPO / 'work/tr1200-v0.1.1-imagebuilder/staging_dir/host/bin/apk')
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    lock = json.loads((HERE / 'artifacts.lock.json').read_text())
    source = lock['source']
    if not valid(REPO / source['path'], source):
        raise SystemExit('Archived theme source verification failed.')
    kit = output / 'offline-kit'
    packages = kit / 'packages'
    packages.mkdir(parents=True, exist_ok=True)
    for item in lock['packages']:
        path = packages / item['filename']
        if not path.exists():
            temporary = path.with_suffix('.part')
            with urllib.request.urlopen(item['url'], timeout=60) as response:
                temporary.write_bytes(response.read())
            if not valid(temporary, item):
                raise SystemExit('Downloaded package verification failed: ' + item['name'])
            temporary.replace(path)
        if not valid(path, item):
            raise SystemExit('Cached package verification failed: ' + item['name'])
        print('Verified:', item['name'], item['version'])
    for name in ('apply.sh', 'rollback.sh', 'README.md', 'VALIDATION.md', 'validation.json', 'FIELD-TEST.md', 'field-validation.json'):
        shutil.copy2(HERE / name, kit / name)
    # Transfer check on BusyBox. Source authenticity is checked against the fixed lock above.
    checksums = ''.join(hashlib.md5((packages / p['filename']).read_bytes(), usedforsecurity=False).hexdigest() + '  packages/' + p['filename'] + '\n' for p in lock['packages'])
    (kit / 'packages.verify').write_text(checksums)
    archive = output / 'tr1200-argon-3.1.2-offline-kit.tar.gz'
    with tarfile.open(archive, 'w:gz') as tar:
        for name in ('apply.sh', 'rollback.sh', 'README.md', 'VALIDATION.md', 'validation.json', 'FIELD-TEST.md', 'field-validation.json', 'packages.verify', 'packages'):
            tar.add(kit / name, arcname='tr1200-argon-3.1.2/' + name)
    if args.apk.is_file():
        theme = next(item for item in lock['packages'] if item['name'] == 'luci-theme-argon')
        preview = output / 'preview'
        with tempfile.TemporaryDirectory(prefix='argon-extract-', dir=output) as temporary:
            unpacked = Path(temporary)
            result = subprocess.run([str(args.apk.resolve()), 'extract', '--allow-untrusted', '--no-chown', '--destination', str(unpacked), str(packages / theme['filename'])], capture_output=True)
            if result.returncode:
                raise SystemExit('Theme extraction failed.')
            shutil.copytree(HERE / 'preview', preview, dirs_exist_ok=True)
            shutil.copytree(unpacked / 'www/luci-static/argon', preview / 'assets/argon', dirs_exist_ok=True)
        print('Local preview:', preview / 'overview.html')
    else:
        print('Preview assets skipped; pass --apk with an APK v3 host tool to generate them.')
    print('Offline kit:', archive)
    print('No router was contacted.')


if __name__ == '__main__':
    main()
