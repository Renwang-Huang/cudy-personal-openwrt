#!/usr/bin/env python3
"""Inspect a generated sysupgrade image without running its contents."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tarfile

project = Path(__file__).resolve().parents[1]
cfg = json.loads((project / 'config.json').read_text())
images = list((project / 'output').glob('*-squashfs-sysupgrade.bin'))
if len(images) != 1:
    raise SystemExit(f'Expected one sysupgrade image, found {len(images)}')
image = images[0]
blob = image.read_bytes()
marker = blob.rfind(b'FWx0')
# The metadata object has nested objects: locate the metadata_version key instead.
key = blob.rfind(b'"metadata_version"', 0, marker)
start = blob.rfind(b'{', 0, key)
if marker < 0 or key < 0 or start < 0:
    raise SystemExit('Missing OpenWrt fwtool metadata')
metadata = json.loads(blob[start:marker].decode().strip())
assert metadata['version']['target'] == cfg['target'], metadata
assert 'cudy,tr3000-256mb-v1' in metadata['supported_devices'], metadata
assert 'cudy,tr3000-v2-mod' not in metadata['supported_devices'], metadata
assert metadata['version']['version'] == cfg['openwrt_version'], metadata

verification_dir = project / 'work/verification'
verification_dir.mkdir(parents=True, exist_ok=True)
with tarfile.open(image, 'r:') as archive:
    kernel = archive.extractfile(f"sysupgrade-{cfg['profile']}/kernel").read()
    root = archive.extractfile(f"sysupgrade-{cfg['profile']}/root").read()
root_path = verification_dir / 'root.squashfs'
root_path.write_bytes(root)

def fdt_properties(data):
    header = struct.unpack_from('>10I', data)
    assert header[0] == 0xd00dfeed and header[1] <= len(data)
    offset, strings = header[2], header[3]
    stack, result = [], {}
    while offset < header[1]:
        token = struct.unpack_from('>I', data, offset)[0]
        offset += 4
        if token == 1:
            end = data.index(b'\0', offset)
            stack.append(data[offset:end].decode())
            offset = (end + 4) & ~3
        elif token == 2:
            stack.pop()
        elif token == 3:
            size, name_offset = struct.unpack_from('>II', data, offset)
            offset += 8
            name_start = strings + name_offset
            name_end = data.index(b'\0', name_start)
            name = data[name_start:name_end].decode()
            path = '/' + '/'.join(part for part in stack if part)
            result[(path, name)] = data[offset:offset+size]
            offset = (offset + size + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            return result
        else:
            raise ValueError(f'Invalid FDT token {token}')
    raise ValueError('Missing FDT end token')

device = None
for match in re.finditer(re.escape(b'\xd0\x0d\xfe\xed'), kernel):
    try:
        props = fdt_properties(kernel[match.start():])
    except (ValueError, AssertionError, IndexError, struct.error, UnicodeError):
        continue
    if b'cudy,tr3000-256mb-v1' in props.get(('/', 'compatible'), b'').split(b'\0'):
        device = props
        break
assert device is not None, 'Expected device tree missing from kernel'
ubi_nodes = [path for (path, key), value in device.items()
             if key == 'label' and value.rstrip(b'\0') == b'ubi']
assert len(ubi_nodes) == 1
ubi_offset, ubi_size = struct.unpack('>II', device[(ubi_nodes[0], 'reg')])
assert (ubi_offset, ubi_size) == (0x5c0000, 0xe600000)

script = subprocess.check_output(['unsquashfs', '-cat', str(root_path),
                                  'etc/uci-defaults/99-personalize'])
assert script == (project / 'files/etc/uci-defaults/99-personalize').read_bytes()
shadow = subprocess.check_output(['unsquashfs', '-cat', str(root_path), 'etc/shadow'])
root_entry = next(line for line in shadow.decode().splitlines() if line.startswith('root:'))
assert root_entry.split(':')[1] in ('', '!', '*'), 'Unexpected embedded root password hash'
manifest_path = next((project / 'output').glob('*.manifest'))
manifest = manifest_path.read_text()
package_names = {line.split()[0] for line in manifest.splitlines() if line.strip()}
for package in cfg['packages']:
    assert package in package_names, f'Missing requested package: {package}'
assert 'luci-app-passwall' not in package_names

report = {
    'image': image.name,
    'bytes': len(blob),
    'sha256': hashlib.sha256(blob).hexdigest(),
    'metadata': metadata,
    'kernel_sha256': hashlib.sha256(kernel).hexdigest(),
    'rootfs_sha256': hashlib.sha256(root).hexdigest(),
    'model': device[('/', 'model')].rstrip(b'\0').decode(),
    'ubi_offset': ubi_offset,
    'ubi_bytes': ubi_size,
    'requested_packages_present': cfg['packages'],
    'package_count': len(package_names),
    'personalization_file_verified': True,
    'private_root_password_embedded': False,
    'current_kwrt_board_accepted_by_metadata': False,
    'runtime_tested': False,
    'migration_tested': False,
    'status': 'candidate-requires-migration-review'
}
(project / 'output/verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
