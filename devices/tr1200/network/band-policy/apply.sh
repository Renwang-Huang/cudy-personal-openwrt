#!/bin/sh
# Split downstream Wi-Fi policies without changing the upstream STA or nodes.
set -eu
umask 077
BACKUP=/root/network-backups/band-policy-before
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
case "${1:---check}" in --check|--apply) ;; *) echo 'Usage: sh apply.sh [--check|--apply]'; exit 2 ;; esac
[ "$(id -u)" = 0 ]
[ "$(cat /tmp/sysinfo/board_name)" = cudy,tr1200-v1 ]
[ -z "$(uci changes)" ]
[ "$(uci -q get network.lan.ipaddr)" = 192.168.20.1 ]
[ "$(uci -q get wireless.default_radio0.device)" = radio0 ]
[ "$(uci -q get wireless.default_radio1.device)" = radio1 ]
[ "$(uci -q get wireless.default_radio0.network)" = lan ]
[ "$(uci -q get wireless.default_radio1.network)" = lan ]
[ "$(uci -q get passwall.@global[0].enabled)" = 1 ]
[ -z "$(uci -q get network.direct24 || true)" ]
[ -z "$(uci -q get dhcp.direct24dns || true)" ]
[ -z "$(uci -q get passwall.wifi24_direct || true)" ]
[ -z "$(uci -q get passwall.wifi5_proxy || true)" ]
[ ! -e "$BACKUP" ]
[ -f "$DIR/rollback.sh" ]
base_dns=$(ubus call uci get '{"config":"dhcp","type":"dnsmasq"}' | jsonfilter -e '@.values.*[".name"]' | head -n 1)
lan_zone=$(uci -q show firewall | sed -n "s/^firewall\.\([^=]*\)\.name='lan'$/\1/p" | head -n 1)
[ -n "$base_dns" ] && [ -n "$lan_zone" ]
[ "$(uci -q get "dhcp.$base_dns")" = dnsmasq ]
[ "$(uci -q get dhcp.lan.interface)" = lan ]
echo 'TR1200 band-policy preflight passed.'
[ "${1:---check}" = --apply ] || exit 0
mkdir -p "$BACKUP"
for config in network wireless dhcp firewall passwall; do cp -p "/etc/config/$config" "$BACKUP/$config"; done
cp "$DIR/rollback.sh" "$BACKUP/rollback.sh"
chmod 700 "$BACKUP/rollback.sh"
recover() {
	status=$?
	trap - EXIT HUP INT TERM
	if [ "$status" -ne 0 ]; then "$BACKUP/rollback.sh"; fi
	exit "$status"
}
trap recover EXIT
trap 'exit 1' HUP INT TERM
uci batch <<'UCI'
set network.direct24_device=device
set network.direct24_device.name='br-direct24'
set network.direct24_device.type='bridge'
set network.direct24_device.bridge_empty='1'
set network.direct24=interface
set network.direct24.proto='static'
set network.direct24.device='br-direct24'
set network.direct24.ipaddr='192.168.24.1'
set network.direct24.netmask='255.255.255.0'
set network.direct24.delegate='0'
set network.direct24.ip6assign='0'
set wireless.default_radio0.network='direct24'
set wireless.default_radio0.disabled='0'
set wireless.radio0.disabled='0'
set wireless.default_radio1.disabled='0'
set wireless.radio1.disabled='0'
set dhcp.direct24dns=dnsmasq
set dhcp.direct24dns.nonwildcard='1'
set dhcp.direct24dns.noresolv='1'
set dhcp.direct24dns.localservice='1'
set dhcp.direct24dns.domainneeded='1'
set dhcp.direct24dns.boguspriv='1'
set dhcp.direct24dns.rebind_protection='1'
set dhcp.direct24dns.port='53'
set dhcp.direct24dns.local='/direct24.lan/'
set dhcp.direct24dns.domain='direct24.lan'
set dhcp.direct24dns.leasefile='/tmp/dhcp.direct24.leases'
add_list dhcp.direct24dns.interface='direct24'
add_list dhcp.direct24dns.notinterface='lo'
add_list dhcp.direct24dns.server='223.5.5.5'
set dhcp.direct24=dhcp
set dhcp.direct24.instance='direct24dns'
set dhcp.direct24.interface='direct24'
set dhcp.direct24.start='100'
set dhcp.direct24.limit='150'
set dhcp.direct24.leasetime='12h'
set dhcp.direct24.ignore='0'
set dhcp.direct24.ra='disabled'
set dhcp.direct24.dhcpv6='disabled'
set passwall.@global[0].acl_enable='1'
set passwall.wifi24_direct=acl_rule
set passwall.wifi24_direct.enabled='1'
set passwall.wifi24_direct.remarks='WiFi 2.4G - Direct'
set passwall.wifi24_direct.interface='direct24'
set passwall.wifi24_direct.mode='0'
set passwall.wifi24_direct.use_global_config='0'
set passwall.wifi24_direct.tcp_no_redir_ports='1:65535'
set passwall.wifi24_direct.udp_no_redir_ports='1:65535'
set passwall.wifi24_direct.tcp_proxy_mode='disable'
set passwall.wifi24_direct.udp_proxy_mode='disable'
set passwall.wifi5_proxy=acl_rule
set passwall.wifi5_proxy.enabled='1'
set passwall.wifi5_proxy.remarks='WiFi 5G and LAN - PassWall'
set passwall.wifi5_proxy.interface='lan'
set passwall.wifi5_proxy.mode='1'
set passwall.wifi5_proxy.use_global_config='1'
UCI
uci set "dhcp.$base_dns.nonwildcard=1"
uci add_list "dhcp.$base_dns.notinterface=direct24"
uci set "dhcp.lan.instance=$base_dns"
uci add_list "firewall.$lan_zone.network=direct24"
for config in network wireless dhcp firewall passwall; do uci commit "$config"; done
fw4 check
/etc/init.d/network reload
wifi reload radio0
# Some init-script paths return nonzero even after procd starts both instances.
# Verify the generated pools and live processes instead of masking a real failure.
/etc/init.d/dnsmasq restart || true
dns_ready=0
for delay in 1 1 1 1 1; do
	dns_state=$(ubus call service list '{"name":"dnsmasq"}')
	if [ "$(printf '%s\n' "$dns_state" | jsonfilter -e "@.dnsmasq.instances[\"$base_dns\"].running")" = true ] &&
	   [ "$(printf '%s\n' "$dns_state" | jsonfilter -e '@.dnsmasq.instances.direct24dns.running')" = true ]; then
		dns_ready=1
		break
	fi
	sleep "$delay"
done
[ "$dns_ready" = 1 ]
grep -q '^dhcp-range=set:lan,' "/var/etc/dnsmasq.conf.$base_dns"
grep -q '^dhcp-range=set:direct24,' /var/etc/dnsmasq.conf.direct24dns
/etc/init.d/firewall reload
/etc/init.d/passwall restart
grep -qxF "$BACKUP/" /etc/sysupgrade.conf || printf '%s/\n' "$BACKUP" >> /etc/sysupgrade.conf
trap - EXIT HUP INT TERM
echo 'Band policy applied: 2.4G data/DNS direct; 5G and existing LAN use PassWall rules.'
