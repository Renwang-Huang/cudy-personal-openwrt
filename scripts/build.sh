#!/usr/bin/env bash
set -euo pipefail
umask 022
export TZ=UTC LANG=C LC_ALL=C
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
overlay_dir="$project_dir/work/normalized-overlay"
python3 - "$project_dir/files" "$overlay_dir" <<'PY'
from pathlib import Path
import shutil, stat, sys
source, target = map(Path, sys.argv[1:])
if target.exists():
    shutil.rmtree(target)
shutil.copytree(source, target, symlinks=True)
for path in [target, *target.rglob('*')]:
    if path.is_symlink():
        continue
    if path.is_dir():
        path.chmod(0o755)
    else:
        # Git does not retain group-write bits; normalize these while preserving
        # deliberately restrictive file modes and executable flags.
        path.chmod(stat.S_IMODE(path.stat().st_mode) & ~0o022)
PY
mkdir -p "$project_dir/output"
make -C "$builder_dir" image "${build_args[@]}" \
  "FILES=$overlay_dir" "BIN_DIR=$project_dir/output" "$@"
