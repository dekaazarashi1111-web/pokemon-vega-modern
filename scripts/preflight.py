from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from common import (
    HashMismatchError,
    hashes,
    input_expectations,
    load_toml,
    logical_path,
    output_expectations,
    repo_root,
    resolved_input_paths,
    verified_hashes,
)


def version(cmd: list[str]) -> str:
    try:
        proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
        return (proc.stdout or proc.stderr).splitlines()[0]
    except Exception as exc:
        return f'ERROR: {exc}'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='config/project.toml')
    args = parser.parse_args()
    root = repo_root()
    cfg = load_toml(root / args.config)
    expected = cfg['expected']
    rows = []
    ok = True
    resolved = resolved_input_paths(root, cfg)
    for key, rel in cfg['inputs'].items():
        path = resolved.get(key, root / rel)
        if path.exists() and path.is_file():
            actual_hashes = hashes(path)
            status = 'OK'
            if key in ('clean_rom', 'vega_ips', 'factory_ups'):
                try:
                    verified_hashes(path, input_expectations(expected, key), key)
                except (HashMismatchError, ValueError):
                    status = 'HASH-MISMATCH'
                    ok = False
            rows.append((key, status, logical_path(root, path), actual_hashes))
        elif key == 'audit_zip':
            rows.append((key, 'OPTIONAL-MISSING', logical_path(root, path), {}))
        else:
            rows.append((key, 'MISSING', logical_path(root, path), {}))
            ok = False

    output_contract_rows = []
    for name in ('vega', 'factory'):
        try:
            contract = output_expectations(expected, name)
            output_contract_rows.append((name, 'OK', contract))
        except ValueError as exc:
            output_contract_rows.append((name, 'CONFIG-ERROR', {'error': str(exc)}))
            ok = False

    reference_rows = []
    for name in ('vega', 'factory'):
        path = root / f'build/reference/{name}.gba'
        if not path.is_file():
            reference_rows.append((name, 'NOT-BUILT', logical_path(root, path), {}))
            continue
        try:
            actual = verified_hashes(path, output_expectations(expected, name), f'{name} reference')
            reference_rows.append((name, 'OK', logical_path(root, path), actual))
        except (HashMismatchError, ValueError) as exc:
            reference_rows.append(
                (name, 'HASH-MISMATCH', logical_path(root, path), {'error': str(exc)})
            )
            ok = False

    tools = ['git','make','python3','arm-none-eabi-gcc','arm-none-eabi-as','arm-none-eabi-objdump','arm-none-eabi-nm']
    tool_rows = [(tool, shutil.which(tool) or 'MISSING', version([tool, '--version']) if shutil.which(tool) else '') for tool in tools]

    out = root / 'reports/generated/preflight.md'
    out.parent.mkdir(parents=True, exist_ok=True)
    lines = ['# Preflight', '', f'Generated: {datetime.now(timezone.utc).isoformat()}', '', '## Inputs', '', '| Name | Status | Path | Hashes |', '|---|---|---|---|']
    for name, status, path, h in rows:
        lines.append(f"| {name} | {status} | `{path}` | `{json.dumps(h, ensure_ascii=False)}` |")
    lines += ['', '## Expected reference contract', '', '| Name | Status | Expected |', '|---|---|---|']
    for name, status, contract in output_contract_rows:
        lines.append(f'| {name} | {status} | `{json.dumps(contract, ensure_ascii=False)}` |')
    lines += ['', '## Reference cache', '', '| Name | Status | Path | Hashes |', '|---|---|---|---|']
    for name, status, path, h in reference_rows:
        lines.append(f'| {name} | {status} | `{path}` | `{json.dumps(h, ensure_ascii=False)}` |')
    lines += ['', '## Tools', '', '| Tool | Path | Version |', '|---|---|---|']
    for tool, path, ver in tool_rows:
        lines.append(f'| {tool} | `{path}` | `{ver}` |')
    out.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(out)
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
