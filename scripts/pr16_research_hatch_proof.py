#!/usr/bin/env python3
"""Pure proof/archive boundaries; no emulator or repository mutation."""
from __future__ import annotations

import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
SELF = 'scripts/pr16_research_hatch_proof.py'
TEST = 'tests/test_pr16_research_hatch_proof.py'
WF = '.github/workflows/pr16-research-hatch-proof-20260925.yml'
PPM_HEADER = b'P6\n240 160\n255\n'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def archive(raw, metadata, expected, run_id, source):
    """Bind the whole ZIP and reject duplicates, extras, paths and zip bombs."""
    need(type(run_id) is int and run_id > 0, 'run ID')
    need(type(source) is str and re.fullmatch('[0-9a-f]{40}', source), 'source SHA')
    need(type(metadata.get('id')) is int and metadata['id'] > 0, 'artifact ID')
    need(metadata.get('expired') is False, 'unexpired artifact')
    digest = metadata.get('digest')
    need(type(digest) is str and re.fullmatch('sha256:[0-9a-f]{64}', digest), 'artifact digest')
    need(type(metadata.get('size_in_bytes')) is int, 'artifact size type')
    need(identity(raw) == {'size': metadata['size_in_bytes'], 'sha256': digest[7:]}, 'whole artifact identity')
    owner = metadata.get('workflow_run', {})
    need(type(owner.get('id')) is int and owner['id'] == run_id and owner.get('head_sha') == source, 'artifact origin')
    need(type(expected) is dict and 0 < len(expected) <= 128, 'expected archive entries')
    for name in expected:
        need(type(name) is str and re.fullmatch('[A-Za-z0-9][A-Za-z0-9_.-]{0,127}', name) and '..' not in name, 'flat safe member name')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        infos = z.infolist()
        need(len(infos) == len(expected) and {x.filename for x in infos} == set(expected), 'exact unique archive entries')
        need(sum(x.file_size for x in infos) <= 16000000, 'archive expansion bound')
        result = {}
        for item in infos:
            need(not item.is_dir() and not item.flag_bits & 1 and item.file_size <= 4000000, 'regular bounded archive entry')
            mode = (item.external_attr >> 16) & 0o170000
            need(mode in (0, 0o100000), 'no archive symlink')
            value = z.read(item)
            if expected[item.filename] is not None:
                need(identity(value) == expected[item.filename], 'member identity ' + item.filename)
            result[item.filename] = value
    return result


def frame(raw):
    """Only rendering integrity, not proof that a depicted Pokemon is correct."""
    need(raw.startswith(PPM_HEADER) and len(raw) == len(PPM_HEADER) + 240 * 160 * 3, 'exact PPM frame')
    pixels = raw[len(PPM_HEADER):]
    colors = len({pixels[i:i+3] for i in range(0, len(pixels), 3)})
    return {'identity': identity(raw), 'distinct_colors': colors, 'nonblank': colors > 1}


def reflected(raw, source, commit):
    need(re.fullmatch(b'[0-9a-f]{40}\n', raw) is not None, 'reflected SHA text')
    sha = raw.decode().strip()
    need(commit.get('sha') == sha and [p['sha'] for p in commit.get('parents', [])] == [source], 'exact reflected commit parent')
    return sha

