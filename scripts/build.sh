#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
builder_dir="$project_dir/work/openwrt-imagebuilder-25.12.5-mediatek-filogic.Linux-x86_64"
if [[ ! -f "$builder_dir/Makefile" ]]; then
  printf '%s\n' 'Extract the verified ImageBuilder archive into work/ first.' >&2
  exit 1
fi
mapfile -t build_args < <(python3 - "$project_dir/config.json" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
print('PROFILE=' + cfg['profile'])
print('PACKAGES=' + ' '.join(cfg['packages']))
print('EXTRA_IMAGE_NAME=' + cfg['image_name'])
PY
)
mkdir -p "$project_dir/output"
make -C "$builder_dir" image "${build_args[@]}" \
  "FILES=$project_dir/files" "BIN_DIR=$project_dir/output" "$@"
