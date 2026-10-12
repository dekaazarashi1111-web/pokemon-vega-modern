#!/usr/bin/env python3
"""成功4原本だけからBubbleの最小4byte型を受領。ROM/旧試験/readerは再走しない。"""
from __future__ import annotations
import collections
import copy
import io
import json
import stat
import zipfile
from pathlib import Path
import pr16_weather_bubble as model
import pr16_dex_hof_blastoise_chain as previous

ROOT = Path(__file__).resolve().parents[1]
HEAD = '3aada9217cc80627496adf33756d8fc2de3b5765'
RUN, JOB, ARTIFACT = 38040440848, 114179438484, 11665870186
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
WF = '.github/workflows/pr16-weather-bubble-reader.yml'
EVIDENCE = 'content/modernization/pr16_weather_bubble_evidence'
CHECKPOINT = 'content/modernization/pr16_weather_bubble_checkpoint.json'
GUIDE = 'docs/PR16_WEATHER_BUBBLE_ACCEPTANCE_JA.md'
NAMESPACE = 'weather_bubble_reference_chain'
KIND = 'rooted_weather_bubble_4bpp_minimum_asset'
FILES = {
    'measurement.json': dict(size=42289, sha256='9b3d4036968f5e88c5e69afee88a8e65d44281b68d86995b060be19bcaed2205'),
    'parent.json': dict(size=12927, sha256='80b7c65e97fe74417879e96e59bbe83db76eabfd1bea62f05477b0a80edbdc6b'),
    'provenance.json': dict(size=34477, sha256='54df49cc2a52273c98e2339c9ad173ea2d0787477630060e28aea07c7ebf985b'),
    'tests.json': dict(size=2610, sha256='a07f29f4245fd164952de33f336cd0b8984f8125492eb3a3c89d3a4658cd303e'),
}
ZIP_ID = dict(size=21420, sha256='f3d0cfed7517d5a1c73d6eadf9c1fa0024ccbcd9bc36c915cc07edf099ef681f')
need, identity, canonical = model.need, model.identity, model.canonical


def exact(a, b):
    """JSONのbool/int、list/tuple、subclassを同値扱いしない。"""
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(type(k) is str and exact(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return type(a) in (str, int, bool, type(None)) and a == b


def read(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, '重複JSON key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('JSONの浮動小数点/非有限数を拒否')
    need(type(raw) is bytes and b'\0' not in raw, 'text bytesのみ')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs,
                      parse_float=reject, parse_constant=reject)


def regular(root, name):
    root, rel = Path(root).resolve(), Path(name)
    need(type(name) is str and not rel.is_absolute() and '..' not in rel.parts and
         '\\' not in name and rel.as_posix() == name, '閉じた相対path')
    path = root / rel
    need(not any(p.is_symlink() for p in (path, *path.parents)) and path.is_file(), 'regular fileだけ')
    return path.read_bytes()


def unpack(raw):
    need(type(raw) is bytes and exact(identity(raw), ZIP_ID), '独立取得ZIP全identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        rows = archive.infolist()
        need(len(rows) == 4 and {r.filename for r in rows} == set(FILES), 'flatな原本4個だけ')
        need(all(not r.is_dir() and not stat.S_ISLNK(r.external_attr >> 16) and
                 not r.flag_bits & 1 and r.file_size == FILES[r.filename]['size'] for r in rows), 'ZIP member安全境界')
        files = {name: archive.read(name) for name in FILES}
    verify_files(files)
    return files


def verify_files(files):
    need(type(files) is dict and set(files) == set(FILES), '閉4原本')
    need(all(type(files[n]) is bytes and exact(identity(files[n]), meta) for n, meta in FILES.items()),
         '原本完全byte。改変後の自己申告hashを受け付けない')
    values = {n: read(b) for n, b in files.items()}
    m, p, t, a = (values[n] for n in ('measurement.json', 'provenance.json', 'tests.json', 'parent.json'))
    need(exact(p['files'], {n: FILES[n] for n in FILES if n != 'provenance.json'}), '内部3hash')
    need(p['context']['source_head'] == HEAD and p['context']['run_id'] == RUN, '測定source/run')
    need(exact(m['candidate'], model.CANDIDATE) and m['formal_classification_accepted'] is False and
         m['whole_asset_equal'] is True and m['type_candidate'] is True, '測定と受入の分離')
    need(exact(m['claims'], model.CLAIMS) and exact(m['inherited'], dict(classified=783,hits=874,unclassified=91)), '非主張と783親')
    need(m['target'] == model.HIT and exact(m['independent_asset'], model.sources.ASSET_ID), '独立64byte画像')
    positive = m['finite_reader']
    need(exact(positive['asset_reads'], [dict(address=model.ASSET+offset,size=2) for offset in range(0,64,2)]) and
         exact(positive['output_identity'], m['independent_asset']) and positive['consumed_bytes'] == 64 and
         positive['code_steps'] == 38 and positive['reader_stack_frame']['root_frame_bytes'] == 12 and
         positive['reader_stack_frame']['entry_sp'] == positive['reader_stack_frame']['return_sp'], '実reader全64byteと実stack帰還')
    for name in ('finite_reader','no_allocation_control','already_created_control'):
        need(exact(m[name]['claims'], model.CLAIMS) and exact(m[name]['contract'], model.CONTRACT), '条件を安全主張へ昇格しない')
    need(all(m[n]['consumed_bytes'] == 0 and m[n]['asset_reads'] == [] for n in ('no_allocation_control','already_created_control')), '両陰性の未消費')
    need(t['tests_run'] == len(set(t['tests'])) == 32 and t['failures'] == t['errors'] == t['skipped'] == 0, '実行済み32試験を継承')
    need(exact(a['audit_identity'], previous.PARENT_AUDIT_ID) and exact(a['input_bindings'], previous.PARENT_INPUT_IDENTITIES), '正式62親原本だけ')
    return values


def verify_sources(values, root=ROOT):
    p, a = values['provenance.json'], values['parent.json']
    for bindings in (p['context']['code_bindings'], p['dependency_bindings'], a['input_bindings']):
        for name, meta in bindings.items():
            need(exact(identity(regular(root,name)), meta), '測定時source/保存親不変: '+name)
    need(len(p['context']['code_bindings']) == 6 and len(a['input_bindings']) == 62, 'source境界')


def metadata(run, job, artifact):
    """APIの巨大envelopeを正規化し、受領した同run/job/全stepだけを固定。"""
    for key,value in dict(id=RUN,head_sha=HEAD,head_branch=BRANCH,run_attempt=1,status='completed',conclusion='success',path=WF).items():
        need(exact(run.get(key),value), 'run '+key)
    need(run['repository']['full_name'] == run['head_repository']['full_name'] == REPO, 'forkを拒否')
    for key,value in dict(id=JOB,run_id=RUN,name='bubble-reader',status='completed',conclusion='success',head_sha=HEAD).items():
        need(exact(job.get(key),value), 'job '+key)
    steps = job['steps']
    need(type(steps) is list and len(steps) == 9 and len({s['number'] for s in steps}) == 9 and
         [s['number'] for s in steps] == sorted(s['number'] for s in steps) and
         all(s['status'] == 'completed' and s['conclusion'] == 'success' for s in steps), '全9step成功を必須化')
    for key,value in dict(id=ARTIFACT,name='pr16-weather-bubble-reader-text-only',size_in_bytes=ZIP_ID['size'],expired=False,digest='sha256:'+ZIP_ID['sha256']).items():
        need(exact(artifact.get(key),value), 'artifact '+key)
    need(exact(artifact['workflow_run'], dict(id=RUN,repository_id=1358127462,head_repository_id=1358127462,head_branch=BRANCH,head_sha=HEAD)), 'artifact同run/source')
    return dict(run_id=RUN,job_id=JOB,artifact_id=ARTIFACT,source_head=HEAD,run_attempt=1,conclusion='success',
                zip_identity=copy.deepcopy(ZIP_ID),steps=[{k:s[k] for k in ('number','name','status','conclusion')} for s in steps])


def verify_log(raw):
    """生成/検証済みと公開済みの各4hashを、取得job logの順序付き抄録へ結ぶ。"""
    markers = ('PASS_CURRENT_BUBBLE_BEFORE_PUBLICATION','PASS_CLOSED_FOUR_BUBBLE_JSON')
    rows = []
    for line in raw.decode('utf-8-sig').splitlines():
        start = line.find('{')
        if start < 0 or not any(marker in line for marker in markers):
            continue
        row = read(line[start:].encode())
        need(row.get('status') in markers and exact(row.get('files'),FILES), '生成/公開4hash')
        if row['status'] == markers[0]:
            need(row['context']['source_head'] == HEAD and row['context']['run_id'] == RUN and row['formal_acceptance'] is False, '生成log source/run')
        rows.append(row)
    need([r['status'] for r in rows] == list(markers), '順序/欠落/重複/partialを拒否')
    return dict(job_log_identity=identity(raw),generated_validated_file_identities=copy.deepcopy(FILES),published_file_identities=copy.deepcopy(FILES))


def parent(root=ROOT):
    return previous.parent(*[regular(root,n) for n in previous.PARENT_INPUTS])


def build(audit, files):
    values = verify_files(files)
    need(exact(identity(previous.canonical(audit)),previous.PARENT_AUDIT_ID), '783親全identity。診断namespace/二重適用を拒否')
    old = next(h for h in audit['hits'] if h['address'] == model.HIT)
    need(exact(old,values['parent.json']['target']) and old['accepted'] is False, '実測時4byte未知')
    need(model.ASSET <= model.HIT and model.HIT + 4 <= model.ASSET + 64, '全4byteが独立画像/実消費範囲内')
    evidence = dict(measurement_identity=copy.deepcopy(FILES['measurement.json']),
        source_head=HEAD,run_id=RUN,classified_window=dict(address=model.HIT,size=4),
        asset=copy.deepcopy(values['measurement.json']['asset']),sheet=model.SHEET,
        root=model.ENTRY,loader=model.LOAD,copy=model.CPU,
        input_contract=copy.deepcopy(model.CONTRACT),claims=copy.deepcopy(model.CLAIMS))
    witness = dict(id=0,address=model.HIT,size=4,kind=KIND,evidence=evidence,evidence_identity=identity(canonical(evidence)))
    change = dict(**{k:old[k] for k in previous.FIELDS},classification='FALSE_POSITIVE_TYPED_REFERENCE_'+KIND.upper(),accepted=True,witness_ids=[0])
    return dict(schema_version=1,status='ACCEPTED_ONE_CONDITIONAL_WEATHER_BUBBLE_MINIMUM_ASSET_TYPE',
        namespace=NAMESPACE,parent_audit_identity=copy.deepcopy(previous.PARENT_AUDIT_ID),
        candidate=copy.deepcopy(model.CANDIDATE),evidence_bindings={EVIDENCE+'/'+n:copy.deepcopy(v) for n,v in FILES.items()},
        inherited_classified=783,inherited_unclassified=91,inherited_candidates=874,
        classified=784,unclassified=90,newly_classified=1,changes=[change],witnesses=[witness],
        claims=copy.deepcopy(model.CLAIMS),donor_safe_bytes=0,native_processes=0,
        old_full_rom_scan_runs=0,old_scope_test_reruns=0,measurement_replays=0)


def materialize(audit, delta, files):
    need(exact(delta,build(audit,files)), '閉じたsingleton差分。原本hashが合ってもcounter/claim/範囲を変更しない')
    full = copy.deepcopy(audit)
    change = delta['changes'][0]
    index = next(i for i,h in enumerate(full['hits']) if h['address'] == model.HIT)
    full['hits'][index] = dict(**{k:change[k] for k in previous.FIELDS},classification=change['classification'],
                              accepted=True,evidence=[{NAMESPACE+'_witness':0}])
    full.update(classified=784,unclassified=90,classifications=dict(collections.Counter(h['classification'] for h in full['hits'])))
    full[NAMESPACE] = copy.deepcopy(delta)
    need(all(exact(a,b) for i,(a,b) in enumerate(zip(audit['hits'],full['hits'])) if i != index), '他873行不変')
    need(all(exact(v,full[k]) for k,v in audit.items() if k not in ('hits','classified','unclassified','classifications')), '全30受入namespace/source/claim不変')
    return full


def frontier(full):
    rows = [dict(hit=copy.deepcopy(h),owners=copy.deepcopy(h['owner_candidates'])) for h in full['hits'] if not h['accepted']]
    need(len(rows) == 90 and all(r['owners'] == [] for r in rows), '残90unknownを無改作/順序保存')
    return dict(candidate=copy.deepcopy(model.CANDIDATE),total=90,owner_unknown=0,unowned_unknown=90,rows=rows,
                donor_eligible=False,indirect_reference_completeness_claimed=False)


def restore_parent(root=ROOT):
    """次scope用784親。Blastoise診断namespaceを混ぜず62原本と今回4原本から復元。"""
    files = {n:regular(root,EVIDENCE+'/'+n) for n in FILES}
    values = verify_files(files)
    verify_sources(values,root)
    audit = parent(root)
    delta = read(regular(root,EVIDENCE+'/reference-chain.json'))
    full = materialize(audit,delta,files)
    need(exact(read(regular(root,EVIDENCE+'/unknown-frontier.json')),frontier(full)), '保存frontier全90行')
    cp = read(regular(root,CHECKPOINT))
    need(exact(cp['delta_identity'],identity(canonical(delta))) and
         exact(cp['full_audit_identity'],identity(previous.canonical(full))) and
         exact(cp['unknown_identity'],identity(canonical(frontier(full)))), '受入checkpoint完全identity')
    return full


if __name__ == '__main__':
    audit = restore_parent()
    print(json.dumps(dict(status='PASS_SAVED_BUBBLE_784_90',classified=audit['classified'],unclassified=audit['unclassified'],
                          native_processes=0,measurement_replays=0,old_scope_test_reruns=0,donor_safe_bytes=0),sort_keys=True))
