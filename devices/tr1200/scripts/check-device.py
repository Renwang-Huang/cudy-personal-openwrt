#!/usr/bin/env python3
"""Check a manually collected device inventory. Never connect, write or flash."""
import argparse
import json
from pathlib import Path

def evaluate(snapshot):
    errors, warnings = [], []
    board = snapshot.get('board_name', '').strip()
    if board not in {'cudy,tr1200', 'cudy,tr1200-v1'}:
        errors.append('Expected OpenWrt TR1200 identity; OEM R46 and other models are not approved for direct sysupgrade')
    if not snapshot.get('model', '').startswith('Cudy TR1200'):
        errors.append('Model information missing or inconsistent')
    expected = {
        'u-boot': (0, 0x30000), 'u-boot-env': (0x30000, 0x10000),
        'factory': (0x40000, 0x10000), 'firmware': (0x50000, 0xf80000),
        'debug': (0xfd0000, 0x10000), 'bdinfo': (0xff0000, 0x10000),
    }
    def number(value):
        if isinstance(value, bool):
            raise ValueError('boolean is not an offset')
        return int(str(value), 16 if str(value).lower().startswith('0x') else 10)
    regions = {}
    for entry in snapshot.get('mtd', []):
        name = entry.get('name', '').strip()
        if name not in set(expected) | {'backup'}:
            continue
        if name in regions:
            errors.append('Duplicate partition name: ' + name)
        try:
            regions[name] = (number(entry['offset']), number(entry['size']))
        except (ValueError, TypeError, KeyError):
            errors.append('Missing or invalid actual offset/size: ' + name)
    for name, region in expected.items():
        if regions.get(name) != region:
            errors.append('Unexpected or unknown actual partition range: ' + name)
    if regions.get('backup') == (0xfe000, 0x10000):
        warnings.append('Old DTS backup offset bug detected; this named partition is not the real flash-tail backup region')
    elif regions.get('backup') != (0xfe0000, 0x10000):
        errors.append('Unknown backup partition layout')
    return {
        'board_name': board, 'inventory_structurally_consistent': not errors,
        'errors': errors, 'warnings': warnings,
        'manual_checks_still_required': [
            'physical TR1200 1.0 label and original firmware version',
            'matching image SHA-256 and successful on-device sysupgrade -T without force',
            'verified off-device bootloader, environment, factory and bdinfo backups',
            'WAN-side official recovery request and correct matching original firmware',
            'stable power, isolated wired bring-up and no retained old configuration',
        ],
        'hardware_tested_by_this_program': False, 'flash_performed': False,
        'automatic_flash_approval': False,
    }

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('snapshot', type=Path)
    args = parser.parse_args()
    report = evaluate(json.loads(args.snapshot.read_text()))
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['inventory_structurally_consistent'] else 2)

if __name__ == '__main__':
    main()
