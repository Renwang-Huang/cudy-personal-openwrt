#!/usr/bin/env python3
"""Prepare verified official recovery files locally; never start TFTP or flash."""
import hashlib
import json
from pathlib import Path
import zipfile

project = Path(__file__).resolve().parents[3]
reference = project / 'reference/tr1200'
lock = json.loads((reference / 'archives.lock.json').read_text())
stock = next(item for item in lock['references']
             if item['filename'] == 'TR1200-R46-2.5.41-stock.zip')
archive = reference / stock['filename']
if hashlib.sha256(archive.read_bytes()).hexdigest() != stock['sha256']:
    raise SystemExit('Official stock archive SHA-256 mismatch')
with zipfile.ZipFile(archive) as bundle:
    if bundle.testzip() is not None:
        raise SystemExit('Official stock archive ZIP CRC mismatch')
    names = [name for name in bundle.namelist() if name.endswith('.bin')]
    if len(names) != 1 or not names[0].startswith('TR1200-R46-'):
        raise SystemExit('Unexpected model or archive layout')
    name = names[0]
    firmware = bundle.read(name)
    checksum, filename = bundle.read('md5.txt').decode().strip().split(None, 1)
    if filename != name or hashlib.md5(firmware).hexdigest() != checksum:
        raise SystemExit('Vendor-provided firmware MD5 mismatch')
folder = project / 'work/tr1200-recovery-kit'
folder.mkdir(mode=0o700, exist_ok=True)
path = folder / 'recovery.bin'
if path.exists() and path.read_bytes() != firmware:
    raise SystemExit('Existing recovery.bin differs; refusing to overwrite')
path.write_bytes(firmware)
report = {
    'model': 'Cudy TR1200 1.0 / R46; confirm physical hardware version before use',
    'original_filename': name, 'bytes': len(firmware),
    'recovery_bin_sha256': hashlib.sha256(firmware).hexdigest(),
    'vendor_md5_verified': True, 'zip_crc_verified': True,
    'official_archive_sha256': stock['sha256'],
    'official_guide': 'https://www.cudy.com/zh-cn/blogs/faq/how-to-recovery-the-cudy-router-from-openwrt-firmware-to-cudy-official-firmware',
    'physical_port': 'WAN', 'computer_ipv4': '192.168.1.88', 'requested_filename': 'recovery.bin',
    'tftp_server_started': False, 'router_contacted': False, 'recovery_tested_on_hardware': False,
}
(folder / 'recovery-manifest.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
