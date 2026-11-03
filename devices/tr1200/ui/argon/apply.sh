#!/bin/sh
# Optional UI installation. Run --check first. This does not flash firmware.
set -eu
umask 077
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
BACKUP=/root/ui-backups/argon-v3.1.2
ACTION=${1:---check}
case "$ACTION" in --check|--apply) ;; *) echo 'Usage: sh apply.sh [--check|--apply]'; exit 2 ;; esac
fail() { echo "$*" >&2; exit 1; }
[ "$(id -u)" = 0 ] || fail 'Root is required on the router.'
# shellcheck disable=SC1091
. /etc/openwrt_release
[ "$DISTRIB_RELEASE" = 25.12.5 ] || fail 'This kit requires OpenWrt 25.12.5.'
[ "$DISTRIB_TARGET" = ramips/mt76x8 ] || fail 'Unexpected platform.'
BOARD=$(ubus call system board | jsonfilter -e '@.board_name')
[ "$BOARD" = 'cudy,tr1200-v1' ] || fail 'This kit is only for Cudy TR1200 v1.'
apk info -e luci-theme-bootstrap >/dev/null 2>&1 || fail 'Keep Bootstrap installed before proceeding.'
if apk info -e luci-theme-argon >/dev/null 2>&1; then
    fail 'Argon is already installed. Review the existing installation first.'
fi
[ ! -e "$BACKUP" ] || fail 'A previous backup exists. Keep it and review before repeating.'
AVAILABLE=$(df -Pk /overlay | awk 'NR == 2 { print $4 }')
[ "${AVAILABLE:-0}" -ge 4096 ] || fail 'At least 4 MiB free overlay space is required.'
set -- "$DIR"/packages/*.apk
[ "$#" = 7 ] || fail 'Exactly seven fixed packages are required.'
for file in "$@"; do
    if [ ! -f "$file" ] || [ -L "$file" ]; then fail 'Unexpected package file.'; fi
done
(
    cd "$DIR"
    md5sum -c packages.verify >/dev/null 2>&1
) || fail 'The offline package set is incomplete or changed.'
apk --no-network --repositories-file /dev/null add --simulate --allow-untrusted "$DIR"/packages/*.apk
echo 'Preflight passed; no package or configuration changes have been made.'
[ "$ACTION" = --apply ] || exit 0
mkdir -p "$BACKUP"
cp -p /etc/config/luci "$BACKUP/luci"
if [ -f /etc/config/argon ]; then cp -p /etc/config/argon "$BACKUP/argon"; fi
cp "$DIR/rollback.sh" "$BACKUP/rollback.sh"
chmod 700 "$BACKUP/rollback.sh"
restore_on_error() {
    cp -p "$BACKUP/luci" /etc/config/luci
    if [ -f "$BACKUP/argon" ]; then cp -p "$BACKUP/argon" /etc/config/argon; fi
    /etc/init.d/rpcd restart >/dev/null 2>&1 || true
    echo "Installation did not complete; the previous LuCI configuration was restored. Logs: $BACKUP/install.log" >&2
}
trap restore_on_error EXIT
if ! apk --no-network --repositories-file /dev/null add --allow-untrusted "$DIR"/packages/*.apk >"$BACKUP/install.log" 2>&1; then
    exit 1
fi
uci batch <<'UCI'
set luci.main.mediaurlbase='/luci-static/argon'
set luci.main.lang='zh_cn'
set argon.@global[0].login_style='centered'
set argon.@global[0].mode='normal'
set argon.@global[0].online_wallpaper='none'
set argon.@global[0].blur='0'
set argon.@global[0].blur_dark='0'
set argon.@global[0].transparency='1'
set argon.@global[0].transparency_dark='1'
commit argon
commit luci
UCI
/etc/init.d/rpcd restart
trap - EXIT
echo "Argon installed. Open a fresh browser page. UI rollback: sh $BACKUP/rollback.sh"
