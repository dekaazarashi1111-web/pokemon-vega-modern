#!/usr/bin/env python3
"""固定first originの新有限命令調査と直前symbol測定の成功原本受領。"""
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
import pr16_first_origin as m
import pr16_donor_origins as symbols
import pr16_wiki_r0_reconcile_actions as a
import pr16_wiki_r0_publish as publication

ROOT=Path(__file__).resolve().parents[1]
START='c615eb6f384f25de4ce67fd64e851b6047726c4e'
TASK='USER-20261011-FIRST-ORIGIN-BOUNDS'
BRANCH='codex/modernization-followup-20260908'
STATE='content/modernization/pr16_wiki_first_execution_plan.json'
GUIDE='docs/PR16_FOREST_WALLPAPER_ASSET_JA.md'
PARENT='content/modernization/pr16_donor_origins_checkpoint.json'
MAP='content/modernization/pr16_donor_origins_evidence/symbol-frontier.json'
RECEIPT='content/modernization/pr16_donor_origins_evidence/actions-completion.json'
REPORT='content/modernization/pr16_first_origin_checkpoint.json'
EVIDENCE='content/modernization/pr16_first_origin_evidence'
FACTS=EVIDENCE+'/bounded-code-facts.json'
TESTS=EVIDENCE+'/bounds-tests.txt'
CODE={'scripts/pr16_first_origin.py','scripts/pr16_first_origin_actions.py',
      'tests/test_pr16_first_origin.py','.github/workflows/pr16-first-origin.yml'}
LOGS={'design/run_log.md','design/version_log.md'}
OUTPUTS={REPORT,FACTS,TESTS,RECEIPT,STATE,GUIDE,*LOGS}
WORK=ROOT/'.local/pr16-first-origin'
PUBLIC=WORK/'public'
PHASE='preflight'
SOURCE_COMMIT='c75f352304d529f6ba92d4f74b9cf8b5c3810788'
PUBLIC_BLOBS={'src/money.c':'4a9a4f464f9d1771386d6575faeaaad28b1eda3b',
              'src/script_pokemon_util.c':'bc11dc001b4399ecd25b8699e316816e1ebd8058',
              'ld_script.ld':'9a4b45031e93c1e1da8186d8c697332710526048'}


def read(name):
    path=ROOT/name;m.need(path.is_file() and not path.is_symlink(),'通常file: '+name)
    return path.read_bytes()


def write(name,value):a.changed_write(name,symbols.encode(value) if type(value) is dict else value)


def source(path,blob):
    url='https://raw.githubusercontent.com/pret/pokefirered/'+SOURCE_COMMIT+'/'+path
    with urllib.request.urlopen(url,timeout=90) as response:raw=response.read(100001)
    m.need(len(raw)<=100000,'公開source上限')
    return raw,dict(repository='pret/pokefirered',commit=SOURCE_COMMIT,path=path,**m.bind_public(raw,blob))


def receive_symbols():
    run=publication.accepted_run(38089484705,'3cdd1b0fef4d83eadc1a9b6197bfdbac24196e65',
        ['Bind selected origin symbols without replaying accepted measurements','Run actions/upload-artifact@v4'])
    artifact=a.fetch('actions/artifacts/11683572845')
    m.need(artifact['name']=='pr16-donor-origins-public-text' and not artifact['expired'] and
           artifact['digest']=='sha256:05bda8001cb4b6e47a3687a122ac8f6bcb9d7073b33ddee6cbf5c872b7d50cdd' and
           artifact['workflow_run']['id']==run['id'] and artifact['workflow_run']['head_sha']==run['source_head'], 'symbol artifact identity')
    raw=a.fetch('actions/artifacts/11683572845/zip',binary=True)
    m.need(m.identity(raw)==dict(size=199354,sha256=artifact['digest'][7:]),'symbol ZIP全identity')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        names=archive.namelist();m.need(len(names)==len(set(names))==5,'closed5members')
        expected={'pr16_donor_origins_checkpoint.json':PARENT,'symbol-frontier.json':MAP,
                  'symbol-tests.txt':'content/modernization/pr16_donor_origins_evidence/symbol-tests.txt'}
        m.need(set(names)==set(expected)|{'scoped-context.zip','result.json'},'closed member名')
        members={}
        for info in archive.infolist():
            m.need(info.file_size<2_000_000 and (info.external_attr>>16)&0o170000!=0o120000,'有限通常member')
            members[info.filename]=archive.read(info)
        for name,path in expected.items():m.need(members[name]==read(path)==a.git('show',START+':'+path),'測定公開原本byte不変')
        result=json.loads(members['result.json'])
        m.need(result['commit']==START and result['status']=='DONE' and result['new_unit_tests']==20 and
               result['actions_run_id']==run['id'] and result['source_head']==run['source_head'],'symbol result束縛')
        with zipfile.ZipFile(io.BytesIO(members['scoped-context.zip'])) as context:
            for info in context.infolist():
                path=Path(info.filename)
                m.need(not path.is_absolute() and '..' not in path.parts and info.file_size<2_000_000 and
                       (info.external_attr>>16)&0o170000!=0o120000,'context安全範囲')
                m.need(context.read(info)==a.git('show',START+':'+path.as_posix()),'全context committed byte')
    return dict(schema_version=1,status='COMPLETED_ORIGIN_SYMBOL_ACTIONS_RECEIVED',measurement_commit=START,
                actions=run,artifact_id=artifact['id'],zip_identity=m.identity(raw),
                member_identities={n:m.identity(b) for n,b in sorted(members.items())},
                measurement_replays=0,old_scope_test_reruns=0,claims=dict(symbols.CLAIMS))


def main():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY')==a.REPO and os.environ.get('GITHUB_REF')=='refs/heads/'+BRANCH
           and os.environ.get('GITHUB_RUN_ATTEMPT')=='1','同branch初回のみ')
    head=a.git('rev-parse','HEAD').decode().strip();m.need(head==os.environ['GITHUB_SHA'],'event HEAD')
    observed=a.live(head)
    m.need(set(a.git('diff','--name-only',START,head).decode().splitlines())==CODE,'新4source範囲')
    m.need(not WORK.exists() and not (ROOT/REPORT).exists() and not (ROOT/RECEIPT).exists(),'完了scope再走禁止')
    m.need(not a.git('status','--porcelain','--untracked-files=no').strip(),'tracked clean')
    nested=a.git('ls-files','--','scripts/AGENTS.md','tests/AGENTS.md','docs/AGENTS.md','design/AGENTS.md',
                  'content/AGENTS.md','content/modernization/AGENTS.md','.github/AGENTS.md','.github/workflows/AGENTS.md')
    m.need(not nested.strip(),'追加AGENTS読取りが必要')
    state=json.loads(read(STATE));m.need(state['next_action']['id']=='SAVE_CAPACITY_FIRST_ORIGIN_SOURCE_AND_CONSUMER', '現在のnext')
    m.need(symbols.blob(read(PARENT))=='0a95e6b6a46bb9f5af39f82fed45ee477e21be34' and
           symbols.blob(read(MAP))=='63f18a4568046f49e4bc38a292714b0730b125cf','symbol測定原本')
    protected={PARENT,MAP,'CHATGPT_RESUME.md','docs/PR16_WIKI_FIRST_EXECUTION_POLICY_JA.md',
        'content/modernization/pr16_donor_window_checkpoint.json','content/modernization/pr16_donor_window_evidence/windows.json',
        'scripts/pr16_donor_origins.py','scripts/pr16_donor_origins_actions.py','tests/test_pr16_donor_origins.py'}
    before={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in protected}
    PUBLIC.mkdir(parents=True)
    PHASE='new-tests-and-prior-receipt'
    stream=io.StringIO();tests=unittest.TextTestRunner(stream=stream,verbosity=2).run(
        unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_first_origin.py'))
    (PUBLIC/'bounds-tests.txt').write_text(stream.getvalue())
    m.need(tests.wasSuccessful() and tests.testsRun==35 and not tests.skipped,'新35試験')
    subprocess.run(['python3','-B','scripts/validate_task_graph.py'],cwd=ROOT,check=True,capture_output=True)
    receipt=receive_symbols()
    PHASE='fixed-public-source'
    public={};texts={}
    for path,blob in PUBLIC_BLOBS.items():texts[path],public[path]=source(path,blob)
    m.need(all(name.encode() in texts['src/money.c'] for name in (*m.CALLS,'HideMoneyBox')), 'money source意味')
    m.need(b'src/money.o(.text);\n        src/script_pokemon_util.o(.text);' in texts['ld_script.ld'],'公開link順序')
    frontier=json.loads(read(MAP));symbol_source=frontier['public_symbol_source']
    url='https://raw.githubusercontent.com/'+symbol_source['repository']+'/'+symbol_source['commit']+'/'+symbol_source['path']
    with urllib.request.urlopen(url,timeout=90) as response:raw_symbols=response.read(symbol_source['size']+1)
    m.need(m.identity(raw_symbols)=={k:symbol_source[k] for k in ('size','sha256')} and symbols.blob(raw_symbols)==symbol_source['git_blob'],'全JP symbol出典')
    names=set(m.CALLS)|{'HideMoneyBox','HealPlayerParty','__subsf3','__mulsf3'}
    selected={}
    for number,line in enumerate(raw_symbols.decode().splitlines(),1):
        row=line.split('\t')
        if len(row)==8 and row[4] in names:
            m.need(row[4] not in selected,'公開name重複')
            selected[row[4]]=dict(address=int(row[1],16),line=number,fields=row,row_sha256=m.identity(line.encode())['sha256'])
    m.need(set(selected)==names,'公開symbol必要行')
    m.need(selected['HideMoneyBox']['address']==m.SCOPES['preceding_public_entry'][0] and
           selected['HealPlayerParty']['address']==m.SCOPES['following_public_entry'][0], '固定前後entry')
    PHASE='new-candidate-scope'
    import pr16_dex_hof_capacity_actions as reconstruction
    import pr16_dex_hof_donor as donor
    reconstruction.OUT=WORK/'candidate';reconstruction.OUT.mkdir()
    with (WORK/'private-reconstruction.log').open('w') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        candidate,checkpoint=reconstruction.reconstruct()
        m.need(m.identity(candidate)==m.CANDIDATE and checkpoint['candidate']==m.CANDIDATE,'現候補全identity')
        owners=donor.bind_owners(candidate,checkpoint)
    m.need(len(owners)==115,'現owner115')
    binary=WORK/'candidate.gba';binary.write_bytes(candidate)
    hits=[]
    for item in frontier['origins']:
        hit=item['hit'];data=candidate[hit['address']-m.BASE:hit['address']-m.BASE+4]
        m.need(m.identity(data)=={k:hit[k] for k in ('size','sha256')} and donor.canonical(int.from_bytes(data,'little'))==hit['target'],'保存10originの現候補byte/target')
        hits.append(dict(hit=hit,matching_current_owners=m.overlap_owners(hit,owners),current_four_bytes_bound=True))
    ranges={name:m.disassemble(binary,candidate,address,size) for name,(address,size) in m.SCOPES.items()}
    cfg=m.normal_return_cfg(ranges['preceding_public_entry']['instructions'],selected['HideMoneyBox']['address'])
    expected_calls=[selected[name]['address'] for name in m.CALLS]
    cfg['matches_public_money_call_order']=[row['target'] for row in cfg['calls']]==expected_calls
    cfg['actual_runtime_execution_observed']=False
    overlap=[r for r in ranges['first_origin_envelope']['instructions'] if r['address']<m.HIT+4 and m.HIT<r['address']+r['size']]
    facts=dict(schema_version=1,status='FIRST_ORIGIN_BOUNDED_BYTES_AND_CODE_SHAPES_BOUND_CONSUMER_UNPROVEN',
        candidate=m.CANDIDATE,selected_hits=hits,public_sources=public,public_symbol_source=symbol_source,
        public_symbol_rows=selected,ranges=ranges,preceding_entry_normal_return_cfg=cfg,
        first_origin_overlapping_instruction_shapes=overlap,claims=dict(m.CLAIMS),
        objdump_version=subprocess.check_output(['arm-none-eabi-objdump','--version'],text=True).splitlines()[0],
        limitations_ja=['public JP前後labelとGNU ARMv4T命令形を現候補へ束縛。命令形だけで実code/owner/consumerとしない。',
                        'CFGは前entryと同期call正常帰還の条件付き。未知control/範囲外/間接分岐を境界として残す。',
                        'このprobeからformal FALSE_POSITIVEを発行しない。窓外read/owner内origin/間接参照・保存統合は未証明。'])
    encoded=symbols.encode(facts);write(FACTS,encoded)
    saved=(read(FACTS),(ROOT/FACTS).stat().st_mtime_ns)
    m.need(read(FACTS)==symbols.encode(json.loads(read(FACTS))) and saved==(read(FACTS),(ROOT/FACTS).stat().st_mtime_ns),'read-only canonical byte/mtime')
    m.need(before=={n:(m.identity(read(n)),(ROOT/n).stat().st_mtime_ns) for n in before},'全旧原本byte/mtime保全')
    m.need(m.identity(binary.read_bytes())==m.CANDIDATE,'一時候補も全byte不変')
    PHASE='record-and-nonforce-push'
    goal=('保存したfirst-origin有限命令/owner事実から0x080A006Fの実型とconsumerを確定する。'
          '前後labelや逆アセンブル形だけの分類は禁止。実必要reader/配置元へ閉じる。'
          '正式785/89、安全容量0。既受入symbol20試験/今回35試験/有限ROM測定をsource不変なら再走しない。'
          '全874scanと旧Forest/Bubbleは再走せず、窓外跨りread/旧owner内origin/間接参照を残す。')
    report=dict(schema_version=1,task=TASK,status=facts['status'],source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,candidate=m.CANDIDATE,claims=dict(m.CLAIMS),rom_reconstructions=1,
        new_unit_tests=35,facts_path=FACTS,facts_identity=m.identity(encoded),symbol_actions_receipt_path=RECEIPT,
        read_only_check_passed=True,protected_inputs_unchanged=True,task_graph_passed=True,
        source_bindings={n:m.identity(read(n)) for n in sorted(CODE)},preserved_inputs={n:v[0] for n,v in sorted(before.items())},
        observed_head_checks=observed,next_ja=goal)
    write(REPORT,report);write(RECEIPT,receipt);write(TESTS,stream.getvalue().encode())
    state['owner_execution_plan']['technical_lanes']['save_capacity'].update(status=facts['status'],checkpoint_path=REPORT,next_ja=goal)
    state['next_action']=dict(id='SAVE_CAPACITY_FIRST_ORIGIN_TYPED_CONSUMER',goal_ja=goal,
        read_paths=[GUIDE,REPORT,FACTS,RECEIPT,'scripts/pr16_first_origin.py'],
        done_ja='現候補の実owner/実consumerと対象4byteの解釈を有限証明。形のみのFALSE_POSITIVE化禁止。')
    state['observed_head_checks']=observed
    state['recording']['status']='R0_READY_FIRST_ORIGIN_BOUNDED_FACTS_SAVE_INTEGRATION_PENDING'
    state['recording']['last_execution']=dict(task=TASK,source_head=head,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        actions_completion_confirmed=False,new_unit_tests=35,accepted_tests_rerun=0,new_native_processes=0,rom_reconstructions=1,
        read_only_check_passed=True,task_graph_passed=True,classified=785,unclassified=89,donor_safe_bytes=0)
    write(STATE,state)
    old=read(GUIDE).decode();m.need('## 先頭originの現候補有限範囲' not in old,'guide重複禁止')
    old=old.replace('## 次の未完作業','## 以前の停止点（履歴）')
    old+=(f'\n## 先頭originの現候補有限範囲\n\n新候補復元1回で全SHA/115ownerと保存10originを照合。'
        f'4個の有限範囲、前entryの条件付きCFG、first originと交差する命令形を記録しました。'
        f'前entryの公開money呼出順一致={cfg["matches_public_money_call_order"]}、境界数={len(cfg["boundaries"])}。'
        '形を実consumer証明には昇格していません。\n\n'
        f'[有限事実](../{FACTS}) / [checkpoint](../{REPORT}) / [symbol成功Actions受領](../{RECEIPT})。'
        '新35試験・読取専用byte/mtime・task graph・全旧原本保全。native0、旧受入再走0、正式785/89、安全容量0。'
        '\n\n## 次の未完作業\n\n'+goal+'\n')
    write(GUIDE,old.encode())
    now=dt.datetime.now(dt.timezone.utc).isoformat()
    block=(f'\n## {now}\n- Timestamp: {now}\n- Task: {TASK} / first originの有限現候補証拠\n'
        '- Version: first-origin-bounds-v1\n- Status: DONE（有限測定。実consumer/保存統合は未完）\n'
        '- Summary: 完了symbol Actions/ZIP全5member/公開treeを受領。新候補復元1回で保存10originと115ownerを束縛し、4有限範囲の命令形と前entryの条件付きCFGを保存。\n'
        '- Files changed: 新有限検証器/35境界試験/専用Actions、有限事実とcheckpoint、symbol成功receipt、固定引継ぎMD/JSON、両ログ。\n'
        '- Verify: 新35 tests、現候補全SHA、115owner、10origin全4byte/hash/target、read-only byte/mtime、旧原本保全、task graph。最終index新規private違反0と全体guard結果は別記録。\n'
        '- Boundary: 逆アセンブル形はowner/実consumerの証明ではない。正式785/89・安全容量0、ROM/Save101/R0/baseline不変。新native0/旧試験再走0。\n'
        '- Commit: この記録を含む同branch単親通常commit。実SHAはGit履歴/Actions resultを参照。\n'
        '- Network: 同repo PR/ref/Actions/固定private入力、固定公開pret/pokefirered c75f3523のsrc/money.c・src/script_pokemon_util.c・ld_script.ld、ComplexRobot/frlg-sym c04a3154のJP auditをGET。同branch非force push。\n'
        '- Sources: https://github.com/pret/pokefirered/tree/c75f352304d529f6ba92d4f74b9cf8b5c3810788 ; https://github.com/ComplexRobot/frlg-sym/tree/c04a31542086b20d8c6ee641eaa70b8db6713fd3 。前後関数と配置順/JP対応行を有限範囲と照合。\n')
    for name in LOGS:
        old=read(name);m.need(('- Task: '+TASK+' /').encode() not in old,'同task重複禁止');write(name,old+block.encode())
    publication.final_index(START,CODE|OUTPUTS,REPORT)
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==head,'push前競合')
    for name in CODE|OUTPUTS:m.need(a.git('show',':'+name)==read(name),'最終index全byte')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 保存10originと先頭有限命令範囲を検証し引継ぎを記録')
    a.git('push','origin','HEAD:'+BRANCH)
    pushed=a.git('rev-parse','HEAD').decode().strip();m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0]==pushed,'push後HEAD')
    for name in CODE|OUTPUTS:m.need(a.git('show','HEAD:'+name)==read(name),'commit blob読戻し')
    for name in (FACTS,REPORT,RECEIPT):(PUBLIC/Path(name).name).write_bytes(read(name))
    context={*CODE,STATE,GUIDE,REPORT,FACTS,RECEIPT,
        'scripts/pr16_forest_wallpaper_receipt.py','scripts/pr16_dex_hof_blastoise_chain.py',
        'content/modernization/pr16_forest_wallpaper_receipt.json',
        'content/modernization/pr16_forest_wallpaper_receipt_evidence/reference-chain.json',
        'content/modernization/pr16_forest_wallpaper_receipt_evidence/unknown-frontier.json'}
    with zipfile.ZipFile(PUBLIC/'scoped-context.zip','w',zipfile.ZIP_DEFLATED) as archive:
        for name in sorted(context):archive.writestr(name,read(name))
    (PUBLIC/'result.json').write_bytes(symbols.encode(dict(status='DONE',task=TASK,commit=pushed,source_head=head,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']),new_unit_tests=35,rom_reconstructions=1,claims=m.CLAIMS)))
    print(f'RESULT=DONE TASK={TASK} VERIFY=PASS COMMIT={pushed}')


if __name__=='__main__':
    try:main()
    except Exception as exc:
        if PUBLIC.exists():
            (PUBLIC/'failure.json').write_bytes(symbols.encode(dict(status='FAILED_NOT_ACCEPTED',phase=PHASE,
                exception_type=type(exc).__name__,frames=[dict(source=Path(f.filename).name,line=f.lineno,function=f.name)
                    for f in traceback.extract_tb(exc.__traceback__) if '/scripts/' in f.filename])))
        print(f'RESULT=STOPPED TASK={TASK} VERIFY=FAIL COMMIT=- PHASE={PHASE}');sys.exit(1)
