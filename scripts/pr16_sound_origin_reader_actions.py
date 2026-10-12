#!/usr/bin/env python3
"""固定音声readerの有限測定と一度だけの受領。完了原本の再走・自己受領loopはしない。"""
from __future__ import annotations
import contextlib
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
import pr16_sound_origin_reader as m
import pr16_sound_origin_asset_actions as prior
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=m.asset.ROOT
BASE='49d6193516ded14ccc12368a9582d1af931c03fc'
TASK='USER-20261011-SOUND-ORIGIN-READER'
RECEIPT_TASK='USER-20261011-SOUND-ORIGIN-RECEIPT'
BRANCH=prior.BRANCH
STATE,GUIDE,LOGS=prior.STATE,prior.GUIDE,prior.LOGS
ASSET_CP=prior.REPORT
ASSET_PROOF=prior.EVIDENCE+'/asset-binding.json'
EVIDENCE='content/modernization/pr16_sound_origin_reader_evidence'
REPORT='content/modernization/pr16_sound_origin_reader_checkpoint.json'
PROOF=EVIDENCE+'/reader-proof.json'
REQUEST='content/modernization/pr16_sound_origin_reader_completion_request.json'
RECEIPT='content/modernization/pr16_sound_origin_reader_receipt.json'
WORK=ROOT/'.local/pr16-sound-origin-reader'
PUBLIC=WORK/'public'
WF='.github/workflows/pr16-sound-origin-reader.yml'
STEP='Verify sound reader or receive completed measurement without replay'
ARTIFACT='pr16-sound-origin-reader-public-text'
CODE={'scripts/pr16_sound_origin_reader.py','scripts/pr16_sound_origin_reader_actions.py',
      'tests/test_pr16_sound_origin_reader.py','tools/mgba_pr16_sound_origin_reader.c',WF}
MEASURE_FILES={PROOF,EVIDENCE+'/native.json',EVIDENCE+'/reader-tests.txt',EVIDENCE+'/asset-completion.json'}
FORMAL_FILES={EVIDENCE+'/'+n for n in ('reference-chain.json','unknown-frontier.json','window-progress.json','actions-completion.json')}
PARENT_CHAIN='content/modernization/pr16_typed_origins_receipt_evidence/reference-chain.json'
PARENT_FRONTIER='content/modernization/pr16_typed_origins_receipt_evidence/unknown-frontier.json'
PARENT_WINDOW='content/modernization/pr16_typed_origins_receipt_evidence/window-progress.json'
FAILED_ATTEMPTS=[dict(run_id=38097199893,source_head='7fdc382275bd5c2a4ea32f892c1dfabd2ce588bc',
    artifact_id=11686771077,artifact_sha256='31b11dce77ad32ace79875d79e7eb8ea7f09a6f247d785e7fd12b33686849900',
    conclusion='failure',phase='new-fixed-mixer-sources',rom_reconstructions=0,native_processes=0,
    reason_ja='非対象のcompiler-local同名labelまで一意化して停止。必要な5名のみ一意化し、対象の重複/欠落は引き続き拒否。追加3境界試験。')]
PHASE='preflight'
ATTEMPT=dict(accepted_tests_rerun=0,accepted_native_replays=0,rom_reconstructions=0,native_processes=0)


def read(name):return prior.read(name)
def write(name,value):return prior.write(name,value)
def load(name):return json.loads(read(name))
def public(name,value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def command(args):
    result=subprocess.run([str(x) for x in args],cwd=ROOT,capture_output=True,timeout=300)
    if result.returncode:
        # Fixed-source diagnostics only. Never publish a reconstruction log or private input bytes.
        message=result.stderr.decode(errors='replace').replace(str(ROOT),'.')[-2400:]
        public('command-failure.json',dict(phase=PHASE,tool=Path(str(args[0])).name,exit_code=result.returncode,diagnostic=message))
    m.need(result.returncode==0,'command failed')
    return result.stdout


def inherited():
    cp=load(ASSET_CP)
    expected={**cp['source_bindings'],**cp['evidence_bindings'],**cp['preserved_inputs']}
    for name,want in expected.items():m.need(m.identity(read(name))==want,'受入済みasset原本全identity: '+name)
    m.need(cp['candidate']==m.CANDIDATE and cp['status']=='EXACT_PCM_ASSET_BOUND_READER_PENDING','受入済みasset境界')
    proof=load(ASSET_PROOF)
    m.need(proof['asset']['origin']==m.HIT and proof['asset']['sample_index']==1831 and
           proof['asset']['header_samples']==13800 and proof['conversion']['payload_samples']==13801 and
           len(proof['source_voice_rows'])==3 and proof['independent_cpp_equal']is True,'固定assetとheader/payload差')
    names=set(expected)|{ASSET_CP}
    return cp,proof,{n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in names}


def public_sources():
    data={};bindings={}
    sources=[('pret/pokefirered',m.SOURCE,p,b,1_000_000) for p,b in m.SOURCES.items()]
    s=m.SYMBOL_SOURCE
    sources.append((s['repository'],s['commit'],s['path'],s['git_blob'],5_000_000))
    for repo,commit,path,want,limit in sources:
        with urllib.request.urlopen('https://raw.githubusercontent.com/'+repo+'/'+commit+'/'+path,timeout=90) as response:
            raw=response.read(limit+1)
        m.need(len(raw)<=limit and m.blob(raw)==want,'固定公開source全blob')
        data[path]=raw;bindings[path]=dict(repository=repo,commit=commit,path=path,git_blob=want,**m.identity(raw))
        dest=WORK/'upstream'/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    symbols=m.symbol_map(data[s['path']])
    return data,bindings,symbols


def build_mixer(data,symbols):
    need_names=('SoundMainRAM','SoundMainRAM_Unk1','voicegroup002','voicegroup156','voicegroup157')
    m.need(all(n in symbols for n in need_names),'必要な固定JPsymbol')
    start=symbols['SoundMainRAM']['address']&~1
    source=WORK/'mixer.s';source.write_bytes(m.mixer_source(data['src/m4a_1.s']))
    obj,elf,binary=(WORK/n for n in ('mixer.o','mixer.elf','mixer.bin'))
    command(['arm-none-eabi-as','-mcpu=arm7tdmi','-mthumb-interwork','-I',WORK/'upstream','-o',obj,source])
    undefined=command(['arm-none-eabi-nm','-u',obj]).decode().split()
    m.need(undefined==['U','SoundMainRAM_Unk1'],'mixer external dependency集合')
    command(['arm-none-eabi-ld','--build-id=none','-Ttext='+hex(start),'-e','SoundMainRAM',
        '--defsym=SoundMainRAM_Unk1='+hex(symbols['SoundMainRAM_Unk1']['address']&~1),'-o',elf,obj])
    command(['arm-none-eabi-objcopy','-O','binary','-j','.text',elf,binary])
    names={row.split()[-1]:int(row.split()[0],16) for row in command(['arm-none-eabi-nm','--defined-only',elf]).decode().splitlines()
        if len(row.split())==3}
    m.need(all(n in names for n in ('SoundMainRAM','SoundMainRAM_End','_081DD044','_081DD240')),'固定mixer local labels')
    m.need(names['SoundMainRAM']&~1==start and names['SoundMainRAM_End']==symbols['SoundMainRAM_Unk1']['address']&~1,'全function終端と後続一致')
    metadata=dict(source_body_identity=m.identity(source.read_bytes()),object_identity=m.identity(obj.read_bytes()),
        linked_text_identity=m.identity(binary.read_bytes()),start=start,end_exclusive=names['SoundMainRAM_End'],
        arm_entry=names['_081DD044'],stop_before_thumb_channel_dispatch=names['_081DD240'],
        public_symbols={n:symbols[n] for n in need_names})
    return binary.read_bytes(),metadata


def build_voices(saved,symbols):
    source=WORK/'voices.s';obj=WORK/'voices.o';elf=WORK/'voices.elf';binary=WORK/'voices.bin'
    text=('.include "asm/macros/music_voice.inc"\n.syntax unified\n.section .rodata\n'
          '.global fixed_voices\nfixed_voices:\n.set '+m.asset.SYMBOL+', '+hex(m.asset.START)+'\n')
    for row in saved:text+='\t'+row['source_text']+'\n'
    source.write_text(text)
    command(['arm-none-eabi-as','-mcpu=arm7tdmi','-I',WORK/'upstream','-o',obj,source])
    command(['arm-none-eabi-ld','--build-id=none','-e','fixed_voices','-o',elf,obj])
    command(['arm-none-eabi-objcopy','-O','binary','-j','.rodata',elf,binary])
    raw=binary.read_bytes();m.need(len(raw)==36,'3個の完全voice macro展開')
    result=[]
    for i,row in enumerate(saved):
        expected=m.voice_bytes(row['source_text'],m.asset.START)
        m.need(raw[i*12:i*12+12]==expected,'GNU voice macroと独立12byte生成が一致')
        address=symbols[row['group']]['address']+row['slot']*12
        result.append((row,address,expected))
    return result


def run_native(raw,mixer,tables):
    version=command(['dpkg-query','-W','-f=${Version}','libmgba-dev']).decode().strip()
    lib=m.identity(Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes())
    m.need(version=='0.10.2+dfsg-1.1build3' and lib==dict(size=1968536,sha256='0c87a12341640e6a2d325e59e76eb4b002947771ad4d8814b216e3b99817d68d'),'固定mGBA runtime')
    defines=dict(MIX_START=mixer['start'],MIX_ARM=mixer['arm_entry'],MIX_STOP=mixer['stop_before_thumb_channel_dispatch'],
        MIX_CODE_END=mixer['end_exclusive'],**{'VOICE'+str(i):t['address'] for i,t in enumerate(tables)})
    exe=WORK/'native'
    command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',ROOT/'tools/mgba_pr16_sound_origin_reader.c',
        *['-D'+k+'='+hex(v)+'u' for k,v in defines.items()],'-lmgba','-lm','-o',exe])
    candidate=WORK/'candidate.gba';candidate.write_bytes(raw)
    ATTEMPT['native_processes']=1;public('attempt.json',ATTEMPT)
    result=command([exe,candidate])
    value=json.loads(result)
    m.check_native(value,raw[m.HIT-0x08000000:m.HIT-0x08000000+128])
    m.need(candidate.read_bytes()==raw,'native後の全ROM原本不変')
    return value,dict(package_version=version,library_identity=lib,native_source_identity=m.identity(read('tools/mgba_pr16_sound_origin_reader.c')),
        native_binary_identity=m.identity(exe.read_bytes()),compile_defines=defines)


def publish(base,head,allowed,report,task):
    publication.final_index(base,allowed,report)
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push直前HEAD競合')
    for name in allowed:m.need(a.git('show',':'+name)==read(name),'最終index全byte')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',task+': 音声実readerの検証と継続点を保存')
    a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'commit blob読戻し')
    return pushed


def guide(section,body,goal):
    text=read(GUIDE).decode();m.need(section not in text,'引継ぎ重複禁止')
    text=text.replace('## 次の未完作業','## 以前の停止点（履歴）')
    write(GUIDE,(text+'\n## '+section+'\n\n'+body+'\n\n## 次の未完作業\n\n'+goal+'\n').encode())


def log(task,summary,verify):
    now=prior.stamp()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {task} / 選定窓の条件付き音声reader\n'
        '- Version: sound-origin-reader-v1\n- Status: DONE（記載の限定scope。保存容量/統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 新reader/試験/native/有限Actions、証拠と固定引継ぎMD/JSON、両ログ。\n'
        f'- Verify: {verify}\n'
        '- Boundary: 自然note dispatch・通常IWRAMコピー実行・全alternative reader不在・退役/移管は非主張。'
        'donor/lease/安全容量0、旧受入/R0/ROM/Save101/baseline不変。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはGit履歴とActions resultから照合。\n'
        '- Network: 固定GitHub PR/ref/Actions原本、同branch非force push。新公開出典は'
        ' https://github.com/pret/pokefirered/tree/'+m.SOURCE+' のm4a_1.s/定数/music_voice.incと固定JPsymbol。'
        '検索語 SoundMainRAM voice_directsound。非圧縮波形は符号付き1byte補間で消費する。asset生成/既受入native再走なし。\n')
    for name in LOGS:
        old=read(name);m.need(('- Task: '+task+' /').encode() not in old,'同task追記済み');write(name,old+block.encode())


def finish_public(names,result):
    for name in names:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((set(names)|CODE|{STATE,GUIDE,ASSET_CP,ASSET_PROOF,PARENT_CHAIN,PARENT_FRONTIER,PARENT_WINDOW})-LOGS):
            z.writestr(name,read(name))
    public('result.json',result)
    print('RESULT=DONE TASK='+result['task']+' VERIFY=PASS COMMIT='+result['commit'])


def build(head,observed):
    global PHASE
    m.need(set(a.git('diff','--name-only',BASE,head).decode().splitlines())==CODE,'new reader code scope')
    m.need(not (ROOT/REPORT).exists() and not (ROOT/RECEIPT).exists(),'実reader無変更再走禁止')
    state=load(STATE);lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SOUND_ORIGIN_ACTUAL_READER' and
           [lane[k] for k in ('classified','unclassified','donor_safe_bytes')]==[787,87,0],'現行未完readerだけ')
    asset_cp,saved,before=inherited()
    for attempt in FAILED_ATTEMPTS:
        failed=a.fetch('actions/runs/'+str(attempt['run_id']))
        m.need(failed['status']=='completed' and failed['conclusion']=='failure' and failed['head_sha']==attempt['source_head'],'記録した失敗runの実在/全HEAD')
    PHASE='receive-completed-asset-without-replay'
    completed_asset=publication.accepted_run(38095546359,'45ef40242033f2c0bc00d1f3b189d949fd255b89',
        ['Bind fixed sound asset without replaying accepted readers','Run actions/upload-artifact@v4'])
    completed_asset.update(checkpoint=ASSET_CP,checkpoint_identity=m.identity(read(ASSET_CP)),record_commit=BASE,
        accepted_test_reruns=0,asset_regenerations=0)
    PHASE='new-reader-33-unit-tests'
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_sound_origin_reader.py'))
    public('reader-tests.txt',stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun==33 and not tests.skipped,'新reader33境界試験')
    command(['python3','-B','scripts/validate_task_graph.py'])
    PHASE='new-fixed-mixer-sources'
    data,sources,symbols=public_sources()
    PHASE='compile-entire-fixed-mixer'
    generated,mixer=build_mixer(data,symbols)
    public('compiled-mixer.json',mixer)
    PHASE='compile-three-fixed-voice-macros'
    prepared_tables=build_voices(saved['source_voice_rows'],symbols)
    PHASE='exact-candidate-for-new-reader'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions']=1;public('attempt.json',ATTEMPT)
    with (WORK/'private-reconstruction.log').open('w') as stream,contextlib.redirect_stdout(stream),contextlib.redirect_stderr(stream):
        raw,cp=reconstruction.reconstruct()
    m.need(m.identity(raw)==m.CANDIDATE and cp['candidate']==m.CANDIDATE,'現候補全SHA/owner配置')
    PHASE='bind-entire-mixer-and-three-voice-tables'
    mixer.update(m.bind_mixer(raw,generated,mixer['start'],mixer['end_exclusive']))
    tables=[m.bind_table(raw,row,address,expected) for row,address,expected in prepared_tables]
    public('current-binding.json',dict(mixer=mixer,table_bindings=tables))
    PHASE='actual-native-26-conditional-reader-cases'
    native,runtime=run_native(raw,mixer,tables)
    proof=dict(schema_version=1,status='CONDITIONAL_PCM_READER_VERIFIED_RECEIPT_PENDING',source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),candidate=m.CANDIDATE,asset_checkpoint=ASSET_CP,
        asset_proof_path=ASSET_PROOF,asset_proof_identity=m.identity(read(ASSET_PROOF)),
        public_sources=sources,mixer=mixer,table_bindings=tables,runtime=runtime,native=native,
        independent_model_equal=True,original_inputs_preserved=True,formal_classification_changes=0,
        formal_classified=787,formal_unclassified=87,selected_unknown_origins=8,donor_safe_bytes=0,
        new_unit_tests=33,rom_reconstructions=1,native_processes=1,accepted_tests_rerun=0,
        accepted_asset_generations=0,accepted_native_replays=0,full_rom_scans=0,
        natural_entry_reachability_proven=False,actual_runtime_iwram_copy_proven=False,
        all_alternative_readers_excluded=False,retirement_or_transfer_complete=False,
        indirect_reference_completeness_claimed=False,formal_rom_changed=False,formal_save_changed=False)
    PHASE='deterministic-readonly-check-and-record'
    for name,value in [(PROOF,proof),(EVIDENCE+'/native.json',native),(EVIDENCE+'/asset-completion.json',completed_asset),
                       (EVIDENCE+'/reader-tests.txt',read_local_test())]:write(name,value)
    stable={n:(read(n),(ROOT/n).stat().st_mtime_ns) for n in MEASURE_FILES}
    m.need(m.encode(load(PROOF))==read(PROOF) and load(PROOF)['native']==load(EVIDENCE+'/native.json'),'stored canonical proof/native一致')
    m.check_native(load(EVIDENCE+'/native.json'),raw[m.HIT-0x08000000:m.HIT-0x08000000+128])
    m.need(stable=={n:(read(n),(ROOT/n).stat().st_mtime_ns) for n in stable},'read-only check byte/mtime不変')
    m.need(before=={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in before},'受入済み全原本byte/mtime不変')
    goal='音声実readerの完了runと公開artifactを一度受領し、保存した787/87と選定8行から0x084723AFだけを正式788/86・残7行へ移す。33試験/26native/asset32試験/既受入reader/ROM全scanは再走しない。安全容量0、自然dispatch/IWRAM通常配置/全alias/退役/保存統合は未完。'
    report=dict(schema_version=1,task=TASK,status=proof['status'],source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,candidate=m.CANDIDATE,
        proof_path=PROOF,proof_identity=m.identity(read(PROOF)),source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        preserved_inputs={n:v[0] for n,v in before.items()},evidence_bindings={n:m.identity(read(n)) for n in sorted(MEASURE_FILES)},
        attempt=ATTEMPT,prior_attempts=FAILED_ATTEMPTS,new_unit_tests=33,native_cases=26,formal_classified=787,formal_unclassified=87,
        remaining_selected_origins=8,donor_safe_bytes=0,formal_classification_changes=0,
        received_asset_completion=EVIDENCE+'/asset-completion.json',read_only_check_passed=True,task_graph_passed=True,
        observed_head_checks=observed,next_ja=goal)
    write(REPORT,report)
    lane.update(status=proof['status'],checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SOUND_READER_COMPLETION_RECEIPT',goal_ja=goal,
        read_paths=[GUIDE,REPORT,PROOF,PARENT_CHAIN,PARENT_FRONTIER,PARENT_WINDOW],
        done_ja='実在する成功完了run/公開原本/不変sourceへ束縛し、単一originの型分類と次の7行を記録する。')
    state['observed_head_checks']=observed
    state['recording'].pop('pending_sound_asset_run',None)
    state['recording'].update(status='R0_READY_SOUND_READER_VERIFIED_RECEIPT_PENDING',
        received_sound_asset_completion=EVIDENCE+'/asset-completion.json',
        pending_sound_reader_run=dict(run_id=int(os.environ['GITHUB_RUN_ID']),source_head=head,report=REPORT,
            status='COMPLETION_NOT_YET_OBSERVED',replay_forbidden=True))
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,new_unit_tests=33,accepted_tests_rerun=0,new_native_processes=1,
        native_cases=26,rom_reconstructions=1,read_only_check_passed=True,task_graph_passed=True,
        classified=787,unclassified=87,donor_safe_bytes=0)
    write(STATE,state)
    guide('音声実readerの有限検証（完了原本の受領待ち）',
        '保存assetは再生成せず、固定voice macroの3行と現候補の全12byteを束縛。固定SoundMainRAM全bodyをJP配置へリンクして現ROMと全byte一致。'
        '実ROM命令をmGBAで26ケース（20 ARM補間・6 Thumb波形初期化）だけ実行し、対象4byteの実LDRSB、全読取順、符号拡張、出力全byte、cursor/count/phase、非所有RAM不変を独立整数modelと比較しました。'
        f'[reader証拠](../{PROOF}) / [checkpoint](../{REPORT})。'
        'これは自然note dispatchや通常IWRAMコピー実行の受入ではありません。新33試験/26ケース、新native1、旧受入再走0。'
        '正式分類はrun成功完了の外部受領まで787/87・選定8・安全容量0のままです。',goal)
    log(TASK,'現候補の実voice3行/全mixerを束縛し、対象PCMを26有限ケースで消費。正式分類は成功完了受領まで保留。',
        '新33境界試験・固定GNU macro/全mixer一致・26 native全出力/読取/状態/非所有RAM・独立Python model・byte/mtime・task graph PASS。新scope再構成1/native1、旧受入再走0。初回run38097199893はsymbol adapter境界で停止（再構成/native0）し、必要5名の一意性を保った修正と3追加試験で解消。')
    pushed=publish(BASE,head,CODE|MEASURE_FILES|{REPORT,STATE,GUIDE,*LOGS},REPORT,TASK)
    finish_public(MEASURE_FILES|{REPORT},dict(status='DONE',task=TASK,source_head=head,commit=pushed,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),new_unit_tests=33,native_cases=26,rom_reconstructions=1,
        native_processes=1,accepted_tests_rerun=0,formal_classification_changes=0,donor_safe_bytes=0))


def read_local_test():return (PUBLIC/'reader-tests.txt').read_bytes()


def receipt(head,observed):
    global PHASE
    PHASE='receive-completed-reader-without-replay'
    m.need(not (ROOT/RECEIPT).exists(),'同reader受領済み。再実行しない')
    request=load(REQUEST);cp=load(REPORT);proof=load(PROOF)
    m.need(request['schema_version']==1 and request['actions_run_id']==cp['actions_run_id'] and
        request['source_head']==cp['source_head'] and request['checkpoint_identity']==m.identity(read(REPORT)), '受領依頼と測定原本')
    record_head=request['record_commit']
    a.git('merge-base','--is-ancestor',record_head,head)
    m.need(set(a.git('diff','--name-only',record_head,head).decode().splitlines())=={REQUEST},'測定commit以降は明示受領依頼だけ')
    for name,want in {**cp['source_bindings'],**cp['preserved_inputs'],**cp['evidence_bindings']}.items():
        m.need(m.identity(read(name))==want and a.git('show',record_head+':'+name)==read(name),'測定全原本不変')
    m.need(cp['proof_identity']==m.identity(read(PROOF)) and cp['candidate']==m.CANDIDATE,'測定proof identity')
    run=publication.accepted_run(request['actions_run_id'],request['source_head'],[STEP,'Run actions/upload-artifact@v4'])
    metadata=a.fetch('actions/artifacts/'+str(request['artifact']['id']))
    m.need(not metadata['expired'] and all(metadata[k]==request['artifact'][k] for k in ('id','name','size_in_bytes','digest')) and
        metadata['workflow_run']['id']==request['actions_run_id'] and metadata['workflow_run']['head_sha']==request['source_head'],'公開artifact identity')
    archive=a.fetch('actions/artifacts/'+str(metadata['id'])+'/zip',binary=True)
    m.need(len(archive)==metadata['size_in_bytes'] and m.identity(archive)['sha256']==metadata['digest'].removeprefix('sha256:'),'原本ZIP全identity')
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        for name in MEASURE_FILES|{REPORT}:
            key=name.rsplit('/',1)[-1];m.need(z.namelist().count(key)==1 and z.getinfo(key).file_size<1_000_000,'有限単一text member')
            m.need(z.read(key)==read(name),'archiveの測定textとcommit全byte一致')
        result=json.loads(z.read('result.json'))
    m.need(result['commit']==record_head and result['source_head']==request['source_head'] and
        result['status']=='DONE' and result['native_cases']==26 and result['native_processes']==1 and
        result['formal_classification_changes']==0,'受領する完了result scope')
    protected=set(cp['source_bindings'])|set(cp['preserved_inputs'])|MEASURE_FILES|{REPORT}
    before={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in protected}
    chain,front,window=m.promote(load(PARENT_CHAIN),load(PARENT_FRONTIER),load(PARENT_WINDOW),proof,run)
    chain.update(parent_chain_path=PARENT_CHAIN,parent_frontier_path=PARENT_FRONTIER,parent_window_path=PARENT_WINDOW,
        proof_path=PROOF,proof_identity=m.identity(read(PROOF)),witnesses=[dict(
            origin=m.HIT,asset_proof_path=ASSET_PROOF,asset_proof_identity=proof['asset_proof_identity'],
            actual_table_entries=proof['table_bindings'],actual_mixer=proof['mixer'],native_path=EVIDENCE+'/native.json',
            native_identity=m.identity(read(EVIDENCE+'/native.json')),native_cases=26,
            independent_model_equal=True,conditional_finite_reader_only=True,
            natural_entry_reachability_proven=False,actual_runtime_iwram_copy_proven=False,
            all_alternative_readers_excluded=False,donor_safe_bytes=0)])
    outputs={EVIDENCE+'/reference-chain.json':chain,EVIDENCE+'/unknown-frontier.json':front,EVIDENCE+'/window-progress.json':window}
    run.update(artifact={k:metadata[k] for k in ('id','name','size_in_bytes','digest')},record_commit=record_head,
        checkpoint_path=REPORT,checkpoint_identity=m.identity(read(REPORT)),measurement_replays=0,native_replays=0)
    outputs[EVIDENCE+'/actions-completion.json']=run
    for name,value in outputs.items():write(name,value)
    m.need(all(m.encode(load(n))==read(n) for n in outputs),'正式出力canonical JSON')
    m.need(before=={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in before},'原本byte/mtime不変')
    command(['python3','-B','scripts/validate_task_graph.py'])
    next_address=window['next_address']
    goal=(f'残る選定窓7行の先頭0x{next_address:08X}を保存symbol近傍から固定公開asset/現候補へ束縛し、実consumerを有限scopeで検証する。'
        '正式788分類/86未知・安全容量0。音声asset32試験/reader33試験/26 native・旧受入・全874scan・窓最適化は無変更再走しない。'
        '窓外跨りread/旧owner内origin/間接参照/退役・移管/保存controller・heap・局所Saveは未完。')
    receipt_value=dict(schema_version=1,task=RECEIPT_TASK,status='SOUND_ORIGIN_FORMALLY_ACCEPTED_788_86',
        source_head=head,accepted_measurement=run,measurement_checkpoint=REPORT,measurement_proof=PROOF,
        candidate=m.CANDIDATE,formal_classified=788,formal_unclassified=86,selected_unknown_origins=7,
        donor_safe_bytes=0,newly_classified_origins=[m.HIT],evidence_bindings={n:m.identity(read(n)) for n in sorted(outputs)},
        accepted_tests_rerun=0,rom_reconstructions=0,new_native_processes=0,read_only_check_passed=True,
        task_graph_passed=True,observed_head_checks=observed,next_ja=goal)
    write(RECEIPT,receipt_value)
    state=load(STATE);lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SOUND_READER_COMPLETION_RECEIPT' and
        [lane[k] for k in ('classified','unclassified','donor_safe_bytes')]==[787,87,0],'正式受領の親状態')
    lane.update(status=receipt_value['status'],checkpoint_path=RECEIPT,classified=788,unclassified=86,
        selected_unknown_origins=7,donor_safe_bytes=0,next_ja=goal,
        reference_chain_path=EVIDENCE+'/reference-chain.json',unknown_frontier_path=EVIDENCE+'/unknown-frontier.json',
        window_progress_path=EVIDENCE+'/window-progress.json')
    state['next_action']=dict(id='SAVE_CAPACITY_SELECTED_WINDOW_NEXT_ASSET_BINDING',goal_ja=goal,
        read_paths=[GUIDE,RECEIPT,EVIDENCE+'/window-progress.json',prior.SYMBOLS,PROOF],
        done_ja='次の未分類originのasset/実readerを根拠に追加し、保存原本を継承して容量と保存安全性へ進む。')
    state['observed_head_checks']=observed
    state['recording'].pop('pending_sound_reader_run',None)
    state['recording'].update(status='R0_READY_SOUND_ORIGIN_FORMALLY_ACCEPTED_788_86',
        received_sound_reader_completion=EVIDENCE+'/actions-completion.json')
    state['recording']['last_execution']=dict(task=RECEIPT_TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        received_completed_run=request['actions_run_id'],actions_completion_confirmed=False,received_measurement_completion_confirmed=True,
        accepted_tests_rerun=0,new_native_processes=0,rom_reconstructions=0,
        read_only_check_passed=True,task_graph_passed=True,classified=788,unclassified=86,donor_safe_bytes=0)
    write(STATE,state)
    guide('音声originの成功原本受領と正式分類',
        f'run {run["id"]} の完了success、全job/必須step、公開artifactの全hash、測定commitと全textを照合。'
        '保存原本を再走せず0x084723AFだけを符号付きPCMの条件付き実readerとして正式追加しました。'
        '**正式788分類/86未知、選定窓は残7行、安全容量0**。3voice table→WaveData→有限ARM補間の証拠であり、自然dispatch・通常IWRAM配置・全代替reader不在は主張しません。'
        f'[受領checkpoint](../{RECEIPT}) / [reference chain](../{EVIDENCE}/reference-chain.json) / [次の7行](../{EVIDENCE}/window-progress.json)。'
        'この受領で新native/旧試験/ROM再構成は0。全旧原本/R0/ROM/Save101/baseline不変。',goal)
    log(RECEIPT_TASK,'成功済み実readerのrun/artifact/commit/source全byteを受領し単一音声originを追加。正式787/87→788/86、選定8→7、安全容量0。',
        '原本完了success/全必須step・artifact全hash/全測定text・保存原本byte/mtime・canonical JSON・task graph PASS。測定再走/native/ROM再構成0。')
    pushed=publish(record_head,head,FORMAL_FILES|{REQUEST,RECEIPT,STATE,GUIDE,*LOGS},RECEIPT,RECEIPT_TASK)
    finish_public(FORMAL_FILES|{RECEIPT},dict(status='DONE',task=RECEIPT_TASK,source_head=head,commit=pushed,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),accepted_measurement_run=request['actions_run_id'],
        formal_classified=788,formal_unclassified=86,selected_unknown_origins=7,donor_safe_bytes=0,
        accepted_tests_rerun=0,native_processes=0,rom_reconstructions=0))


def main():
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and
        os.environ.get('GITHUB_RUN_ATTEMPT')=='1','指定repo/branchの初回だけ')
    m.need(not WORK.exists(),'新しい有限runner scope');PUBLIC.mkdir(parents=True)
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    nested=a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','tools/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
        'content/AGENTS.md','content/modernization/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    m.need(not nested.strip(),'追加AGENTS読取りが必要')
    if (ROOT/REQUEST).exists():receipt(head,observed)
    else:build(head,observed)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__)
            if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,attempt=ATTEMPT))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__)
        sys.exit(1)
