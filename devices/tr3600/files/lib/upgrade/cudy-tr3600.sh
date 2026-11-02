#!/bin/sh
# SPDX-License-Identifier: GPL-2.0-only
# Cudy's documented boot_param/dual_boot protocol, using upstream OpenWrt NAND
# writers. Slot names come from the bootloader, never from a guessed UBI index.

cudy_tr3600_param() {
    cat "/sys/module/boot_param/parameters/$1" 2>/dev/null
}

cudy_tr3600_slot_plan() {
    [ "$(cudy_tr3600_param dual_boot)" = Y ] || return 1
    CUDY_CURRENT_SLOT="$(cudy_tr3600_param boot_image_slot)"
    CUDY_TARGET_SLOT="$(cudy_tr3600_param upgrade_image_slot)"
    local current_kernel current_root
    current_kernel="$(cudy_tr3600_param boot_kernel_part)"
    current_root="$(cudy_tr3600_param boot_rootfs_part)"
    CUDY_TARGET_KERNEL="$(cudy_tr3600_param upgrade_kernel_part)"
    CUDY_TARGET_ROOT="$(cudy_tr3600_param upgrade_rootfs_part)"
    case "$CUDY_CURRENT_SLOT:$CUDY_TARGET_SLOT:$current_kernel:$current_root:$CUDY_TARGET_KERNEL:$CUDY_TARGET_ROOT" in
        0:1:kernel:rootfs:kernel2:rootfs2|1:0:kernel2:rootfs2:kernel:rootfs) ;;
        *) return 1 ;;
    esac
    [ "$(cudy_tr3600_param rootfs_data_part)" = rootfs_data ] || return 1
    [ "$(cudy_tr3600_param env_part)" = u-boot-env ] || return 1
}

cudy_tr3600_check_state() {
    cudy_tr3600_slot_plan || {
        echo 'TR3600: missing or inconsistent Cudy dual-slot boot parameters.' >&2
        return 1
    }
    CUDY_UBI="$(nand_find_ubi ubi)"
    case "$CUDY_UBI" in ubi[0-9]*) ;; *) return 1 ;; esac
    local name volume
    for name in u-boot-env kernel kernel2 rootfs rootfs2 rootfs_data; do
        volume="$(nand_find_volume "$CUDY_UBI" "$name")"
        [ -n "$volume" ] || {
            echo "TR3600: expected UBI volume is missing: $name" >&2
            return 1
        }
    done
    local environment_slot
    environment_slot="$(fw_printenv -n dual_boot.current_slot 2>/dev/null)" || return 1
    [ "$environment_slot" = "$CUDY_CURRENT_SLOT" ] || {
        echo 'TR3600: U-Boot environment and running slot disagree.' >&2
        return 1
    }
}

cudy_tr3600_check_image() {
    cudy_tr3600_check_state || return 1
    local member
    for member in kernel root; do
        tar tf "$1" | grep -qx "sysupgrade-cudy_tr3600-v1/$member" || return 1
    done
}

cudy_tr3600_verify_volume() {
    local image="$1" member="$2" volume_name="$3"
    local length expected actual volume
    length="$(tar xOf "$image" "sysupgrade-cudy_tr3600-v1/$member" | wc -c)"
    [ "$length" -gt 0 ] || return 1
    expected="$(tar xOf "$image" "sysupgrade-cudy_tr3600-v1/$member" | sha256sum)"
    expected="${expected%% *}"
    volume="$(nand_find_volume "$CUDY_UBI" "$volume_name")"
    [ -n "$volume" ] || return 1
    actual="$(head -c "$length" "/dev/$volume" | sha256sum)"
    actual="${actual%% *}"
    [ "$expected" = "$actual" ]
}

cudy_tr3600_do_upgrade() {
    local image="$1"
    cudy_tr3600_check_image "$image" || return 1
    CI_UBIPART=ubi
    CI_KERNPART="$CUDY_TARGET_KERNEL"
    CI_ROOTPART="$CUDY_TARGET_ROOT"
    # Power loss before the last commit leaves the running slot selected.
    fw_setenv "dual_boot.slot_${CUDY_TARGET_SLOT}_invalid" 1 || return 1
    nand_do_flash_file "$image" || return 1
    cudy_tr3600_verify_volume "$image" kernel "$CI_KERNPART" || return 1
    cudy_tr3600_verify_volume "$image" root "$CI_ROOTPART" || return 1
    fw_setenv "dual_boot.slot_${CUDY_TARGET_SLOT}_invalid" 0 || return 1
    fw_setenv dual_boot.current_slot "$CUDY_TARGET_SLOT" || return 1
    nand_do_upgrade_success
}
