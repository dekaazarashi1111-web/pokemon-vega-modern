#!/usr/bin/env python3
"""Preserve purchased-gear originals and bind screens, without claiming gameplay.

This helper is shared by the existing pr16_purchased_gear runner. It does NOT
create another controller, alter the ROM, choose a route, change mechanics,
reconfigure a battle policy, or approve a phase/release. Call bind_screens only
after the existing validator has validated the actual native process outputs.
"""
from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

SELF = 'scripts/pr16_purchased_gear_evidence.py'
TEST = 'tests/test_pr16_purchased_gear_evidence.py'
CASES = frozenset(('eelektross-active', 'eelektross-no-toggle',
                   'eelektross-cancel-toggle', 'eelektross-cold-policy-reset'))
SCREEN_NAMES = ('fixture', 'opened', 'purchased', 'bag-stone', 'give-menu',
                'give-party', 'equipped', 'equip-menus-closed', 'physical-map-boundary',
                'natural-equipped-battle', 'native-turn', 'reverted-field', 'battle-reloaded')
PPM_HEADER = b'P6\n240 160\n255\n'
PPM_SIZE = len(PPM_HEADER) + 240 * 160 * 3


def need(condition: bool, reason: str) -> None:
    if not condition:
        raise ValueError(reason)


def prepare_output(root: Path, path: Path) -> Path:
    """Reserve a new dedicated .local directory; never erase/reuse an old run."""
    root, path = Path(root), Path(path)
    need(root.is_absolute() and path.is_absolute(), 'gear evidence paths must be absolute')
    need('..' not in root.parts and '..' not in path.parts, 'gear evidence path traversal forbidden')
    local = root / '.local'
    need(path != local and path.is_relative_to(local), 'gear output must be a dedicated .local directory')
    need(root.is_dir(), 'gear repository root is missing')
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'gear output symlink ancestor forbidden')
    need(not path.exists(), 'gear output already exists; retain that original and choose a new directory')
    # exist_ok=False ensures a concurrent creator is not silently reused.
    path.mkdir(parents=True, exist_ok=False)
    return path


def required_screens(validated: dict) -> tuple[str, ...]:
    """Distinguish old 3-core evidence from revised same-session/cold controls."""
    need(type(validated) is dict and validated.get('status') == 'PASS', 'native result was not validated PASS')
    need(validated.get('case') in CASES, 'unknown gear evidence case')
    version = validated.get('schema_version')
    need(type(version) is int and version in (1, 2), 'unsupported gear result schema')
    witness = validated.get('witness')
    need(type(witness) is dict and type(witness.get('reloaded')) is int and witness['reloaded'] >= 0,
         'invalid intermediate cold-core witness')
    cores = validated.get('fresh_cores')
    need(type(cores) is int, 'gear fresh_cores must be integer')
    if version == 1:
        need(validated['case'] != 'eelektross-cold-policy-reset' and cores == 3 and witness['reloaded'] > 0,
             'old evidence is not a 3-core run; do not relabel it')
        cold = True
    else:
        cold = validated.get('cold_reload_before_encounter')
        need(type(cold) is bool and cold == (validated['case'] == 'eelektross-cold-policy-reset'),
             'cold-policy control identity differs')
        need(cores == 2 + int(cold) and (witness['reloaded'] > 0) == cold,
             'screen expectation differs from actual cold-core witness')
    return SCREEN_NAMES + (('equipped-reloaded',) if cold else ())


def read_ppm(path: Path) -> bytes:
    """Bounded, regular, non-symlink read. Screenshot bytes are not a quality vote."""
    need(not any(p.is_symlink() for p in (path, *path.parents)), 'screenshot symlink forbidden')
    # O_NOFOLLOW rejects replacement with a symlink between the checks/open.
    flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_NONBLOCK', 0)
    fd = os.open(path, flags)
    with os.fdopen(fd, 'rb') as stream:
        meta = os.fstat(stream.fileno())
        need(stat.S_ISREG(meta.st_mode) and meta.st_size == PPM_SIZE, 'screenshot is not a fixed-size regular PPM')
        raw = stream.read(PPM_SIZE + 1)
    need(len(raw) == PPM_SIZE and raw.startswith(PPM_HEADER), 'screenshot is truncated or dimensions/header differ')
    return raw


def bind_screens(output: Path, name: str, validated: dict) -> dict:
    need(name in CASES and validated.get('case') == name, 'screen/result case mismatch')
    required = required_screens(validated)
    files = {}
    for suffix in required:
        path = output / (name + '-' + suffix + '.ppm')
        raw = read_ppm(path)
        files[path.name] = dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest(), width=240, height=160)
    return dict(schema_version=1, status='SCREEN_BYTES_BOUND_NOT_VISUALLY_ACCEPTED',
                case=name, native_result_schema=validated['schema_version'],
                required_screens=len(required), files=files, visual_review_completed=False,
                presentation_accepted=False, full_p05_acceptance=False, release_ready=False)
