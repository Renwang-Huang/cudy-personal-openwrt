#!/usr/bin/env python3
"""Prepare the locked TR3600 source, feeds, external toolchain and patches."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess

project = Path(__file__).resolve().parents[3]
os.umask(0o022)
device = project / 'devices/tr3600'
lock = json.loads((device / 'build.lock.json').read_text())
source = project / 'work/tr3600-source'
subprocess.run(['bash', str(device / 'scripts/fetch-source.sh')], check=True)

toolchain = lock['toolchain']
archive = project / 'downloads' / toolchain['filename']
if not archive.exists():
    subprocess.run(['curl', '--fail', '--location', '--retry', '3',
                    '--connect-timeout', '15', '--output', str(archive),
                    toolchain['url']], check=True)
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
if digest != toolchain['sha256']:
    raise SystemExit('External toolchain SHA-256 mismatch')
toolchain_root = project / 'work' / toolchain['filename'].removesuffix('.tar.zst')
if not toolchain_root.exists():
    subprocess.run(['tar', '--zstd', '-xf', str(archive), '-C', str(project / 'work')], check=True)
compiler_root = toolchain_root / 'toolchain-aarch64_cortex-a53_gcc-14.3.0_musl'

marker = source / '.tr3600-patches.json'
patches = sorted((device / 'patches').glob('*.patch'))
hashes = {patch.name: hashlib.sha256(patch.read_bytes()).hexdigest() for patch in patches}
if hashes != lock['patches']:
    raise SystemExit('Patch contents do not match build.lock.json')
for relative, expected in lock['local_source_files'].items():
    if hashlib.sha256((device / relative).read_bytes()).hexdigest() != expected:
        raise SystemExit(f'Local build input differs from the lock: {relative}')
if marker.exists():
    if json.loads(marker.read_text()) != hashes:
        raise SystemExit('Patch inputs changed; use a fresh source checkout before preparing')
else:
    for patch in patches:
        if patch.name.startswith('003-'):
            shutil.copyfile(patch, source / 'target/linux/mediatek/patches-6.12/999-ubi-add-configurable-rootdev.patch')
        else:
            subprocess.run(['git', 'apply', '--check', str(patch)], cwd=source, check=True)
            subprocess.run(['git', 'apply', str(patch)], cwd=source, check=True)
    marker.write_text(json.dumps(hashes, indent=2) + '\n')

shutil.copyfile(device / 'config/feeds.conf', source / 'feeds.conf.default')
subprocess.run(['./scripts/feeds', 'update', '-a'], cwd=source, check=True)
for line in (source / 'feeds.conf.default').read_text().splitlines():
    if not line or line.startswith('#'):
        continue
    _, name, url = line.split()
    revision = url.split('^')[1]
    actual = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source / 'feeds' / name, text=True).strip()
    if revision != actual:
        raise SystemExit(f'Unexpected feed revision: {name} {actual}')
subprocess.run(['./scripts/feeds', 'install', '-a'], cwd=source, check=True)
shutil.copytree(device / 'source-overlay', source, dirs_exist_ok=True)
shutil.copyfile(device / 'config/minimal.config', source / '.config')
subprocess.run(['./scripts/ext-toolchain.sh', '--toolchain', str(compiler_root),
                '--overwrite-config', '--config', 'mediatek/filogic'], cwd=source, check=True)
shutil.copytree(device / 'files', source / 'files', dirs_exist_ok=True)
for path in [source / 'files', *(source / 'files').rglob('*')]:
    if path.is_dir():
        path.chmod(0o755)
subprocess.run(['make', 'defconfig'], cwd=source, check=True)
config = (source / '.config').read_text()
for setting in ['CONFIG_TARGET_mediatek_filogic_DEVICE_cudy_tr3600-v1=y',
                'CONFIG_PACKAGE_kmod-mt7990-firmware=y', 'CONFIG_PACKAGE_kmod-mt7996e=y',
                'CONFIG_PACKAGE_kmod-hwmon-pwmfan=y', 'CONFIG_PACKAGE_luci-ssl=y',
                'CONFIG_PACKAGE_luci-i18n-base-zh-cn=y', 'CONFIG_EXTERNAL_TOOLCHAIN=y']:
    if setting not in config.splitlines():
        raise SystemExit(f'Required setting missing: {setting}')
print(source)
