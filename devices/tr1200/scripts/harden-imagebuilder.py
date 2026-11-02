#!/usr/bin/env python3
"""Apply two pinned TR1200 fixes, preserving every byte of kernel machine code."""
import hashlib
import json
import lzma
import os
from pathlib import Path
import struct
import subprocess

project = Path(__file__).resolve().parents[3]
device = project / 'devices/tr1200'
lock = json.loads((device / 'build.lock.json').read_text())
builder = project / lock['workspace']
kdir = builder / 'build_dir/target-mipsel_24kc_musl/linux-ramips_mt76x8'
kernel = kdir / 'cudy_tr1200-v1-kernel.bin'
dtb = kdir / 'image-mt7628an_cudy_tr1200-v1.dtb'
saved = builder / '.tr1200-official-baseline'
saved.mkdir(exist_ok=True)
for path, expected in [(kernel, lock['official_kernel_sha256']), (dtb, lock['official_dtb_sha256'])]:
    baseline = saved / path.name
    if not baseline.exists():
        data = path.read_bytes()
        if hashlib.sha256(data).hexdigest() != expected:
            raise SystemExit(f'Unexpected official binary: {path.name}')
        baseline.write_bytes(data)
    if hashlib.sha256(baseline.read_bytes()).hexdigest() != expected:
        raise SystemExit(f'Baseline checksum mismatch: {path.name}')

for name, expected in lock['patches'].items():
    patch = project / 'reference/tr1200' / name
    if hashlib.sha256(patch.read_bytes()).hexdigest() != expected:
        raise SystemExit(f'Pinned upstream patch mismatch: {name}')
marker = saved / 'patches.json'
if not marker.exists():
    targets = {
        'openwrt-pr-22648.patch': 'target/linux/ramips/image/mt76x8.mk',
        'openwrt-pr-23812.patch': 'target/linux/ramips/dts/mt7628an_cudy_tr1200-v1.dts',
    }
    for name, target in targets.items():
        patch = project / 'reference/tr1200' / name
        sections = patch.read_text().split('diff --git ')
        selected = [section for section in sections
                    if section.startswith('a/' + target + ' b/' + target + '\n')]
        if len(selected) != 1:
            raise SystemExit(f'Expected one device-specific patch: {name}')
        content = 'diff --git ' + selected[0]
        command = ['patch', '--batch', '--forward', '--fuzz=0', '-p1']
        subprocess.run(command + ['--dry-run'], input=content, text=True,
                       cwd=builder, check=True)
        subprocess.run(command, input=content, text=True, cwd=builder, check=True)
    targetinfo = builder / '.targetinfo'
    text = targetinfo.read_text()
    needle = 'Target-Profile-SupportedDevices: cudy,tr1200-v1 R46'
    if text.count(needle) != 1:
        raise SystemExit('Unexpected official target profile')
    targetinfo.write_text(text.replace(needle,
                         'Target-Profile-SupportedDevices: cudy,tr1200-v1 cudy,tr1200'))
    profiles = builder / '.profiles.mk'
    if profiles.exists():
        text = profiles.read_text()
        needle = 'DEVICE_cudy_tr1200-v1_SUPPORTED_DEVICES:=cudy,tr1200-v1 R46'
        if text.count(needle) != 1:
            raise SystemExit('Unexpected generated profile')
        profiles.write_text(text.replace(needle,
                            'DEVICE_cudy_tr1200-v1_SUPPORTED_DEVICES:=cudy,tr1200-v1 cudy,tr1200'))
    marker.write_text(json.dumps(lock['patches'], indent=2) + '\n')
elif json.loads(marker.read_text()) != lock['patches']:
    raise SystemExit('Patches changed; use a fresh ImageBuilder workspace')

original_dtb = (saved / dtb.name).read_bytes()
dtb.write_bytes(original_dtb)
node = '/palmbus@10000000/spi@b00/flash@0/partitions/partition@fe0000'
subprocess.run(['fdtput', '-t', 'x', str(dtb), node, 'reg', 'fe0000', '10000'], check=True)
fixed_dtb = dtb.read_bytes()
# A pinned official DTB and a fixed-width property update make the comparison
# exact: these are the only two changed bytes, not a recompiled/reordered tree.
expected_dtb = bytearray(original_dtb)
expected_dtb[3276:3284] = struct.pack('>II', 0xfe0000, 0x10000)
if fixed_dtb != bytes(expected_dtb):
    raise SystemExit('Unexpected changes outside the backup reg property')

original_kernel = (saved / kernel.name).read_bytes()
header = struct.unpack('>7I4B32s', original_kernel[:64])
payload = lzma.decompress(original_kernel[64:64+header[3]])
if not payload.endswith(original_dtb):
    raise SystemExit('Official kernel does not end with the pinned DTB')
machine_code = payload[:-len(original_dtb)]
tools = builder / 'staging_dir/host/bin'
env = {**os.environ, 'SOURCE_DATE_EPOCH': str(header[2])}

def repack(data, stem):
    raw = saved / (stem + '.raw')
    compressed = saved / (stem + '.lzma')
    image = saved / (stem + '.bin')
    raw.write_bytes(data)
    subprocess.run([str(tools / 'lzma'), 'e', str(raw), '-lc1', '-lp2', '-pb2',
                    str(compressed)], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([str(tools / 'mkimage'), '-A', 'mips', '-O', 'linux', '-T', 'kernel',
                    '-C', 'lzma', '-a', hex(header[4]), '-e', hex(header[5]),
                    '-n', header[11].rstrip(b'\0').decode(), '-d', str(compressed),
                    str(image)], check=True, env=env, stdout=subprocess.DEVNULL)
    return image.read_bytes()

if repack(payload, 'roundtrip') != original_kernel:
    raise SystemExit('Official uImage round-trip differs; refusing modification')
fixed_kernel = repack(machine_code + fixed_dtb, 'fixed')
kernel.write_bytes(fixed_kernel)
report = {
    'official_roundtrip_byte_identical': True,
    'kernel_machine_code_byte_identical': True,
    'kernel_machine_code_bytes': len(machine_code),
    'kernel_machine_code_sha256': hashlib.sha256(machine_code).hexdigest(),
    'dtb_changed_byte_offsets': [i for i, (a, b) in enumerate(zip(original_dtb, fixed_dtb)) if a != b],
    'patched_dtb_sha256': hashlib.sha256(fixed_dtb).hexdigest(),
    'patched_kernel_sha256': hashlib.sha256(fixed_kernel).hexdigest(),
    'supported_devices': lock['hardening']['supported_devices'],
    'patches': lock['patches'], 'hardware_tested': False,
}
(builder / 'tr1200-hardening.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
