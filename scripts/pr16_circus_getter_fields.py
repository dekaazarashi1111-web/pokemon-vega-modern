#!/usr/bin/env python3
"""Circus getterのVar ID/field index混同のみ修復。旧ARM再compile/30勝再走なし。"""
from __future__ import annotations
import hashlib
import json
import re
import struct
from pathlib import Path
import pr16_circus_getter_abi as g

ROOT = Path(__file__).resolve().parents[1]
TASK = 'USER-20260920-CIRCUS-GETTER-FIELDS'
BASE_HEAD = '27c1556ddeabb06b652e64ab937d68c3f0105540'
RUNTIME = 'overlays/circus_streak/circus_streak_runtime.c'
FIXTURE = 'tests/fixtures/pr16_circus_getter_fields.json'
SELF = 'scripts/pr16_circus_getter_fields.py'
TEST = 'tests/test_pr16_circus_getter_fields.py'
WORKFLOW = '.github/workflows/pr16-circus-getter-fields.yml'
FILES = (SELF, TEST, FIXTURE, WORKFLOW, RUNTIME)
GETTER = 0x09FF58DC
LENGTH = 224
STATE_GET = 0x091269B8
# (PC-relative load, literal address, old Var ID, typed field index, name).
FIELDS = ((0x09FF58EC,0x09FF5998,0x403A,0,'NUMBER'),
          (0x09FF590C,0x09FF59A0,0x5017,3,'BATTLE_TYPE'),
          (0x09FF593A,0x09FF59A8,0x5018,4,'TIER'),
          (0x09FF594E,0x09FF59AC,0x5015,1,'PARTY_SIZE'),
          (0x09FF5962,0x09FF59B0,0x5016,2,'LEVEL'))
need = g.need


def fixture():
    return json.loads((ROOT/FIXTURE).read_text())


def repair_getter(raw):
    """命令も分岐も変更せず、確認した５literalだけを置換。二重適用は拒否。"""
    expected = fixture()['getter']
    need(g.identity(raw) == expected['identity'] and len(raw) == LENGTH, 'getter preimage identity')
    out = bytearray(raw); rows = []
    for pc, address, old, field, name in FIELDS:
        instruction = struct.unpack_from('<H', raw, pc-GETTER)[0]
        need(instruction & 0xff00 == 0x4800, 'expected LDR r0 literal')
        need(((pc+4)&~3)+4*(instruction&255) == address, 'PC-relative literal owner')
        at = address-GETTER
        need(struct.unpack_from('<I',raw,at)[0] == old and 0 <= field <= 10, 'typed field/preimage')
        before,after = struct.pack('<I',old),struct.pack('<I',field)
        out[at:at+4] = after
        rows.append(dict(offset=address-g.BASE,before=before.hex(),after=after.hex(),
                         load_pc=pc,field=name,old_var_id=old,field_index=field))
    rollback = bytearray(out)
    for row in rows:
        at=row['offset']+g.BASE-GETTER;rollback[at:at+4]=bytes.fromhex(row['before'])
    need(bytes(rollback)==raw, 'getter rollback')
    return bytes(out),rows


def repaired_source(source):
    anchor='EXPORT uint16_t CircusStreakRuntimeGet('
    need(source.count(anchor)==1, 'getter source boundary')
    start=source.index(anchor);end=source.index('\nEXPORT ',start+len(anchor))
    body=source[start:end]
    for _,_,old,field,name in FIELDS:
        before=f'STATE_GET(0x{old:04X}u)'
        need(body.count(before)==1, 'source Var ID owner: '+name)
        body=body.replace(before,f'STATE_GET(CIRCUS_FIELD_{name})')
    enum=('/* VegaFacilityStateGetはVarGetではなく、T06の0..10 field ABI。 */\n'
          'enum CircusFacilityStateField {\n'
          '    CIRCUS_FIELD_NUMBER = 0, CIRCUS_FIELD_PARTY_SIZE = 1,\n'
          '    CIRCUS_FIELD_LEVEL = 2, CIRCUS_FIELD_BATTLE_TYPE = 3, CIRCUS_FIELD_TIER = 4\n};\n\n')
    return source[:start]+enum+body+source[end:]


def build(parent, meta):
    import pr16_circus_getter_followup as p
    from pr16_bp_party_retention_successor import existing_requests
    from tools.rom_allocator import build_allocation_report_from_csv
    middle, proof = p.build(parent,meta)  # 既受入の引数保持中継だけを再配置、compileなし。
    f=fixture();state=parent[STATE_GET-g.BASE:STATE_GET-g.BASE+256]
    need(g.identity(state)==f['state_get']['identity'] and state[:12].hex()=='70b504000a2801d9002070bd',
         'typed state API compiled bound')
    raw=middle[GETTER-g.BASE:GETTER-g.BASE+LENGTH]
    fixed,patches=repair_getter(raw)
    need((fixed,patches)==repair_getter(raw), 'independent literal assembly')
    candidate=bytearray(middle);candidate[GETTER-g.BASE:GETTER-g.BASE+LENGTH]=fixed;candidate=bytes(candidate)
    requests=existing_requests(proof['allocation']);changed=[]
    for row,request in zip(proof['allocation']['allocations'],requests):
        a,z=row['start'],row['end_exclusive']
        if candidate[a:z]!=middle[a:z]:
            need(row['name']=='pr16_circus_streak_runtime' and a<=GETTER-g.BASE
                 and GETTER-g.BASE+LENGTH<=z,'getter allocation owner')
            request['content_sha256']=g.identity(candidate[a:z])['sha256'];changed.append(row['name'])
    need(changed==['pr16_circus_streak_runtime'],'exactly one getter runtime owner')
    allocation=build_allocation_report_from_csv(ROOT/'config/rom_regions.csv',requests)
    need(allocation['summaries']['overlap_count']==0,'field repair overlap')
    for row in allocation['allocations']:
        need(g.identity(candidate[row['start']:row['end_exclusive']])['sha256']==row['content_sha256'],
             'field repair allocation content')
    proof['patches']+=patches
    rollback=bytearray(candidate)
    for row in proof['patches']:
        at=row['offset'];rollback[at:at+len(bytes.fromhex(row['before']))]=bytes.fromhex(row['before'])
    need(bytes(rollback)==parent,'whole-ROM rollback to accepted parent')
    proof.update(candidate=g.identity(candidate),allocation=allocation,
        changed_prior_allocations=proof['changed_prior_allocations']+changed,
        old_getter_runtime_unchanged=False,getter_instructions_unchanged=True,
        typed_field_repair=dict(original_failure_run=35500143124,field_patches=patches,
            getter_before=g.identity(raw),getter_after=g.identity(fixed),state_api=g.identity(state),
            instruction_bytes_changed=0,save_owner_changed=False,legacy_fallback_unchanged=True,
            source_mapping='scripts/build_battle_core.py: enum VegaFacilityStateField'))
    return candidate,proof


def pipeline():
    import pr16_circus_getter_followup as p
    return p,p.b


def checkpoint(value, phase):
    import os,subprocess
    from datetime import datetime,timezone
    p,b=pipeline();head=b.scope();state=b.resume.validate(ROOT);backlog=b.load(b.resume.BACKLOG)
    need(state['latest_native_run']==34946969126 and not state['release_ready'],'formal BP/release boundary')
    row=next(x for x in backlog['remaining_conditions'] if x['id']=='PHYSICAL_CIRCUS_ADMISSION')
    need(row['success_evidence'] is None and not row.get('complete'),'formal Circus boundary')
    rid=int(os.environ['GITHUB_RUN_ID']);good=value.get('native_verified') is True
    value.update(recording_run=rid,recording_source_head=head)
    if good:
        stop='getterの５つのfield indexを修復。真正Save30から自然getter30・正規抑制抽選/自然callee・帰還・通常Save/fresh Continueを検証。完了Actions/画面照合と正式Circus受入は未完。'
        nxt='このrunの完了Actions・原本・画面を照合し正式Circus受入へ接続する。native/30勝prefix/旧ARMを重複実行しない。'
    elif phase=='START':
        stop='APIへ旧Var IDを渡すgetterの原因を固定ROM/型定義で確定。命令/分岐/Save ABIを変えず５literalを修復する契約を検証。新nativeは真正Save30 cacheからだけ起動する。'
        nxt='進行中のgetter fields runのみ確認。最初の未達だけ修復し、30勝prefix/旧builder/ARM再compileを行わない。'
    else:
        stop='getter field修復の実停止を保存。未観測を成功にしない。'+str(value.get('failures',[]))
        nxt='pr16_circus_getter_followup.jsonの最初の未達のみ修復。真正Save30 cacheから継続し、受入済み30勝/ABI/他施設を重複実行しない。'
    state['circus_getter_followup']=dict(path=p.REPORT,run_id=rid,classification=value['classification'],candidate=value['candidate'])
    state['bp']['current_stop']=state['source_change_review_ja']=stop
    state['bp']['next_step']=state['next_action']['goal_ja']=nxt
    state['next_action']['id']='CIRCUS_GETTER_FIELDS_RECEIPT' if good else 'CIRCUS_GETTER_FIELDS_NATIVE'
    state['next_action']['read_paths']=[p.REPORT,*FILES,'tools/mgba_pr16_circus_getter_trace.h',b.resume.BACKLOG]
    state['observed_head']=head;state['observed_date_jst']='2026-09-20'
    state['observed_head_semantics']='記録直前のremote HEAD。新candidate/実行数はgetter report、旧30勝受入は旧candidateのまま。'
    state['observed_head_checks']=dict(scope_head=head,runs=value['predecessor_checks'],reason_ja='先行Actions完了を実API照合。この記録中runの最終状態はreceiptで確認する。')
    state['pending_runs']=[dict(run_id=rid,tested_head=value['source_head'],status='in_progress',scope='circus-getter-fields')]
    state['session_execution_summary']={k:value.get(k,0) for k in ('new_emulator_processes','arm_compiles','arm_links','accepted_standalone_replays','prefix_wins_reexecuted')}
    state['session_execution_summary']['scope_ja']='旧ABI20契約/30勝原本を継承。新field契約のみ追加。既存中継8byte/新tail12byte/５literal20byteだけ。'
    note='getter field repair runを最優先確認。APIは0..10 index、旧Var IDではない。真正Save30限定、30勝prefix/旧ARM/64抽選反復禁止。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    row['getter_checkpoint']=p.REPORT;row['resume']=nxt
    prefix=f'evidence/pr16_circus_getter/{rid}/';evidence={}
    for path in sorted((p.OUT/'execution').rglob('*')):
        if not path.is_file() or path.suffix not in ('.json','.c','.h','.stdout','.stderr'):continue
        name=prefix+'execution/'+path.relative_to(p.OUT/'execution').as_posix()
        raw=path.read_bytes();b.write(name,raw);evidence[name]=b.identity(raw)
    value['text_evidence']=evidence;immutable=prefix+phase.lower()+'.json'
    b.write(p.REPORT,b.stable(value));b.write(immutable,b.stable(value));b.write(b.resume.BACKLOG,b.stable(backlog))
    for name in (*FILES,p.REPORT,immutable,*evidence,b.resume.BACKLOG):
        state['source_bindings'][name]=b.identity((ROOT/name).read_bytes())
    state['logs_synchronized']=state['p08_resume_synchronized']=True
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    for label,args in [('resume',[__import__('sys').executable,'-m','unittest','discover','-s','tests','-p','test_pr16_resume.py','-v']),('task-graph',[__import__('sys').executable,'scripts/validate_task_graph.py'])]:
        raw,err,proc=b.capture(args,label+'-'+phase);need(b.exited(proc)==0,label+' failed')
    stamp=datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths=[*FILES,p.REPORT,immutable,b.resume.STATE,b.resume.DOC,b.resume.BACKLOG,*evidence,*b.LOGS]
    entry=(f'\n\n## {stamp} — {TASK}-{phase}\n- Timestamp: {stamp}\n- Task: {TASK} / getter field ABI修復\n'
           f'- Status: {"DONE" if good else "STOPPED"}（正式Circus/P08受入は別）\n- Version: pr16-circus-getter-fields-v1\n'
           '- Summary: '+stop+'\n- Files changed: '+', '.join(paths)+'\n'
           f'- Verify: 新field契約{value["host_tests"]["tests_run"]}件PASS、resume/task graph、index差分private guard、diff check。旧20 ABI契約再実行0。native結果はreport。\n'
           '- Commit: この記録を含む同branch非force commit。自己SHAはreceipt/remoteで照合。\n'
           '- Network: GitHub先行run35500143124 failure/35502970203採取failure/35503126098採取successを照合。検索語VegaFacilityStateGet/CircusStreakRuntimeGet。固定build_battle_core.pyとrom_bridge.cが根拠。新規外部source導入なし、host libmgba依存のみ。ROM/save/cacheはGit/artifactへ追加しない。\n'
           '- Next: '+nxt+'\n')
    for name in b.LOGS:
        path=ROOT/name;need(f'{TASK}-{phase}\n' not in path.read_text(),'duplicate phase log')
        with path.open('a') as stream:stream.write(entry)
    subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True)
    changed=set(b.command('git','diff','--cached','--name-only',head).splitlines());need(changed and changed<=set(paths),'stage scope')
    import pr16_ring_compiled_record as guard
    guard.BASE,guard.OUT,guard.ALLOWED=head,p.OUT,changed;guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': '+phase+' 型付きfield・原本・固定引継ぎ・両ログ'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    committed=b.scope();need(not b.command('git','status','--porcelain','--untracked-files=no'),'dirty after push')
    (p.OUT/('receipt-'+phase+'.json')).write_bytes(b.stable(dict(task=TASK,phase=phase,commit=committed,source_head=head,run_id=rid,non_force_push=True)))
    print('RESULT='+('DONE' if good else 'STOPPED')+' TASK='+TASK+' VERIFY=PASS COMMIT='+committed)


def prepare():
    import io,os,subprocess,sys,zipfile
    p,b=pipeline();head=b.scope();p.OUT.mkdir(parents=True,exist_ok=True)
    old=b.load(p.REPORT);state=b.resume.validate(ROOT)
    need(old['recording_run']==35500143124 and not old['native_verified']
         and old['getter_calls'][0]['result']==0 and old['getter_calls'][0]['owner_current']==30,
         'only observed getter-zero stop may resume')
    modified={SELF,TEST,FIXTURE,WORKFLOW}
    need(set(b.command('git','diff','--name-only',BASE_HEAD,head).splitlines())==modified,'unreviewed change scope')
    checks=[]
    for rid,sha,conclusion in ((35500143124,'5b600c1362bb3db1d4af4a532395b3589b8c6b38','failure'),
                              (35502970203,'39fef638dd532a79a234f91509713f3890437d6b','failure'),
                              (35503126098,BASE_HEAD,'success')):
        run=b.api('actions/runs/'+str(rid))
        need(run['head_sha']==sha and run['status']=='completed' and run['conclusion']==conclusion,'predecessor still active or changed')
        checks.append(dict(id=rid,head_sha=sha,status='completed',conclusion=conclusion))
    artifact=b.api('actions/artifacts/10600794915')
    archive=dict(size=221044,sha256='5487e5e02040d6f07714a85ae47b92844883445cc1831190085bdca1565dbaee')
    need(artifact['workflow_run']['id']==35500143124 and not artifact['expired']
         and artifact['digest']=='sha256:'+archive['sha256'],'getter-zero artifact identity')
    raw=subprocess.check_output(['gh','api','repos/'+b.REPO+'/actions/artifacts/10600794915/zip'],cwd=ROOT)
    need(b.identity(raw)==archive,'getter-zero archive bytes')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        original=json.loads(z.read('native-result.json'))
        need(original['getter_calls']==old['getter_calls'] and original['failures']==old['failures'],'getter-zero original drift')
    source=(ROOT/RUNTIME).read_text();need(b.identity(source.encode())==state['source_bindings'][RUNTIME],'runtime source drift')
    (ROOT/RUNTIME).write_text(repaired_source(source))
    for name in FILES:state['source_bindings'][name]=b.identity((ROOT/name).read_bytes())
    b.write(b.resume.STATE,b.stable(state));b.write(b.resume.DOC,b.resume.render(state).encode());b.resume.validate(ROOT)
    raw,err,proc=b.capture([sys.executable,'-m','unittest','discover','-s','tests','-p',Path(TEST).name,'-v'],'field-contracts')
    need(b.exited(proc)==0 and b'\nOK\n' in err,'new field contracts failed')
    count=int(re.search(rb'Ran (\d+) tests',err)[1])
    value=dict(schema_version=1,task=TASK,classification='CIRCUS_GETTER_FIELDS_IMPLEMENTED_NATIVE_OPEN',
        source_head=head,predecessor_checks=checks,original_failure=old['original_failure'],original=p.previous.original(),
        previous_attempt=dict(run_id=35500143124,conclusion='failure',getter_calls=old['getter_calls'],archive=archive,
                              immutable='evidence/pr16_circus_getter/35500143124/finish.json'),
        inherited_abi_tests=old['host_tests'],host_tests=dict(tests_run=count,failures=0,errors=0,skips=0,successful=True),
        sources={name:b.identity((ROOT/name).read_bytes()) for name in FILES},candidate=g.PARENT,
        new_emulator_processes=0,arm_compiles=0,arm_links=0,accepted_standalone_replays=0,prefix_wins_reexecuted=0,
        rom_changes=0,native_verified=False,physical_admission_accepted=False,suppression_accepted=False,
        release_ready=False,visual_review_completed=False,failures=[])
    checkpoint(value,'START')


def main(command):
    p,b=pipeline()
    if command=='prepare':prepare()
    elif command=='native':
        # p.nativeが呼ぶbuildだけを差し替える。旧buildは別名で保持し再帰させない。
        original=p.build
        def wrapped(parent,meta):
            p.build=original
            try:return build(parent,meta)
            finally:p.build=wrapped
        p.build=wrapped;p.native()
    elif command=='finish':
        path=p.OUT/'native-result.json';value=json.loads(path.read_text()) if path.exists() else b.load(p.REPORT)
        if not path.exists():value['failures'].append(dict(stage='setup',error='cache/dependency unavailable; no bootstrap'))
        checkpoint(value,'FINISH')
    elif command=='pack':p.pack()
    elif command=='result':
        value=b.load(p.REPORT);need(value['native_verified'] and not value['failures'],'suppression remains open')
    else:raise ValueError('unknown command')


if __name__=='__main__':
    import sys
    need(len(sys.argv)==2,'command required');main(sys.argv[1])
