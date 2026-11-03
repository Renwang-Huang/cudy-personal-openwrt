#!/bin/sh
# Run manually on the intended TR1200. Prints metadata only; no writes, dumps,
# network changes, reboots, recovery traffic, or firmware upgrade commands.
# OpenWrt jshn initializes variables by reading unset values; nounset breaks it.
set -e
[ -r /usr/share/libubox/jshn.sh ] || {
  echo 'OpenWrt JSON helper is required; do not run this on another host.' >&2
  exit 1
}
# shellcheck source=/dev/null
. /usr/share/libubox/jshn.sh
json_init
json_add_string board_name "$(cat /tmp/sysinfo/board_name 2>/dev/null || true)"
json_add_string model "$(cat /tmp/sysinfo/model 2>/dev/null || true)"
json_add_string kernel "$(uname -r)"
json_add_string openwrt_release "$(cat /etc/openwrt_release 2>/dev/null || true)"
json_add_string proc_mtd "$(cat /proc/mtd 2>/dev/null || true)"
json_add_array mtd
for entry in /sys/class/mtd/mtd[0-9]*; do
  [ -d "$entry" ] || continue
  number="${entry##*/mtd}"
  case "$number" in ''|*[!0-9]*) continue ;; esac
  json_add_object ''
  json_add_string device "${entry##*/}"
  for field in name size erasesize offset flags; do
    json_add_string "$field" "$(cat "$entry/$field" 2>/dev/null || true)"
  done
  json_close_object
done
json_close_array
json_add_boolean contains_flash_backup 0
json_add_boolean physical_device_identity_verified 0
json_add_boolean recovery_tested 0
json_dump
