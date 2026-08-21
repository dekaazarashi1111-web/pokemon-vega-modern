#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace_dir=$(cd -- "${script_dir}/.." && pwd)
bin_dir=${XDG_BIN_HOME:-${HOME}/.local/bin}
data_dir=${XDG_DATA_HOME:-${HOME}/.local/share}/vega-codex-battle
libexec_dir=${data_dir}/libexec
launcher=${bin_dir}/vega-codex-battle
installed_cli=${libexec_dir}/vega_codex_battle.py
installed_protocol=${libexec_dir}/codex_battle_bridge_protocol.json

source_cli=${workspace_dir}/tools/vega_codex_battle.py
source_protocol=${workspace_dir}/generated/runtime/codex_battle_bridge_protocol.json

test -f "${source_cli}" || {
    printf '%s\n' "CLI source is missing" >&2
    exit 1
}
test -f "${source_protocol}" || {
    printf '%s\n' "Run the Stage 43 builder before installing the CLI" >&2
    exit 1
}

install -d -m 0755 "${bin_dir}"
install -d -m 0700 "${data_dir}" "${libexec_dir}"
install -m 0755 "${source_cli}" "${installed_cli}"
install -m 0644 "${source_protocol}" "${installed_protocol}"

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
