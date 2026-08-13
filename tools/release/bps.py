"""Minimal deterministic BPS encoder/decoder used by the T18 release.

The encoder deliberately uses only SourceRead, TargetRead, and TargetCopy.
TargetCopy makes the 16 MiB ``0xFF`` ROM expansion compact without relying on
an external patch utility.  The decoder accepts all four BPS action types so
the round-trip gate validates the serialized patch rather than an in-memory
shortcut.
"""

from __future__ import annotations

import zlib
from dataclasses import dataclass


MAGIC = b"BPS1"
SOURCE_READ = 0
TARGET_READ = 1
SOURCE_COPY = 2
TARGET_COPY = 3


class BpsError(ValueError):
    """Malformed patch or source/target identity mismatch."""


def _crc32(raw: bytes | bytearray) -> int:
    return zlib.crc32(raw) & 0xFFFFFFFF


def _encode_number(value: int) -> bytes:
    """Encode the BPS variable-length integer representation."""

    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise BpsError("BPS number must be a non-negative integer")
    result = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        if value == 0:
            result.append(byte | 0x80)
            return bytes(result)
        result.append(byte)
        value -= 1


def _encode_signed(value: int) -> bytes:
    encoded = ((-value) << 1 | 1) if value < 0 else value << 1
    return _encode_number(encoded)


@dataclass
class _Reader:
    raw: bytes
    cursor: int
    end: int

    def number(self, label: str) -> int:
        value = 0
        shift = 1
        iterations = 0
        while True:
            if self.cursor >= self.end:
                raise BpsError(f"truncated BPS {label}")
            byte = self.raw[self.cursor]
            self.cursor += 1
            value += (byte & 0x7F) * shift
            iterations += 1
            if byte & 0x80:
                return value
            shift <<= 7
            value += shift
            if iterations > 9:
                raise BpsError(f"BPS {label} is too large")

    def signed(self, label: str) -> int:
        value = self.number(label)
        magnitude = value >> 1
        return -magnitude if value & 1 else magnitude


def _equal_run(source: bytes, target: bytes, offset: int) -> int:
    end = min(len(source), len(target))
    cursor = offset
    while cursor < end and source[cursor] == target[cursor]:
        cursor += 1
    return cursor - offset


def _repeat_run(target: bytes, offset: int) -> int:
    byte = target[offset]
    cursor = offset + 1
    while cursor < len(target) and target[cursor] == byte:
        cursor += 1
    return cursor - offset


def _has_equal_run(source: bytes, target: bytes, offset: int, minimum: int) -> bool:
    end = offset + minimum
    return end <= len(source) and end <= len(target) and source[offset:end] == target[offset:end]


def _has_repeat_run(target: bytes, offset: int, minimum: int) -> bool:
    end = offset + minimum
    if end > len(target):
        return False
    return target[offset:end] == target[offset:offset + 1] * minimum


def _action(action_type: int, length: int) -> bytes:
    if action_type not in (SOURCE_READ, TARGET_READ, SOURCE_COPY, TARGET_COPY):
        raise BpsError("unknown BPS action type")
    if length <= 0:
        raise BpsError("BPS action length must be positive")
    return _encode_number(((length - 1) << 2) | action_type)


def create_bps(source: bytes, target: bytes, *, metadata: bytes = b"") -> bytes:
    """Create a deterministic BPS patch and self-check its exact round trip."""

    if not isinstance(source, bytes) or not isinstance(target, bytes):
        raise BpsError("BPS source and target must be bytes")
    if not isinstance(metadata, bytes):
        raise BpsError("BPS metadata must be bytes")

    patch = bytearray(MAGIC)
    patch.extend(_encode_number(len(source)))
    patch.extend(_encode_number(len(target)))
    patch.extend(_encode_number(len(metadata)))
    patch.extend(metadata)

    offset = 0
    target_relative = 0
    while offset < len(target):
        equal = _equal_run(source, target, offset) if (
            offset < len(source) and source[offset] == target[offset]
        ) else 0
        if equal >= 4:
            patch.extend(_action(SOURCE_READ, equal))
            offset += equal
            continue

        repeat = _repeat_run(target, offset)
        if repeat >= 16:
            patch.extend(_action(TARGET_READ, 1))
            patch.append(target[offset])
            offset += 1
            copy_source = offset - 1
            patch.extend(_action(TARGET_COPY, repeat - 1))
            patch.extend(_encode_signed(copy_source - target_relative))
            target_relative = copy_source + repeat - 1
            offset += repeat - 1
            continue

        literal_start = offset
        offset += 1
        while offset < len(target):
            if _has_equal_run(source, target, offset, 4):
                break
            if _has_repeat_run(target, offset, 16):
                break
            offset += 1
        literal = target[literal_start:offset]
        patch.extend(_action(TARGET_READ, len(literal)))
        patch.extend(literal)

    patch.extend(_crc32(source).to_bytes(4, "little"))
    patch.extend(_crc32(target).to_bytes(4, "little"))
    patch.extend(_crc32(patch).to_bytes(4, "little"))
    encoded = bytes(patch)
    if apply_bps(source, encoded) != target:
        raise BpsError("internal BPS round-trip mismatch")
    return encoded


def apply_bps(source: bytes, patch: bytes) -> bytes:
    """Apply a BPS patch, validating source, patch, and target CRCs."""

    if not isinstance(source, bytes) or not isinstance(patch, bytes):
        raise BpsError("BPS source and patch must be bytes")
    if len(patch) < len(MAGIC) + 12 or not patch.startswith(MAGIC):
        raise BpsError("BPS header is missing or patch is truncated")
    if _crc32(patch[:-4]) != int.from_bytes(patch[-4:], "little"):
        raise BpsError("BPS patch CRC mismatch")

    commands_end = len(patch) - 12
    reader = _Reader(patch, len(MAGIC), commands_end)
    source_size = reader.number("source size")
    target_size = reader.number("target size")
    metadata_size = reader.number("metadata size")
    if source_size != len(source):
        raise BpsError(f"BPS source size mismatch: expected {source_size}, got {len(source)}")
    if reader.cursor + metadata_size > commands_end:
        raise BpsError("truncated BPS metadata")
    reader.cursor += metadata_size

    output = bytearray()
    source_relative = 0
    target_relative = 0
    while len(output) < target_size:
        action = reader.number("action")
        action_type = action & 3
        length = (action >> 2) + 1
        if len(output) + length > target_size:
            raise BpsError("BPS action exceeds target size")

        if action_type == SOURCE_READ:
            start = len(output)
            end = start + length
            if end > len(source):
                raise BpsError("BPS SourceRead exceeds source")
            output.extend(source[start:end])
        elif action_type == TARGET_READ:
            end = reader.cursor + length
            if end > commands_end:
                raise BpsError("BPS TargetRead is truncated")
            output.extend(patch[reader.cursor:end])
            reader.cursor = end
        elif action_type == SOURCE_COPY:
            source_relative += reader.signed("SourceCopy offset")
            end = source_relative + length
            if source_relative < 0 or end > len(source):
                raise BpsError("BPS SourceCopy exceeds source")
            output.extend(source[source_relative:end])
            source_relative = end
        else:
            target_relative += reader.signed("TargetCopy offset")
            if target_relative < 0 or target_relative >= len(output):
                raise BpsError("BPS TargetCopy starts outside decoded target")
            for _ in range(length):
                if target_relative >= len(output):
                    raise BpsError("BPS TargetCopy read is not overlap-safe")
                output.append(output[target_relative])
                target_relative += 1

    if reader.cursor != commands_end:
        raise BpsError("BPS command stream has trailing data")
    expected_source_crc = int.from_bytes(patch[-12:-8], "little")
    expected_target_crc = int.from_bytes(patch[-8:-4], "little")
    if _crc32(source) != expected_source_crc:
        raise BpsError("BPS source CRC mismatch")
    if _crc32(output) != expected_target_crc:
        raise BpsError("BPS target CRC mismatch")
    return bytes(output)
