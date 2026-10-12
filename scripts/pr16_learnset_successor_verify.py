#!/usr/bin/env python3
"""後継表だけの独立2生成・原本全行保存・純読取検証。旧受入は再実行しない。"""
from __future__ import annotations
import argparse
from collections import Counter
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
sys.path.insert(0, str(ROOT))
from tools import pr16_learnset_successor as s

CODE = ('tools/pr16_learnset_successor.py', 'tests/test_pr16_learnset_successor.py',
        'scripts/pr16_learnset_successor_verify.py')
WORK = ROOT / '.local/pr16-learnset-successor'
EXPECTED = '.github/pr16-learnset-successor-local.json'


def restore_official(destination: Path) -> dict:
    """有効な完了artifactを再利用。原本ZIPの再採取・39旧試験は呼ばない。"""
    from pr16_learnset_baseline_record import validate_run, read_proof
    from pr16_wiki_reconcile import fetch
    p = s.read_json(ROOT / (s.BASE + 'pr16_learnset_baseline_checkpoint.json'))
    request = {'run_id': p['run_id'], 'source_head': p['source_head'],
               'artifact_id': p['artifact']['id'], 'artifact_sha256': p['artifact']['sha256']}
    run = fetch(f"actions/runs/{p['run_id']}")
    jobs = fetch(f"actions/runs/{p['run_id']}/jobs?per_page=100")
    artifacts = fetch(f"actions/runs/{p['run_id']}/artifacts?per_page=100")
    artifact = validate_run(run, jobs, artifacts, request)
    raw = fetch(f"actions/artifacts/{artifact['id']}/zip", binary=True)
    read_proof(raw, request)
    destination.mkdir(parents=True, exist_ok=False)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        for name in ('official_baseline.jsonl', 'official_index.json', 'owner_approved_overlay.json'):
            with z.open('outputs/' + name) as src, (destination / name).open('xb') as dst:
                for block in iter(lambda: src.read(1048576), b''):
                    dst.write(block)
    return {'reused_accepted_run_id': run['id'], 'source_head': run['head_sha'],
            'artifact': {k: artifact[k] for k in ('id', 'name', 'digest', 'size_in_bytes', 'expires_at')},
            'new_source_acquisition': False, 'old_tests_executed': 0}


def fingerprint(value: dict) -> str:
    return hashlib.sha256(s.encode(value)).hexdigest()


def audit_tables(official: Path, output: Path, receipt: dict) -> dict:
    """生成器の分類関数を呼ばず、source全行のdigest/order/重複を独立検査する。"""
    expected, seen, ordinal = {}, set(), Counter()
    for row in s.rows(official / 'official_baseline.jsonl'):
        sid = row['target_species_id']
        key = ('official_baseline', sid, ordinal[sid])
        expected[key] = (fingerprint(row), row['consumer'], row['source_route']['project_move_id'])
        ordinal[sid] += 1
    for species in s.rows(ROOT / (s.VEGA + 'adopted_vega_original_baseline.jsonl')):
        for family, routes in species['methods'].items():
            for row in routes:
                expected['vega_original_baseline', species['species_id'], family, row['order']] = (
                    fingerprint(row), family, row['move_id'])
    def consume(row, excluded=False):
        if row['layer'] == 'official_baseline':
            key = (row['layer'], row['species_id'], row['source_order'])
            source = row['provenance']
        else:
            key = (row['layer'], row['species_id'], row['consumer'], row['source_order'])
            source = row['provenance']['source_route']
        s.require(key not in seen and expected.get(key) == (fingerprint(source), row['consumer'], row['move_id']),
                  '独立audit: 原本field/order/consumer/重複不一致')
        seen.add(key)
        s.require((row['move_id'] == 1063) is excluded, '独立audit: Side Changeの除外境界不一致')
        s.require(row['disposition'] == (s.DECLINED if excluded else 'BASELINE_SELECTED'), '独立audit: disposition不一致')
    counts = Counter()
    species_ids = None
    hatch_eggs = {}
    for family in s.CONSUMERS:
        ids = []
        for block in s.rows(output / (family + '.jsonl')):
            ids.append(block['species_id'])
            s.require(block['runtime_applied'] is False, 'runtime適用への昇格')
            for row in block['routes']:
                s.require(row['consumer'] == family and row['species_id'] == block['species_id'], 'consumer区画不一致')
                consume(row)
                counts[family] += 1
            if family == 'egg':
                hatch_eggs[block['species_id']] = {r['move_id'] for r in block['routes'] if not r['conditional_egg']}
        s.require(ids == sorted(set(ids)) and len(ids) == 1671, 'consumer全Species区画欠落/重複')
        s.require(species_ids is None or ids == species_ids, 'consumerのSpecies集合不一致')
        species_ids = ids
    excluded = list(s.rows(output / 'excluded_routes.jsonl'))
    for row in excluded:
        consume(row, True)
    s.require(seen == set(expected) and len(seen) == 128447, '原本行の欠落/追加')
    s.require(dict(counts) == receipt['consumers'] and sum(counts.values()) == 128288, '全consumer集計不一致')
    s.require(len(excluded) == 159 and len({r['species_id'] for r in excluded}) == 103, '除外全数不一致')
    original_links = {r['row_key']: fingerprint(r) for r in s.rows(ROOT / (s.VEGA + 'nondirect_egg.jsonl'))}
    links, gaps, link_seen = [], [], set()
    for row in s.rows(output / 'vega_hatch_links.jsonl'):
        key = row['provenance']['row_key']
        s.require(key not in link_seen and original_links.get(key) == fingerprint(row['provenance']), '孵化原本の改変/重複')
        link_seen.add(key)
        s.require(row['direct_grant'] is False and row['shared_grant'] is False, '非直接eggの無断付与')
        present = row['move_id'] in hatch_eggs[row['hatch_species_id']]
        s.require(row['hatch_selected_direct_egg_membership'] is present, '孵化先新baseline照合不一致')
        if not present:
            gaps.append({'row_key':key,'receiver_species_id':row['receiver_species_id'],
                         'hatch_species_id':row['hatch_species_id'],'move_id':row['move_id']})
        links.append(row)
    s.require(link_seen == set(original_links) and len(gaps) == receipt['hatch_baseline_membership_gaps'], '孵化全数不一致')
    old = {r['species_id']:r for r in s.rows(ROOT / (s.WIKI + 'learnsets.jsonl'))}
    diffs = list(s.rows(output / 'candidate_diff.jsonl'))
    s.require([r['species_id'] for r in diffs] == species_ids, '旧候補差分Species不一致')
    for diff in diffs:
        before = old[diff['species_id']]['routes']
        s.require(len(diff['old_entries']) == len(before), '旧候補行の欠落')
        for order, (entry, row) in enumerate(zip(diff['old_entries'],before)):
            s.require((entry['old_order'],entry['move_id'],entry['move_key'],entry['old_route'])
                      == (order,row['move_id'],row['move_key'],row['route']), '旧候補行identity不一致')
    coverage = list(s.rows(output / 'species_coverage.jsonl'))
    unselected = [r for r in coverage if r['selection'] not in ('OFFICIAL_SOURCE_SELECTED','VEGA_SOURCE_SELECTED')]
    s.require(len(unselected) == 191 and all(r['automatic_fallback'] is False for r in coverage), '非選択種fallback境界不一致')
    return {'source_rows_accounted':len(seen),'selected_rows':sum(counts.values()),
            'side_change_excluded':len(excluded),'vega_hatch_links':len(links),
            'hatch_baseline_membership_gaps':gaps,'unselected_species':unselected,
            'candidate_diff_summary':[{k:v for k,v in row.items() if k != 'old_entries'} for row in diffs],
            'runtime_applied':False,'issue19_complete':False,'release_ready':False}


def snapshot(paths):
    return {str(p): (s.identity(p),p.stat().st_mtime_ns) for p in paths}


def verify(official: Path | None, work: Path) -> dict:
    s.require(not work.exists(), '検証出力の再利用/上書きは禁止')
    work.mkdir(parents=True)
    if official is None:
        official = work/'official'
        source = restore_official(official)
    else:
        source = {'local_accepted_artifact_reuse':True,'old_tests_executed':0}
    (work/'source-actions.json').write_bytes(s.encode(source))
    command = [sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_learnset_successor.py','-v']
    completed = subprocess.run(command,cwd=ROOT,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (work/'unit.txt').write_text(completed.stdout,encoding='utf-8')
    s.require(completed.returncode == 0 and re.findall(r'^Ran (\d+) tests in ',completed.stdout,re.M) == ['39']
              and re.search(r'\nOK\s*$',completed.stdout), '39新試験未成功')
    cli = [sys.executable,'-B','tools/pr16_learnset_successor.py','generate','--official',str(official)]
    for seed, name in ((17,'a'),(53,'b')):
        result = subprocess.run(cli+['--output',str(work/name)],cwd=ROOT,env=dict(os.environ,PYTHONHASHSEED=str(seed)),
                                text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (work/(name+'.txt')).write_text(result.stdout,encoding='utf-8')
        s.require(result.returncode == 0, '独立生成失敗: '+result.stdout[-1500:])
    ra, rb = (s.read_json(work/name/'receipt.json') for name in ('a','b'))
    s.require(ra == rb, '独立2生成が不一致')
    watched = list((work/'a').iterdir()) + list((work/'b').iterdir()) + list(official.iterdir())
    watched += [ROOT/name for name in ra['inputs'] if (ROOT/name).is_file()]
    before = snapshot(watched)
    checked = s.check(ROOT,official,work/'a')
    s.require(before == snapshot(watched) and checked == ra, '純読取byte/mtime不変条件違反')
    audit = audit_tables(official,work/'a',ra)
    (work/'compact-review.json').write_bytes(s.encode(audit))
    (work/'receipt.json').write_bytes(s.encode(ra))
    expected_path = ROOT/EXPECTED
    local_match = None
    if expected_path.is_file():
        expected = s.read_json(expected_path)
        s.require(expected['files'] == ra['files'], 'ローカル/Actions出力不一致')
        s.require(expected['code'] == {p:s.identity(ROOT/p) for p in CODE}, '検証code identity不一致')
        local_match = True
    report = {'status':'PASS_SUCCESSOR_TABLES_ONLY','source_head':os.environ.get('GITHUB_SHA'),
              'run_id':int(os.environ.get('GITHUB_RUN_ID','0')),'focused_tests':39,
              'two_process_outputs_identical':True,'readonly_byte_mtime_unchanged':True,
              'independent_source_row_audit':True,'source_rows_accounted':audit['source_rows_accounted'],
              'code':{p:s.identity(ROOT/p) for p in CODE},'files':ra['files'],
              'local_and_actions_output_identical':local_match,
              'rom_changes':0,'new_native_runs':0,'accepted_native_reruns':0,
              'official_baseline_reruns':0,'vega_source_reruns':0,'runtime_applied':False,
              'issue19_complete':False,'release_ready':False}
    (work/'verify.json').write_bytes(s.encode(report))
    if not os.environ.get('GITHUB_SHA'):
        (work/'local-expectation.json').write_bytes(s.encode({'files':ra['files'],'code':report['code']}))
    print(json.dumps({k:v for k,v in report.items() if k not in ('files','code')},ensure_ascii=False,sort_keys=True))
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--official',type=Path);parser.add_argument('--work',type=Path,default=WORK)
    args=parser.parse_args();verify(args.official,args.work)
