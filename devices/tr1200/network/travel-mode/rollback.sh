#!/bin/sh
# Restore only the configuration saved before this travel preparation.
set -eu
BACKUP=/root/network-backups/travel-quality-before
for config in network wireless dhcp firewall passwall system; do [ -f "$BACKUP/$config" ]; done
if [ -x /etc/init.d/travelmate ]; then
	/etc/init.d/travelmate stop || true
	/etc/init.d/travelmate disable || true
fi
/etc/init.d/passwall stop || true
for config in network wireless dhcp firewall passwall system; do
	cp -p "$BACKUP/$config" "/etc/config/$config"
	uci -q revert "$config" || true
done
cp -p "$BACKUP/direct_host" /usr/share/passwall/rules/direct_host
if [ -f "$BACKUP/travelmate" ]; then
	cp -p "$BACKUP/travelmate" /etc/config/travelmate
	uci -q revert travelmate || true
fi
if [ -f "$BACKUP/travelmate-functions.sh" ]; then
	cp -p "$BACKUP/travelmate-functions.sh" /usr/lib/travelmate-functions.sh
fi
rm -f /etc/sysctl.d/99-tr1200-travel.conf
rm -f /usr/share/nftables.d/chain-pre/mangle_output/20-tr1200-captive.nft
rm -f /usr/libexec/cudy-uplink-sync /etc/hotplug.d/iface/98-tr1200-uplink
sysctl -w "net.ipv4.tcp_mtu_probing=$(cat "$BACKUP/tcp_mtu_probing")"
status=0
/etc/init.d/network reload || status=1
wifi reload radio0 || status=1
/etc/init.d/dnsmasq restart || true
/etc/init.d/firewall reload || status=1
/etc/init.d/passwall start || status=1
echo 'Previous routing and proxy configuration restored; added tools remain installed but disabled.'
exit "$status"
