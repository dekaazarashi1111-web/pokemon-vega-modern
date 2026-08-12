from __future__ import annotations

import io
import subprocess
import zipfile
from pathlib import Path, PurePosixPath

from common import repo_root, user_absolute_path_lines


BLOCKED_SUFFIXES = {
    '.gba', '.gb', '.gbc', '.nds', '.sav', '.srm', '.ips', '.ups', '.bps',
    '.xdelta', '.xdelta3',
}
BLOCKED_PARTS = {'inputs/private', 'inputs/source_archives', 'userfile'}
DOCUMENT_SUFFIXES = {'.md', '.txt', '.rst', '.adoc', '.json', '.csv'}
MAX_TRACKED_ZIP_ENTRIES = 100_000


def tracked_files(root: Path) -> list[str]:
    proc = subprocess.run(
        ['git', 'ls-files', '--cached', '-z'],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode('utf-8', errors='replace').splitlines()
        raise RuntimeError(detail[0] if detail else 'git ls-files failed')
    return [
        item.decode('utf-8', errors='surrogateescape')
        for item in proc.stdout.split(b'\0')
        if item
    ]


def index_blob(root: Path, relative_path: str) -> bytes:
    """Read the exact blob staged in the Git index, never the working tree."""

    proc = subprocess.run(
        ['git', 'cat-file', 'blob', f':{relative_path}'],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = proc.stderr.decode('utf-8', errors='replace').splitlines()
        raise RuntimeError(detail[0] if detail else f'cannot read index blob: {relative_path}')
    return proc.stdout


def _content_bytes(content: bytes | Path) -> bytes:
    return content if isinstance(content, bytes) else content.read_bytes()


def blocked_zip_members(content: bytes | Path) -> list[str]:
    """List ROM/patch payloads in a tracked ZIP without extracting it."""

    try:
        with zipfile.ZipFile(io.BytesIO(_content_bytes(content))) as archive:
            infos = archive.infolist()
            if len(infos) > MAX_TRACKED_ZIP_ENTRIES:
                return [f'<too-many-entries:{len(infos)}>']
            blocked = []
            for info in infos:
                normalized = info.filename.replace('\\', '/')
                suffix = PurePosixPath(normalized).suffix.lower()
                if not info.is_dir() and suffix in BLOCKED_SUFFIXES:
                    blocked.append(normalized)
            return blocked
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return ['<invalid-or-unreadable-zip>']


def document_user_path_lines(content: bytes | Path) -> list[int]:
    try:
        text = _content_bytes(content).decode('utf-8', errors='replace')
    except OSError:
        return [-1]
    return user_absolute_path_lines(text)


def main() -> int:
    root = repo_root()
    try:
        tracked = tracked_files(root)
    except RuntimeError as exc:
        print(f'ERROR: private file guard could not inspect Git index: {exc}')
        return 1

    private_files: list[str] = []
    binary_archives: list[tuple[str, list[str]]] = []
    absolute_paths: list[tuple[str, list[int]]] = []
    index_errors: list[tuple[str, str]] = []
    for rel in tracked:
        rel_posix = Path(rel).as_posix()
        relative = Path(rel_posix)
        if relative.name == '.gitkeep':
            continue
        if relative.suffix.lower() in BLOCKED_SUFFIXES or any(
            rel_posix == part or rel_posix.startswith(part + '/') for part in BLOCKED_PARTS
        ):
            private_files.append(rel_posix)
            continue
        blob: bytes | None = None
        if relative.suffix.lower() == '.zip' or relative.suffix.lower() in DOCUMENT_SUFFIXES:
            try:
                blob = index_blob(root, rel)
            except RuntimeError as exc:
                index_errors.append((rel_posix, str(exc)))
                continue
        if relative.suffix.lower() == '.zip':
            assert blob is not None
            blocked = blocked_zip_members(blob)
            if blocked:
                binary_archives.append((rel_posix, blocked))
        if relative.suffix.lower() in DOCUMENT_SUFFIXES:
            assert blob is not None
            lines = document_user_path_lines(blob)
            if lines:
                absolute_paths.append((rel_posix, lines))

    if private_files or binary_archives or absolute_paths or index_errors:
        if private_files:
            print('ERROR: private ROM/patch files are tracked by Git:')
            for rel in private_files:
                print(f'  {rel}')
        if binary_archives:
            print('ERROR: tracked ZIP archives contain private ROM/patch payloads:')
            for rel, members in binary_archives:
                preview = ', '.join(members[:5])
                suffix = f' (+{len(members) - 5} more)' if len(members) > 5 else ''
                print(f'  {rel}: {preview}{suffix}')
        if absolute_paths:
            print('ERROR: tracked documents contain machine-specific user paths:')
            for rel, lines in absolute_paths:
                display = 'unreadable' if lines == [-1] else ','.join(map(str, lines))
                print(f'  {rel}: lines {display}')
        if index_errors:
            print('ERROR: private file guard could not read staged Git blobs:')
            for rel, detail in index_errors:
                print(f'  {rel}: {detail}')
        return 1
    print('Private file guard: OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
