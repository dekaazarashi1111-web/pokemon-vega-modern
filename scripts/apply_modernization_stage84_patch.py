#!/usr/bin/env python3
"""Apply a pinned engineering BPS to a NEW file; never read or modify a save."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'tools' / 'release'))
from bps import apply_bps

SIZE = 33554432
S80 = '6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3'
S83 = '09e9d8cf085d175299b58e93347e3beb2467c3c09016130f7d35ce033fa50096'
S84 = '55cf145e7dd1c8e2568fe9c733b597f8c4bc3d31b7d6fa233a7b4821d1b62c3b'
PATCHES = {
    'stage80-to-stage84.bps': (434, '9be63cbf93363d29b303778a57894325914dcb2c685cead6acfdc32b51eb4d3f', S80, S84),
    'stage83-to-stage84.bps': (35, '386092e4d0e2166a7c1b6b8a962c077747f95404344201dbb584faa673e6cd45', S83, S84),
    'stage84-to-stage80.bps': (434, '5252ab57273912ce8adb23b23b8a0865f9dc4cb111523edc142eb7699975f206', S84, S80),
    'stage84-to-stage83.bps': (35, '9839f6d994868dbbcea75e6f636e64984b7e18593e890140d7aab8422161ffd8', S84, S83),
}


def require(value: bool, message: str) -> None:
    if not value:
        raise ValueError(message)


def no_links(path: Path) -> Path:
    path = path.absolute()
    require('..' not in path.parts, 'parent traversal is not allowed')
    require(not any(p.is_symlink() for p in (path, *path.parents)), 'symbolic links are not allowed')
    return path


def read_regular(path: Path, size: int) -> bytes:
    path = no_links(path)
    with path.open('rb') as stream:
        before = os.fstat(stream.fileno())
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1, 'one regular file required')
        require(before.st_size == size, 'input size mismatch')
        data = stream.read(size + 1)
        after = os.fstat(stream.fileno())
    require((before.st_ino, before.st_dev, before.st_size, before.st_mtime_ns) ==
            (after.st_ino, after.st_dev, after.st_size, after.st_mtime_ns), 'input changed while reading')
    require(len(data) == size, 'input size changed')
    return data


def apply(patch: Path, source: Path, output: Path) -> dict:
    patch, source, output = (no_links(p) for p in (patch, source, output))
    require(source.suffix.lower() == output.suffix.lower() == '.gba', 'ROM .gba paths required; saves forbidden')
    require(not output.exists() and output != source and output != patch, 'output must be a new file')
    require(output.parent.is_dir(), 'create a separate output directory first')
    require(patch.name in PATCHES, 'only the four pinned engineering patches are accepted')
    count, expected_patch, expected_source, expected_target = PATCHES[patch.name]
    delta = read_regular(patch, count)
    require(hashlib.sha256(delta).hexdigest() == expected_patch, 'patch SHA-256 mismatch')
    original = read_regular(source, SIZE)
    require(hashlib.sha256(original).hexdigest() == expected_source, 'source SHA-256 mismatch; Stage62/clean ROM not supported')
    result = apply_bps(original, delta)
    require(len(result) == SIZE and hashlib.sha256(result).hexdigest() == expected_target, 'target SHA-256 mismatch')
    # Exclusive creation is intentional: even an existing zero-byte destination is protected.
    with output.open('xb') as stream:
        stream.write(result)
        stream.flush()
        os.fsync(stream.fileno())
    require(hashlib.sha256(read_regular(output, SIZE)).hexdigest() == expected_target, 'written output differs')
    require(hashlib.sha256(read_regular(source, SIZE)).hexdigest() == expected_source, 'source changed')
    return {'status': 'PATCH_APPLIED_NOT_RELEASE_ACCEPTANCE', 'size': SIZE, 'sha256': expected_target,
            'source_unchanged': True, 'save_files_accessed': False, 'release_ready': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('patch', 'source', 'output'):
        parser.add_argument('--' + name, type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(apply(args.patch, args.source, args.output), indent=2)); return 0
    except (OSError, ValueError) as exc:
        print('refused: ' + str(exc), file=sys.stderr); return 1


if __name__ == '__main__':
    raise SystemExit(main())
