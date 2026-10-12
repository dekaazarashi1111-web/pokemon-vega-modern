#!/usr/bin/env python3
"""保存済み限定測定は再走せず、現ownerとchild fetchの新しい有限scopeを実行する。"""
from __future__ import annotations
import contextlib
import datetime as dt
import io
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_berry_consumer as m
import pr16_berry_origin as b
import pr16_berry_origin_actions as old
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=b.ROOT
WORK=ROOT/'.local/pr16-berry-consumer'
PUBLIC=WORK/'public'
WF='.github/workflows/pr16-berry-consumer.yml'
CODE={WF,'scripts/pr16_berry_consumer.py','scripts/pr16_berry_consumer_actions.py',
      'tests/test_pr16_berry_consumer.py','tools/mgba_pr16_berry_consumer.c'}
EVIDENCE='content/modernization/pr16_berry_consumer_evidence'
REPORT='content/modernization/pr16_berry_consumer_checkpoint.json'
PROOFS={EVIDENCE+'/'+n for n in ('binding-completion.json','consumer-proof.json','native.json','consumer-tests.txt')}
PHASE='preflight'
ATTEMPT={'accepted_test_reruns':0,'rom_reconstructions':0,'native_processes':0,'full_rom_scans':0}
read,load,write,snapshot=old.read,old.load,old.write,old.snapshot


def public(name,value):
    (PUBLIC/name).write_bytes(b.encode(value) if isinstance(value,dict) else value)


def command(args,timeout=180):
    result=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,timeout=timeout)
    if result.returncode != 0:
        executable=Path(str(args[0])).name
        diagnostic=result.stderr.decode(errors='replace')[:12000] if executable in {'cc','native'} else ''
        diagnostic=diagnostic.replace(str(ROOT),'[workspace]')
        public('command-failure.json',{'executable':executable,'returncode':result.returncode,'stderr':diagnostic})
    b.need(result.returncode==0,'新scope command failure: '+Path(str(args[0])).name)
    return result


def receive_binding():
    done=publication.accepted_run(38099840927,'359d3fae20d5d0e25342c0e1b8daac921aa0e646',
        ['Verify new berry origin binding without accepted replay','Run actions/upload-artifact@v4'])
    item=a.fetch('actions/artifacts/11687346108')
    wanted={'size':98324,'sha256':'34127bc87ef8c9870b68dceace0e1672618720caa3f24a06693a535d1ed39610'}
    b.need(item['name']=='pr16-berry-origin-public-text' and item['expired']is False and
           item['size_in_bytes']==wanted['size'] and item['digest']=='sha256:'+wanted['sha256'] and
           item['workflow_run']['id']==done['id'],'完了binding artifact metadata')
    raw=a.fetch('actions/artifacts/11687346108/zip',binary=True);b.need(b.identity(raw)==wanted,'完了binding全ZIP')
    members=old.zip_members(raw)
    b.need(set(members)=={'attempt.json','bounded-binding.json','binding-tests.txt','pr16_berry_origin_checkpoint.json',
                         'prior-actions.json','result.json','scoped-context.zip'},'全7公開member')
    context=old.zip_members(members['scoped-context.zip'])
    b.need(len(context)==25,'全25保存text')
    for name,data in context.items():
        data.decode();b.need(b'\0'not in data and data==a.git('show',m.BASE+':'+name),'公開commit全text読戻し')
    result=m.strict(members['result.json'])
    b.need(result['commit']==m.BASE and result['new_unit_tests']==20 and result['native_processes']==0 and
           members['pr16_berry_origin_checkpoint.json']==read(old.REPORT),'限定測定原本')
    done.update(artifact={k:item[k] for k in ('id','name','digest','size_in_bytes')},published_commit=m.BASE,
        members={n:b.identity(v) for n,v in members.items()},context_bindings={n:b.identity(v) for n,v in context.items()},
        accepted_test_reruns=0,native_replays=0,candidate_reconstructions_for_receipt=0)
    return done


def new_sources():
    result={}
    for path,blob in m.HEADERS.items():
        raw=old.download('https://raw.githubusercontent.com/pret/pokefirered/'+b.SOURCE+'/'+path,100000)
        b.need(b.blob(raw)==blob,'固定struct header全blob')
        result[path]={'repository':'pret/pokefirered','commit':b.SOURCE,'git_blob':blob,**b.identity(raw)}
    s=b.SYMBOL_SOURCE
    raw=old.download('https://raw.githubusercontent.com/'+s['repository']+'/'+s['commit']+'/'+s['path'],5000000)
    b.need(b.identity(raw)=={k:s[k] for k in ('size','sha256')} and b.blob(raw)==s['git_blob'],'固定JP RAM symbol入力')
    return result,m.ram_symbols(raw)


def native(raw,saved,ram,contract):
    version=command(['dpkg-query','-W','-f=${Version}','libmgba-dev']).stdout.decode().strip()
    library=b.identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())
    b.need(version=='0.10.2+dfsg-1.1build3' and library==m.LIBRARY,'固定mGBA runtime')
    names={'TASK':'Task_BerryFixMain','INIT':'MultiBootInit','MASTER':'MultiBootStartMaster'}
    defines={}
    for short,name in names.items():
        row=saved['consumer_frontier'][name]
        defines[short+'_START']=row['region_start'];defines[short+'_END']=row['region_end_exclusive']
        b.need(b.identity(b.section(raw,0x08000000,row['region_start'],row['region_end_exclusive']-row['region_start']))==row['region_identity'],'保存実行body全identity')
    defines.update(TASKS=ram['gTasks']['address'],MB_START=ram['gMultibootStart']['address'],
        MB_SIZE=ram['gMultibootSize']['address'],PARAM=ram['gMultibootParam']['address'],BL_REL=contract['relative_bl_target'])
    image=WORK/'candidate.gba';image.write_bytes(raw);image_before=(b.identity(image.read_bytes()),image.stat().st_mtime_ns)
    exe=WORK/'native'
    args=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',ROOT/'tools/mgba_pr16_berry_consumer.c',
          *('-D'+k+'='+hex(v) for k,v in sorted(defines.items())),'-o',exe,'-lmgba']
    compiled=command(args);b.need(not compiled.stdout and not compiled.stderr,'strict compile diagnostics')
    ATTEMPT['native_processes']=1;public('attempt.json',ATTEMPT)
    process=command([exe,image],timeout=150)
    b.need(not process.stderr,'native diagnostics')
    result=m.strict(process.stdout)
    b.need((b.identity(image.read_bytes()),image.stat().st_mtime_ns)==image_before,'native入力byte/mtime不変')
    return result,{'defines':defines,'source':b.identity(read('tools/mgba_pr16_berry_consumer.c')),
                   'binary':b.identity(exe.read_bytes()),'library':library,'package_version':version,
                   'compiler':command(['cc','--version']).stdout.decode().splitlines()[0],
                   'process':{'returncode':0,'timed_out':False,'spawn_error':None},'stdout_identity':b.identity(process.stdout),
                   'input_byte_and_mtime_unchanged':True,'cases':{'host_init':3,'host_master':13,'child':2}}


def append_logs(summary,eligible):
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    text=(f'\n## {now}\n- Timestamp: {now}\n- Task: {m.TASK} / 現multiboot ownerと条件付きchild fetch\n'
          '- Version: berry-consumer-v1\n- Status: DONE（有限scope。正式分類は完了run受領後）\n'
          f'- Summary: {summary}\n- Files changed: 新consumer model/20試験/native harness/Actions、証拠JSON、固定引継ぎMD/JSON、両ログ。\n'
          '- Verify: 新20境界試験、実Task初期化3ケース、実Master境界13ケース、child fixture2ケースの有限観測、'
          '旧binding完了全7ZIP/25text、原本byte/mtime不変、task graph、最終index検査。\n'
          f'- Boundary: child全4byte命令読取の受領候補={eligible}。正式788/86・選定残7・安全容量0。'
          '自然到達/実ケーブル転送/全alias/退役・移管/保存controller/全story/実Saveは受入しない。\n'
          '- Commit: この追記を含む単親通常commit。実SHAはGit履歴とActions resultに記録。\n'
          '- Network: 同repo PR/ref/Actions/artifact GET、固定JPsymbolの新RAM名範囲と固定公開task/MultibootParam headerを確認。'
          '公開source https://github.com/pret/pokefirered/tree/'+b.SOURCE+' 。同branch非force push。\n')
    for path in old.LOGS:
        previous=read(path);b.need(('- Task: '+m.TASK+' /').encode()not in previous,'同task二重追記禁止');write(path,previous+text.encode())


def run():
    global PHASE
    b.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+old.BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同branch初回だけ')
    b.need(not WORK.exists(),'新scopeのみ');PUBLIC.mkdir(parents=True)
    head=a.git('rev-parse','HEAD').decode().strip();b.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    b.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    b.need(set(a.git('diff','--name-only',m.BASE,head).decode().splitlines())==CODE,'新5sourceだけ')
    b.need(not (ROOT/REPORT).exists(),'保存済みconsumerは再走しない')
    b.need(not a.git('ls-files','--','tools/AGENTS.md').strip(),'追加tools AGENTS読取りが必要')
    parent=load(old.REPORT);saved=load(old.EVIDENCE+'/bounded-binding.json');state=load(old.STATE)
    b.need(state['next_action']['id']=='SAVE_CAPACITY_BERRY_ORIGIN_ACTUAL_OWNER_READER' and
           saved['candidate']==b.CANDIDATE and saved['formal_classified']==788 and saved['formal_unclassified']==86,
           '現行next/親境界')
    protected=set(parent['source_bindings'])|set(parent['evidence_bindings'])|set(parent['preserved_inputs'])|{old.REPORT}
    for name,want in {**parent['source_bindings'],**parent['evidence_bindings'],**parent['preserved_inputs']}.items():
        b.need(b.identity(read(name))==want,'保存原本全identity: '+name)
    before=snapshot(protected)
    PHASE='new-consumer-tests'
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_berry_consumer.py'))
    public('consumer-tests.txt',stream.getvalue().encode())
    b.need(tests.wasSuccessful() and tests.testsRun==20 and not tests.skipped,'新consumer20試験')
    command(['python3','-B','scripts/validate_task_graph.py'])
    PHASE='receive-completed-binding-without-replay';receipt=receive_binding()
    PHASE='new-ram-owner-source-bindings';headers,ram=new_sources()
    PHASE='one-new-consumer-scope-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT=WORK/'candidate-build';reconstruction.OUT.mkdir();ATTEMPT['rom_reconstructions']=1;public('attempt.json',ATTEMPT)
    with (WORK/'private-reconstruction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):raw,cp=reconstruction.reconstruct()
    b.need(cp['candidate']==b.CANDIDATE,'候補/配置owner不変');region=b.bind_hit(raw);contract=m.instruction_contract(region)
    PHASE='actual-host-owner-and-child-fixtures';result,toolchain=native(raw,saved,ram,contract);accept=m.classify(result,contract)
    proof={'schema_version':1,**accept,'candidate':b.CANDIDATE,'saved_binding_path':old.EVIDENCE+'/bounded-binding.json',
           'saved_binding_identity':b.identity(read(old.EVIDENCE+'/bounded-binding.json')),'ram_symbols':ram,
           'public_struct_headers':headers,'public_ram_symbol_source':b.SYMBOL_SOURCE,'instruction_contract':contract,
           'native_toolchain':toolchain,'native_summary':result,'formal_classified':788,'formal_unclassified':86,
           'selected_unknown_origins':7,'formal_classification_changes':0,**ATTEMPT}
    for name,value in [('binding-completion.json',receipt),('consumer-proof.json',proof),('native.json',result),('consumer-tests.txt',stream.getvalue().encode())]:write(EVIDENCE+'/'+name,value)
    after=snapshot(PROOFS);b.need(m.strict(read(EVIDENCE+'/consumer-proof.json'))==proof and snapshot(PROOFS)==after,'保存後read-only検査')
    b.need(snapshot(protected)==before,'旧原本byte/mtime不変')
    eligible=accept['classification_eligible_after_completed_run_receipt']
    goal=('完了consumer run・全artifact・commit原本を外部受領し、保存証拠だけで0x086C51BFの条件付き命令型分類を反映する。'
          if eligible else '現multiboot ownerは実Task/実Masterで束縛済み。保存child fixtureの停止点から、0x086C51BF全4byteの実命令読取りを新scopeで結ぶ。')
    goal+='今回のbinding/consumer20試験・native/候補復元と旧受入は再走しない。正式788/86・選定残7・安全容量0。自然転送/全alias/旧owner退役/保存controller/heap/局所Saveは未完。'
    report={'schema_version':1,'task':m.TASK,**accept,'source_head':head,'candidate':b.CANDIDATE,
            'actions_run_id':int(os.environ['GITHUB_RUN_ID']),'actions_completion_confirmed':False,
            'received_binding_completion':receipt['id'],'source_bindings':{n:b.identity(read(n)) for n in sorted(CODE)},
            'evidence_bindings':{n:b.identity(read(n)) for n in sorted(PROOFS)},'preserved_inputs':{n:v[0] for n,v in before.items()},
            'new_unit_tests':20,'task_graph_passed':True,'read_only_check_passed':True,'formal_classified':788,
            'formal_unclassified':86,'selected_unknown_origins':7,'observed_head_checks':observed,'next_ja':goal,**ATTEMPT}
    write(REPORT,report)
    lane=state['owner_execution_plan']['technical_lanes']['save_capacity'];lane.update(status=accept['status'],checkpoint_path=REPORT,next_ja=goal)
    state['next_action']={'id':'SAVE_CAPACITY_BERRY_CONSUMER_COMPLETION_RECEIPT' if eligible else 'SAVE_CAPACITY_BERRY_CHILD_INSTRUCTION_FETCH',
        'goal_ja':goal,'read_paths':[old.GUIDE,REPORT,EVIDENCE+'/consumer-proof.json',EVIDENCE+'/native.json',old.PROGRESS],
        'done_ja':'実ownerと全4byte readerの完了run受領後にだけ正式分類を更新し、残件と安全容量境界を保つ。'}
    state['observed_head_checks']=observed
    state['recording']['last_execution']={k:report[k] for k in ('task','source_head','actions_run_id','actions_completion_confirmed',
        'new_unit_tests','task_graph_passed','read_only_check_passed','formal_classified','formal_unclassified','donor_safe_bytes',*ATTEMPT)}
    state['recording'].update(status=accept['status'],received_berry_binding_completion=EVIDENCE+'/binding-completion.json',
        pending_berry_consumer_run={'run_id':int(os.environ['GITHUB_RUN_ID']),'source_head':head,'report':REPORT,
                                   'status':'COMPLETION_NOT_YET_OBSERVED','replay_forbidden':True})
    state['recording'].pop('pending_berry_origin_run',None);write(old.STATE,state)
    summary=('現Taskをtask id 0/7/15から実行しasset開始・全長・masterpと状態4→5を確認。'
             '実MultiBootStartMasterで16byte丸め・下限/上限・早期/後期reset・paletteの13ケースを確認。'
             f'全bundleを同一byteでRAM配置したchild fixture2件のfetch mask={[r["fetch_mask"] for r in result["children"]]}、'
             f'全4byte読取受領候補={eligible}。ROM変更0、実Save0。')
    text=read(old.GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    b.need('## 現multiboot ownerと条件付きchild fetch'not in text,'MD二重追記禁止')
    text+='\n## 現multiboot ownerと条件付きchild fetch\n\n'+summary+'\n\n'+f'[consumer証拠](../{EVIDENCE}/consumer-proof.json) / [checkpoint](../{REPORT})。'
    text+='新consumer20試験、host16ケース、child2fixture。旧binding20試験/候補復元と旧音声受入は再走なし。正式788/86・残7・安全容量0。自然到達や実ケーブル転送は非主張。\n\n## 次の未完作業\n\n'+goal+'\n'
    write(old.GUIDE,text.encode());append_logs(summary,eligible)
    PHASE='final-index-and-nonforce-push';allowed=CODE|PROOFS|old.LOGS|{REPORT,old.STATE,old.GUIDE}
    publication.final_index(m.BASE,allowed,REPORT)
    b.need(a.git('ls-remote','origin','refs/heads/'+old.BRANCH).decode().split()[0]==head,'push前HEAD競合')
    for name in allowed:b.need(a.git('show',':'+name)==read(name),'最終index全byte')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',m.TASK+': 現ownerとchild有限観測を保存');a.git('push','origin','HEAD:'+old.BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip();b.need(a.git('ls-remote','origin','refs/heads/'+old.BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:b.need(a.git('show','HEAD:'+name)==read(name),'commit全blob読戻し')
    for name in PROOFS|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed|protected)-old.LOGS):z.writestr(name,read(name))
    public('result.json',{'status':'DONE_FINITE_CONSUMER_SCOPE','commit':pushed,'source_head':head,'actions_run_id':int(os.environ['GITHUB_RUN_ID']),
        'classification_eligible_after_completed_run_receipt':eligible,'formal_classified':788,'formal_unclassified':86,
        'selected_unknown_origins':7,'donor_safe_bytes':0,'new_unit_tests':20,**ATTEMPT})
    print(f'RESULT=DONE TASK={m.TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[{'path':f.filename[len(str(ROOT))+1:],'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',{'status':'NOT_ACCEPTED','phase':PHASE,'exception_type':type(exc).__name__,'frames':frames,'attempt':ATTEMPT})
        print('RESULT=BLOCKED TASK='+m.TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__);sys.exit(1)
