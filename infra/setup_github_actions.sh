#!/usr/bin/env bash
set -euo pipefail

readonly TRUSTED_PATH="/usr/bin:/bin:/usr/games"
readonly PATH="$TRUSTED_PATH"
export PATH

root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
manifest=${root}/infra/toolchain_manifest.json
mode=check

case "${1:---check}" in
  --check) mode=check ;;
  --install) mode=install ;;
  *)
    printf '%s\n' "Usage: bash infra/setup_github_actions.sh [--check|--install]" >&2
    exit 2
    ;;
esac

test -r "${manifest}" || {
  printf '%s\n' "ERROR: toolchain manifestがありません" >&2
  exit 1
}

if test "${mode}" = install; then
  mapfile -t apt_specs < <(
    /usr/bin/python3 -I - "${manifest}" <<'PY'
import json
import sys
with open(sys.argv[1], encoding="utf-8") as stream:
    manifest = json.load(stream)
for package in manifest["apt"]["packages"]:
    if package.get("install", False):
        # GitHub-hosted Ubuntuのsecurity revisionは継続更新されるため、
        # package revisionではなく下段の実行tool identityを固定する。
        print(package["name"])
PY
  )
  /usr/bin/sudo /usr/bin/apt-get update
  /usr/bin/sudo /usr/bin/env DEBIAN_FRONTEND=noninteractive \
    /usr/bin/apt-get install -y --no-install-recommends "${apt_specs[@]}"
fi

/usr/bin/python3 -I - "${manifest}" <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys

manifest = json.load(open(sys.argv[1], encoding="utf-8"))
checks = {
    "python": ["/usr/bin/python3", "--version"],
    "host_cc": ["/usr/bin/cc", "--version"],
    "arm_none_eabi_gcc": ["/usr/bin/arm-none-eabi-gcc", "--version"],
    "mgba": ["/usr/games/mgba", "--version"],
}
for name, command in checks.items():
    expected = manifest["tools"][name]["version_contains"]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    output = completed.stdout + completed.stderr
    if completed.returncode or expected not in output:
        raise SystemExit(
            f"GitHub Actions toolchain: FAIL {name}: expected={expected!r}"
        )
    print(f"[OK] {name}: {manifest['tools'][name]['version']}")

library = Path("/usr/lib/x86_64-linux-gnu/libmgba.so")
header = Path("/usr/include/mgba/core/core.h")
if not library.is_file() or not header.is_file():
    raise SystemExit("GitHub Actions toolchain: FAIL libmGBA development files")
print("GitHub Actions toolchain: PASS")
PY
