#!/bin/sh
# Restore the exact private configuration saved before band separation.
set -eu
BACKUP=/root/network-backups/band-policy-before
for config in network wireless dhcp firewall passwall; do [ -f "$BACKUP/$config" ]; done
/etc/init.d/passwall stop || true
for config in network wireless dhcp firewall passwall; do
	cp -p "$BACKUP/$config" "/etc/config/$config"
	uci -q revert "$config" || true
done
status=0
/etc/init.d/network reload || status=1
wifi reload radio0 || status=1
/etc/init.d/dnsmasq restart || true
base_dns=$(ubus call uci get '{"config":"dhcp","type":"dnsmasq"}' | jsonfilter -e '@.values.*[".name"]' | head -n 1)
dns_ready=0
for delay in 1 1 1 1 1; do
	dns_state=$(ubus call service list '{"name":"dnsmasq"}')
	if [ -n "$base_dns" ] &&
	   [ "$(printf '%s\n' "$dns_state" | jsonfilter -e "@.dnsmasq.instances[\"$base_dns\"].running")" = true ]; then
		dns_ready=1
		break
	fi
	sleep "$delay"
done
[ "$dns_ready" = 1 ] || status=1
/etc/init.d/firewall reload || status=1
if [ "$(uci -q get passwall.@global[0].enabled)" = 1 ]; then /etc/init.d/passwall start || status=1; fi
if [ "$status" = 0 ]; then
	echo 'Previous wireless, DHCP, firewall and proxy settings restored.'
else
	echo 'Configuration restored; one or more services require inspection.' >&2
fi
exit "$status"
