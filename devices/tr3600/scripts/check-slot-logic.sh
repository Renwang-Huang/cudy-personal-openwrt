#!/usr/bin/env bash
# Exercise planning and failure paths with stubs; never open flash devices.
set -euo pipefail
device_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source "$device_dir/files/lib/upgrade/cudy-tr3600.sh"
dual=Y current=0 target=1 fixture_kernel=kernel fixture_root=rootfs
target_kernel=kernel2 target_root=rootfs2 env_slot=0 missing_volume=
cudy_tr3600_param() {
    case "$1" in
        dual_boot) echo "$dual";; boot_image_slot) echo "$current";;
        upgrade_image_slot) echo "$target";; boot_kernel_part) echo "$fixture_kernel";;
        boot_rootfs_part) echo "$fixture_root";; upgrade_kernel_part) echo "$target_kernel";;
        upgrade_rootfs_part) echo "$target_root";; rootfs_data_part) echo rootfs_data;;
        env_part) echo u-boot-env;; *) return 1;;
    esac
}
nand_find_ubi() { echo ubi0; }
nand_find_volume() { [[ "$2" != "$missing_volume" ]] && echo ubi0_3; }
fw_printenv() { echo "$env_slot"; }
cudy_tr3600_check_state
[[ "$CUDY_TARGET_KERNEL" == kernel2 && "$CUDY_TARGET_ROOT" == rootfs2 ]]
current=1 target=0 fixture_kernel=kernel2 fixture_root=rootfs2
target_kernel=kernel target_root=rootfs env_slot=1
cudy_tr3600_check_state
[[ "$CUDY_TARGET_KERNEL" == kernel && "$CUDY_TARGET_ROOT" == rootfs ]]
target=1
if cudy_tr3600_check_state 2>/dev/null; then exit 1; fi
target=0 env_slot=0
if cudy_tr3600_check_state 2>/dev/null; then exit 1; fi
env_slot=1 missing_volume=u-boot-env
if cudy_tr3600_check_state 2>/dev/null; then exit 1; fi
missing_volume= dual=N
if cudy_tr3600_check_state 2>/dev/null; then exit 1; fi
fw_setenv() { echo 'UNEXPECTED FLASH METADATA WRITE' >&2; exit 99; }
nand_do_flash_file() { echo 'UNEXPECTED FLASH WRITE' >&2; exit 99; }
if cudy_tr3600_do_upgrade ignored-image 2>/dev/null; then exit 1; fi
dual=Y events='' flash_failure=0 verify_failure=''
cudy_tr3600_check_image() { cudy_tr3600_check_state; }
fw_setenv() { events+="env:$1=$2;"; }
nand_do_flash_file() { events+="flash:$CI_KERNPART:$CI_ROOTPART;"; return "$flash_failure"; }
cudy_tr3600_verify_volume() { events+="verify:$2;"; [[ "$2" != "$verify_failure" ]]; }
nand_do_upgrade_success() { events+='success;'; }
cudy_tr3600_do_upgrade ignored-image
[[ "$events" == 'env:dual_boot.slot_0_invalid=1;flash:kernel:rootfs;verify:kernel;verify:root;env:dual_boot.slot_0_invalid=0;env:dual_boot.current_slot=0;success;' ]]
events='' flash_failure=1
if cudy_tr3600_do_upgrade ignored-image; then exit 1; fi
[[ "$events" == 'env:dual_boot.slot_0_invalid=1;flash:kernel:rootfs;' ]]
events='' flash_failure=0 verify_failure=root
if cudy_tr3600_do_upgrade ignored-image; then exit 1; fi
[[ "$events" == 'env:dual_boot.slot_0_invalid=1;flash:kernel:rootfs;verify:kernel;verify:root;' ]]
echo 'Slot checks passed: both directions, inconsistent state rejection, no writes on invalid state, write/readback/commit ordering, no slot switch after flash or verification failure.'
