#!/usr/bin/env python3
"""P08候補Wikiを決定的に生成・純読取検査する。ゲームや受入試験は実行しない。"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, ROOT, digest, need, selected_candidate, stable
from pr16_candidate_wiki_render import tree_hash, validate_links


def read_tree(root: Path) -> dict[str, bytes]:
    """symlink、特殊fileを黙って除外せず拒否する。"""
    need(not root.is_symlink(), 'Wiki root symlink')
    if not root.exists():
        return {}
    need(root.is_dir(), 'Wiki rootはdirectoryでなければならない')
    files = {}
    for path in sorted(root.rglob('*')):
        need(not path.is_symlink(), 'Wiki child symlink')
        if path.is_dir():
            continue
        need(path.is_file(), 'Wiki special file')
        files[path.relative_to(root).as_posix()] = path.read_bytes()
    return files


def compare(root: Path, expected: dict[str, bytes]) -> str:
    actual = read_tree(root)
    need(set(actual) == set(expected), 'Wiki missing/stale output')
    need(all(actual[name] == raw for name, raw in expected.items()), 'Wiki changed output')
    return tree_hash(actual)


def reject_writes(event: str, args: tuple) -> None:
    """check中のPython file書込やchild processをfail closedで拒否する。"""
    if event == 'open':
        _path, mode, flags = args
        need(not (isinstance(mode, str) and any(c in mode for c in 'wax+')), 'check書込open禁止')
        need(not (flags & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND)), 'check書込flag禁止')
    if event in {'os.remove', 'os.rmdir', 'os.rename', 'os.mkdir', 'os.link', 'os.symlink',
                 'os.chmod', 'os.chown', 'os.truncate', 'os.utime', 'subprocess.Popen', 'os.system', 'os.exec', 'os.posix_spawn'}:
        raise ValueError('check副作用禁止: ' + event)


def generate(inputs: Inputs) -> tuple[dict[str, bytes], dict]:
    from pr16_candidate_wiki_inputs import candidate_bytes
    from pr16_candidate_wiki_details import details
    from pr16_candidate_wiki_catalog import assemble
    from pr16_candidate_wiki_render import render
    from pr16_candidate_wiki_mega_quality import normalize, append_audit
    from pr16_candidate_wiki_consumers import enrich, append_pages
    from pr16_candidate_wiki_runtime_z import enrich as enrich_runtime_z, append_pages as append_runtime_z
    from pr16_candidate_wiki_effect_origin import enrich as enrich_effects, append_pages as append_effects
    from pr16_candidate_wiki_hidden_patch import enrich as enrich_hidden_patch, append_pages as append_hidden_patch
    from pr16_candidate_wiki_creation import enrich as enrich_creation, append_pages as append_creation
    from pr16_candidate_wiki_link_graph import enrich as enrich_link_graph, append_pages as append_link_graph
    candidate = selected_candidate(inputs)
    for name in ('scripts/build_pr16_candidate_wiki.py', 'scripts/pr16_candidate_wiki_catalog.py',
                 'scripts/pr16_candidate_wiki_render.py', 'scripts/pr16_candidate_wiki_mega_quality.py',
                 'scripts/pr16_candidate_wiki_consumers.py', 'scripts/pr16_wiki_source_snapshot.py'):
        inputs.raw(name)
    raw = candidate_bytes(inputs)
    model = enrich(normalize(assemble(details(inputs, raw), inputs)), inputs)
    enrich_runtime_z(model, inputs, raw)
    enrich_effects(model, inputs)
    enrich_hidden_patch(model, inputs)
    enrich_creation(model, inputs, raw)
    enrich_link_graph(model, inputs, raw)
    need(model['candidate'] == candidate, 'Wiki選択候補不一致')
    files = render(model)
    append_audit(files, model)
    append_pages(files, model)
    append_runtime_z(files, model)
    append_effects(files, model)
    append_hidden_patch(files, model)
    append_creation(files, model)
    append_link_graph(files, model)
    index = __import__('json').loads(files.pop('data/index.json'))
    index.update(mega_mapping_summary=model['mega_mapping_summary'], consumer_audit_summary=model['followup_audit']['summary'], issue18_complete=False,
                 snapshot_scope='ALL_ID_DOCUMENTATION_WITH_EXPLICIT_AUDIT_GAPS',
                 files={name: {'size': len(raw), 'sha256': digest(raw)} for name, raw in sorted(files.items())},
                 payload_tree_sha256=tree_hash(files))
    files['data/index.json'] = stable(index)
    validate_links(files)
    return files, index


def execute(command: str, inputs: Inputs) -> dict:
    need(command in {'build', 'check'}, 'command不正')
    candidate = selected_candidate(inputs)
    output = inputs.path('docs/wiki/p08-candidate-' + candidate['sha256'][:8])
    files, index = generate(inputs)
    actual = read_tree(output)
    if command == 'build':
        # 管理外fileを削除しない。変更差分だけをUTF-8 textとして書き込む。
        need(not set(actual) - set(files), 'Wiki stale fileを手動確認してください')
        for name, raw in sorted(files.items()):
            need(name.endswith(('.md', '.json', '.jsonl')) and b'\0' not in raw, 'Wiki非text出力')
            raw.decode('utf-8')
            if actual.get(name) != raw:
                path = output / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(raw)
    result = compare(output, files)
    return {'status': 'PASS', 'command': command, 'candidate': candidate,
            'output': output.relative_to(inputs.root).as_posix(), 'files': len(files),
            'bytes': sum(map(len, files.values())), 'tree_sha256': result,
            'internal_links': validate_links(files), 'counts': index['counts'],
            'record_counts': index['record_counts'], 'check_writes': 0,
            'new_native_runs': 0, 'rom_changes': 0, 'issue18_complete': False}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('build', 'check'))
    args = parser.parse_args()
    if args.command == 'check':
        sys.addaudithook(reject_writes)
    print(stable(execute(args.command, Inputs())).decode(), end='')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('candidate wiki: ' + str(exc), file=sys.stderr)
        raise SystemExit(1)
