#!/usr/bin/env bash
set -euo pipefail
umask 022
export TZ=UTC LANG=C LC_ALL=C
device_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
project_dir="$(cd -- "$device_dir/../.." && pwd)"
builder_dir="$(python3 - "$project_dir" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
print(root / json.loads((root / 'devices/tr1200/build.lock.json').read_text())['workspace'])
PY
)"
if [[ ! -f "$builder_dir/Makefile" ]]; then
  printf '%s\n' 'Run devices/tr1200/scripts/prepare.py first.' >&2
  exit 1
fi
mapfile -t build_args < <(python3 - "$device_dir/config.json" <<'PY'
import json, sys
cfg = json.load(open(sys.argv[1]))
print('PROFILE=' + cfg['profile'])
print('PACKAGES=' + ' '.join(cfg['packages']))
print('EXTRA_IMAGE_NAME=' + cfg['image_name'])
PY
)
overlay_dir="$project_dir/work/tr1200-normalized-overlay"
python3 - "$device_dir/files" "$overlay_dir" <<'PY'
from pathlib import Path
import shutil, stat, sys
source, target = map(Path, sys.argv[1:])
if target.exists():
    shutil.rmtree(target)
shutil.copytree(source, target, symlinks=True)
for path in [target, *target.rglob('*')]:
    if not path.is_symlink():
        path.chmod(0o755 if path.is_dir() else stat.S_IMODE(path.stat().st_mode) & ~0o022)
PY
output_dir="$(python3 - "$project_dir" <<'PY'
import json, sys
from pathlib import Path
root = Path(sys.argv[1])
print(root / json.loads((root / 'devices/tr1200/build.lock.json').read_text())['output_directory'])
PY
)"
mkdir -p "$output_dir"
make -C "$builder_dir" image "${build_args[@]}" \
  "FILES=$overlay_dir" "BIN_DIR=$output_dir" "$@"
