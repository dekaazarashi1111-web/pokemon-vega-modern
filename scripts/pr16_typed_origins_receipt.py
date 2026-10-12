#!/usr/bin/env python3
"""保存済み二originを読取専用で正式受領する。ROM/reader/旧試験は実行しない。"""
from __future__ import annotations
import collections
import copy
import io
from pathlib import Path
import stat
import zipfile
from pr16_forest_wallpaper_receipt import need, exact, identity, encode, read, regular

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
SOURCE = '85f9700fe8725322eb28c5bb1be8ec3af739c50b'
MEASURED = 'd71ce11174a0410dd0d0bb7bfcebf104d14bfbc2'
RUN, JOB, ARTIFACT = 38092235316, 114330857734, 11683989837
WORKFLOW = '.github/workflows/pr16-typed-origins.yml'
CHECKPOINT = 'content/modernization/pr16_typed_origins_checkpoint.json'
PROOF = 'content/modernization/pr16_typed_origins_evidence/reader-profiles.json'
REPORT = 'content/modernization/pr16_typed_origins_receipt.json'
EVIDENCE = 'content/modernization/pr16_typed_origins_receipt_evidence'
NAMESPACE = 'typed_origins_reference_chain'
HITS = (0x080A006F, 0x081C96E9)
KINDS = ('literal_u32_gpu_and_thumb_callback_cross_field', 'thumb_bl_tail_and_add_head')
CANDIDATE = dict(size=33554432, sha256='0641af703570747e9b8e0754b4e8fad2f78bcc7f733743242214316cededd583')
PARENT_ID = dict(size=5408731, sha256='f88d65c235eda330aef618776bff97037d5ca2c4c9fbea53798217dcb5bda669')
ZIP_ID = dict(size=107962, sha256='910d4829d1063f141e3d9ed4f964d1d177e266251ae2621579d32ee9c2d36567')
FILES = {
    'attempt.json': dict(size=165, sha256='154951dc47db6755b84aa2af1f4cc7e52623f79a7761ecad563d7c6a5d00a66c'),
    'actions-completion.json': dict(size=1923, sha256='52f31c6a3ba5f07581b53b8c3604ca56fb19c2d6305972eb2e112f7334860701'),
    'bounded-actions-completion.json': dict(size=1923, sha256='52f31c6a3ba5f07581b53b8c3604ca56fb19c2d6305972eb2e112f7334860701'),
    'bounded-discovery.json': dict(size=74666, sha256='b2d1495a31c4315730edc74e07a8c1fd32c947d0f2cd616b027339e47cb34df6'),
    'pr16_typed_origins_checkpoint.json': dict(size=6878, sha256='eee0837aa8f925a1b150c687a4124bee91710dc4c9eff03b3e6e6e183f2d30ea'),
    'reader-profiles.json': dict(size=19614, sha256='761b8488dcdfcdea82373f050356f247297befecf7fee5e4c871029339182303'),
    'reader-tests.txt': dict(size=1581, sha256='c5c0145603a96e84cf45f26640549f81724b05d56f37b257a5e74f1586e8e6d9'),
    'result.json': dict(size=914, sha256='9b5fce920f312383b52c705a32b0e8b2805ecacc823f416d999d955216dfa000'),
    'scoped-context.zip': dict(size=86748, sha256='be0d09c1cc756833c55ba1a68b266652c239975afaa94463a6bf447cd5b7e15f'),
}
CLAIMS = dict(accepted_measurement_replays=0, accepted_test_reruns=0,
    actual_gpu_flush_or_irq_executed=False, actual_runtime_execution_observed=False,
    all_alternative_readers_excluded=False, conditional_finite_reader_only=True,
    donor_eligible=False, donor_leased=False, donor_safe_bytes=0,
    floating_point_callee_body_executed=False, formal_classification_accepted=False,
    formal_rom_changed=False, formal_save_changed=False,
    indirect_reference_completeness_claimed=False, native_processes=0,
    natural_entry_reachability_proven=False)
STEP_NAMES = [(1,'Set up job'), (2,'Run actions/checkout@v4'), (3,'Run actions/setup-python@v5'),
    (4,'Install scoped ARM reconstruction tools'),
    (5,'Execute new typed origin readers and receive prior bounds without replay'),
    (6,'Run actions/upload-artifact@v4'), (11,'Post Run actions/setup-python@v5'),
    (12,'Post Run actions/checkout@v4'), (13,'Complete job')]
CONTEXT_NAMES = {
    '.github/workflows/pr16-typed-origins.yml',
    'content/modernization/pr16_first_origin_evidence/actions-completion.json',
    'content/modernization/pr16_forest_wallpaper_receipt_evidence/reference-chain.json',
    'content/modernization/pr16_forest_wallpaper_receipt_evidence/unknown-frontier.json',
    CHECKPOINT, PROOF, 'content/modernization/pr16_typed_origins_evidence/bounded-discovery.json',
    'content/modernization/pr16_wiki_first_execution_plan.json',
    'docs/PR16_FOREST_WALLPAPER_ASSET_JA.md',
    'scripts/pr16_dex_hof_lifetime_root.py', 'scripts/pr16_dex_hof_runtime_sprite.py',
    'scripts/pr16_forest_wallpaper_receipt.py', 'scripts/pr16_typed_origins.py',
    'scripts/pr16_typed_origins_actions.py', 'scripts/pr16_weather_bubble_receipt.py',
    'tests/test_pr16_typed_origins.py',
}


def intervals(rows):
    need(type(rows) is list and all(type(r['address']) is int and type(r['size']) is int and
         r['size'] in (2, 4) and r['address'] % 2 == 0 for r in rows), '完全な整列命令/field範囲')
    return [(r['address'], r['size']) for r in rows]


def coverage(address, spans):
    """対象4byteを覆う相対offsetと長さ。BLの先頭/末尾を取り違えない。"""
    out = []
    for start, size in spans:
        lo, hi = max(address, start), min(address + 4, start + size)
        if lo < hi:
            out.append(dict(container_address=start, container_size=size,
                            container_offset=lo-start, hit_offset=lo-address, size=hi-lo))
    need(sorted(i for r in out for i in range(r['hit_offset'], r['hit_offset']+r['size'])) == list(range(4)),
         '対象4byteの重複なし完全被覆')
    return out


def profiles(p):
    """固定原本hashに加え、型・実consumer・停止点・限定条件を独立に検査する。"""
    need(exact(p['candidate'], CANDIDATE) and exact(p['claims'], CLAIMS), '候補/非主張')
    rows = p['profiles']; need(type(rows) is list and len(rows) == 3, '閉3profile')
    fields = p['literal_fields']
    need(exact([(r['address']) for r in fields], [0x080A006C, 0x080A0070]) and
         exact([r['size'] for r in fields], [4,4]) and
         exact([r['value'] for r in fields], [0x1111,0x0809FED5]), 'aligned literal二field')
    need(exact([r['address'] for r in p['hits']], list(HITS)) and
         exact([r['size'] for r in p['hits']], [4,4]), '閉二hit')
    for i, row in enumerate(rows):
        need(exact(row['claims'], CLAIMS), 'profile非主張')
        spans = intervals(row['instructions'])
        need(len(spans) == len(set(spans)), '命令重複禁止')
        intervals(row['reads'])
        if i == 2:
            continue
        need(type(row['field_index']) is int and row['field_index'] == i and
             exact(row['literal'],fields[i]), 'field順序/identity')
        need(row['status'] == 'PASS_CONDITIONAL_ACTUAL_LITERAL_READER' and
             type(row['caller_condition']) is str and len(row['caller_condition']) > 20 and
             type(row['consumer_condition']) is str and len(row['consumer_condition']) > 20, '限定caller/consumer')
        entry, call, target, reg, stop, store, pc = (
            (0x0809FFF4,0x0809FFF8,0x08000A38,1,'first_actual_u16_buffer_store',
             dict(address=0x03000048,size=2,value=0x1111),0x08000A4A) if i == 0 else
            (0x080A0022,0x080A0024,0x080006F4,0,'actual_callback_setter_return',
             dict(address=0x0300313C,size=4,value=0x0809FED5),0x080006F6))
        need(exact(row['call'],dict(address=call,target=target)) and row['stop']==stop and
             exact(row['store'],store) and exact(row['store_pc'],pc), '実call/typed store/stop')
        need(exact([row['load'][k] for k in ('entry','load','pool','register')],
                   [entry,entry,fields[i]['address'],reg]), '実LDR/argument register')
        need(exact(row['arguments'],[72,0x1111] if i==0 else [0x0809FED5,None]), '実引数')
        need((entry,2) in spans and (call,4) in spans and (pc,2) in spans and
             (fields[i]['address'],4) in intervals(row['reads']), '実LDR/BL/store fetch')
        need(any(exact(r, {k:v for k,v in fields[i].items() if k!='value'}) for r in row['reads']), 'literal全hash read')
    r = rows[2]
    need(r['status']=='PASS_CONDITIONAL_ACTUAL_THUMB_READER' and
         exact([r['entry'],r['stop'],r['input_bits']], [0x081C96DC,0x081C96EE,[0,0]]) and
         type(r['conditions_ja']) is str and len(r['conditions_ja']) > 30, 'Thumb入口/停止/同期条件')
    need(exact(r['call'],dict(address=0x081C96E8,target=0x081C94B8)) and
         exact(r['opaque_call'],dict(arguments=[0x03007EF0,0x03007EC0],return_pc=0x081C96EC,
                                    sp=0x03007EC0,target=0x081C94B8)), '実BL/callee正常帰還境界')
    expected = [(a,2) for a in range(0x081C96DC,0x081C96E8,2)] + [(0x081C96E8,4),(0x081C96EC,2)]
    need(intervals(r['instructions'])==expected and
         intervals(r['reads'])==[(a,2) for a in range(0x081C96DC,0x081C96EE,2)], '実完全BL幅/直後ADD fetch')
    need(exact(p['public_symbol_rows']['__subsf3']['address'],r['entry']) and
         exact(p['public_symbol_rows']['gMain']['address']+12,rows[1]['store']['address']) and
         exact(p['public_symbol_rows']['sGpuRegBuffer']['address']+72,rows[0]['store']['address']), '固定symbol/field offset')
    return [coverage(HITS[0],[(f['address'],f['size']) for f in fields]),
            coverage(HITS[1],[(0x081C96E8,4),(0x081C96EC,2)])]


def measurement(cp_raw, proof_raw):
    need(exact(identity(cp_raw),FILES['pr16_typed_origins_checkpoint.json']) and
         exact(identity(proof_raw),FILES['reader-profiles.json']), '測定原本全identity')
    cp, p = read(cp_raw), read(proof_raw)
    need(cp['source_head']==SOURCE and exact(cp['actions_run_id'],RUN) and
         exact(cp['claims'],CLAIMS) and cp['actions_completion_confirmed'] is False, '測定source/未受領履歴')
    need(exact([cp['new_profiles'],cp['new_unit_tests'],cp['rom_reconstructions']], [3,20,1]) and
         exact(cp['proof_identity'],identity(proof_raw)) and cp['proof_path']==PROOF, '成功測定だけ継承')
    return cp,p,profiles(p)


def zip_members(raw, expected):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        rows=z.infolist()
        need(len(rows)==len(expected) and {r.filename for r in rows}==set(expected), '閉member/重複・欠落禁止')
        for r in rows:
            path=Path(r.filename)
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in r.filename and
                 path.as_posix()==r.filename and not r.is_dir() and not stat.S_ISLNK(r.external_attr>>16) and
                 not r.flag_bits&1 and 0<=r.file_size<=2_000_000, 'ZIPの通常有限text境界')
        return {r.filename:z.read(r) for r in rows}


def unpack(raw):
    need(exact(identity(raw),ZIP_ID), '独立取得済みZIP全identity')
    files=zip_members(raw,FILES)
    need(all(exact(identity(files[n]),meta) for n,meta in FILES.items()), '全9member hash')
    measurement(files['pr16_typed_origins_checkpoint.json'],files['reader-profiles.json'])
    result=read(files['result.json'])
    need(exact([result[k] for k in ('status','source_head','commit','actions_run_id','new_unit_tests','new_profiles')],
               ['DONE',SOURCE,MEASURED,RUN,20,3]) and exact(result['claims'],CLAIMS), '原本公開commit/result')
    tests=files['reader-tests.txt'].decode(); rows=[r for r in tests.splitlines() if r.startswith('test_')]
    need(len(rows)==len(set(rows))==20 and all(r.endswith(' ... ok') for r in rows) and tests.endswith('\nOK\n'), '旧20試験の成功記録だけを受領')
    context=zip_members(files['scoped-context.zip'],CONTEXT_NAMES)
    return files,context


def metadata(run,jobs,artifact):
    for k,v in dict(id=RUN,head_sha=SOURCE,head_branch=BRANCH,path=WORKFLOW,event='push',run_attempt=1,
                    status='completed',conclusion='success').items(): need(exact(run.get(k),v),'run '+k)
    need(run['repository']['full_name']==run['head_repository']['full_name']==REPO,'同repo/fork拒否')
    need(exact(jobs['total_count'],1) and len(jobs['jobs'])==1,'全job')
    job=jobs['jobs'][0]
    for k,v in dict(id=JOB,run_id=RUN,head_sha=SOURCE,name='typed-origins',status='completed',conclusion='success').items():
        need(exact(job.get(k),v),'job '+k)
    steps=[{k:s[k] for k in ('number','name','status','conclusion')} for s in job['steps']]
    need(exact(steps,[dict(number=n,name=s,status='completed',conclusion='success') for n,s in STEP_NAMES]),'全9step/順序/skip拒否')
    for k,v in dict(id=ARTIFACT,name='pr16-typed-origins-public-text',size_in_bytes=ZIP_ID['size'],
                    expired=False,digest='sha256:'+ZIP_ID['sha256']).items(): need(exact(artifact.get(k),v),'artifact '+k)
    need(exact(artifact['workflow_run'],dict(id=RUN,repository_id=1358127462,head_repository_id=1358127462,
                                            head_branch=BRANCH,head_sha=SOURCE)),'artifact同source/run')
    return dict(run_id=RUN,job_id=JOB,artifact_id=ARTIFACT,source_head=SOURCE,measurement_commit=MEASURED,
                status='completed',conclusion='success',run_attempt=1,steps=steps,zip_identity=copy.deepcopy(ZIP_ID))


def sources(cp,root=ROOT):
    bindings={CHECKPOINT:FILES['pr16_typed_origins_checkpoint.json'],PROOF:FILES['reader-profiles.json']}
    for key in ('source_bindings','preserved_inputs'):
        for name,meta in cp[key].items():
            need(name not in bindings or exact(bindings[name],meta),'source binding競合')
            bindings[name]=meta
    for name,meta in bindings.items(): need(exact(identity(regular(root,name)),meta),'測定source/旧原本不変: '+name)
    return bindings


def build(parent_raw,cp_raw,proof_raw):
    need(exact(identity(parent_raw),PARENT_ID),'正式785親全identity/二重適用拒否')
    parent=read(parent_raw); cp,p,cover=measurement(cp_raw,proof_raw)
    need(exact([parent['classified'],parent['unclassified'],len(parent['hits'])],[785,89,874]),'正式親件数')
    need(len({h['address'] for h in parent['hits']})==874 and NAMESPACE not in parent,'親重複/再適用拒否')
    changes=[]; witnesses=[]
    for i,address in enumerate(HITS):
        matches=[h for h in parent['hits'] if h['address']==address]
        need(len(matches)==1,'唯一の対象origin')
        h=matches[0]
        need(h['accepted'] is False and h['classification']=='UNCLASSIFIED' and h['owner_candidates']==[] and
             exact({k:h[k] for k in ('address','size','sha256')},p['hits'][i]),'未知hitの全identity')
        changed=copy.deepcopy(h)
        changed.update(accepted=True,classification='FALSE_POSITIVE_TYPED_REFERENCE_'+KINDS[i].upper(),
                       evidence=[{NAMESPACE+'_witness':i}])
        changes.append(changed)
        chosen=p['profiles'][:2] if i==0 else p['profiles'][2:]
        witnesses.append(dict(id=i,address=address,size=4,kind=KINDS[i],coverage=cover[i],
            source_head=SOURCE,run_id=RUN,profile_identities=[identity(encode(r)) for r in chosen],
            conditions=[{k:v for k,v in r.items() if k in ('caller_condition','consumer_condition','conditions_ja','stop')}
                        for r in chosen]))
    claims=dict(CLAIMS,formal_classification_accepted=True)
    return dict(schema_version=1,status='ACCEPTED_TWO_CONDITIONAL_TYPED_ORIGINS',namespace=NAMESPACE,
        parent_audit_identity=copy.deepcopy(PARENT_ID),candidate=copy.deepcopy(CANDIDATE),
        measurement_path=CHECKPOINT,measurement_identity=identity(cp_raw),proof_path=PROOF,proof_identity=identity(proof_raw),
        inherited_classified=785,inherited_unclassified=89,inherited_candidates=874,classified=787,unclassified=87,
        newly_classified=2,changes=changes,witnesses=witnesses,claims=claims,donor_safe_bytes=0,
        native_processes=0,rom_reconstructions=0,measurement_replays=0,old_scope_test_reruns=0)


def materialize(parent_raw,delta,cp_raw,proof_raw):
    need(exact(delta,build(parent_raw,cp_raw,proof_raw)),'閉二件差分/条件/counter/claim改作拒否')
    parent=read(parent_raw); full=copy.deepcopy(parent); replacements={h['address']:h for h in delta['changes']}
    full['hits']=[copy.deepcopy(replacements.get(h['address'],h)) for h in parent['hits']]
    full.update(classified=787,unclassified=87,classifications=dict(collections.Counter(h['classification'] for h in full['hits'])))
    full[NAMESPACE]=copy.deepcopy(delta)
    need(sum(h['accepted'] is True for h in full['hits'])==787,'受入行総数')
    need(sum(not exact(a,b) for a,b in zip(parent['hits'],full['hits']))==2,'他872行不変')
    need(all(exact(v,full[k]) for k,v in parent.items() if k not in ('hits','classified','unclassified','classifications')),'全旧namespace不変')
    return full


def frontier(full):
    rows=[dict(hit=copy.deepcopy(h),owners=copy.deepcopy(h['owner_candidates'])) for h in full['hits'] if h['accepted'] is False]
    need(len(rows)==87 and all(r['owners']==[] for r in rows),'未知87行')
    return dict(candidate=copy.deepcopy(CANDIDATE),total=87,owner_unknown=0,unowned_unknown=87,rows=rows,
                donor_eligible=False,indirect_reference_completeness_claimed=False)


def restore_785_raw(root=ROOT):
    import pr16_forest_wallpaper_receipt as previous
    import pr16_weather_bubble_receipt as wire
    return wire.previous.canonical(previous.restore_parent(root))


def restore_parent(root=ROOT):
    """後続用787親。保存textの検証だけで復元し、測定/旧testsは一切呼ばない。"""
    cp_raw,proof_raw=regular(root,CHECKPOINT),regular(root,PROOF)
    cp,_,_=measurement(cp_raw,proof_raw);sources(cp,root)
    parent_raw=restore_785_raw(root); delta=read(regular(root,EVIDENCE+'/reference-chain.json'))
    full=materialize(parent_raw,delta,cp_raw,proof_raw); report=read(regular(root,REPORT))
    for k,v in dict(classified=787,unclassified=87,donor_safe_bytes=0,delta_identity=identity(encode(delta)),
                    full_audit_identity=identity(encode(full)),unknown_identity=identity(encode(frontier(full)))).items():
        need(exact(report.get(k),v),'保存正式receipt '+k)
    need(exact(read(regular(root,EVIDENCE+'/unknown-frontier.json')),frontier(full)),'保存frontier')
    need(report['measurement_actions']['run_id']==RUN and report['measurement_actions']['conclusion']=='success','測定Actions受領')
    for group in ('receipt_code_bindings','evidence_bindings'):
        for name,meta in report[group].items(): need(exact(identity(regular(root,name)),meta),'保存source/evidence: '+name)
    return full


if __name__=='__main__':
    audit=restore_parent()
    print(encode(dict(status='PASS_SAVED_TYPED_ORIGINS_787_87',classified=audit['classified'],
        unclassified=audit['unclassified'],donor_safe_bytes=0,measurement_replays=0,rom_reconstructions=0)).decode(),end='')
