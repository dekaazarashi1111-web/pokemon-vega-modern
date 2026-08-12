from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import shutil
import struct
import tempfile
import zlib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from common import (
    compare_hashes,
    hashes,
    load_toml,
    logical_path,
    output_expectations,
    project_path,
    repo_root,
    resolved_input_paths,
    stable_digest,
    verified_hashes,
    verify_required_inputs,
    write_json,
)


CACHE_FILE = '.artifact-cache.json'
AUDIT_ARTIFACTS = {
    'exact_conflicts.csv',
    'exact_conflicts.json',
    'exact_conflicts.md',
}
REFERENCE_NAMES = {'vega': 'vega.gba', 'factory': 'factory.gba'}
LEGACY_REFERENCE_NAMES = {
    'vega': 'vega_reference.gba',
    'factory': 'factory_reference.gba',
}


@dataclass(frozen=True)
class ByteRange:
    start: int
    end: int


def _union_ranges(ranges: list[ByteRange]) -> list[ByteRange]:
    result: list[ByteRange] = []
    for current in sorted(
        (item for item in ranges if item.end > item.start),
        key=lambda item: (item.start, item.end),
    ):
        if not result or current.start > result[-1].end:
            result.append(current)
        elif current.end > result[-1].end:
            result[-1] = ByteRange(result[-1].start, current.end)
    return result


def _intersect_ranges(left: list[ByteRange], right: list[ByteRange]) -> list[ByteRange]:
    result: list[ByteRange] = []
    left_index = right_index = 0
    while left_index < len(left) and right_index < len(right):
        start = max(left[left_index].start, right[right_index].start)
        end = min(left[left_index].end, right[right_index].end)
        if start < end:
            result.append(ByteRange(start, end))
        if left[left_index].end < right[right_index].end:
            left_index += 1
        else:
            right_index += 1
    return result


def _read_ups_vli(data: bytes, position: int, limit: int) -> tuple[int, int]:
    value = 0
    shift = 1
    while True:
        if position >= limit:
            raise ValueError('Truncated UPS variable-length integer')
        byte = data[position]
        position += 1
        value += (byte & 0x7F) * shift
        if byte & 0x80:
            return value, position
        shift <<= 7
        value += shift
        if shift > (1 << 63):
            raise ValueError('UPS variable-length integer is unreasonably large')


def _apply_ips_compact(source: bytes, patch: bytes) -> tuple[bytearray, list[ByteRange]]:
    if not patch.startswith(b'PATCH'):
        raise ValueError('Invalid IPS header')
    output = bytearray(source)
    records: list[ByteRange] = []
    position = 5
    while True:
        if position + 3 > len(patch):
            raise ValueError('Truncated IPS before EOF')
        if patch[position:position + 3] == b'EOF':
            position += 3
            break
        offset = int.from_bytes(patch[position:position + 3], 'big')
        position += 3
        if position + 2 > len(patch):
            raise ValueError('Truncated IPS record header')
        length = int.from_bytes(patch[position:position + 2], 'big')
        position += 2
        if length:
            if position + length > len(patch):
                raise ValueError('Truncated IPS raw record')
            payload = patch[position:position + length]
            position += length
        else:
            if position + 3 > len(patch):
                raise ValueError('Truncated IPS RLE record')
            length = int.from_bytes(patch[position:position + 2], 'big')
            value = patch[position + 2]
            position += 3
            if length == 0:
                raise ValueError('IPS RLE record has zero length')
            payload = bytes([value]) * length
        end = offset + length
        if end > len(output):
            output.extend(b'\0' * (end - len(output)))
        output[offset:end] = payload
        records.append(ByteRange(offset, end))

    trailing = len(patch) - position
    if trailing == 3:
        target_size = int.from_bytes(patch[position:position + 3], 'big')
        if target_size < len(output):
            del output[target_size:]
        elif target_size > len(output):
            output.extend(b'\0' * (target_size - len(output)))
    elif trailing:
        raise ValueError(f'Unsupported trailing IPS data ({trailing} bytes)')
    return output, _union_ranges(records)


def _apply_ups_compact(
    source: bytes, patch: bytes
) -> tuple[bytearray, list[ByteRange], int]:
    if not patch.startswith(b'UPS1') or len(patch) < 16:
        raise ValueError('Invalid or truncated UPS file')
    expected_patch_crc = struct.unpack('<I', patch[-4:])[0]
    actual_patch_crc = zlib.crc32(patch[:-4]) & 0xFFFFFFFF
    if actual_patch_crc != expected_patch_crc:
        raise ValueError(
            f'UPS patch CRC mismatch: {actual_patch_crc:08X} != {expected_patch_crc:08X}'
        )

    footer = len(patch) - 12
    position = 4
    input_size, position = _read_ups_vli(patch, position, footer)
    output_size, position = _read_ups_vli(patch, position, footer)
    source_crc, target_crc, _ = struct.unpack('<III', patch[-12:])
    if len(source) != input_size:
        raise ValueError(f'UPS input size mismatch: {len(source)} != {input_size}')
    actual_source_crc = zlib.crc32(source) & 0xFFFFFFFF
    if actual_source_crc != source_crc:
        raise ValueError(
            f'UPS source CRC mismatch: {actual_source_crc:08X} != {source_crc:08X}'
        )

    output = bytearray(output_size)
    output[:min(len(source), output_size)] = source[:output_size]
    records: list[ByteRange] = []
    offset = 0
    while position < footer:
        relative, position = _read_ups_vli(patch, position, footer)
        offset += relative
        start = offset
        while True:
            if position >= footer:
                raise ValueError('Truncated UPS XOR block')
            xor_byte = patch[position]
            position += 1
            if xor_byte == 0:
                break
            if offset >= output_size:
                raise ValueError('UPS XOR block writes beyond declared output size')
            source_byte = source[offset] if offset < len(source) else 0
            output[offset] = source_byte ^ xor_byte
            offset += 1
        records.append(ByteRange(start, offset))
        offset += 1
    if position != footer:
        raise ValueError('Malformed UPS footer alignment')
    actual_target_crc = zlib.crc32(output) & 0xFFFFFFFF
    if actual_target_crc != target_crc:
        raise ValueError(
            f'UPS target CRC mismatch: {actual_target_crc:08X} != {target_crc:08X}'
        )
    return output, _union_ranges(records), target_crc


def _zero_padded_slice(data: bytes | bytearray, start: int, end: int) -> bytes:
    payload = bytes(data[start:min(end, len(data))]) if start < len(data) else b''
    return payload + b'\0' * ((end - start) - len(payload))


def run_compact_exact_audit(
    clean_path: Path,
    ips_path: Path,
    ups_path: Path,
    out_dir: Path,
    *,
    write_reference_roms: bool,
) -> None:
    """Generate exact reports without materializing millions of dict entries."""

    clean = clean_path.read_bytes()
    ips_data = ips_path.read_bytes()
    ups_data = ups_path.read_bytes()
    vega, ips_ranges = _apply_ips_compact(clean, ips_data)
    factory, ups_ranges, factory_crc = _apply_ups_compact(clean, ups_data)
    overlaps = _intersect_ranges(ips_ranges, ups_ranges)

    statuses: list[tuple[int, str]] = []
    same_count = different_count = 0
    for overlap in overlaps:
        for offset in range(overlap.start, overlap.end):
            vega_byte = vega[offset] if offset < len(vega) else 0
            factory_byte = factory[offset] if offset < len(factory) else 0
            status = 'SAME_TARGET' if vega_byte == factory_byte else 'DIFFERENT_TARGET'
            statuses.append((offset, status))
            if status == 'SAME_TARGET':
                same_count += 1
            else:
                different_count += 1

    exact_ranges: list[tuple[int, int, str]] = []
    for offset, status in statuses:
        if exact_ranges and exact_ranges[-1][1] == offset and exact_ranges[-1][2] == status:
            start, _, previous_status = exact_ranges[-1]
            exact_ranges[-1] = (start, offset + 1, previous_status)
        else:
            exact_ranges.append((offset, offset + 1, status))

    rows: list[dict[str, str | int]] = []
    for number, (start, end, status) in enumerate(exact_ranges, 1):
        rows.append(
            {
                'id': number,
                'status': status,
                'file_offset_start': f'0x{start:08X}',
                'file_offset_end_inclusive': f'0x{end - 1:08X}',
                'gba_address_start': f'0x{0x08000000 + start:08X}',
                'gba_address_end_inclusive': f'0x{0x08000000 + end - 1:08X}',
                'length': end - start,
                'clean_hex': _zero_padded_slice(clean, start, end).hex().upper(),
                'vega_target_hex': _zero_padded_slice(vega, start, end).hex().upper(),
                'factory_target_hex': _zero_padded_slice(factory, start, end).hex().upper(),
            }
        )

    out_dir.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        'id', 'status', 'file_offset_start', 'file_offset_end_inclusive',
        'gba_address_start', 'gba_address_end_inclusive', 'length', 'clean_hex',
        'vega_target_hex', 'factory_target_hex',
    ]
    with (out_dir / 'exact_conflicts.csv').open(
        'w', newline='', encoding='utf-8-sig'
    ) as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    total = same_count + different_count
    summary = {
        'inputs': {
            'clean_rom_size': len(clean),
            'clean_crc32': f'{zlib.crc32(clean) & 0xFFFFFFFF:08X}',
            'clean_sha256': hashlib.sha256(clean).hexdigest(),
            'vega_ips': ips_path.name,
            'vega_ips_sha256': hashlib.sha256(ips_data).hexdigest(),
            'factory_ups': ups_path.name,
            'factory_ups_sha256': hashlib.sha256(ups_data).hexdigest(),
        },
        'outputs': {
            'vega_size': len(vega),
            'vega_crc32': f'{zlib.crc32(vega) & 0xFFFFFFFF:08X}',
            'vega_sha256': hashlib.sha256(vega).hexdigest(),
            'factory_size': len(factory),
            'factory_crc32': f'{factory_crc:08X}',
            'factory_sha256': hashlib.sha256(factory).hexdigest(),
        },
        'comparison': {
            'double_touched_bytes': total,
            'same_target_bytes': same_count,
            'different_target_bytes': different_count,
            'exact_status_range_count': len(exact_ranges),
            'same_target_percent': round(100 * same_count / total, 8) if total else 0,
            'different_target_percent': round(100 * different_count / total, 8) if total else 0,
        },
        'ranges': rows,
    }
    write_json(out_dir / 'exact_conflicts.json', summary)
    comparison = summary['comparison']
    lines = [
        '# Clean ROMを使った厳密競合判定', '',
        f"- Clean CRC32: `{summary['inputs']['clean_crc32']}`",
        f"- Vega output CRC32: `{summary['outputs']['vega_crc32']}`",
        f"- Factory output CRC32: `{summary['outputs']['factory_crc32']}`",
        f"- 両パッチが触るbytes: **{comparison['double_touched_bytes']:,}**",
        f"- 同じ値へ変更: **{comparison['same_target_bytes']:,}**",
        f"- 異なる値へ変更: **{comparison['different_target_bytes']:,}**", '',
        '`SAME_TARGET`でも、周辺のポインタ依存やRAM/save構造が互換とは限りません。',
        '`DIFFERENT_TARGET`は、少なくともバイト単位で明確な移植判断が必要です。',
        'このツールは統合ROMを生成しません。',
    ]
    (out_dir / 'exact_conflicts.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')

    if write_reference_roms:
        references = out_dir / 'reference_roms'
        references.mkdir()
        (references / 'vega_reference.gba').write_bytes(vega)
        (references / 'factory_reference.gba').write_bytes(factory)


def build_compact_references(
    clean_path: Path, ips_path: Path, ups_path: Path, out_dir: Path
) -> None:
    clean = clean_path.read_bytes()
    vega, _ = _apply_ips_compact(clean, ips_path.read_bytes())
    factory, _, _ = _apply_ups_compact(clean, ups_path.read_bytes())
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / 'vega_reference.gba').write_bytes(vega)
    (out_dir / 'factory_reference.gba').write_bytes(factory)


def _manifest_records(seed: Path) -> dict[str, str]:
    manifest = seed / 'MANIFEST.sha256'
    if not manifest.is_file():
        raise RuntimeError(f'Audit seed has no MANIFEST.sha256: {seed.name}')
    records: dict[str, str] = {}
    for line_number, line in enumerate(manifest.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        match = re.fullmatch(r'([0-9a-fA-F]{64})\s+\*?(.+)', line)
        if not match:
            raise RuntimeError(f'Invalid audit seed manifest line {line_number}')
        digest, relative_text = match.groups()
        relative = PurePosixPath(relative_text)
        if relative.is_absolute() or '..' in relative.parts or '\\' in relative_text:
            raise RuntimeError(f'Unsafe audit seed manifest path on line {line_number}')
        records[relative.as_posix()] = digest.lower()
    return records


def verify_seed_tools(seed: Path) -> dict[str, dict[str, str | int]]:
    records = _manifest_records(seed)
    result: dict[str, dict[str, str | int]] = {}
    for relative in (
        'tools/analyze_patches.py',
        'tools/build_reference_roms.py',
        'tools/verify_with_clean_rom.py',
    ):
        if relative not in records:
            raise RuntimeError(f'Audit seed manifest does not pin {relative}')
        path = seed / relative
        result[relative] = verified_hashes(
            path, {'sha256': records[relative]}, f'audit seed {relative}'
        )
    return result


def find_seed(root: Path) -> Path:
    external = root / 'vendor/audit_seed_external'
    bundled = root / 'audit_seed'
    for candidate in (external, bundled):
        if (candidate / 'tools/verify_with_clean_rom.py').is_file():
            verify_seed_tools(candidate)
            return candidate
        nested = sorted(candidate.rglob('tools/verify_with_clean_rom.py')) if candidate.exists() else []
        if nested:
            seed = nested[0].parents[1]
            verify_seed_tools(seed)
            return seed
    raise SystemExit('Audit seed not found')


def artifact_manifest(directory: Path) -> dict[str, dict[str, str | int]]:
    result: dict[str, dict[str, str | int]] = {}
    if not directory.is_dir():
        return result
    for path in sorted(directory.rglob('*')):
        if not path.is_file() or path.name == CACHE_FILE:
            continue
        relative = path.relative_to(directory).as_posix()
        actual = hashes(path)
        result[relative] = {
            'size': actual['size'],
            'sha256': actual['sha256'],
        }
    return result


def cache_matches(directory: Path, cache_key: str, required_files: set[str]) -> bool:
    marker = directory / CACHE_FILE
    if not marker.is_file() or not required_files.issubset(
        {path.relative_to(directory).as_posix() for path in directory.rglob('*') if path.is_file()}
    ):
        return False
    try:
        data = json.loads(marker.read_text(encoding='utf-8'))
    except (OSError, ValueError, TypeError):
        return False
    return (
        data.get('schema_version') == 1
        and data.get('cache_key') == cache_key
        and data.get('artifacts') == artifact_manifest(directory)
    )


def write_cache(directory: Path, cache_key: str, descriptor: dict[str, Any]) -> None:
    write_json(
        directory / CACHE_FILE,
        {
            'schema_version': 1,
            'cache_key': cache_key,
            'descriptor': descriptor,
            'artifacts': artifact_manifest(directory),
        },
    )


def _output_dir_ready(path: Path, cache_valid: bool, replace_existing: bool) -> bool:
    """Return True for a reusable cache; otherwise enforce overwrite policy."""

    if cache_valid:
        return True
    if path.exists() and any(path.iterdir()) and not replace_existing:
        raise FileExistsError(
            f'Output directory {path} is not the requested hash cache; choose another '
            'directory or pass --replace-existing explicitly'
        )
    return False


def promote_directory(staging: Path, destination: Path, replace_existing: bool) -> None:
    """Atomically place staging, rolling back if an explicit replacement fails."""

    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and not any(destination.iterdir()):
        destination.rmdir()
    if not destination.exists():
        os.replace(staging, destination)
        return
    if not replace_existing:
        raise FileExistsError(f'Refusing to replace existing output: {destination}')
    backup = Path(
        tempfile.mkdtemp(prefix=f'.{destination.name}.backup-', dir=destination.parent)
    )
    backup.rmdir()
    os.replace(destination, backup)
    try:
        os.replace(staging, destination)
    except BaseException:
        os.replace(backup, destination)
        raise
    else:
        shutil.rmtree(backup)


def _validate_audit_summary(path: Path, expected: dict[str, Any]) -> None:
    try:
        summary = json.loads(path.read_text(encoding='utf-8'))
        outputs = summary['outputs']
    except (OSError, ValueError, KeyError, TypeError) as exc:
        raise RuntimeError('Exact audit did not produce a valid output summary') from exc
    for name in ('vega', 'factory'):
        actual = {
            'size': outputs[f'{name}_size'],
            'crc32': outputs[f'{name}_crc32'],
            'sha256': outputs[f'{name}_sha256'],
        }
        mismatches = compare_hashes(actual, output_expectations(expected, name))
        if mismatches:
            raise RuntimeError(
                f'{name} audit output mismatch ({"; ".join(mismatches)})'
            )


def _reference_outputs_valid(reference_dir: Path, expected: dict[str, Any]) -> bool:
    for name, filename in REFERENCE_NAMES.items():
        path = reference_dir / filename
        if not path.is_file():
            return False
        try:
            verified_hashes(path, output_expectations(expected, name), f'{name} reference')
        except (OSError, ValueError):
            return False
    return True


def _copy_known_references(root: Path, reference_dir: Path, expected: dict[str, Any]) -> bool:
    """Materialize known-good existing outputs without reapplying either patch."""

    candidates = {
        'vega': [
            reference_dir / LEGACY_REFERENCE_NAMES['vega'],
            root / 'inputs/reference/vega_reference_provided.gba',
        ],
        'factory': [
            reference_dir / LEGACY_REFERENCE_NAMES['factory'],
            root / 'inputs/reference/factory_reference_provided.gba',
        ],
    }
    selected: dict[str, Path] = {}
    for name, paths in candidates.items():
        target = reference_dir / REFERENCE_NAMES[name]
        if target.exists():
            try:
                verified_hashes(target, output_expectations(expected, name), f'{name} reference')
                selected[name] = target
                continue
            except ValueError as exc:
                raise FileExistsError(f'Refusing to overwrite invalid reference: {target}') from exc
        for candidate in paths:
            if not candidate.is_file():
                continue
            try:
                verified_hashes(candidate, output_expectations(expected, name), f'{name} reference')
            except ValueError:
                continue
            selected[name] = candidate
            break
    if set(selected) != set(REFERENCE_NAMES):
        return False

    reference_dir.mkdir(parents=True, exist_ok=True)
    for name, source in selected.items():
        target = reference_dir / REFERENCE_NAMES[name]
        if source == target:
            continue
        with source.open('rb') as input_handle, target.open('xb') as output_handle:
            shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
    return True


def _normalize_generated_references(staging: Path, expected: dict[str, Any]) -> None:
    for name, legacy_name in LEGACY_REFERENCE_NAMES.items():
        legacy = staging / legacy_name
        target = staging / REFERENCE_NAMES[name]
        if legacy.is_file() and legacy != target:
            os.replace(legacy, target)
        verified_hashes(target, output_expectations(expected, name), f'{name} reference')


def _new_staging(destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    return Path(
        tempfile.mkdtemp(prefix=f'.{destination.name}.staging-', dir=destination.parent)
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Run an exact audit and/or create hash-pinned local reference ROMs.'
    )
    parser.add_argument('--config', default='config/project.toml')
    parser.add_argument(
        '--target', choices=('audit', 'references', 't00'), default='audit',
        help='audit (default), references only, or the complete T00 audit+references target',
    )
    parser.add_argument(
        '--write-reference-roms', action='store_true',
        help='compatibility flag: run audit and also create the two reference ROMs',
    )
    parser.add_argument('--t00', action='store_true', help='alias for --target t00')
    parser.add_argument('--out-dir', default='reports/generated/exact_audit')
    parser.add_argument('--reference-dir', default='build/reference')
    parser.add_argument(
        '--replace-existing', action='store_true',
        help='explicitly replace a nonmatching output directory after staging succeeds',
    )
    args = parser.parse_args()

    root = repo_root()
    cfg = load_toml(project_path(root, args.config))
    expected = cfg['expected']
    seed = find_seed(root)
    resolved = resolved_input_paths(root, cfg)
    input_hashes = verify_required_inputs(resolved, expected)
    for name in ('vega', 'factory'):
        output_expectations(expected, name)

    clean = resolved['clean_rom']
    ips = resolved['vega_ips']
    ups = resolved['factory_ups']
    tool_hashes = verify_seed_tools(seed)
    descriptor = {
        'inputs': input_hashes,
        'expected_outputs': {
            name: output_expectations(expected, name) for name in ('vega', 'factory')
        },
        'tools': tool_hashes,
        'runner': hashes(Path(__file__)),
        'seed': logical_path(root, seed),
    }
    cache_key = stable_digest(descriptor)

    target = 't00' if args.t00 else args.target
    write_audit = target in ('audit', 't00') or args.write_reference_roms
    write_references = target in ('references', 't00') or args.write_reference_roms
    out = project_path(root, args.out_dir)
    reference_dir = project_path(root, args.reference_dir)

    audit_cached = write_audit and cache_matches(out, cache_key, AUDIT_ARTIFACTS)
    if write_audit:
        _output_dir_ready(out, audit_cached, args.replace_existing)

    references_cached = False
    if write_references:
        if _reference_outputs_valid(reference_dir, expected):
            write_cache(reference_dir, cache_key, descriptor)
            references_cached = True
        elif _copy_known_references(root, reference_dir, expected):
            write_cache(reference_dir, cache_key, descriptor)
            references_cached = True
        elif reference_dir.exists() and any(reference_dir.iterdir()) and not args.replace_existing:
            raise FileExistsError(
                f'Reference directory {reference_dir} contains nonmatching outputs; '
                'choose another directory or pass --replace-existing explicitly'
            )

    need_audit = write_audit and not audit_cached
    need_references = write_references and not references_cached
    audit_stage: Path | None = None
    reference_stage: Path | None = None
    try:
        if need_audit:
            audit_stage = _new_staging(out)
            run_compact_exact_audit(
                clean,
                ips,
                ups,
                audit_stage,
                write_reference_roms=need_references,
            )
            _validate_audit_summary(audit_stage / 'exact_conflicts.json', expected)

            if need_references:
                generated = audit_stage / 'reference_roms'
                reference_stage = _new_staging(reference_dir)
                for legacy_name in LEGACY_REFERENCE_NAMES.values():
                    os.replace(generated / legacy_name, reference_stage / legacy_name)
                generated.rmdir()
                _normalize_generated_references(reference_stage, expected)

            write_cache(audit_stage, cache_key, descriptor)

        elif need_references:
            reference_stage = _new_staging(reference_dir)
            build_compact_references(clean, ips, ups, reference_stage)
            _normalize_generated_references(reference_stage, expected)

        if reference_stage is not None:
            write_cache(reference_stage, cache_key, descriptor)
            promote_directory(reference_stage, reference_dir, args.replace_existing)
            reference_stage = None
        if audit_stage is not None:
            promote_directory(audit_stage, out, args.replace_existing)
            audit_stage = None
    finally:
        for staging in (audit_stage, reference_stage):
            if staging is not None and staging.exists():
                shutil.rmtree(staging)

    if write_references:
        status = 'reused' if references_cached else 'written'
        print(f'Reference ROMs {status} under {logical_path(root, reference_dir)}')
    if write_audit:
        status = 'reused' if audit_cached else 'written'
        print(f'Exact audit {status} under {logical_path(root, out)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
