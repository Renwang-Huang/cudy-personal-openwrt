#!/usr/bin/env python3
"""Read-only inspection of the TR3600 candidate and its compiled device tree."""
import base64
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import tarfile

project = Path(__file__).resolve().parents[3]
device_dir = project / 'devices/tr3600'
subprocess.run(['bash', str(device_dir / 'scripts/check-slot-logic.sh')],
               check=True, stdout=subprocess.PIPE)
output = project / 'work/tr3600-source/bin/targets/mediatek/filogic'
images = list(output.glob('*cudy_tr3600-v1-squashfs-sysupgrade.bin'))
if len(images) != 1:
    raise SystemExit(f'Expected one TR3600 sysupgrade image, found {len(images)}')
image = images[0]
blob = image.read_bytes()
marker = blob.rfind(b'FWx0')
key = blob.rfind(b'"metadata_version"', 0, marker)
assert marker > 0 and key > 0
metadata = json.loads(blob[blob.rfind(b'{', 0, key):marker].decode().strip())
assert metadata['version']['target'] == 'mediatek/filogic'
assert 'cudy,tr3600-v1' in metadata['supported_devices']
assert 'R126' in metadata['supported_devices']
assert not any('tr3000' in name for name in metadata['supported_devices'])

with tarfile.open(image, 'r:') as archive:
    prefix = 'sysupgrade-cudy_tr3600-v1/'
    kernel = archive.extractfile(prefix + 'kernel').read()
    root = archive.extractfile(prefix + 'root').read()
scratch = project / 'work/tr3600-verification'
scratch.mkdir(parents=True, exist_ok=True)
root_path = scratch / 'root.squashfs'
root_path.write_bytes(root)

def fdt_properties(data):
    header = struct.unpack_from('>10I', data)
    assert header[0] == 0xd00dfeed and header[1] <= len(data)
    offset, strings = header[2], header[3]
    stack, properties = [], {}
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
            start = strings + name_offset
            name = data[start:data.index(b'\0', start)].decode()
            properties[('/' + '/'.join(part for part in stack if part), name)] = data[offset:offset+size]
            offset = (offset + size + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            return properties
        else:
            raise ValueError(f'Invalid FDT token {token}')
    raise ValueError('Missing FDT end token')

props = None
for match in re.finditer(re.escape(b'\xd0\x0d\xfe\xed'), kernel):
    try:
        candidate = fdt_properties(kernel[match.start():])
    except (ValueError, AssertionError, IndexError, struct.error, UnicodeError):
        continue
    if b'cudy,tr3600-v1' in candidate.get(('/', 'compatible'), b'').split(b'\0'):
        props = candidate
        break
assert props is not None, 'TR3600 device tree missing'

def cells(value):
    return struct.unpack('>' + 'I' * (len(value) // 4), value)

partitions = {}
for (path, name), value in props.items():
    if name == 'label' and (path, 'reg') in props and '/partition@' in path:
        partitions[value.rstrip(b'\0').decode()] = cells(props[(path, 'reg')])
expected = {'BL2': (0, 0x100000), 'backup': (0x100000, 0x80000),
            'Factory': (0x180000, 0x400000), 'bdinfo': (0x580000, 0x40000),
            'FIP': (0x5c0000, 0x200000), 'ubi': (0x7c0000, 0xe840000)}
assert partitions == expected, partitions
fan = next(path for (path, name), value in props.items()
           if name == 'compatible' and value == b'pwm-fan\0')
pwm = cells(props[(fan, 'pwms')])
assert pwm[1:] == (0, 50000), pwm
assert (fan, 'pinctrl-0') not in props
assert cells(props[(fan, 'cooling-levels')]) == (0, 64, 128, 192, 255)
for (path, name), value in props.items():
    if path.endswith('/band@0') and name == 'nvmem-cells':
        assert cells(value)[-1] == 0
    if path.endswith('/band@1') and name == 'nvmem-cells':
        assert cells(value)[-1] == 16

def read_root(name):
    return subprocess.check_output(['unsquashfs', '-cat', str(root_path), name])

for relative in ['etc/uci-defaults/99-personalize', 'lib/upgrade/cudy-tr3600.sh',
                 'etc/init.d/cudy-boot-success']:
    assert read_root(relative) == (device_dir / 'files' / relative).read_bytes(), relative
platform = read_root('lib/upgrade/platform.sh').decode()
assert 'cudy_tr3600_do_upgrade' in platform and 'cudy_tr3600_check_image' in platform
assert 'u-boot-env' in read_root('etc/uci-defaults/30_uboot-envtools').decode()
root_entry = next(line for line in read_root('etc/shadow').decode().splitlines() if line.startswith('root:'))
assert root_entry.split(':')[1] in ('', '!', '*')
certificates = re.findall(b'-----BEGIN CERTIFICATE-----\\s*(.*?)\\s*-----END CERTIFICATE-----',
                          read_root('etc/ssl/certs/ca-certificates.crt'), re.S)
certificate_ids = [hashlib.sha256(base64.b64decode(value)).hexdigest() for value in certificates]
assert certificates and len(certificate_ids) == len(set(certificate_ids)), 'Duplicate CA certificates in bundle'
assert 'https://downloads.openwrt.org/releases/25.12.5/' in read_root('etc/apk/repositories.d/distfeeds.list').decode()
manifests = list(output.glob('*cudy_tr3600-v1.manifest'))
if not manifests:
    manifests = list(output.glob('*mediatek-filogic.manifest'))
assert len(manifests) == 1, 'Expected a unique firmware package manifest'
manifest_path = manifests[0]
manifest = manifest_path.read_text()
packages = {line.split()[0] for line in manifest.splitlines() if line.strip()}
required = ['luci-ssl', 'luci-i18n-base-zh-cn', 'luci-i18n-firewall-zh-cn',
            'kmod-mt7990-firmware', 'kmod-mt7996e', 'kmod-hwmon-pwmfan',
            'kmod-cudy-bootcount', 'mt7987-2p5g-phy-firmware', 'kmod-usb3']
assert not set(required) - packages, set(required) - packages
assert not {'luci-app-passwall', 'luci-app-openclash', 'luci-app-store'} & packages
listing = subprocess.check_output(['unsquashfs', '-ll', str(root_path)], text=True)
assert 'cudy_bootcount.ko' in listing
assert 'mt7990_wm.bin' in listing
assert 'etc/rc.d/S99cudy-boot-success' in listing
initramfs = list(output.glob('*cudy_tr3600-v1-initramfs-kernel.bin'))
assert len(initramfs) == 1, 'Recovery/initramfs kernel missing'
report = {
    'image': image.name, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest(),
    'metadata': metadata, 'kernel_sha256': hashlib.sha256(kernel).hexdigest(),
    'rootfs_sha256': hashlib.sha256(root).hexdigest(), 'partitions': partitions,
    'fan_pwm_channel': 0, 'fan_period_ns': 50000,
    'required_packages_present': required, 'package_count': len(packages),
    'slot_logic_stub_tests_passed': True, 'private_root_password_embedded': False,
    'ca_bundle_certificates': len(certificates), 'duplicate_ca_certificates': False,
    'hardware_tested': False, 'wifi7_mlo_tested': False, 'dual_slot_upgrade_tested_on_hardware': False,
    'status': 'TR3600 v1 experimental candidate; requires hardware migration review',
    'initramfs_sha256': hashlib.sha256(initramfs[0].read_bytes()).hexdigest()
}
(output / 'tr3600-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
