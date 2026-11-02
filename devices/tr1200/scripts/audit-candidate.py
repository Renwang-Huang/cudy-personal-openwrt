#!/usr/bin/env python3
"""Run corruption rejection and real MIPS userspace checks, without a router."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import struct
import importlib.util
import zipfile
import lzma
import zlib

project = Path(__file__).resolve().parents[3]
device = project / 'devices/tr1200'
lock = json.loads((device / 'build.lock.json').read_text())
output = project / lock['output_directory']
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--qemu', default=shutil.which('qemu-mipsel-static') or shutil.which('qemu-mipsel'))
args = parser.parse_args()
if not args.qemu:
    raise SystemExit('Install qemu-user/qemu-user-static or supply --qemu; no checks skipped')
qemu = str(Path(args.qemu).resolve())
target_env = {key: value for key, value in os.environ.items()
              if key not in {'LD_LIBRARY_PATH', 'LD_PRELOAD', 'QEMU_LD_PREFIX', 'QEMU_CPU'}}
verify = device / 'scripts/verify-image.py'
subprocess.run([sys.executable, str(verify)], check=True, stdout=subprocess.DEVNULL)
report = json.loads((output / 'tr1200-verification.json').read_text())
image = output / report['image']
manifest = next(output.glob('*.manifest'))
blob = image.read_bytes()
rejected = []
spec = importlib.util.spec_from_file_location('tr1200_check_device', device / 'scripts/check-device.py')
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)
regions = {
    'u-boot': (0, 0x30000), 'u-boot-env': (0x30000, 0x10000),
    'factory': (0x40000, 0x10000), 'firmware': (0x50000, 0xf80000),
    'debug': (0xfd0000, 0x10000), 'backup': (0xfe0000, 0x10000), 'bdinfo': (0xff0000, 0x10000),
}
fixture = {'board_name': 'cudy,tr1200-v1', 'model': 'Cudy TR1200 v1',
           'mtd': [{'name': name, 'offset': str(offset), 'size': str(size)}
                   for name, (offset, size) in regions.items()]}
assert checker.evaluate(fixture)['inventory_structurally_consistent']
legacy = json.loads(json.dumps(fixture)); legacy['board_name'] = 'cudy,tr1200'
assert checker.evaluate(legacy)['inventory_structurally_consistent']
for board in ['cudy,tr3000-v1', 'cudy,tr3600-v1', 'R46', '']:
    wrong = {**fixture, 'board_name': board}
    assert not checker.evaluate(wrong)['inventory_structurally_consistent'], board
wrong = json.loads(json.dumps(fixture)); wrong['mtd'][3]['size'] = '33554432'
assert not checker.evaluate(wrong)['inventory_structurally_consistent']
wrong = json.loads(json.dumps(fixture)); del wrong['mtd'][3]['offset']
assert not checker.evaluate(wrong)['inventory_structurally_consistent']
with tempfile.TemporaryDirectory(prefix='tr1200-negative-', dir=project / 'work') as temporary:
    scratch = Path(temporary)
    def reject(name, data, manifest_text=None, optimize=False):
        (scratch / image.name).write_bytes(data)
        (scratch / manifest.name).write_text(manifest.read_text() if manifest_text is None else manifest_text)
        cmd = [sys.executable] + (['-O'] if optimize else [])
        result = subprocess.run(cmd + [str(verify), '--output-dir', str(scratch)],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0:
            raise SystemExit('Corrupt/incompatible input accepted: ' + name)
        rejected.append(name)
    data = bytearray(blob); data[4] ^= 1
    reject('uimage_header_crc_corruption', data)
    data = bytearray(blob); data[80] ^= 1
    reject('kernel_payload_crc_corruption', data)
    reject('wrong_device_metadata', blob.replace(b'cudy,tr1200', b'cudy,tr9999'))
    data = bytearray(blob)
    data[report['rootfs_offset']:report['rootfs_offset']+4] = b'FAIL'
    reject('missing_squashfs_header', data)
    reject('missing_chinese_luci_package', blob,
           '\n'.join(line for line in manifest.read_text().splitlines()
                     if not line.startswith('luci-i18n-base-zh-cn ')) + '\n')
    reject('unsupported_namespace_jail', blob, manifest.read_text() + 'procd-ujail - 1\n')
    trailer = blob.rfind(b'FWx0')
    metadata_start = blob.rfind(b'{', 0, blob.rfind(b'"metadata_version"', 0, trailer))
    oversized = blob[:metadata_start] + b'\0' * lock['firmware_partition']['bytes'] + blob[metadata_start:]
    reject('firmware_partition_overflow', oversized)
    reject('disabled_python_assertions', blob, optimize=True)

with tempfile.TemporaryDirectory(prefix='tr1200-userspace-', dir=project / 'work') as temporary:
    scratch = Path(temporary)
    archive = project / 'reference/tr1200/TR1200-V1-intermediate.zip'
    reference_lock = json.loads((project / 'reference/tr1200/archives.lock.json').read_text())
    item = next(item for item in reference_lock['references'] if item['filename'] == archive.name)
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == item['sha256']
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        intermediate = bundle.read('TR1200-OpenWRT-Flash.bin')
    offset = 0x50000
    header = struct.unpack_from('>7I4B32s', intermediate, offset)
    assert header[0] == 0x27051956 and header[7:11] == (5, 5, 2, 3)
    kernel_data = intermediate[offset+64:offset+64+header[3]]
    assert zlib.crc32(kernel_data) == header[6]
    assert b'cudy,tr1200\0' in lzma.decompress(kernel_data)
    root_offset = offset + 64 + header[3]
    assert intermediate[root_offset:root_offset+4] == b'hsqs'
    root_size = struct.unpack_from('<Q', intermediate, root_offset+40)[0]
    intermediate_squashfs = scratch / 'intermediate.squashfs'
    intermediate_squashfs.write_bytes(intermediate[root_offset:root_offset+root_size])
    intermediate_root = scratch / 'intermediate-root'
    subprocess.run(['unsquashfs', '-no-progress', '-d', str(intermediate_root), '-excludes',
                    str(intermediate_squashfs), 'dev'], check=True, stdout=subprocess.DEVNULL)
    intermediate_release = (intermediate_root / 'etc/openwrt_release').read_text()
    assert "DISTRIB_RELEASE='23.05.3'" in intermediate_release
    extracted_metadata = scratch / 'intermediate-extracted-metadata.json'
    subprocess.run([qemu, '-cpu', '24KEc', '-L', str(intermediate_root),
                    str(intermediate_root / 'usr/bin/fwtool'), '-i', str(extracted_metadata),
                    str(image)], check=True, env=target_env)
    assert json.loads(extracted_metadata.read_text()) == report['metadata']
    root = scratch / 'root'
    # Device nodes are intentionally excluded; no root privileges or mounts.
    subprocess.run(['unsquashfs', '-no-progress', '-d', str(root), '-excludes',
                    str(project / 'work/tr1200-verification/root.squashfs'), 'dev'],
                   check=True, stdout=subprocess.DEVNULL)
    def target(relative, *arguments):
        return subprocess.check_output([qemu, '-cpu', '24KEc', '-L', str(root), str(root / relative),
                                        *arguments], text=True, stderr=subprocess.STDOUT, env=target_env)
    assert target('bin/busybox', 'echo', 'MIPS userspace works').strip() == 'MIPS userspace works'
    dnsmasq_version = target('usr/sbin/dnsmasq', '--version').splitlines()[0]
    dnsmasq_config = scratch / 'dnsmasq.conf'
    dnsmasq_config.write_text('port=0\nno-hosts\nno-resolv\n')
    dnsmasq_test = target('usr/sbin/dnsmasq', '--test', '--conf-file=' + str(dnsmasq_config)).strip()
    assert 'syntax check OK' in dnsmasq_test

    config = scratch / 'config'; config.mkdir()
    state = scratch / 'state'; state.mkdir()
    shutil.copyfile(root / 'etc/config/luci', config / 'luci')
    # /bin/config_generate creates system and network before uci-defaults.
    (config / 'system').write_text("config system\n option hostname 'OpenWrt'\n option timezone 'UTC'\n")
    # Representative stock-generated network, before the personalization hook.
    # The test checks that this actual hook preserves the WAN and VLAN settings.
    (config / 'network').write_text('''config device 'lan_device'
 option name 'br-lan'
 option type 'bridge'
 list ports 'eth0.1'
config interface 'lan'
 option device 'br-lan'
 option proto 'static'
 option ipaddr '192.168.1.1'
 option netmask '255.255.255.0'
config interface 'wan'
 option device 'eth0.2'
 option proto 'dhcp'
config switch 'switch0'
 option name 'switch0'
 option enable_vlan '1'
config switch_vlan 'lan_vlan'
 option device 'switch0'
 option vlan '1'
 option ports '0 6t'
config switch_vlan 'wan_vlan'
 option device 'switch0'
 option vlan '2'
 option ports '1 6t'
''')
    command = [qemu, '-cpu', '24KEc', '-L', str(root), str(root / 'sbin/uci'), '-c', str(config), '-t', str(state)]
    wrapper_dir = scratch / 'bin'; wrapper_dir.mkdir()
    wrapper = wrapper_dir / 'uci'
    wrapper.write_text('#!/bin/sh\nexec ' + shlex.join(command) + ' "$@"\n')
    wrapper.chmod(0o755)
    env = {**target_env, 'PATH': str(wrapper_dir) + os.pathsep + os.environ['PATH']}
    script = root / 'etc/uci-defaults/99-personalize'
    subprocess.run(['/bin/sh', str(script)], check=True, env=env)
    def get(key):
        return subprocess.check_output(command + ['get', key], text=True, env=target_env).strip()
    expected = {
        'system.@system[0].hostname': 'TR1200-Personal', 'luci.main.lang': 'zh_cn',
        'network.lan.ipaddr': '10.0.0.1', 'network.lan.netmask': '255.255.255.0',
        'network.lan.device': 'br-lan', 'network.wan.device': 'eth0.2',
        'network.wan.proto': 'dhcp', 'network.lan_vlan.ports': '0 6t',
        'network.wan_vlan.ports': '1 6t', 'network.switch0.enable_vlan': '1',
    }
    for key, value in expected.items():
        assert get(key) == value, key
    first = {p.name: p.read_bytes() for p in config.iterdir() if p.is_file()}
    subprocess.run(['/bin/sh', str(script)], check=True, env=env)
    assert first == {p.name: p.read_bytes() for p in config.iterdir() if p.is_file()}
    remaining_changes = subprocess.check_output(command + ['changes'], text=True, env=target_env).strip()
    assert remaining_changes == '', remaining_changes

    abi = {}
    for name in ['bin/busybox', 'sbin/init', 'sbin/procd', 'sbin/uci', 'usr/sbin/dnsmasq', 'usr/sbin/dropbear']:
        # OpenWrt sstrip removes section tables. Read the runtime ELF program
        # header PT_MIPS_ABIFLAGS rather than relying on stripped sections.
        data = (root / name).read_bytes()
        assert data[:7] == b'\x7fELF\x01\x01\x01'
        assert struct.unpack_from('<H', data, 18)[0] == 8, name
        offset = struct.unpack_from('<I', data, 28)[0]
        size, count = struct.unpack_from('<HH', data, 42)
        flags = []
        for index in range(count):
            header = struct.unpack_from('<8I', data, offset + index * size)
            if header[0] == 0x70000003:
                flags.append(struct.unpack_from('<H6B4I', data, header[1]))
        assert len(flags) == 1 and flags[0][1:3] == (32, 2) and flags[0][6] == 3, name
        abi[name] = 'MIPSEL ELF32, MIPS32r2, soft float'
    actual_packages = {p.name.removesuffix('.list') for p in (root / 'lib/apk/packages').glob('*.list')}
    expected_packages = {line.split()[0] for line in manifest.read_text().splitlines() if line.strip()}
    assert actual_packages == expected_packages, (actual_packages ^ expected_packages)
    for name in ['mt7603e', 'mt7615e', 'cfg80211', 'mac80211', 'ehci-hcd', 'ohci-hcd']:
        module = root / 'lib/modules/6.12.94' / (name + '.ko')
        text = subprocess.check_output(['readelf', '-p', '.modinfo', str(module)], text=True)
        assert 'vermagic=6.12.94 ' in text, name

audit = {
    'image_sha256': report['sha256'], 'corrupt_inputs_rejected': rejected,
    'actual_mips_busybox_executed': True, 'actual_mips_uci_executed': True,
    'personalization_values_verified': expected, 'personalization_idempotent': True,
    'wan_and_vlan_configuration_preserved': True, 'actual_package_lists_match_manifest': True,
    'dnsmasq': dnsmasq_version, 'dnsmasq_config_syntax_test': dnsmasq_test,
    'critical_executable_abi': abi, 'kernel_module_vermagic_verified': True,
    'qemu_cpu_model': '24KEc',
    'device_inventory_guards_tested': True,
    'archived_intermediate_version_verified': '23.05.3 r23809-234f1a2efa',
    'archived_intermediate_legacy_board_verified': 'cudy,tr1200',
    'actual_intermediate_mips_fwtool_parses_candidate': True,
    'full_system_boot_emulated': False, 'hardware_tested': False,
    'physical_label_bootloader_recovery_and_calibration_backups_verified': False,
}
(output / 'tr1200-offline-audit.json').write_text(json.dumps(audit, indent=2) + '\n')
print(json.dumps(audit, indent=2))
