#!/usr/bin/env bash
set -euo pipefail
umask 022
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../../.." && pwd)"
source_dir="$project_dir/work/tr3600-source"
revision="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["source_commit"])' "$project_dir/devices/tr3600/build.lock.json")"
if [[ ! -d "$source_dir/.git" ]]; then
  mkdir -p "$source_dir"
  git -C "$source_dir" init -q
  git -C "$source_dir" remote add origin https://github.com/openwrt/openwrt.git
  git -C "$source_dir" -c protocol.version=2 fetch --depth=1 --no-tags origin "$revision"
  git -C "$source_dir" checkout --detach FETCH_HEAD
fi
actual="$(git -C "$source_dir" rev-parse HEAD)"
[[ "$actual" == "$revision" ]] || { printf '%s\n' 'Unexpected source revision; inspect work/tr3600-source.' >&2; exit 1; }
printf '%s\n' "$source_dir"
