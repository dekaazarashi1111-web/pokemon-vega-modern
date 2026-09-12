#!/usr/bin/env python3
"""Recover the unique applicable patch from the rejected PR16 workflow blob."""

from __future__ import annotations

import argparse
import base64
import bz2
import gzip
import hashlib
import itertools
import lzma
from pathlib import Path
import subprocess
import tempfile
import zlib

BROKEN_BLOB = "520f756df53f4f9c369e15db80aacb2afebcedcb"
REPORTED_PATCH_SHA256 = "25ba5d62212cfdc52a19912f7f68ff842e98975ed814ba8b5d5e61fb7f3e0cf"
EXPECTED_PATHS = {
    "tools/mgba_pr16_generic_form_carry.c",
    "scripts/pr16_generic_form_carry.py",
    "tests/test_pr16_generic_form_carry.py",
}
EXPECTED_PREIMAGE_BLOBS = {
    "tools/mgba_pr16_generic_form_carry.c": "c22866860b67b353b0d09bbcb8da84b47b9b363f",
    "scripts/pr16_generic_form_carry.py": "74ef73488f48b705c69d528672f2aaa13323d910",
    "tests/test_pr16_generic_form_carry.py": "84f7fbaac6ede4bc9500313d615e33ad83ce20c1",
}
BASE64_ALPHABET = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


def git(*args: str, cwd: Path | None = None) -> bytes:
    command = ["git"]
    if cwd is not None:
        command += ["-C", str(cwd)]
    command += list(args)
    return subprocess.check_output(command)


def extract_payload(raw: bytes) -> bytes:
    marker = b"PATCH_B64: >-"
    marker_at = raw.find(marker)
    if marker_at < 0:
        raise SystemExit("PATCH_B64 folded-block marker is absent")
    line_start = raw.rfind(b"\n", 0, marker_at) + 1
    marker_line_end = raw.find(b"\n", marker_at)
    if marker_line_end < 0:
        raise SystemExit("PATCH_B64 marker has no following line")
    marker_line = raw[line_start:marker_line_end]
    marker_indent = len(marker_line) - len(marker_line.lstrip(b" "))

    lines: list[bytes] = []
    for line in raw[marker_line_end + 1 :].splitlines():
        if not line.strip():
            if lines:
                break
            continue
        indent = len(line) - len(line.lstrip(b" "))
        if indent <= marker_indent:
            break
        lines.append(line.strip())
    payload = b"".join(lines)
    if not payload:
        raise SystemExit("embedded PATCH_B64 payload is empty")
    return payload


def contiguous_groups(offsets: list[int]) -> list[tuple[int, int]]:
    groups: list[tuple[int, int]] = []
    for _, members in itertools.groupby(
        enumerate(offsets), key=lambda pair: pair[1] - pair[0]
    ):
        positions = [pair[1] for pair in members]
        groups.append((positions[0], positions[-1] + 1))
    return groups


def replacement_options(groups: list[tuple[int, int]]):
    single = [bytes([value]) for value in BASE64_ALPHABET]
    if len(groups) == 1:
        for width in (0, 1, 2):
            for parts in itertools.product(single, repeat=width):
                yield (b"".join(parts),)
        return
    choices = [b""] + single
    yield from itertools.product(choices, repeat=len(groups))


def replace_groups(
    source: bytes,
    groups: list[tuple[int, int]],
    replacements: tuple[bytes, ...],
) -> bytes:
    output = bytearray()
    previous = 0
    for (start, end), replacement in zip(groups, replacements):
        output.extend(source[previous:start])
        output.extend(replacement)
        previous = end
    output.extend(source[previous:])
    return bytes(output)


def decoded_variants(encoded: bytes):
    if len(encoded) % 4:
        return
    try:
        packed = base64.b64decode(encoded, validate=True)
    except Exception:
        return
    yield "base64", packed
    for name, decoder in (
        ("zlib", zlib.decompress),
        ("gzip", gzip.decompress),
        ("raw-deflate", lambda data: zlib.decompress(data, -15)),
        ("bz2", bz2.decompress),
        ("lzma", lzma.decompress),
    ):
        try:
            yield name, decoder(packed)
        except Exception:
            pass


def patch_paths(patch: bytes) -> set[str]:
    paths: set[str] = set()
    for line in patch.splitlines():
        if line.startswith(b"+++ b/"):
            try:
                paths.add(line[6:].decode("utf-8"))
            except UnicodeDecodeError:
                return set()
    return paths


def applies_cleanly(patch: bytes, worktree: Path) -> bool:
    with tempfile.NamedTemporaryFile(prefix="pr16-form-", suffix=".patch") as handle:
        handle.write(patch)
        handle.flush()
        result = subprocess.run(
            [
                "git",
                "-C",
                str(worktree),
                "apply",
                "--check",
                "--whitespace=error-all",
                handle.name,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    return result.returncode == 0


def shell_value(value: str) -> str:
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789,._:-")
    if not value or any(character not in safe for character in value):
        raise SystemExit(f"unsafe recovery environment value: {value!r}")
    return value


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--worktree", type=Path, required=True)
    parser.add_argument("--patch-output", type=Path, required=True)
    parser.add_argument("--env-output", type=Path, required=True)
    args = parser.parse_args()

    for path, expected in EXPECTED_PREIMAGE_BLOBS.items():
        actual = git("hash-object", path, cwd=args.worktree).decode().strip()
        print(f"preimage {actual}  {path}")
        if actual != expected:
            raise SystemExit(f"preimage blob differs for {path}: {actual} != {expected}")

    raw = git("cat-file", "blob", BROKEN_BLOB)
    actual_blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
    if actual_blob != BROKEN_BLOB:
        raise SystemExit(f"broken workflow blob differs: {actual_blob} != {BROKEN_BLOB}")

    payload = extract_payload(raw)
    allowed = set(BASE64_ALPHABET + b"=")
    invalid = [index for index, value in enumerate(payload) if value not in allowed]
    if not 1 <= len(invalid) <= 4:
        raise SystemExit(
            f"expected one to four invalid base64 bytes, found {len(invalid)}: {invalid[:20]}"
        )
    groups = contiguous_groups(invalid)

    candidates: dict[str, tuple[bytes, tuple[bytes, ...], str]] = {}
    attempts = 0
    decoded = 0
    structurally_valid = 0
    for replacements in replacement_options(groups):
        attempts += 1
        encoded = replace_groups(payload, groups, replacements)
        for codec, patch in decoded_variants(encoded) or ():
            decoded += 1
            if not patch.startswith(b"diff --git "):
                continue
            if patch_paths(patch) != EXPECTED_PATHS:
                continue
            structurally_valid += 1
            digest = hashlib.sha256(patch).hexdigest()
            if digest in candidates:
                continue
            if applies_cleanly(patch, args.worktree):
                candidates[digest] = (patch, replacements, codec)

    print(
        "payload diagnostics",
        f"bytes={len(payload)}",
        f"mod4={len(payload) % 4}",
        f"invalid_offsets={invalid}",
        f"invalid_hex={[hex(payload[index]) for index in invalid]}",
        f"groups={groups}",
        f"attempts={attempts}",
        f"decoded_variants={decoded}",
        f"structurally_valid={structurally_valid}",
        f"applicable_candidates={list(candidates)}",
    )
    if len(candidates) != 1:
        raise SystemExit(
            f"expected exactly one structurally valid applicable recovery, found {len(candidates)}"
        )

    recovered_sha, (patch, replacements, codec) = next(iter(candidates.items()))
    args.patch_output.write_bytes(patch)
    values = {
        "RECOVERED_INVALID_OFFSETS": ",".join(map(str, invalid)),
        "RECOVERED_INVALID_HEX": ",".join(f"0x{payload[index]:02x}" for index in invalid),
        "RECOVERED_REPLACEMENTS_HEX": ",".join(
            replacement.hex() or "deleted" for replacement in replacements
        ),
        "RECOVERED_CODEC": codec,
        "RECOVERED_PATCH_SHA256": recovered_sha,
        "REPORTED_PATCH_SHA256": REPORTED_PATCH_SHA256,
        "REPORTED_DIGEST_MATCH": str(recovered_sha == REPORTED_PATCH_SHA256).lower(),
    }
    args.env_output.write_text(
        "".join(f"{key}={shell_value(value)}\n" for key, value in values.items()),
        encoding="utf-8",
    )
    print(args.env_output.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main()
