#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace_dir=$(cd -- "${script_dir}/.." && pwd)
bin_dir=${XDG_BIN_HOME:-${HOME}/.local/bin}
data_dir=${XDG_DATA_HOME:-${HOME}/.local/share}/vega-codex-battle
libexec_dir=${data_dir}/libexec
launcher=${bin_dir}/vega-codex-battle
installed_cli=${libexec_dir}/vega_codex_battle.py
installed_protocol=${libexec_dir}/windows_box14_vault_protocol.json
installed_catalog=${libexec_dir}/catalog.json
installed_rom=${libexec_dir}/windows_box14_vault.gba

source_cli=${workspace_dir}/tools/vega_codex_battle.py
source_rebinder=${workspace_dir}/tools/rebind_vega_codex_battle_protocol.py
baseline_resolver=${workspace_dir}/tools/active_play_baseline.py
baseline_manifest=${VEGA_CODEX_BATTLE_BASELINE_SOURCE:-${workspace_dir}/config/active_play_baseline.json}
source_protocol=${VEGA_CODEX_BATTLE_PROTOCOL_SOURCE:-${workspace_dir}/generated/runtime/windows_box14_vault_protocol.json}
source_catalog=${workspace_dir}/content/codex_battle/catalog.json
source_rom=${VEGA_CODEX_BATTLE_ROM_SOURCE:-}
source_stage=${VEGA_CODEX_BATTLE_STAGE:-}

test -f "${source_cli}" || {
    printf '%s\n' "CLI source is missing" >&2
    exit 1
}
test -f "${source_rebinder}" || {
    printf '%s\n' "Protocol ROM rebinder is missing" >&2
    exit 1
}
test -f "${baseline_resolver}" || {
    printf '%s\n' "Active play baseline resolver is missing" >&2
    exit 1
}
test -f "${source_protocol}" || {
    printf '%s\n' "Run the Windows Box 14 vault builder before installing the CLI" >&2
    exit 1
}
if test -z "${source_rom}"; then
    baseline_resolution=$(python3 "${baseline_resolver}" resolve \
        --manifest "${baseline_manifest}" --workspace "${workspace_dir}") || {
        printf '%s\n' "Active play baseline is unavailable or invalid" >&2
        exit 1
    }
    IFS=$'\t' read -r source_rom baseline_stage <<< "${baseline_resolution}"
    if test -n "${source_stage}" && test "${source_stage}" != "${baseline_stage}"; then
        printf '%s\n' "Active play baseline stage conflicts with VEGA_CODEX_BATTLE_STAGE" >&2
        exit 1
    fi
    source_stage=${baseline_stage}
fi
test -f "${source_catalog}" || {
    printf '%s\n' "Canonical battle catalog is missing" >&2
    exit 1
}
test -f "${source_rom}" || {
    printf '%s\n' "Windows Box 14 vault ROM is missing" >&2
    exit 1
}
python3 -c 'import PIL' || {
    printf '%s\n' "Pillow is required for automatic team preview PNGs" >&2
    exit 1
}

install -d -m 0755 "${bin_dir}"
install -d -m 0700 "${data_dir}" "${libexec_dir}"
install -m 0755 "${source_cli}" "${installed_cli}"
install -m 0644 "${source_catalog}" "${installed_catalog}"
install -m 0600 "${source_rom}" "${installed_rom}"

rebind_args=(
    --protocol "${source_protocol}"
    --rom "${installed_rom}"
    --output "${installed_protocol}"
    --rom-path "windows_box14_vault.gba"
)
if test -n "${source_stage}"; then
    rebind_args+=(--stage "${source_stage}")
fi
python3 "${source_rebinder}" "${rebind_args[@]}"
chmod 0644 "${installed_protocol}"

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
