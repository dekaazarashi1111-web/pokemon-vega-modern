from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import tempfile
import zlib
from pathlib import Path
from typing import Any, Mapping


INPUT_EXPECTATION_KEYS: dict[str, dict[str, str]] = {
    'clean_rom': {
        'size': 'clean_size',
        'crc32': 'clean_crc32',
        'md5': 'clean_md5',
        'sha1': 'clean_sha1',
        'sha256': 'clean_sha256',
    },
    'vega_ips': {'sha256': 'vega_ips_sha256'},
    'factory_ups': {'sha256': 'factory_ups_sha256'},
}

OUTPUT_EXPECTATION_KEYS: dict[str, dict[str, str]] = {
    'vega': {
        'size': 'vega_output_size',
        'crc32': 'vega_output_crc32',
        'sha256': 'vega_output_sha256',
    },
    'factory': {
        'size': 'factory_output_size',
        'crc32': 'factory_output_crc32',
        'sha256': 'factory_output_sha256',
    },
}


class HashMismatchError(ValueError):
    """Raised when a pinned input or output does not match its contract."""


def load_toml(path: Path) -> dict[str, Any]:
    import tomllib
    with path.open('rb') as f:
        return tomllib.load(f)


def hashes(path: Path) -> dict[str, str | int]:
    crc = 0
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    sha256 = hashlib.sha256()
    size = 0
    with path.open('rb') as f:
        while chunk := f.read(1024 * 1024):
            size += len(chunk)
            crc = zlib.crc32(chunk, crc)
            md5.update(chunk)
            sha1.update(chunk)
            sha256.update(chunk)
    return {
        'size': size,
        'crc32': f'{crc & 0xffffffff:08x}',
        'md5': md5.hexdigest(),
        'sha1': sha1.hexdigest(),
        'sha256': sha256.hexdigest(),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, check=check, text=True, capture_output=True)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    fd, temporary_name = tempfile.mkstemp(prefix=f'.{path.name}.', suffix='.tmp', dir=path.parent)
    temporary = Path(temporary_name)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8', newline='\n') as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_path(root: Path, value: str | os.PathLike[str]) -> Path:
    """Return a lexically project-contained path without resolving symlinks.

    Private inputs are intentionally allowed to be symlinks into ``userfile``.
    Resolving those links here would both leak a user path and make state files
    machine-specific, so containment is checked on the link path itself.
    """

    relative = Path(value)
    if relative.is_absolute():
        raise ValueError(f'Project path must be relative: {relative.name or "<root>"}')
    root_absolute = Path(os.path.abspath(root))
    candidate = Path(os.path.abspath(root_absolute / relative))
    try:
        candidate.relative_to(root_absolute)
    except ValueError as exc:
        raise ValueError(f'Project path escapes workspace: {relative}') from exc
    return candidate


def logical_path(root: Path, path: Path) -> str:
    """Convert an in-project path to a portable POSIX path without dereferencing it."""

    root_absolute = Path(os.path.abspath(root))
    candidate = path if path.is_absolute() else root_absolute / path
    candidate = Path(os.path.abspath(candidate))
    try:
        return candidate.relative_to(root_absolute).as_posix()
    except ValueError as exc:
        raise ValueError(f'Path is outside the workspace: {path.name}') from exc


def expectation_spec(
    expected: Mapping[str, Any],
    definitions: Mapping[str, Mapping[str, str]],
    name: str,
) -> dict[str, str | int]:
    fields = definitions[name]
    missing = [config_key for config_key in fields.values() if config_key not in expected]
    if missing:
        raise ValueError(f'Missing required expected values for {name}: {", ".join(missing)}')
    return {hash_name: expected[config_key] for hash_name, config_key in fields.items()}


def input_expectations(expected: Mapping[str, Any], name: str) -> dict[str, str | int]:
    return expectation_spec(expected, INPUT_EXPECTATION_KEYS, name)


def output_expectations(expected: Mapping[str, Any], name: str) -> dict[str, str | int]:
    return expectation_spec(expected, OUTPUT_EXPECTATION_KEYS, name)


def compare_hashes(
    actual: Mapping[str, str | int], expected: Mapping[str, str | int]
) -> list[str]:
    mismatches: list[str] = []
    for key, expected_value in expected.items():
        actual_value = actual.get(key)
        if key == 'size':
            equal = actual_value == int(expected_value)
        else:
            equal = str(actual_value).lower() == str(expected_value).lower()
        if not equal:
            mismatches.append(f'{key}: expected {expected_value}, got {actual_value}')
    return mismatches


def verified_hashes(
    path: Path, expected: Mapping[str, str | int], label: str
) -> dict[str, str | int]:
    actual = hashes(path)
    mismatches = compare_hashes(actual, expected)
    if mismatches:
        raise HashMismatchError(f'{label} hash mismatch ({"; ".join(mismatches)})')
    return actual


def verify_required_inputs(
    paths: Mapping[str, Path], expected: Mapping[str, Any]
) -> dict[str, dict[str, str | int]]:
    results: dict[str, dict[str, str | int]] = {}
    for name in INPUT_EXPECTATION_KEYS:
        path = paths.get(name)
        if path is None or not path.is_file():
            raise FileNotFoundError(f'Missing required input: {name}')
        results[name] = verified_hashes(path, input_expectations(expected, name), name)
    return results


def stable_digest(data: Any) -> str:
    encoded = json.dumps(
        data, ensure_ascii=False, sort_keys=True, separators=(',', ':')
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def tree_sha256(root: Path, *, exclude_names: frozenset[str] = frozenset({'.git'})) -> str:
    """Hash a source tree deterministically without following symlinks."""

    digest = hashlib.sha256()
    for path in sorted(root.rglob('*'), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root)
        if any(part in exclude_names for part in relative.parts):
            continue
        relative_bytes = relative.as_posix().encode('utf-8')
        if path.is_symlink():
            kind = b'L'
            payload = os.readlink(path).encode('utf-8')
        elif path.is_dir():
            kind = b'D'
            payload = b''
        elif path.is_file():
            kind = b'F'
            payload = bytes.fromhex(sha256_file(path))
        else:
            kind = b'O'
            payload = b''
        digest.update(kind)
        digest.update(len(relative_bytes).to_bytes(8, 'big'))
        digest.update(relative_bytes)
        digest.update(len(payload).to_bytes(8, 'big'))
        digest.update(payload)
    return digest.hexdigest()


_USER_PATH_PATTERNS = (
    re.compile(r'(?i)(?<![A-Za-z0-9:])[A-Z]:[\\/]+Users[\\/]+[^\\/\s\"\'`<>]+(?:[\\/][^\s\"\'`<>]*)?'),
    re.compile(r'(?i)(?<![A-Za-z0-9:])/mnt/[a-z]/Users/[^/\s\"\'`<>]+(?:/[^\s\"\'`<>]*)?'),
    re.compile(r'(?<![A-Za-z0-9:])/home/[^/\s\"\'`<>]+(?:/[^\s\"\'`<>]*)?'),
    re.compile(r'(?<![A-Za-z0-9:])/Users/[^/\s\"\'`<>]+(?:/[^\s\"\'`<>]*)?'),
)


def redact_user_paths(value: str) -> str:
    for pattern in _USER_PATH_PATTERNS:
        value = pattern.sub('<user-path>', value)
    return value


def user_absolute_path_lines(value: str) -> list[int]:
    """Return 1-based line numbers containing machine-specific user paths."""

    result: set[int] = set()
    for pattern in _USER_PATH_PATTERNS:
        for match in pattern.finditer(value):
            result.add(value.count('\n', 0, match.start()) + 1)
    return sorted(result)


def resolved_input_paths(root: Path, cfg: dict[str, Any]) -> dict[str, Path]:
    defaults = {key: project_path(root, value) for key, value in cfg['inputs'].items()}
    resolved_file = root / 'state/resolved_paths.json'
    if resolved_file.exists():
        try:
            data = json.loads(resolved_file.read_text(encoding='utf-8'))
        except (OSError, ValueError, TypeError):
            return defaults
        if data.get('config_fingerprint') != stable_digest(cfg['inputs']):
            return defaults
        for key, value in data.get('inputs', {}).items():
            if key not in defaults or not isinstance(value, str):
                continue
            try:
                defaults[key] = project_path(root, value)
            except ValueError:
                # Legacy absolute paths are deliberately ignored. The portable
                # config path is the only safe fallback.
                continue
    return defaults
