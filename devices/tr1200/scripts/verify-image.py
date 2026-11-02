#!/usr/bin/env python3
"""Inspect TR1200 NOR firmware without running anything from the image."""
import base64
import hashlib
import json
import lzma
from pathlib import Path
import re
import struct
import subprocess
import zlib
import argparse
import tempfile

if not __debug__:
    raise SystemExit('Run verification without Python optimization; checks must remain enabled')

project = Path(__file__).resolve().parents[3]
device_dir = project / 'devices/tr1200'
cfg = json.loads((device_dir / 'config.json').read_text())
lock = json.loads((device_dir / 'build.lock.json').read_text())
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output-dir', type=Path)
args = parser.parse_args()
output = args.output_dir or project / lock['output_directory']
images = list(output.glob('*cudy_tr1200-v1-squashfs-sysupgrade.bin'))
if len(images) != 1:
    raise SystemExit(f'Expected one TR1200 sysupgrade, found {len(images)}')
image = images[0]
blob = image.read_bytes()
marker = blob.rfind(b'FWx0')
key = blob.rfind(b'"metadata_version"', 0, marker)
assert marker > 0 and key > 0, 'Missing OpenWrt fwtool metadata'
metadata = json.loads(blob[blob.rfind(b'{', 0, key):marker].decode().strip())
with tempfile.TemporaryDirectory(prefix='tr1200-fwtool-', dir=project / 'work') as temporary:
    extracted = Path(temporary) / 'metadata.json'
    tool = project / lock['workspace'] / 'staging_dir/host/bin/fwtool'
    subprocess.run([str(tool), '-i', str(extracted), str(image)], check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert json.loads(extracted.read_text()) == metadata, 'fwtool metadata mismatch'
assert metadata['version']['target'] == cfg['target']
assert metadata['version']['version'] == cfg['openwrt_version']
assert set(metadata['supported_devices']) == set(lock['hardening']['supported_devices'])

# NOR sysupgrade is uImage + SquashFS + padding, rather than the NAND tar
# used by the other two devices in this repository.
header = struct.unpack('>7I4B32s', blob[:64])
assert header[0] == 0x27051956, 'Missing legacy uImage header'
header_for_crc = blob[:4] + b'\0' * 4 + blob[8:64]
assert zlib.crc32(header_for_crc) == header[1], 'uImage header CRC mismatch'
kernel_end = 64 + header[3]
assert kernel_end < len(blob)
assert zlib.crc32(blob[64:kernel_end]) == header[6], 'uImage data CRC mismatch'
assert header[7:11] == (5, 5, 2, 3), 'Expected Linux/MIPS/kernel/LZMA'
kernel = blob[:kernel_end]
assert hashlib.sha256(kernel).hexdigest() == lock['hardening']['patched_kernel_sha256']
decompressed = lzma.decompress(blob[64:kernel_end])

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
            path = '/' + '/'.join(part for part in stack if part)
            properties[(path, name)] = data[offset:offset+size]
            offset = (offset + size + 3) & ~3
        elif token == 4:
            continue
        elif token == 9:
            return properties, data[:header[1]]
        else:
            raise ValueError(f'Invalid FDT token {token}')
    raise ValueError('Missing FDT end token')

props, dtb = None, None
for match in re.finditer(re.escape(b'\xd0\x0d\xfe\xed'), decompressed):
    try:
        candidate, data = fdt_properties(decompressed[match.start():])
    except (ValueError, AssertionError, IndexError, struct.error, UnicodeError):
        continue
    if b'cudy,tr1200-v1' in candidate.get(('/', 'compatible'), b'').split(b'\0'):
        props, dtb = candidate, data
        break
assert props is not None, 'Expected compiled TR1200 device tree missing'
assert hashlib.sha256(dtb).hexdigest() == lock['hardening']['patched_dtb_sha256']
assert decompressed.endswith(dtb)
machine_code = decompressed[:-len(dtb)]
assert hashlib.sha256(machine_code).hexdigest() == lock['hardening']['kernel_machine_code_sha256']

def cells(value):
    return struct.unpack('>' + 'I' * (len(value) // 4), value)

partitions, readonly = {}, {}
for (path, name), value in props.items():
    if name == 'label' and (path, 'reg') in props and '/partition@' in path:
        label = value.rstrip(b'\0').decode()
        partitions[label] = cells(props[(path, 'reg')])
        readonly[label] = (path, 'read-only') in props
expected = {
    'u-boot': (0, 0x30000), 'u-boot-env': (0x30000, 0x10000),
    'factory': (0x40000, 0x10000), 'firmware': (0x50000, 0xf80000),
    'debug': (0xfd0000, 0x10000),
    'backup': (0xfe0000, 0x10000), 'bdinfo': (0xff0000, 0x10000),
}
assert partitions == expected, partitions
previous_end = 0
for name, (offset, size) in sorted(partitions.items(), key=lambda item: item[1][0]):
    assert offset == previous_end and size > 0 and offset % 0x10000 == 0, name
    previous_end = offset + size
assert previous_end == 16 * 1024 * 1024, 'Unexpected full flash layout'
assert all(readonly[name] for name in expected if name != 'firmware')
assert not readonly['firmware']
assert all(not (name == 'label' and value == b'ubi\0') for (path, name), value in props.items())
assert cells(props[('/esw@10110000', 'mediatek,portmap')]) == (0x3d,)
assert cells(props[('/esw@10110000', 'mediatek,portdisable')]) == (0x3c,)

root_offset = kernel_end
assert blob[root_offset:root_offset+4] == b'hsqs', 'Expected appended SquashFS'
root_bytes = struct.unpack_from('<Q', blob, root_offset + 40)[0]
assert root_offset + root_bytes < marker
root = blob[root_offset:root_offset+root_bytes]
limit = lock['firmware_partition']['bytes']
assert len(blob) < limit, 'Firmware exceeds the official partition limit'
estimated_overlay = limit - ((root_offset + root_bytes + 65535) // 65536) * 65536
assert estimated_overlay >= 2 * 1024 * 1024, 'Insufficient overlay reserve'
scratch = project / 'work/tr1200-verification'
scratch.mkdir(parents=True, exist_ok=True)
root_path = scratch / 'root.squashfs'
root_path.write_bytes(root)

def read_root(name):
    return subprocess.check_output(['unsquashfs', '-cat', str(root_path), name])

relative = 'etc/uci-defaults/99-personalize'
assert read_root(relative) == (device_dir / 'files' / relative).read_bytes()
root_entry = next(line for line in read_root('etc/shadow').decode().splitlines()
                  if line.startswith('root:'))
assert root_entry.split(':')[1] in ('', '!', '*'), 'Unexpected embedded password'
assert 'https://downloads.openwrt.org/releases/25.12.5/' in read_root(
    'etc/apk/repositories.d/distfeeds.list').decode()
network = read_root('etc/board.d/02_network').decode()
assert re.search(r'cudy,tr1200-v1\).*?"0:lan" "1:wan"', network, re.S)
listing = subprocess.check_output(['unsquashfs', '-ll', str(root_path)], text=True)
for directory in ('etc', 'etc/uci-defaults', 'tmp'):
    line = next(line for line in listing.splitlines()
                if line.endswith(' squashfs-root/' + directory))
    assert line.startswith('drwxr-xr-x'), line
for filename in ('mt7603e.ko', 'mt7615e.ko', 'mt7628_e2.bin',
                 'mt7663_n9_rebb.bin', 'mt7663pr2h_rebb.bin'):
    assert filename in listing, filename
assert 'dropbear_rsa_host_key' not in listing and 'dropbear_ed25519_host_key' not in listing
assert not re.search(r' squashfs-root/(?:sbin|usr/sbin)/ujail(?:\s|$)', listing)
for service in ['S19dnsmasq', 'S19firewall', 'S20network', 'S50uhttpd']:
    assert 'etc/rc.d/' + service in listing, service
certificates = re.findall(b'-----BEGIN CERTIFICATE-----\\s*(.*?)\\s*-----END CERTIFICATE-----',
                          read_root('etc/ssl/certs/ca-certificates.crt'), re.S)
certificate_ids = [hashlib.sha256(base64.b64decode(value)).hexdigest() for value in certificates]
assert certificates and len(certificate_ids) == len(set(certificate_ids))
manifests = list(output.glob('*.manifest'))
assert len(manifests) == 1, 'Expected one package manifest'
packages = {line.split()[0] for line in manifests[0].read_text().splitlines() if line.strip()}
required = cfg['packages'] + ['kmod-mt7603', 'kmod-mt7615e', 'kmod-mt7663-firmware-ap',
                              'kmod-usb2', 'kmod-usb-ohci', 'swconfig', 'firewall4']
assert not set(required) - packages, set(required) - packages
assert not {'luci-app-passwall', 'luci-app-openclash', 'luci-app-store'} & packages
assert not {'procd-ujail', 'uxc'} & packages, 'Unsupported namespace/cgroup jail on SMALL_FLASH kernel'
report = {
    'image': image.name, 'bytes': len(blob), 'sha256': hashlib.sha256(blob).hexdigest(),
    'metadata': metadata, 'model': props[('/', 'model')].rstrip(b'\0').decode(),
    'kernel_sha256': hashlib.sha256(kernel).hexdigest(),
    'dtb_sha256': hashlib.sha256(dtb).hexdigest(),
    'official_kernel_machine_code_unchanged': True,
    'kernel_machine_code_sha256': hashlib.sha256(machine_code).hexdigest(),
    'device_tree_change': 'backup reg offset 0xfe000 -> 0xfe0000; all other bytes unchanged',
    'rootfs_sha256': hashlib.sha256(root).hexdigest(), 'rootfs_offset': root_offset,
    'rootfs_squashfs_bytes': root_bytes, 'partitions': partitions,
    'firmware_partition_bytes': limit,
    'estimated_overlay_bytes_before_jffs2_overhead': estimated_overlay,
    'uimage_crcs_valid': True, 'required_packages_present': required,
    'package_count': len(packages), 'private_root_password_embedded': False,
    'private_ssh_host_keys_embedded': False, 'ca_bundle_certificates': len(certificates),
    'duplicate_ca_certificates': False, 'personalization_file_verified': True,
    'inherited_backup_partition_offset_mismatch': False,
    'flash_partitions_contiguous_nonoverlapping': True,
    'legacy_cudy_tr1200_board_accepted_by_metadata': True,
    'oem_R46_direct_sysupgrade_accepted': False,
    'procd_ujail_absent': True,
    'switch_driver_modified': False,
    'boot_time_lan_wan_leak_hardware_tested': False,
    'hardware_tested': False, 'migration_tested': False,
    'status': cfg['status'],
}
(output / 'tr1200-verification.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
