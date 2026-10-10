#!/usr/bin/env python3
"""保存形を再走せず、選定二originの新しい実readerと成功受領を記録する。"""
from __future__ import annotations
import contextlib
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest
import urllib.request
import zipfile
import pr16_typed_origins as m
import pr16_donor_origins as original
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=Path(__file__).resolve().parents[1]
START='d4445cf929deec11d98f0173f4f11c86fe396f05'
TASK='USER-20261011-TYPED-ORIGIN-READERS'
BRANCH='codex/modernization-followup-20260908'
STATE='content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE='docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
PARENT='content/modernization/pr16_first_origin_checkpoint.json'
OLD_FACTS='content/modernization/pr16_first_origin_evidence/bounded-code-facts.json'
RECEIPT='content/modernization/pr16_first_origin_evidence/actions-completion.json'
REPORT='content/modernization/pr16_typed_origins_checkpoint.json'
EVIDENCE='content/modernization/pr16_typed_origins_evidence'
PROOF=EVIDENCE+'/reader-profiles.json'
TESTS=EVIDENCE+'/reader-tests.txt'
DIAGNOSTIC=EVIDENCE+'/bounded-discovery.json'
CODE={'scripts/pr16_typed_origins.py','scripts/pr16_typed_origins_actions.py',
      'tests/test_pr16_typed_origins.py','.github/workflows/pr16-typed-origins.yml'}
LOGS={'design/run_log.md','design/version_log.md'}
OUTPUTS={REPORT,PROOF,TESTS,DIAGNOSTIC,RECEIPT,STATE,GUIDE,*LOGS}
WORK=ROOT/'.local/pr16-typed-origins'
PUBLIC=WORK/'public'
PHASE='preflight'
ATTEMPT=dict(rom_reconstructions_started=0,exact_candidate_bound=False,new_profiles_completed=0,
             accepted_measurement_replays=0,native_processes=0)
SOURCE='c75f352304d529f6ba92d4f74b9cf8b5c3810788'
PUBLIC_BLOBS={'src/main.c':'542b0f5d16dd93107523d11163bfcb70a42b707a',
              'include/main.h':'31b22a3faa75409125257396913689a6a37c98ac',
              'src/gpu_regs.c':'2f52c5be334f90ce41eb52f8d4828e50e6da8e6d'}
ENGINES={'scripts/pr16_dex_hof_runtime_sprite.py':'7eb841b9a06ebedf2f8307ee5c8ff1135aeb355b',
         'scripts/pr16_dex_hof_lifetime_root.py':'83339dbb39cdba0cc21c535c66ceb9ce243c3f22'}
ZIP_ID=dict(size=83395,sha256='4825648ceaeaf9eb9f3185b3787ba310cb6b6d9c2bfb2af47e9b26b3b970b9f2')


def read(name):
    p=ROOT/name;m.need(p.is_file() and not p.is_symlink(),'通常tracked text');return p.read_bytes()


def write(name,value):a.changed_write(name,m.encode(value) if type(value) is dict else value)


def receipt():
    run=publication.accepted_run(38091044744,'06563a617a42e960b3e40ce6e6c0634322161e34',
        ['Bind actual first-origin bounds and receive prior symbols without replay','Run actions/upload-artifact@v4'])
    artifact=a.fetch('actions/artifacts/11683933530')
    m.need(artifact['name']=='pr16-first-origin-public-text' and not artifact['expired'] and
           artifact['size_in_bytes']==ZIP_ID['size'] and artifact['digest']=='sha256:'+ZIP_ID['sha256'] and
           artifact['workflow_run']['id']==run['id'] and artifact['workflow_run']['head_sha']==run['source_head'],'完了測定artifact metadata')
    raw=a.fetch('actions/artifacts/11683933530/zip',binary=True);m.need(m.identity(raw)==ZIP_ID,'ZIP全identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        expected={'actions-completion.json':'content/modernization/pr16_donor_origins_evidence/actions-completion.json',
                  'symbol-actions-completion.json':'content/modernization/pr16_donor_origins_evidence/actions-completion.json',
                  'bounded-code-facts.json':OLD_FACTS,'pr16_first_origin_checkpoint.json':PARENT,
                  'bounds-tests.txt':'content/modernization/pr16_first_origin_evidence/bounds-tests.txt'}
        names=z.namelist();m.need(len(names)==len(set(names))==8 and set(names)==set(expected)|{'attempt.json','scoped-context.zip','result.json'},'閉8member')
        files={}
        for info in z.infolist():
            m.need(info.file_size<2_000_000 and (info.external_attr>>16)&0o170000!=0o120000,'通常有限member')
            files[info.filename]=z.read(info)
        for name,path in expected.items():m.need(files[name]==read(path)==a.git('show',START+':'+path),'公開測定byte不変')
        result=json.loads(files['result.json']);m.need(result['status']=='DONE' and result['commit']==START and
            result['source_head']==run['source_head'] and result['actions_run_id']==run['id'] and result['new_unit_tests']==40,'原本result')
        with zipfile.ZipFile(io.BytesIO(files['scoped-context.zip'])) as context:
            names=context.namelist();m.need(len(names)==len(set(names)),'context重複禁止')
            for info in context.infolist():
                path=Path(info.filename);m.need(not path.is_absolute() and '..' not in path.parts and info.file_size<2_000_000,'context範囲')
                m.need(context.read(info)==a.git('show',START+':'+path.as_posix()),'全context committed byte')
    return dict(schema_version=1,status='COMPLETED_BOUNDED_ACTIONS_RECEIVED_WITHOUT_REPLAY',actions=run,
        artifact_id=artifact['id'],zip_identity=ZIP_ID,measurement_commit=START,
        member_identities={n:m.identity(b) for n,b in sorted(files.items())},
        rom_reconstructions=0,measurement_replays=0,old_scope_test_reruns=0)


def discover(raw,sym):
    """私有入力を物理的に有限sliceへ隔離。旧末尾BL幅曖昧の形は正式proofへ使わない。"""
    import pr16_first_origin as shape
    result=dict(role='DIAGNOSTIC_ONLY_NOT_FORMAL_EVIDENCE',literal_fields=m.validate_fields(raw),
        symbols=sym,ranges={},old_probe_terminal_bl_shape_used_as_evidence=False)
    for name,(address,size) in dict(init=(m.INIT[0],0x080A0088-m.INIT[0]),
        gpu=(sym['SetGpuReg'],192),vblank=(sym['SetVBlankCallback'],32)).items():
        span=m.take(raw,address,size);binary=WORK/'bounded-diagnostic.bin';binary.write_bytes(span)
        text=subprocess.check_output(['arm-none-eabi-objdump','-D','-z','-b','binary','-m','armv4t','-M','force-thumb',
            '--no-show-raw-insn','--adjust-vma='+str(address),str(binary)],text=True)
        rows=shape.parse_disassembly(text,span,address)
        for row in rows:
            if row['mnemonic']=='bl' and row['size']!=4:
                row.update(kind='TRUNCATED_BRANCH_NOT_EVIDENCE',operands=None)
        result['ranges'][name]=dict(address=address,**m.identity(span),instructions=rows)
    return result


def main():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同branch初回のみ')
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(set(a.git('diff','--name-only',START,head).decode().splitlines())==CODE,'新4source scope')
    m.need(not WORK.exists() and not (ROOT/REPORT).exists() and not (ROOT/RECEIPT).exists(),'受入測定再走禁止')
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    nested=a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
        'content/AGENTS.md','content/modernization/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    m.need(not nested.strip(),'追加AGENTS読取りが必要')
    state=json.loads(read(STATE));m.need(state['next_action']['id']=='SAVE_CAPACITY_FIRST_ORIGIN_TYPED_CONSUMER','正本next')
    m.need(original.blob(read(PARENT))=='0b3a70008c95521c63216d092886d2fa747abf8f' and
           original.blob(read(OLD_FACTS))=='e7fc6f99b114b00da5840e6f8479297bc5d2d1dc','固定測定原本')
    for name,blob in ENGINES.items():m.need(original.blob(read(name))==blob,'CPU解釈器原本')
    protected={PARENT,OLD_FACTS,*ENGINES,'CHATGPT_RESUME.md','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md',
        'content/modernization/pr16_donor_window_evidence/windows.json',
        'scripts/pr16_first_origin.py','scripts/pr16_first_origin_actions.py','tests/test_pr16_first_origin.py'}
    before={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in protected}
    PUBLIC.mkdir(parents=True)
    PHASE='new-tests-and-bounded-receipt'
    stream=io.StringIO();test=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_typed_origins.py'))
    (PUBLIC/'reader-tests.txt').write_text(stream.getvalue());m.need(test.wasSuccessful() and test.testsRun==20 and not test.skipped,'新20試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    accepted=receipt();(PUBLIC/'bounded-actions-completion.json').write_bytes(m.encode(accepted))
    PHASE='fixed-public-consumer-source'
    sources={}
    for path,blob in PUBLIC_BLOBS.items():
        with urllib.request.urlopen('https://raw.githubusercontent.com/pret/pokefirered/'+SOURCE+'/'+path,timeout=90) as response:data=response.read(100001)
        m.need(len(data)<=100000 and original.blob(data)==blob,'固定公開consumer blob')
        sources[path]=dict(repository='pret/pokefirered',commit=SOURCE,git_blob=blob,**m.identity(data))
    symbol_source=json.loads(read(OLD_FACTS))['public_symbol_source']
    with urllib.request.urlopen('https://raw.githubusercontent.com/'+symbol_source['repository']+'/'+symbol_source['commit']+'/'+symbol_source['path'],timeout=90) as response:syms=response.read(symbol_source['size']+1)
    m.need(original.blob(syms)==symbol_source['git_blob'],'JP全symbol blob')
    sym,rows=m.symbolic_name(syms,symbol_source)
    PHASE='new-literal-and-instruction-readers'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions_started']=1
    with (WORK/'private-reconstruction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):raw,checkpoint=reconstruction.reconstruct()
    m.need(m.identity(raw)==m.CANDIDATE and checkpoint['candidate']==m.CANDIDATE,'新実reader用候補全SHA')
    ATTEMPT['exact_candidate_bound']=True
    (PUBLIC/'attempt.json').write_bytes(m.encode(ATTEMPT))
    diagnostic=discover(raw,sym);(PUBLIC/'bounded-discovery.json').write_bytes(m.encode(diagnostic))
    proof=m.prove(raw,sym);ATTEMPT['new_profiles_completed']=3
    proof.update(public_sources=sources,public_symbol_source=symbol_source,public_symbol_rows=rows,
        engine_bindings={n:m.identity(read(n)) for n in ENGINES})
    encoded=m.encode(proof);(PUBLIC/'reader-profiles.json').write_bytes(encoded)
    write(PROOF,encoded);write(DIAGNOSTIC,diagnostic);write(TESTS,stream.getvalue().encode());write(RECEIPT,accepted)
    saved=(read(PROOF),(ROOT/PROOF).stat().st_mtime_ns)
    m.need(read(PROOF)==m.encode(json.loads(read(PROOF))) and saved==(read(PROOF),(ROOT/PROOF).stat().st_mtime_ns),'read-only canonical byte/mtime')
    m.need(before=={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in before},'旧原本byte/mtime不変')
    PHASE='record-and-nonforce-push'
    goal=('二originの新3条件付き実readerを保存済み。成功Actions/ZIP全memberとsourceを別受領し、'
          '正式785/89親へ二件だけの型分類差分を適用する。literalの上位1byte+callback下位3byteと、'
          '__subsf3のBL下位3byte+直後ADD上位ではなく先頭1byteを照合する。自然entry/IRQ/GPU flush/浮動callee/全alias不在は主張しない。'
          '安全容量0。今回reader/20試験と旧全scopeの無変更再走を禁止する。')
    report=dict(schema_version=1,task=TASK,status=proof['status'],source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,proof_path=PROOF,proof_identity=m.identity(encoded),
        prior_actions_receipt_path=RECEIPT,new_unit_tests=20,new_profiles=3,rom_reconstructions=1,attempt=ATTEMPT,
        claims=dict(m.CLAIMS),source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        preserved_inputs={n:v[0] for n,v in before.items()},read_only_check_passed=True,task_graph_passed=True,
        observed_head_checks=observed,next_ja=goal)
    write(REPORT,report)
    state['owner_execution_plan']['technical_lanes']['save_capacity'].update(status=proof['status'],checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_TWO_TYPED_ORIGINS_RECEIPT',goal_ja=goal,read_paths=[GUIDE,REPORT,PROOF,RECEIPT,
        'scripts/pr16_typed_origins.py','scripts/pr16_forest_wallpaper_receipt.py'],
        done_ja='新3readerの完了原本を受領し、旧874行/namespaceを保全して二件だけ正式分類。安全容量0と次の未知を明示。')
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_TWO_TYPED_READERS_MEASURED_FORMAL_RECEIPT_PENDING'
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,new_unit_tests=20,new_profiles=3,accepted_tests_rerun=0,new_native_processes=0,
        rom_reconstructions=1,read_only_check_passed=True,task_graph_passed=True,classified=785,unclassified=89,donor_safe_bytes=0)
    write(STATE,state)
    old=read(GUIDE).decode();m.need('## 選定二originの実型reader' not in old,'引継ぎ重複拒否')
    old=old.replace('## 次の未完作業','## 以前の停止点（履歴）')
    old+=(f'\n## 選定二originの実型reader\n\n先頭は0x00001111上位1byteと0x0809FED5下位3byteのliteral跨りです。'
        '実LDRとSetGpuRegのu16 buffer store、SetVBlankCallbackのcallback field書込/帰還を有限解釈しました。'
        '0x081C96E9は公開__subsf3の実BLと直後ADDを、同期callee帰還条件で解釈しました。'
        '自然入口/IRQ/GPU flush/浮動callee本体/全alias不在は証明していません。\n\n'
        f'[新3reader](../{PROOF}) / [checkpoint](../{REPORT}) / [直前Actions受領](../{RECEIPT})。'
        '新20試験、候補復元1、native0、旧試験/測定再走0、読取専用byte/mtimeとtask graph。'
        '旧GNU形の有限窓末尾BL幅は型証明に用いず、実解釈器の同一範囲内完全命令幅で検証しました。'
        '正式785/89・安全容量0は完了受領まで据置。\n\n## 次の未完作業\n\n'+goal+'\n')
    write(GUIDE,old.encode())
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {TASK} / 選定二originの実型reader\n'
        '- Version: typed-origin-readers-v1\n- Status: DONE（新3reader測定。正式受領/退役/保存統合は未完）\n'
        '- Summary: 完了済み有限形Actions/ZIPを再走なしで受領。先頭literal二fieldの実LDR→GPU u16 buffer/callback store、次の__subsf3 BL/ADD fetchを有限条件下で検証。\n'
        '- Files changed: 新reader/20試験/専用Actions、3profile原本、直前成功receipt、固定引継ぎMD/JSON、両ログ。\n'
        '- Verify: 新20 tests、新3profiles、候補全SHA、read-only byte/mtime、旧原本不変、task graph。最終index新規private違反0と全体guard結果はcheckpointへ別記録。\n'
        '- Boundary: 自然entry/IRQ/GPU flush/浮動callee本体/全alias不在は非主張。正式785/89・安全容量0、ROM/Save101/R0/baseline不変。新復元1/native0/旧試験と旧測定再走0。旧形の末尾BL幅は受入証明に不使用。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはGit履歴/Actions resultを参照。\n'
        '- Network: 同repo PR/ref/成功Actions/固定private再構成入力、固定公開source GET、同branch非force push。\n'
        '- Sources: https://github.com/pret/pokefirered/tree/c75f352304d529f6ba92d4f74b9cf8b5c3810788 (src/main.c、include/main.h、src/gpu_regs.c) と固定ComplexRobot/frlg-sym c04a3154。検索/確認: SetVBlankCallback・SetGpuReg・Main.vblankCallback。callback offset0xCとu16 GPU buffer値を実codeに照合。\n')
    for name in LOGS:
        old=read(name);m.need(('- Task: '+TASK+' /').encode() not in old,'同task重複');write(name,old+block.encode())
    publication.final_index(START,CODE|OUTPUTS,REPORT)
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前競合')
    for name in CODE|OUTPUTS:m.need(a.git('show',':'+name)==read(name),'最終index全byte')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 二originの実literal/Thumb consumerを検証し引継ぎを記録');a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip();m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in CODE|OUTPUTS:m.need(a.git('show','HEAD:'+name)==read(name),'commit blob読戻し')
    for name in (REPORT,PROOF,RECEIPT):(PUBLIC/Path(name).name).write_bytes(read(name))
    context={*CODE,*ENGINES,STATE,GUIDE,REPORT,PROOF,DIAGNOSTIC,RECEIPT,
        'scripts/pr16_forest_wallpaper_receipt.py','scripts/pr16_weather_bubble_receipt.py',
        'content/modernization/pr16_forest_wallpaper_receipt_evidence/reference-chain.json',
        'content/modernization/pr16_forest_wallpaper_receipt_evidence/unknown-frontier.json'}
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted(context):z.writestr(name,read(name))
    (PUBLIC/'attempt.json').write_bytes(m.encode(ATTEMPT))
    (PUBLIC/'result.json').write_bytes(m.encode(dict(status='DONE',task=TASK,source_head=head,commit=pushed,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),new_unit_tests=20,new_profiles=3,claims=m.CLAIMS)))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        if PUBLIC.exists():
            (PUBLIC/'failure.json').write_bytes(m.encode(dict(status='FAILED_NOT_ACCEPTED',phase=PHASE,attempt=ATTEMPT,
                exception_type=type(exc).__name__,frames=[dict(source=Path(f.filename).name,line=f.lineno,function=f.name)
                    for f in traceback.extract_tb(exc.__traceback__) if '/scripts/' in f.filename])))
        print(f'RESULT=STOPPED TASK={TASK} VERIFY=FAIL COMMIT=- PHASE={PHASE}');sys.exit(1)
