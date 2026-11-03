#!/bin/sh
# Apply the two standard kernel LED triggers, preserving a configuration backup.
set -eu
umask 077
DIR=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd)
BACKUP=/root/led-backups/starship-calm-before
case "${1:---check}" in --check|--apply) ;; *) echo 'Usage: sh apply.sh [--check|--apply]'; exit 2 ;; esac
[ "$(id -u)" = 0 ] || { echo 'Root is required on the router.' >&2; exit 1; }
BOARD=$(ubus call system board | jsonfilter -e '@.board_name')
[ "$BOARD" = 'cudy,tr1200-v1' ] || { echo 'This preset is only for Cudy TR1200 v1.' >&2; exit 1; }
for led in white:status red:power; do
    [ -w "/sys/class/leds/$led/trigger" ] || exit 1
done
grep -qw timer /sys/class/leds/white:status/trigger
grep -qw netdev /sys/class/leds/red:power/trigger
[ -d /sys/class/net/br-lan ]
[ -f "$DIR/starship-calm.uci" ]
[ -z "$(uci changes system)" ] || { echo 'Commit or revert pending system changes first.' >&2; exit 1; }
echo 'Preset preflight passed.'
[ "${1:---check}" = --apply ] || exit 0
[ ! -e "$BACKUP" ] || { echo 'A previous backup exists; review it before applying again.' >&2; exit 1; }
for section in cudy_starship_white cudy_starship_red; do
    if uci -q get "system.$section" >/dev/null; then
        echo 'This preset is already configured; use the LED settings page.' >&2
        exit 1
    fi
done
mkdir -p "$BACKUP"
cp -p /etc/config/system "$BACKUP/system"
uci -q batch < "$DIR/starship-calm.uci"
/etc/init.d/led enable
/etc/init.d/led reload
echo 'Starship calm indicators applied. Original system configuration is backed up.'
