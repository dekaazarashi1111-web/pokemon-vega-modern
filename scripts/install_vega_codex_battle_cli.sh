#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace_dir=$(cd -- "${script_dir}/.." && pwd)
bin_dir=${XDG_BIN_HOME:-${HOME}/.local/bin}
data_dir=${XDG_DATA_HOME:-${HOME}/.local/share}/vega-codex-battle
libexec_dir=${data_dir}/libexec
launcher=${bin_dir}/vega-codex-battle
installed_cli=${libexec_dir}/vega_codex_battle.py
installed_protocol=${libexec_dir}/codex_battle_runtime_protocol.json
installed_catalog=${libexec_dir}/catalog.json
installed_rom=${libexec_dir}/codex_battle_runtime.gba

source_cli=${workspace_dir}/tools/vega_codex_battle.py
source_protocol=${workspace_dir}/generated/runtime/codex_battle_runtime_protocol.json
source_catalog=${workspace_dir}/content/codex_battle/catalog.json
source_rom=${workspace_dir}/build/stages/44_codex_battle_runtime.gba

test -f "${source_cli}" || {
    printf '%s\n' "CLI source is missing" >&2
    exit 1
}
test -f "${source_protocol}" || {
    printf '%s\n' "Run the Stage 44 builder before installing the CLI" >&2
    exit 1
}
test -f "${source_catalog}" || {
    printf '%s\n' "Stage 44 read-only catalog is missing" >&2
    exit 1
}
test -f "${source_rom}" || {
    printf '%s\n' "Stage 44 ROM is missing" >&2
    exit 1
}
python3 -c 'import PIL' || {
    printf '%s\n' "Pillow is required for automatic team preview PNGs" >&2
    exit 1
}

install -d -m 0755 "${bin_dir}"
install -d -m 0700 "${data_dir}" "${libexec_dir}"
install -m 0755 "${source_cli}" "${installed_cli}"
install -m 0644 "${source_protocol}" "${installed_protocol}"
install -m 0644 "${source_catalog}" "${installed_catalog}"
install -m 0600 "${source_rom}" "${installed_rom}"

if test -e "${launcher}" && ! test -L "${launcher}"; then
    printf '%s\n' "Refusing to replace a non-symlink vega-codex-battle launcher" >&2
    exit 1
fi
ln -sfn "${installed_cli}" "${launcher}"

(
    cd /tmp
    "${launcher}" --help >/dev/null
)

printf '%s\n' "vega-codex-battle install: PASS"
