#!/bin/sh
# Restore only LuCI settings. Retain packages to avoid removing shared dependencies.
set -eu
umask 077
BACKUP=/root/ui-backups/argon-v3.1.2
[ "$(id -u)" = 0 ] || { echo 'Root is required.' >&2; exit 1; }
if [ ! -f "$BACKUP/luci" ] || [ -L "$BACKUP/luci" ]; then
    echo 'Saved LuCI configuration is missing.' >&2
    exit 1
fi
apk info -e luci-theme-bootstrap >/dev/null 2>&1
cp -p "$BACKUP/luci" /etc/config/luci
if [ -f "$BACKUP/argon" ]; then cp -p "$BACKUP/argon" /etc/config/argon; fi
/etc/init.d/rpcd restart
echo 'Previous LuCI settings restored. Open a fresh browser page.'
