#!/bin/sh
# Restore only the replaced LED sections; preserve other system settings.
set -eu
BACKUP=/root/led-backups/health-before
[ -f "$BACKUP/system" ] && [ -f "$BACKUP/previous-leds.uci" ]
if [ -x /etc/init.d/cudy-health-led ]; then
	/etc/init.d/cudy-health-led stop
	/etc/init.d/cudy-health-led disable
fi
uci -q delete system.cudy_health_white || true
uci -q delete system.cudy_health_red || true
[ ! -s "$BACKUP/previous-leds.uci" ] || uci -m import system < "$BACKUP/previous-leds.uci"
uci commit system
/etc/init.d/led reload
if [ -f /etc/sysupgrade.conf ]; then
	awk -v backup="$BACKUP" '
		$0 != "/etc/config/cudy-health-led" && $0 != "/etc/init.d/cudy-health-led" &&
		$0 != "/usr/libexec/cudy-health-led" && $0 != backup
	' /etc/sysupgrade.conf > "$BACKUP/sysupgrade.conf.filtered"
	cat "$BACKUP/sysupgrade.conf.filtered" > /etc/sysupgrade.conf
fi
rm -f /etc/config/cudy-health-led /etc/init.d/cudy-health-led /usr/libexec/cudy-health-led /etc/uci-defaults/97-cudy-health-led
echo 'Previous LED behavior restored; network and proxy configuration preserved.'
