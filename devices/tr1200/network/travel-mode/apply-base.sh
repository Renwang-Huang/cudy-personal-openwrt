#!/bin/sh
# Native OpenWrt / PassWall settings for changing public uplinks.
set -eu
umask 077
BACKUP=/root/network-backups/travel-quality-before
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
case "${1:---check}" in --check|--apply) ;; *) echo 'Usage: sh apply-base.sh [--check|--apply]'; exit 2 ;; esac
[ "$(id -u)" = 0 ]
[ "$(cat /tmp/sysinfo/board_name)" = cudy,tr1200-v1 ]
[ -z "$(uci changes)" ]
[ "$(uci -q get wireless.default_radio0.network)" = direct24 ]
[ "$(uci -q get wireless.default_radio1.network)" = lan ]
[ "$(uci -q get passwall.@global[0].enabled)" = 1 ]
[ "$(uci -q get network.wan.proto)" = dhcp ]
[ "$(uci -q get network.wwan.proto)" = dhcp ]
[ "$(uci -q get dhcp.direct24dns)" = dnsmasq ]
[ ! -e "$BACKUP/applied" ]
[ ! -e /etc/sysctl.d/99-tr1200-travel.conf ]
[ -f "$DIR/rollback.sh" ]
urltests=$(ubus call uci get '{"config":"passwall","type":"nodes"}' |
	jsonfilter -e '@.values[@.protocol="_urltest"][".name"]')
[ -n "$urltests" ]
echo 'Travel base preflight passed.'
[ "${1:---check}" = --apply ] || exit 0
mkdir -p "$BACKUP"
for config in network wireless dhcp firewall passwall system; do
	if [ -f "$BACKUP/$config" ]; then
		cmp -s "/etc/config/$config" "$BACKUP/$config"
	else
		cp -p "/etc/config/$config" "$BACKUP/$config"
	fi
done
[ -f "$BACKUP/direct_host" ] || cp -p /usr/share/passwall/rules/direct_host "$BACKUP/direct_host"
[ -f "$BACKUP/tcp_mtu_probing" ] || cat /proc/sys/net/ipv4/tcp_mtu_probing > "$BACKUP/tcp_mtu_probing"
cp "$DIR/rollback.sh" "$BACKUP/rollback.sh"
chmod 700 "$BACKUP/rollback.sh"
recover() {
	status=$?
	trap - EXIT HUP INT TERM
	if [ "$status" -ne 0 ]; then "$BACKUP/rollback.sh" || true; fi
	exit "$status"
}
trap recover EXIT
trap 'exit 1' HUP INT TERM
uci set network.wan.metric='10'
uci set dhcp.direct24dns.noresolv='0'
uci set dhcp.direct24dns.resolvfile='/tmp/resolv.conf.d/resolv.conf.auto'
uci -q delete dhcp.direct24dns.server || true
uci set 'passwall.@global[0].direct_dns_mode=auto'
for node in $urltests; do
	uci set "passwall.$node.urltest_interval=3m"
	uci set "passwall.$node.urltest_tolerance=150"
done
grep -qxF detectportal.firefox.com /usr/share/passwall/rules/direct_host ||
	printf '\ndetectportal.firefox.com\n' >> /usr/share/passwall/rules/direct_host
mkdir -p /etc/sysctl.d
printf '%s\n' '# TCP path MTU black-hole recovery for router-originated proxy connections.' \
	'net.ipv4.tcp_mtu_probing=1' > /etc/sysctl.d/99-tr1200-travel.conf
sysctl -p /etc/sysctl.d/99-tr1200-travel.conf
for config in network dhcp passwall; do uci commit "$config"; done
/etc/init.d/network reload
/etc/init.d/dnsmasq restart || true
/etc/init.d/passwall restart
fw4 check
grep -qxF "$BACKUP/" /etc/sysupgrade.conf || printf '%s/\n' "$BACKUP" >> /etc/sysupgrade.conf
printf '%s\n' applied > "$BACKUP/applied"
trap - EXIT HUP INT TERM
echo 'Travel base applied: DHCP DNS, lower probe frequency, wired priority and TCP MTU recovery.'
