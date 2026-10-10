#!/usr/bin/env python3
"""音声originだけの固定asset照合・完了受領。旧測定を再走せず同branchへ保存する。"""
from __future__ import annotations
import contextlib
import datetime as dt
import io
import json
import os
import re
import subprocess
import sys
import traceback
import unittest
import urllib.request
import zipfile
import pr16_sound_origin_asset as m
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=m.ROOT
START='7bda26ae87dbd225246c71cd42a15ce20b7da12f'
BRANCH='codex/modernization-followup-20260908'
TASK='USER-20261011-SOUND-ORIGIN-ASSET'
STATE='content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE='docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
PARENT='content/modernization/pr16_typed_origins_receipt.json'
PROGRESS='content/modernization/pr16_typed_origins_receipt_evidence/window-progress.json'
SYMBOLS='content/modernization/pr16_donor_origins_evidence/symbol-frontier.json'
PRIOR_COMPLETION='content/modernization/pr16_typed_origins_receipt_evidence/actions-completion.json'
EVIDENCE='content/modernization/pr16_sound_origin_asset_evidence'
REPORT='content/modernization/pr16_sound_origin_asset_checkpoint.json'
REQUEST='content/modernization/pr16_sound_origin_asset_completion_request.json'
COMPLETE=EVIDENCE+'/actions-completion.json'
WF='.github/workflows/pr16-sound-origin-asset.yml'
CODE={'scripts/pr16_sound_origin_asset.py','scripts/pr16_sound_origin_asset_actions.py',
      'tests/test_pr16_sound_origin_asset.py',WF}
LOGS={'design/run_log.md','design/version_log.md'}
PROOFS={EVIDENCE+'/'+n for n in ('asset-binding.json','asset-tests.txt','prior-actions.json')}
OUTPUTS={REPORT,STATE,GUIDE,*PROOFS,*LOGS}
WORK=ROOT/'.local/pr16-sound-origin-asset'
PUBLIC=WORK/'public'
PHASE='preflight'
ATTEMPT=dict(rom_reconstructions_started=0,exact_candidate_bound=False,accepted_measurement_replays=0,
             native_processes=0,old_scope_test_reruns=0)


def read(name):
    path=ROOT/name
    m.need(path.is_file() and not path.is_symlink(),'通常ファイルのみ')
    return path.read_bytes()


def write(name,value):
    a.changed_write(name,m.encode(value) if isinstance(value,dict) else value)


def stamp():return dt.datetime.now(dt.timezone.utc).isoformat()


def public(name,value):
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def append_logs(task,summary,verify):
    now=stamp()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {task} / 選定窓の音声asset束縛\n'
        '- Version: sound-origin-asset-v1\n- Status: DONE（限定asset束縛。実readerと保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: 音声専用照合器/試験/Actions、証拠、固定引継ぎMD/JSON、両ログ。\n'
        f'- Verify: {verify}\n'
        '- Boundary: 正式787分類/87未知、選定窓の未分類8行、安全容量0を保持。'
        'assetのunused名は未使用証明でない。自然再生/実mixer/全alias不在/退役/保存統合は非主張。'
        '旧受入/R0/ROM/Save101/baseline不変、旧試験再走0。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはGit履歴とActions resultへ記録。\n'
        '- Network: 同repo PR/ref/Actions/artifactのGETと同branch非force push。'
        '公開出典は https://github.com/pret/pokefirered/tree/'+m.SOURCE+' の固定WAV・audio_rules.mk・wav2agb。'
        '検索語 DirectSoundWaveData_unused_sc88pro_unison_slap。音声assetは-b非圧縮規則、名前だけでは未使用と判定しない。\n')
    for name in LOGS:
        old=read(name);m.need(('- Task: '+task+' /').encode() not in old,'同task追記済み');write(name,old+block.encode())


def publish(base,head,allowed,report,task):
    publication.final_index(base,allowed,report)
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push直前HEAD競合')
    for name in allowed:m.need(a.git('show',':'+name)==read(name),'最終index全byte')
    a.git('config','user.name','github-actions[bot]')
    a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',task+': 固定音声assetの検証証拠と引継ぎを保存')
    a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in allowed:m.need(a.git('show','HEAD:'+name)==read(name),'commit blob読戻し')
    return pushed


def source_voice_rows(data):
    """固定sourceの使用箇所。現ROMのtable/consumer成立には昇格しない。"""
    rows=[];group=None;slot=0
    for line,text in enumerate(data.decode().splitlines(),1):
        label=re.fullmatch(r'(voicegroup\d+)::',text)
        if label:group=label.group(1);slot=0
        elif text.strip().startswith('voice_'):
            if m.SYMBOL in text:
                m.need(group is not None,'voicegroup範囲')
                rows.append(dict(group=group,slot=slot,line=line,row_sha256=m.identity(text.encode())['sha256'],
                    source_text=text.strip(),current_table_bound=False))
            slot+=1
    m.need(rows,'固定sourceの参照行')
    return rows


def build(head,observed):
    global PHASE
    m.need(set(a.git('diff','--name-only',START,head).decode().splitlines())==CODE,'新4source scope')
    m.need(not (ROOT/REPORT).exists() and not (ROOT/REQUEST).exists(),'受入asset再走禁止')
    state=json.loads(read(STATE));lane=state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id']=='SAVE_CAPACITY_SELECTED_WINDOW_NEXT_ASSET_BINDING','現行next')
    m.need([lane[k] for k in ('classified','unclassified','donor_safe_bytes')]==[787,87,0],'正式親境界')
    m.need(m.blob(read(PROGRESS))=='e41c3e93b02e8e51767e8801bef9b8cd0ffd929f' and
           m.blob(read(SYMBOLS))=='63f18a4568046f49e4bc38a292714b0730b125cf','固定8行/symbol親')
    progress=json.loads(read(PROGRESS));frontier=json.loads(read(SYMBOLS))
    selected=next(r for r in frontier['origins'] if r['hit']['address']==m.HIT)
    m.need(progress['remaining_count']==8 and progress['next_address']==m.HIT and
           selected['preceding_label']['address']==m.START and selected['following_label']['address']==m.FOLLOWING and
           selected['preceding_label']['labels'][0]['name']==m.SYMBOL,'保存symbol近傍の実数値')
    protected={PARENT,PROGRESS,SYMBOLS,PRIOR_COMPLETION,'CHATGPT_RESUME.md','AGENTS.md',
        'docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md','state/source-lock.json','config/active_play_baseline.json',
        'content/modernization/pr16_typed_origins_evidence/reader-profiles.json',
        'content/modernization/pr16_typed_origins_receipt_evidence/reference-chain.json',
        'content/modernization/pr16_typed_origins_receipt_evidence/unknown-frontier.json',
        'content/modernization/pr16_donor_window_evidence/windows.json','scripts/pr16_dex_hof_capacity_actions.py'}
    before={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in protected}
    PHASE='new-asset-tests'
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_sound_origin_asset.py'))
    public('asset-tests.txt',stream.getvalue().encode())
    m.need(tests.wasSuccessful() and tests.testsRun==32 and not tests.skipped,'新32人工境界試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    PHASE='receive-prior-completion-without-replay'
    prior=publication.accepted_run(38094277247,'da62cb4b0a7cf5e85bca730d164c0822f3d26112',
        ['Receive saved typed origins or record completed receipt','Run actions/upload-artifact@v4'])
    prior.update(saved_receipt_identity=m.identity(read(PRIOR_COMPLETION)),measurement_replays=0)
    PHASE='fixed-public-inputs'
    data={}
    for path,expected in m.BLOBS.items():
        with urllib.request.urlopen('https://raw.githubusercontent.com/pret/pokefirered/'+m.SOURCE+'/'+path,timeout=90) as response:
            raw=response.read(1_000_001)
        m.need(len(raw)<=1_000_000 and m.blob(raw)==expected,'固定source全blob')
        data[path]=raw
        target=WORK/'upstream'/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
    sources=m.source_contract(data)
    PHASE='independent-pcm-conversion'
    public('input-chunks.json',dict(chunks=[dict(id=t.decode('ascii'),size=len(v),offset=o)
        for t,v,o in m.chunks(data[m.WAV])]))
    generated,facts=m.convert_pcm(data[m.WAV])
    public('source-conversion.json',dict(conversion=facts,public_sources=sources,source_voice_rows=source_voice_rows(data['sound/voice_groups.inc'])))
    PHASE='fixed-cpp-converter-whole-output'
    tool=WORK/'upstream/tools/wav2agb'
    subprocess.run(['make','-C',str(tool)],check=True,capture_output=True)
    target=WORK/'independent-pcm.bin'
    subprocess.run([str(tool/'wav2agb'),'-b',str(WORK/'upstream'/m.WAV),str(target)],check=True,capture_output=True)
    m.need(target.read_bytes()==generated,'独立整数生成と固定C++生成の全byte')
    PHASE='new-sound-scope-exact-candidate'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions_started']=1;public('attempt.json',ATTEMPT)
    with (WORK/'private-reconstruction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        raw,checkpoint=reconstruction.reconstruct()
    m.need(m.identity(raw)==m.CANDIDATE and checkpoint['candidate']==m.CANDIDATE,'全32MiBと配置owner束縛')
    ATTEMPT['exact_candidate_bound']=True;public('attempt.json',ATTEMPT)
    PHASE='bounded-entire-asset-and-origin'
    asset=m.compare_asset(raw,generated,m.HIT,m.START,m.FOLLOWING,m.HIT_ID)
    m.need(asset['sample_index']+4<=facts['payload_samples'],'対象4byteは実PCM内。padding除外')
    proof=dict(schema_version=1,status='EXACT_PCM_ASSET_BOUND_READER_PENDING',candidate=m.CANDIDATE,
        public_sources=sources,conversion=facts,asset=asset,independent_cpp_equal=True,
        public_symbol_source=frontier['public_symbol_source'],saved_symbol_neighborhood=selected,
        source_voice_rows=source_voice_rows(data['sound/voice_groups.inc']),
        formal_classified=787,formal_unclassified=87,selected_unknown_origins=8,donor_safe_bytes=0,
        actual_consumer_proven=False,full_rom_scans=0,rom_reconstructions=1,native_processes=0,
        accepted_test_reruns=0,retirement_or_transfer_complete=False,
        outside_target_excludes_access=False,intra_donor_origins_covered=False,indirect_reference_completeness_claimed=False)
    m.need(m.encode(proof)==m.encode(json.loads(m.encode(proof))),'決定的JSON往復')
    for name,value in [(EVIDENCE+'/asset-binding.json',proof),(EVIDENCE+'/prior-actions.json',prior),
                       (EVIDENCE+'/asset-tests.txt',stream.getvalue().encode())]:write(name,value)
    saved={n:(read(n),(ROOT/n).stat().st_mtime_ns) for n in PROOFS}
    m.need(saved=={n:(read(n),(ROOT/n).stat().st_mtime_ns) for n in saved},'check byte/mtime不変')
    m.need(before=={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in before},'全旧原本byte/mtime不変')
    PHASE='record-and-nonforce-push'
    goal=('0x084723AFを含む固定音声asset全byteとWAV/C++/独立PCM生成を束縛済み。'
        '保存assetを再生成せず、固定voicegroup使用行から現候補の実table/音声channel/有限PCM readerへ結ぶ。'
        'unused名を不使用証明にしない。正式787/87・選定未知8件・安全容量0を維持。'
        '音声32試験/全asset/旧reader/全874scan/Forest/Bubble/窓最適化の無変更再走は禁止。'
        '窓外跨りread/旧owner内origin/間接参照/退役・移管/保存controller/heap/局所Saveは未完。')
    report=dict(schema_version=1,task=TASK,status=proof['status'],source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),actions_completion_confirmed=False,
        candidate=m.CANDIDATE,proof_path=EVIDENCE+'/asset-binding.json',proof_identity=m.identity(m.encode(proof)),
        source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},
        preserved_inputs={n:v[0] for n,v in before.items()},evidence_bindings={n:m.identity(read(n)) for n in sorted(PROOFS)},
        new_unit_tests=32,read_only_check_passed=True,task_graph_passed=True,attempt=ATTEMPT,
        formal_classified=787,formal_unclassified=87,remaining_selected_origins=8,donor_safe_bytes=0,
        actual_consumer_proven=False,formal_classification_changes=0,accepted_test_reruns=0,
        rom_reconstructions=1,native_processes=0,observed_head_checks=observed,next_ja=goal)
    write(REPORT,report)
    lane.update(status=proof['status'],checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_SOUND_ORIGIN_ACTUAL_READER',goal_ja=goal,
        read_paths=[GUIDE,REPORT,EVIDENCE+'/asset-binding.json',PROGRESS,SYMBOLS,'scripts/pr16_sound_origin_asset.py'],
        done_ja='保存assetの実table/条件付きPCM readerを束縛し、原本受領後のみ型分類へ追加。安全容量0を維持。')
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_SOUND_ASSET_BOUND_READER_PENDING'
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,new_unit_tests=32,accepted_tests_rerun=0,new_native_processes=0,
        rom_reconstructions=1,read_only_check_passed=True,task_graph_passed=True,classified=787,unclassified=87,donor_safe_bytes=0)
    state['recording']['pending_sound_asset_run']=dict(run_id=int(os.environ['GITHUB_RUN_ID']),source_head=head,
        output_report=REPORT,status='COMPLETION_NOT_YET_OBSERVED',replay_forbidden=True)
    write(STATE,state)
    text=read(GUIDE).decode();m.need('## 選定窓の音声asset全体束縛' not in text,'MD二重追記禁止')
    text=text.replace('## 次の未完作業','## 以前の停止点（履歴）')
    text+=('\n## 選定窓の音声asset全体束縛\n\n固定WAVと実audio_rules.mkの非圧縮規則を、独立整数変換と固定C++ wav2agb -bで全byte照合。'
        f'現候補0641af70の全SHA/配置ownerを照合後、0x08471C78からの全{asset["size"]}byteが一致しました。'
        f'対象0x084723AFはPCM sample index {asset["sample_index"]}からの4byteで、header/整列paddingではありません。\n\n'
        f'[全asset証拠](../{EVIDENCE}/asset-binding.json) / [checkpoint](../{REPORT})。'
        '固定sourceのvoicegroup参照行も記録しましたが、現ROMの実table/実PCM readerは未受入です。unused名を未使用証明にはしません。'
        '新32人工境界試験、C++独立対照、全asset/4byte、決定的read-only check、task graph。新scope候補再構成1、native0、旧受入再走0。'
        '正式787/87・選定未分類8・安全容量0、全旧原本/R0/ROM/Save101/baselineを維持。\n\n## 次の未完作業\n\n'+goal+'\n')
    write(GUIDE,text.encode())
    append_logs(TASK,f'固定音声全{asset["size"]}byteと対象4byte、WAV/固定C++/独立整数PCMの三者を照合。実consumerは未受入。',
        '新32試験・独立C++全byte・現候補全SHA/owner・限定asset・原本byte/mtime・JSON往復・task graph PASS。新ROM再構成1/native0。')
    pushed=publish(START,head,CODE|OUTPUTS,REPORT,TASK)
    for name in PROOFS|{REPORT}:public(name.rsplit('/',1)[-1],read(name))
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as z:
        for name in sorted((CODE|OUTPUTS|protected)-LOGS):z.writestr(name,read(name))
    result=dict(status='DONE',source_head=head,commit=pushed,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        new_unit_tests=32,rom_reconstructions=1,native_processes=0,accepted_test_reruns=0,
        formal_classification_changes=0,donor_safe_bytes=0)
    public('result.json',result)
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


def main():
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同branch初回のみ')
    m.need(not WORK.exists(),'新しい有限scopeのみ');PUBLIC.mkdir(parents=True)
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    nested=a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
        'content/AGENTS.md','content/modernization/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    m.need(not nested.strip(),'追加AGENTS読取りが必要')
    build(head,observed)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        frames=[dict(path=f.filename[len(str(ROOT))+1:],line=f.lineno) for f in traceback.extract_tb(exc.__traceback__)
            if f.filename.startswith(str(ROOT)+'/scripts/')]
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,exception_type=type(exc).__name__,frames=frames,attempt=ATTEMPT))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__)
        sys.exit(1)
