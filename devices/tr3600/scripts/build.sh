#!/usr/bin/env bash
set -euo pipefail
umask 022
export TZ=UTC LANG=C LC_ALL=C
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
source_dir="$project_dir/work/tr3600-source"
export SOURCE_DATE_EPOCH=1782737960
export BUILD_USER=builder BUILD_HOST=openwrt
jobs="${JOBS:-6}"
bash "$project_dir/devices/tr3600/scripts/check-slot-logic.sh"
make -C "$source_dir" -j"$jobs" download
make -C "$source_dir" -j"$jobs" "$@"
