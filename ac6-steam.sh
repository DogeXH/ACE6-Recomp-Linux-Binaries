#!/usr/bin/env bash
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
if [[ ! -f "$script_dir/ac6recomp.toml" ]]; then
  printf 'Run python3 setup.py --iso /path/to/your/game.iso first.\n' >&2
  exit 1
fi
export AC6_GLIBC_RUNTIME="$script_dir/runtime"
export AC6_DECK_TUNE=1
exec /usr/bin/python3 "$script_dir/ac6-launch.py" "$@"
