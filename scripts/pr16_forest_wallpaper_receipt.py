#!/usr/bin/env python3
"""Forest成功原本の読取専用受領。ROM再構成・reader・旧試験は実行しない。"""
from __future__ import annotations
import collections
import copy
import hashlib
import io
import json
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
SOURCE = '948e3773b4909eb7a5baaf77388686a61549e255'
MEASURED_COMMIT = 'bc10f50ea7e3ce338f63d6ab5823644cd4fbe931'
RUN, JOB, ARTIFACT = 38081577392, 114299405185, 11680930584
WORKFLOW = '.github/workflows/pr16-forest-wallpaper-reader.yml'
MEASUREMENT = 'content/modernization/pr16_forest_wallpaper_reader_checkpoint.json'
REPORT = 'content/modernization/pr16_forest_wallpaper_receipt.json'
EVIDENCE = 'content/modernization/pr16_forest_wallpaper_receipt_evidence'
NAMESPACE = 'forest_wallpaper_reference_chain'
KIND = 'rooted_forest_wallpaper_lz10_minimum_asset'
HIT, ASSET = 0x08397492, 0x08397188
ZIP_ID = dict(size=60837, sha256='0791aff7e2f52357b9aa0224d8cbe67942879248b1434230b519d815ff121b9b')
FILES = {
    'checkpoint.json': dict(size=603374, sha256='56e6c8d19bc04a1a6b9d3d199344f48426cc55d2b8da444aa5f9b02970b7012e'),
    'focused-tests.txt': dict(size=3755, sha256='9d4fb82df7f219d77c2e20fd75c0166a342ae51e76fc390da6208d15478ba793'),
    'result.json': dict(size=349, sha256='5416550775f857b8af29470faf31bd5902965d51c0541d3d0d1dd4cc1af8a30c'),
}
PARENT_ID = dict(size=5405033, sha256='be38da073c9a124de94506091d0ce9fe090c407e4ec85d05037f61d36109d850')
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
DECODED = dict(size=1696, sha256='004a48f42202841373162e9732de13007725da29ad997429386cbccf0461a2ea')
CLAIMS = dict(conditional_finite_reader_only=True, actual_runtime_execution_observed=False,
    actual_bios_cpu_executed=False, actual_screen_rendered=False, allocator_implementation_proven=False,
    dma_completion_proven=False, heap_free_proven=False, universal_heap_or_irq_lifetime_proven=False,
    formal_classification_accepted=False, indirect_reference_completeness_claimed=False,
    donor_eligible=False, donor_leased=False, donor_safe_bytes=0, formal_rom_changed=False,
    formal_save_changed=False, native_processes=0, accepted_test_reruns=0, accepted_reader_replays=0)
STEP_NAMES = [(1, 'Set up job'), (2, 'Run actions/checkout@v4'), (3, 'Run actions/setup-python@v5'),
    (4, 'New scoped ARM layout and reconstruction tools'),
    (5, 'Forest actual reader allocation success and failure'), (6, 'Run actions/upload-artifact@v4'),
    (11, 'Post Run actions/setup-python@v5'), (12, 'Post Run actions/checkout@v4'), (13, 'Complete job')]


def need(ok, message):
    if not ok:
        raise ValueError(message)


def exact(a, b):
    if type(a) is not type(b):
        return False
    if type(a) is dict:
        return set(a) == set(b) and all(type(k) is str and exact(a[k], b[k]) for k in a)
    if type(a) is list:
        return len(a) == len(b) and all(exact(x, y) for x, y in zip(a, b))
    return type(a) in (str, int, bool, type(None)) and a == b


def identity(raw):
    need(type(raw) is bytes, 'bytesのみ')
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def read(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, '重複JSON key')
            result[key] = value
        return result
    def reject(value):
        raise ValueError('浮動小数点・非有限数は不可')
    need(type(raw) is bytes and b'\0' not in raw, 'UTF-8 text bytesのみ')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_float=reject, parse_constant=reject)


def regular(root, name):
    root, rel = Path(root), Path(name)
    need(type(name) is str and not rel.is_absolute() and '..' not in rel.parts and
         '\\' not in name and rel.as_posix() == name, '閉じた相対path')
    path = root / rel
    need(not any(p.is_symlink() for p in (path, *path.parents)) and path.is_file(), '通常fileのみ')
    return path.read_bytes()


def profiles(cp):
    """原本hashとは別に、4条件の順序・型・消費・帰還・非主張を検査する。"""
    need(exact(cp['candidate'], CANDIDATE) and exact(cp['claims'], CLAIMS), '候補/非主張')
    need(exact([cp['classified'], cp['unclassified'], cp['donor_safe_bytes']], [784, 90, 0]), '受領前の正式件数')
    need(cp['formal_receipt_created'] is False and cp['actions_completion_confirmed'] is False, '測定と受領の分離')
    need(cp['source_head'] == SOURCE and exact(cp['actions_run_id'], RUN), '測定source/run')
    rows = cp['profiles']
    need(type(rows) is list and len(rows) == 4, '閉4条件')
    expected_calls = [134789168,136084112,134812608,136084104,135231940,135232248,134228892]
    for row, (offset, allocated) in zip(rows, [(0,True),(0,False),(1,True),(1,False)]):
        need(exact([row['wallpaper_offset'], row['allocated']], [offset, allocated]), '条件重複/順序/型')
        need(row['status'] == 'PASS_CONDITIONAL_FINITE_READER' and exact(row['claims'], CLAIMS), '条件付き非主張')
        need(exact([row[k] for k in ('asset_lz_consumed','target_bytes_consumed','heap_bytes_written','instruction_count')],
                   [973,4,1696,130] if allocated else [0,0,0,131]), '全4byte/展開量/有限命令数')
        need(exact(row['decoded'], DECODED if allocated else None), '独立展開hash/NULL非展開')
        need(row['malloc_return_frame_proven'] is True and row['loader_null_return_frame_proven'] is (not allocated)
             and row['heap_live_at_success_stop'] is allocated, '実stack帰還/未解放境界')
        need(exact([c['target'] for c in row['calls']], expected_calls + ([136084112,134704052] if allocated else [])), '実call列')
        need(exact([r['address'] for r in row['table_reads']], [137998108,137998112,137998104]) and
             all(exact(r['size'],4) for r in row['table_reads']), '実table全3field')
        events = row['events']
        returned = [e for e in events if e['kind'] == 'malloc_return']
        need(exact(returned, [dict(address=135231978,kind='malloc_return',sp=50364100)]), 'malloc実帰還位置/SP')
        need(events[-1]['kind'] == ('CreateTask_boundary' if allocated else 'loader_return'), '正しい打切り線')
        if not allocated:
            need(exact(events[-1], dict(address=134812558,kind='loader_return',sp=50364136)), 'NULL loader実帰還')
        fixture = row['caller_fixture']
        need(exact([fixture['box_id'],fixture['direction'],fixture['seeded_bytes'],fixture['storage_address']],
                   [0,0,5,33587200]) and exact(fixture['layout'],cp['source_binding']['layout']), '有限caller条件')
    need(exact(cp['focused_tests'],33) and exact(cp['new_profiles'],4) and cp['old_inputs_unchanged'] is True, '継承済み測定のみ')
    return cp


def measurement(raw):
    need(exact(identity(raw), FILES['checkpoint.json']), '独立取得済み測定原本全hash')
    return profiles(read(raw))


def unpack(raw):
    need(exact(identity(raw),ZIP_ID), '独立取得済みZIP全identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        rows = z.infolist()
        need(len(rows) == 3 and {r.filename for r in rows} == set(FILES), '閉3原本/重複禁止')
        need(all(not r.is_dir() and not stat.S_ISLNK(r.external_attr >> 16) and not r.flag_bits & 1
                 and r.file_size == FILES[r.filename]['size'] for r in rows), 'ZIP安全境界')
        files = {n:z.read(n) for n in FILES}
    need(all(exact(identity(files[n]),v) for n,v in FILES.items()), '全member hash')
    measurement(files['checkpoint.json'])
    result = read(files['result.json'])
    need(result['commit'] == MEASURED_COMMIT and result['source_head'] == SOURCE and result['status'] == 'DONE', '公開commit')
    tests = files['focused-tests.txt'].decode()
    rows = [s for s in tests.splitlines() if s.startswith('test_')]
    need(len(rows) == len(set(rows)) == 33 and all(s.endswith(' ... ok') for s in rows)
         and tests.endswith('\nOK\n'), '成功済み33試験の原本。再実行しない')
    return files


def metadata(run, jobs, artifact):
    for key,value in dict(id=RUN,head_sha=SOURCE,head_branch=BRANCH,run_attempt=1,
                          status='completed',conclusion='success',path=WORKFLOW,event='push').items():
        need(exact(run.get(key),value), 'run '+key)
    need(run['repository']['full_name'] == run['head_repository']['full_name'] == REPO, '同repo/fork拒否')
    need(exact(jobs['total_count'],1) and len(jobs['jobs']) == 1, '全jobを取得')
    job = jobs['jobs'][0]
    for key,value in dict(id=JOB,run_id=RUN,head_sha=SOURCE,name='forest-reader',status='completed',conclusion='success').items():
        need(exact(job.get(key),value), 'job '+key)
    expected_steps = [dict(number=n,name=s,status='completed',conclusion='success') for n,s in STEP_NAMES]
    steps = [{k:s[k] for k in ('number','name','status','conclusion')} for s in job['steps']]
    need(exact(steps,expected_steps), '全9step/順序/skip拒否')
    for key,value in dict(id=ARTIFACT,name='pr16-forest-reader-public-text',size_in_bytes=ZIP_ID['size'],
                          expired=False,digest='sha256:'+ZIP_ID['sha256']).items():
        need(exact(artifact.get(key),value), 'artifact '+key)
    need(exact(artifact['workflow_run'],dict(id=RUN,repository_id=1358127462,head_repository_id=1358127462,
                                            head_branch=BRANCH,head_sha=SOURCE)), 'artifact同source/run')
    return dict(run_id=RUN,job_id=JOB,artifact_id=ARTIFACT,source_head=SOURCE,run_attempt=1,
                status='completed',conclusion='success',zip_identity=copy.deepcopy(ZIP_ID),steps=steps)


def sources(cp, root=ROOT):
    bindings = {MEASUREMENT:FILES['checkpoint.json']}
    for key in ('code_bindings','dependency_bindings','inherited_input_bindings'):
        for name, meta in cp[key].items():
            need(name not in bindings or exact(bindings[name],meta), 'binding競合')
            bindings[name] = meta
    for name, meta in bindings.items():
        need(exact(identity(regular(root,name)),meta), '測定source/保存原本不変: '+name)
    return bindings


def build(audit, raw):
    # 正式784親の読取復元器のみ参照。ROM/有限readerを呼ばない。
    import pr16_weather_bubble_receipt as previous
    cp = measurement(raw)
    need(exact(identity(previous.previous.canonical(audit)),PARENT_ID), '正式784親全identity/二重適用拒否')
    need(exact([audit['classified'],audit['unclassified'],len(audit['hits'])],[784,90,874]), '正式親件数')
    matches = [h for h in audit['hits'] if h['address'] == HIT]
    need(len(matches) == 1 and matches[0]['accepted'] is False and matches[0]['owner_candidates'] == [], '唯一の未知1件')
    need(ASSET <= HIT and HIT+4 <= ASSET+973, '全4byteが消費内。paddingを含めない')
    change = copy.deepcopy(matches[0])
    change.update(classification='FALSE_POSITIVE_TYPED_REFERENCE_'+KIND.upper(),accepted=True,
                  evidence=[{NAMESPACE+'_witness':0}])
    claims = copy.deepcopy(CLAIMS);claims['formal_classification_accepted'] = True
    return dict(schema_version=1,status='ACCEPTED_ONE_CONDITIONAL_FOREST_MINIMUM_ASSET_TYPE',
        namespace=NAMESPACE,parent_audit_identity=copy.deepcopy(PARENT_ID),candidate=copy.deepcopy(CANDIDATE),
        measurement_path=MEASUREMENT,measurement_identity=copy.deepcopy(FILES['checkpoint.json']),
        inherited_classified=784,inherited_unclassified=90,inherited_candidates=874,
        classified=785,unclassified=89,newly_classified=1,changes=[change],
        witnesses=[dict(id=0,address=HIT,size=4,kind=KIND,source_head=SOURCE,run_id=RUN,
                        conditions=copy.deepcopy(cp['conditions']),profile_identities=[identity(encode(p)) for p in cp['profiles']])],
        claims=claims,donor_safe_bytes=0,native_processes=0,rom_reconstructions=0,
        measurement_replays=0,old_scope_test_reruns=0)


def materialize(audit, delta, raw):
    need(exact(delta,build(audit,raw)), '閉じたsingleton差分。counter/条件/claim変更拒否')
    full = copy.deepcopy(audit)
    index = next(i for i,h in enumerate(full['hits']) if h['address'] == HIT)
    full['hits'][index] = copy.deepcopy(delta['changes'][0])
    full.update(classified=785,unclassified=89,classifications=dict(collections.Counter(h['classification'] for h in full['hits'])))
    full[NAMESPACE] = copy.deepcopy(delta)
    need(all(exact(a,b) for i,(a,b) in enumerate(zip(audit['hits'],full['hits'])) if i != index), '他873行不変')
    need(all(exact(v,full[k]) for k,v in audit.items() if k not in ('hits','classified','unclassified','classifications')), '全旧namespace不変')
    need(sum(h['accepted'] is True for h in full['hits']) == 785, '受入行総数')
    return full


def frontier(full):
    rows = [dict(hit=copy.deepcopy(h),owners=copy.deepcopy(h['owner_candidates'])) for h in full['hits'] if h['accepted'] is False]
    need(len(rows) == 89 and all(r['owners'] == [] for r in rows), '未知89行の順序/内容保全')
    return dict(candidate=copy.deepcopy(CANDIDATE),total=89,owner_unknown=0,unowned_unknown=89,rows=rows,
                donor_eligible=False,indirect_reference_completeness_claimed=False)


def restore_parent(root=ROOT):
    import pr16_weather_bubble_receipt as previous
    raw = regular(root,MEASUREMENT)
    cp = measurement(raw);sources(cp,root)
    audit = previous.restore_parent(root)
    delta = read(regular(root,EVIDENCE+'/reference-chain.json'))
    full = materialize(audit,delta,raw)
    need(exact(read(regular(root,EVIDENCE+'/unknown-frontier.json')),frontier(full)), '保存frontier全89行')
    receipt = read(regular(root,REPORT))
    for key, value in dict(delta_identity=identity(encode(delta)),full_audit_identity=identity(previous.previous.canonical(full)),
                           unknown_identity=identity(encode(frontier(full))),classified=785,unclassified=89,donor_safe_bytes=0).items():
        need(exact(receipt.get(key),value), '保存receipt '+key)
    need(receipt['measurement_actions']['conclusion'] == 'success' and receipt['measurement_actions']['run_id'] == RUN,
         '成功測定runの受領')
    for name, meta in receipt['receipt_code_bindings'].items():
        need(exact(identity(regular(root,name)),meta), '受領器source不変: '+name)
    return full


if __name__ == '__main__':
    full = restore_parent()
    print(json.dumps(dict(status='PASS_SAVED_FOREST_785_89',classified=full['classified'],unclassified=full['unclassified'],
                          donor_safe_bytes=0,measurement_replays=0,rom_reconstructions=0,native_processes=0),sort_keys=True))
