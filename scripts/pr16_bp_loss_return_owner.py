#!/usr/bin/env python3
"""固定sourceのcallback参照と実際の分岐候補を区別する読取専用監査。"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from typing import Iterable

SCHEMA_VERSION = 2
TASK = 'USER-20260913-BP-LOSS-RETURN-OWNER'
SOURCE_ROOT = Path('vendor/upstream/CFRU-JP')
TRACKED_BUILD = Path('scripts/build_battle_core.py')
NEEDLES = ('CB2_WhiteOut', 'CB2_ReturnToField', 'EndOfBattleThings', 'EndBattleFlagClear',
           'BATTLE_TYPE_FRONTIER', 'BATTLE_TYPE_BATTLE_TOWER', 'VegaBattlePolicyEnd')
REQUIRED = tuple(n for n in NEEDLES if n != 'BATTLE_TYPE_BATTLE_TOWER')
TEXT_SUFFIXES = {'.c', '.h', '.py'}
CONTEXT = 24
MAX_MATCHES_PER_NEEDLE = 80
MAX_FILE_SIZE = 2_000_000


class OwnerAuditError(ValueError):
    pass


def need(condition: bool, message: str) -> None:
    if not condition:
        raise OwnerAuditError(message)


def stable(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode('utf-8')


def identity(raw: bytes) -> dict[str, object]:
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def safe_path(root: Path, logical: Path) -> Path:
    need(not logical.is_absolute() and '..' not in logical.parts, f'unsafe path: {logical}')
    root = root.resolve()
    path = root / logical
    need(not any(p.is_symlink() for p in (path, *path.parents)), f'symlink rejected: {logical}')
    need(path.resolve() == root or root in path.resolve().parents, f'path escapes root: {logical}')
    return path


def source_files(root: Path) -> list[Path]:
    base = safe_path(root, SOURCE_ROOT)
    need(base.is_dir(), f'missing fixed CFRU source: {SOURCE_ROOT}')
    rows = [p for p in base.rglob('*') if p.is_file() and not p.is_symlink() and p.suffix.lower() in TEXT_SUFFIXES]
    tracked = safe_path(root, TRACKED_BUILD)
    need(tracked.is_file(), f'missing tracked build source: {TRACKED_BUILD}')
    return sorted([*rows, tracked], key=lambda p: p.relative_to(root.resolve()).as_posix())


def read_text(path: Path) -> tuple[bytes, list[str]]:
    raw = path.read_bytes()
    need(len(raw) <= MAX_FILE_SIZE and b'\0' not in raw, 'non-text or oversized source')
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError:
        text = raw.decode('shift_jis')
    return raw, text.splitlines()


def source_identity(root: Path) -> dict[str, object]:
    base = safe_path(root, SOURCE_ROOT)
    result = {'path': SOURCE_ROOT.as_posix()}
    if (base / '.git').exists():
        for label, args in (('commit', ('rev-parse', 'HEAD')), ('tree', ('rev-parse', 'HEAD^{tree}')),
                            ('status', ('status', '--porcelain', '--untracked-files=all'))):
            run = subprocess.run(['git', '-C', str(base), *args], capture_output=True, text=True, check=False)
            need(run.returncode == 0, f'fixed source git {label} failed')
            if label == 'status':
                need(not run.stdout.strip(), 'fixed CFRU source worktree is dirty')
            else:
                result[label] = run.stdout.strip()
    return result


def matches(root: Path, paths: Iterable[Path]) -> tuple[dict, dict]:
    found = {needle: [] for needle in NEEDLES}
    files = {}
    for path in paths:
        raw, lines = read_text(path)
        rel = path.relative_to(root.resolve()).as_posix()
        for line_no, line in enumerate(lines, 1):
            for needle in NEEDLES:
                if needle not in line:
                    continue
                need(len(found[needle]) < MAX_MATCHES_PER_NEEDLE, f'too many matches for {needle}')
                start, end = max(1, line_no - CONTEXT), min(len(lines), line_no + CONTEXT)
                context = '\n'.join(lines[start - 1:end]) + '\n'
                found[needle].append(dict(path=rel, line=line_no, text=line.strip(), context_start=start,
                    context_end=end, context_sha256=hashlib.sha256(context.encode()).hexdigest(), context=context))
                files[rel] = identity(raw)
    for needle in REQUIRED:
        need(found[needle], f'required owner token absent: {needle}')
    return found, files


def callback_owner_candidates(root: Path, paths: Iterable[Path]) -> list[dict]:
    """宣言・コメント・文字列・別関数の偶然の同居は分岐所有者にしない。"""
    candidates = []
    ignored = re.compile(r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', re.S)
    functions = re.compile(r'\b([A-Za-z_]\w*)\s*\([^;{}]*\)\s*\{')
    calls = re.compile(r'\bSetMainCallback2\s*\(\s*(CB2_(?:WhiteOut|ReturnToField\w*))\s*\)')
    for path in paths:
        if path.suffix != '.c':
            continue
        _, lines = read_text(path)
        code = ignored.sub(lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), '\n'.join(lines))
        if 'CB2_WhiteOut' not in code:
            continue
        for match in functions.finditer(code):
            if code[:match.start()].count('{') != code[:match.start()].count('}'):
                continue
            start = match.end() - 1
            depth, end = 1, start + 1
            while end < len(code) and depth:
                depth += (code[end] == '{') - (code[end] == '}')
                end += 1
            need(depth == 0, 'unbalanced candidate function body')
            routes = sorted(set(calls.findall(code[start:end])))
            if 'CB2_WhiteOut' in routes and any(n.startswith('CB2_ReturnToField') for n in routes):
                candidates.append(dict(path=path.relative_to(root.resolve()).as_posix(), function=match[1],
                    line=code[:match.start()].count('\n') + 1, callbacks=routes))
    return candidates


def classify(found: dict, candidates: list[dict] | None = None) -> dict:
    candidates = candidates or []
    whiteout = sorted({r['path'] for r in found['CB2_WhiteOut']})
    returns = sorted({r['path'] for r in found['CB2_ReturnToField']})
    owners = sorted({r['path'] for r in candidates})
    return dict(whiteout_reference_paths=whiteout, field_return_reference_paths=returns,
        whiteout_owner_paths=owners, field_return_owner_paths=owners,
        end_lifecycle_paths=sorted({r['path'] for n in ('EndOfBattleThings', 'EndBattleFlagClear', 'VegaBattlePolicyEnd') for r in found[n]}),
        whiteout_and_return_overlap_paths=owners,
        reference_only_overlap_paths=sorted((set(whiteout) & set(returns)) - set(owners)),
        callback_owner_candidates=candidates, owner_resolved=bool(candidates), source_scan_complete=True,
        candidate_rom_owner_verified=False,
        next_boundary='CANDIDATE_ROM_CALLBACK_BYTES_REQUIRED',
        candidate_rom_changed=False, new_emulator_processes=0, accepted_native_cases_replayed=0)


def render_excerpts(found: dict) -> str:
    blocks = []
    seen = set()
    for needle in NEEDLES:
        blocks.append(f'## {needle}\n')
        for r in found[needle]:
            key = (r['path'], r['context_start'], r['context_end'], r['context_sha256'])
            if key in seen:
                continue
            seen.add(key)
            blocks.append(f"### {r['path']}:{r['line']} lines {r['context_start']}-{r['context_end']} sha256={r['context_sha256']}\n")
            blocks.extend(f'{i:6d}: {line}\n' for i, line in enumerate(r['context'].splitlines(), r['context_start']))
    return ''.join(blocks)


def audit(root: Path) -> tuple[dict, str]:
    root = root.resolve()
    paths = source_files(root)
    found, files = matches(root, paths)
    report = dict(schema_version=SCHEMA_VERSION, task=TASK, classification='SOURCE_ONLY_OWNER_AUDIT_NOT_NATIVE_ACCEPTANCE',
        fixed_source=source_identity(root), needles={k: len(v) for k, v in found.items()}, matched_files=files,
        matches=found, summary=classify(found, callback_owner_candidates(root, paths)),
        release_ready=False, native_bp_earning_accepted=False)
    return report, render_excerpts(found)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--root', type=Path, default=Path('.'))
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args(argv)
    report, excerpts = audit(args.root)
    need(not any(p.is_symlink() for p in (args.output_dir, *args.output_dir.parents)), 'output directory symlink rejected')
    out = args.output_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)
    (out / 'owner-report.json').write_bytes(stable(report))
    (out / 'owner-excerpts.txt').write_text(excerpts, encoding='utf-8', newline='\n')
    print(stable(dict(status='PASS', summary=report['summary'], needles=report['needles'])).decode(), end='')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
