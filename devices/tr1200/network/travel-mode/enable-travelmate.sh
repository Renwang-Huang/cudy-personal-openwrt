#!/bin/sh
# Use the pinned upstream travel manager with the existing wireless uplink.
set -eu
umask 077
BACKUP=/root/network-backups/travel-quality-before
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
case "${1:---check}" in --check|--apply) ;; *) echo 'Usage: sh enable-travelmate.sh [--check|--apply]'; exit 2 ;; esac
[ "$(id -u)" = 0 ]
[ "$(cat /tmp/sysinfo/board_name)" = cudy,tr1200-v1 ]
[ -f "$BACKUP/applied" ]
[ ! -e "$BACKUP/travelmate-applied" ]
[ -z "$(uci changes)" ]
apk info -v | grep -qx 'travelmate-2.4.9-r6'
[ "$(uci -q get wireless.uplink.mode)" = sta ]
[ "$(uci -q get wireless.uplink.network)" = wwan ]
[ "$(uci -q get wireless.uplink.device)" = radio0 ]
[ -s "$DIR/files/usr/lib/travelmate-functions.sh" ]
echo 'Travelmate preflight passed.'
[ "${1:---check}" = --apply ] || exit 0
cp -p /etc/config/travelmate "$BACKUP/travelmate"
cp -p /usr/lib/travelmate-functions.sh "$BACKUP/travelmate-functions.sh"
recover() {
	status=$?
	trap - EXIT HUP INT TERM
	if [ "$status" -ne 0 ]; then "$BACKUP/rollback.sh" || true; fi
	exit "$status"
}
trap recover EXIT
trap 'exit 1' HUP INT TERM
cp "$DIR/files/usr/lib/travelmate-functions.sh" /usr/lib/travelmate-functions.sh
chmod 644 /usr/lib/travelmate-functions.sh
mkdir -p /usr/share/nftables.d/chain-pre/mangle_output
cp "$DIR/files/usr/share/nftables.d/chain-pre/mangle_output/20-tr1200-captive.nft" \
	/usr/share/nftables.d/chain-pre/mangle_output/20-tr1200-captive.nft
mkdir -p /usr/libexec /etc/hotplug.d/iface
cp "$DIR/files/usr/libexec/cudy-uplink-sync" /usr/libexec/cudy-uplink-sync
cp "$DIR/files/etc/hotplug.d/iface/98-tr1200-uplink" /etc/hotplug.d/iface/98-tr1200-uplink
chmod 755 /usr/libexec/cudy-uplink-sync /etc/hotplug.d/iface/98-tr1200-uplink
ssid=$(uci -q get wireless.uplink.ssid)
bssid=$(uci -q get wireless.uplink.bssid || true)
uci batch <<'UCI'
set travelmate.global.trm_enabled='1'
set travelmate.global.trm_iface='wwan'
set travelmate.global.trm_laniface='lan'
set travelmate.global.trm_radio='radio0'
set travelmate.global.trm_captive='1'
set travelmate.global.trm_captiveurl='http://connect.rom.miui.com/generate_204'
set travelmate.global.trm_netcheck='0'
set travelmate.global.trm_proactive='0'
set travelmate.global.trm_autoadd='0'
set travelmate.global.trm_randomize='0'
set travelmate.global.trm_timeout='120'
set travelmate.global.trm_maxwait='60'
set travelmate.global.trm_nice='10'
set travelmate.current=uplink
set travelmate.current.enabled='1'
set travelmate.current.device='radio0'
set travelmate.current.revive='10'
UCI
uci set "travelmate.current.ssid=$ssid"
[ -z "$bssid" ] || uci set "travelmate.current.bssid=$bssid"
uci commit travelmate
fw4 check
/etc/init.d/firewall reload
/etc/init.d/rpcd restart
/etc/init.d/travelmate enable
/etc/init.d/travelmate start
grep -qxF /usr/lib/travelmate-functions.sh /etc/sysupgrade.conf ||
	printf '%s\n' /usr/lib/travelmate-functions.sh >> /etc/sysupgrade.conf
for entry in /usr/share/nftables.d/chain-pre/mangle_output/20-tr1200-captive.nft \
	/etc/sysctl.d/99-tr1200-travel.conf /usr/share/passwall/rules/direct_host \
	/usr/libexec/cudy-uplink-sync /etc/hotplug.d/iface/98-tr1200-uplink; do
	grep -qxF "$entry" /etc/sysupgrade.conf || printf '%s\n' "$entry" >> /etc/sysupgrade.conf
done
printf '%s\n' applied > "$BACKUP/travelmate-applied"
trap - EXIT HUP INT TERM
echo 'Travelmate enabled for saved 2.4 GHz uplinks; unknown open networks and MAC rotation stay disabled.'
