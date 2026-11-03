#!/bin/sh
# Apply on a matching TR1200; network and proxy services are never restarted.
set -eu
umask 077
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
BACKUP=/root/led-backups/health-before
case "${1:---check}" in --check|--apply) ;; *) echo 'Usage: sh apply.sh [--check|--apply]'; exit 2 ;; esac
[ "$(id -u)" = 0 ]
[ "$(cat /tmp/sysinfo/board_name)" = cudy,tr1200-v1 ]
[ -z "$(uci changes)" ] || { echo 'Pending UCI changes must be resolved first.' >&2; exit 1; }
for tool in ubus jsonfilter pgrep nft nslookup timeout curl; do command -v "$tool" >/dev/null; done
for led in white:status red:power; do
	[ -w "/sys/class/leds/$led/brightness" ]
	grep -qw none "/sys/class/leds/$led/trigger"
done
for file in etc/config/cudy-health-led etc/init.d/cudy-health-led etc/uci-defaults/97-cudy-health-led usr/libexec/cudy-health-led; do
	[ -f "$DIR/files/$file" ]
	[ ! -e "/$file" ] || { echo "Already installed: /$file" >&2; exit 1; }
done
[ ! -e "$BACKUP" ] || { echo 'A previous health-LED backup exists; review it before applying.' >&2; exit 1; }
echo 'Health indicator preflight passed.'
[ "${1:---check}" = --apply ] || exit 0
mkdir -p "$BACKUP"
cp -p /etc/config/system "$BACKUP/system"
uci export system | awk '
	/^config / { keep=($2 == "led" && ($3 == "\047cudy_starship_white\047" || $3 == "\047cudy_starship_red\047")) }
	keep { print }
' > "$BACKUP/previous-leds.uci"
[ ! -f /etc/sysupgrade.conf ] || cp -p /etc/sysupgrade.conf "$BACKUP/sysupgrade.conf.before"
cp "$DIR/rollback.sh" "$BACKUP/rollback.sh"
chmod 700 "$BACKUP/rollback.sh"
recover() {
	status=$?
	trap - EXIT HUP INT TERM
	if [ "$status" -ne 0 ]; then "$BACKUP/rollback.sh"; fi
	exit "$status"
}
trap recover EXIT HUP INT TERM
for file in etc/config/cudy-health-led etc/init.d/cudy-health-led etc/uci-defaults/97-cudy-health-led usr/libexec/cudy-health-led; do
	cp "$DIR/files/$file" "/$file"
	case "$file" in etc/config/*) chmod 644 "/$file" ;; *) chmod 755 "/$file" ;; esac
done
/usr/libexec/cudy-health-led --check
/etc/uci-defaults/97-cudy-health-led
rm /etc/uci-defaults/97-cudy-health-led
/etc/init.d/led reload
/etc/init.d/cudy-health-led start
for path in /etc/config/cudy-health-led /etc/init.d/cudy-health-led /usr/libexec/cudy-health-led "$BACKUP"; do
	grep -Fqx "$path" /etc/sysupgrade.conf || printf '%s\n' "$path" >> /etc/sysupgrade.conf
done
trap - EXIT HUP INT TERM
echo 'Steady white/red health indicators enabled; previous LED settings backed up.'
