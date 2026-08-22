#!/usr/bin/env bash
set -euo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
workspace_dir=$(cd -- "${script_dir}/.." && pwd)
source_dir=${workspace_dir}/tools/codex_skills/vega-codex-battle
codex_root=${CODEX_HOME:-${HOME}/.codex}
target_dir=${codex_root}/skills/vega-codex-battle

test -f "${source_dir}/SKILL.md" || {
    printf '%s\n' "vega-codex-battle skill source is missing" >&2
    exit 1
}
if test -e "${target_dir}" && ! test -d "${target_dir}"; then
    printf '%s\n' "Refusing to replace a non-directory skill target" >&2
    exit 1
fi

install -d -m 0700 "${codex_root}" "${codex_root}/skills" "${target_dir}"
install -m 0644 "${source_dir}/SKILL.md" "${target_dir}/SKILL.md"

cmp -s "${source_dir}/SKILL.md" "${target_dir}/SKILL.md"
printf '%s\n' "vega-codex-battle skill install: PASS"
