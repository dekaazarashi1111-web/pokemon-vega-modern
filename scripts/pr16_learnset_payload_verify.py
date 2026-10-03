#!/usr/bin/env python3
"""後継payloadの限定検証/完了run記録。原本再生成・native・ROM書込は呼ばない。"""
from __future__ import annotations
from collections import Counter, defaultdict
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from tools import pr16_learnset_successor as s
from tools import pr16_learnset_payloads as p
from tools import pr16_learnset_species_binding as b
from pr16_resume import STATE, DOC, render

BASE=s.BASE
TASK='USER-20260921-LEARNSET-BASELINE-RESET'
BRANCH='codex/modernization-followup-20260908'
LOCK=BASE+'pr16_learnset_payload_inputs.json'
CHECKPOINT=BASE+'pr16_learnset_payload_checkpoint.json'
EVIDENCE=BASE+'pr16_learnset_payload_evidence'
GUIDE='docs/PR16_LEARNSET_PAYLOADS_JA.md'
REQUEST='.github/pr16-learnset-payload-record.json'
WORK=ROOT/'.local/pr16-learnset-payload'
TABLES=ROOT/'.local/pr16-learnset-binding/tables'
PROOF=('receipt.json','species-bindings.jsonl','binding-routes.jsonl','catalogs.json',
       'audit.json','verification.json','unit-species.txt','unit-payload.txt')
CODE=('tools/pr16_learnset_species_binding.py','tools/pr16_learnset_payloads.py',
      'tests/test_pr16_learnset_species_binding.py','tests/test_pr16_learnset_payloads.py',
      'scripts/pr16_learnset_payload_verify.py','.github/workflows/pr16-learnset-payload.yml',
      '.github/workflows/pr16-learnset-payload-record.yml',LOCK,REQUEST,
      '.github/workflows/pr16-learnset-adapter-sources.yml')


def need(ok,message):
    if not ok:raise ValueError(message)


def git(*args):
    return subprocess.check_output(['git',*args],cwd=ROOT)


def current_pr(head):
    from pr16_wiki_reconcile import fetch
    pr=fetch('pulls/16')
    need(pr['state']=='open' and pr['draft'] is True and not pr['merged']
         and pr['head']['ref']==BRANCH and pr['head']['sha']==head,'PR/remote HEAD競合')


def snapshot(paths):
    return {str(path):(s.identity(path),path.stat().st_mtime_ns) for path in paths}


def independent_audit(folder):
    """compiler/slot補正関数を呼ばず、旧Wikiと原本行から出力byteを全数照合する。"""
    report=s.read_json(folder/'receipt.json')
    for name,ident in report['files'].items():s.bound(folder/name,ident)
    catalog=defaultdict(set)
    for owner in s.rows(ROOT/(s.WIKI+'learnsets.jsonl')):
        for route in owner['routes']:
            if route['route'] not in ('machine','tutor'):continue
            family=route['route'];number=route['slot']
            need(type(number) is int and 1<=number<=({'machine':128,'tutor':64}[family]),'候補Wikiの1始まり境界')
            catalog[family,route['move_id']].add(number-1)
    indexes={(r['consumer'],r['species_id']):r for r in s.rows(folder/'consumer-index.jsonl')}
    ledger={(r['consumer'],r['species_id'],r['source_id']):r for r in s.rows(folder/'route-ledger.jsonl')}
    need(len(indexes)==1671*9 and len(ledger)==128352,'index/ledger全数/重複不一致')
    new=defaultdict(list)
    for row in s.rows(folder/'binding-routes.jsonl'):new[row['consumer'],row['species_id']].append(row)
    need(sum(map(len,new.values()))==64,'明示追加64経路不一致')
    binding={r['species_id']:r for r in s.rows(folder/'species-bindings.jsonl')}
    need(len(binding)==191 and len([r for r in binding.values() if r['policy'] in b.NONPERMANENT])==188,'binding内訳不一致')
    # 1262は未選択191枠ではなく公式選択済み。既存P02解除条件は別正本で保全する。
    ultra=[r for r in s.rows(TABLES/'species_coverage.jsonl') if r['species_id']==1262]
    reverse=[r for r in s.read_json(ROOT/p.CONTRACT_PATHS['p02'])['current_table']['rows']
             if r['source']['canonical_id']==1262 and r['method']['family']=='BATTLE_TRANSFORM'
             and r['condition']['parameter']['value']==0]
    need(1262 not in binding and len(ultra)==1 and ultra[0]['selection']=='OFFICIAL_SOURCE_SELECTED'
         and [r['target']['canonical_id'] for r in reverse]==[1260,1261], '選択済みUltra/2解除先を変更')
    need([r['move_id'] for r in new['level_up',649]]==[33,81,535]
         and [r['move_id'] for r in new['machine',649]]==[489],'Caterpie訂正4経路不一致')
    need({f:len(new[f,1670]) for f in b.CONSUMERS if new[f,1670]}==
         {'egg':4,'level_up':14,'machine':38,'shared_egg':4},'Own Tempo60経路不一致')
    payloads={x.stem:x.read_bytes() for x in folder.glob('*.bin')}
    audited=Counter();original=0;added=0;seen=set();blocked=0;preserved=0;corrected=0
    for family in b.CONSUMERS:
        cursor=0;archive_cursor=0
        blocks=list(s.rows(TABLES/(family+'.jsonl')))
        donors={x['species_id']:x for x in blocks}
        for block in blocks:
            sid=block['species_id'];entry=indexes[family,sid]
            if sid in binding and sid not in (649,1670):
                need(entry['payload'] is None,'除外/未接続ownerを空payload化')
                if sid==1029:
                    need(entry['status']=='BLOCKED_SOURCE_ADOPTION','Floette採用境界を無断解除');blocked+=1
                else:
                    need(entry['status']=='IDENTITY_ONLY_NO_REPLACEMENT' and entry['identity']['preserve_current_moves'] is True,'identity保全不一致');preserved+=1
                continue
            rows=new[family,sid] if sid in (649,1670) else block['routes']
            need(entry['status']=='PAYLOAD_PREPARED_NOT_INSTALLED' and entry['routes']==len(rows),'owner状態/件数不一致')
            if sid==1670:
                expected=donors[1142]['routes']
                need(len(rows)==len(expected),'Own Tempo donor件数不一致')
                for actual,source in zip(rows,expected):
                    need(actual['provenance']==source['provenance']
                         and actual['binding_origin']['record_sha256']==hashlib.sha256(s.encode(source)).hexdigest()
                         and actual['form_key']=='FORM_KEY_ROCKRUFF_OWN_TEMPO','cloneで原本条件を変更')
            for row in rows:
                key=(family,sid,row['source_id']);seen.add(key)
                item=ledger[key]
                need(item['route_sha256']==hashlib.sha256(s.encode(row)).hexdigest()
                     and item['runtime_applied'] is False and item['explicit_binding']==(sid in (649,1670)), '全行provenance/owner不一致')
                audited[family]+=1
                if sid in (649,1670):added+=1
                else:original+=1
                if family in ('machine','tutor'):
                    expect=sorted(catalog[family,row['move_id']])
                    need(item['bit_indexes_zero_based']==expect,'Wikiから独立算出したbitと不一致')
                    corrected+=bool(expect) and sid not in (649,1670)
            where=entry['payload']
            if family in ('pre_evolution_carry','form_change'):
                need(where is None and family not in payloads,'条件付き経路のflat付与禁止')
                continue
            need(where['file']==family+'.bin' and where['offset']==cursor,'配置前payloadの隙間/重複')
            raw=payloads[family][cursor:cursor+where['size']];need(len(raw)==where['size'],'payload範囲外');cursor+=len(raw)
            if family=='level_up':
                expected=[]
                for row in rows:
                    src=row['provenance']['source_route'];lev=src.get('target_learning_level',src.get('learning_level',src.get('level')))
                    expected.append((row['move_id'],lev))
                decoded=list(struct.iter_unpack('<HB',raw))
                need(decoded==expected+[(0,255)],'独立level decode/終端不一致')
            elif family in ('machine','tutor'):
                expect={n for row in rows for n in catalog[family,row['move_id']]}
                decoded={n for n in range(128) if int.from_bytes(raw,'little') & (1<<n)}
                need(len(raw)==16 and decoded==expect,'独立compatibility decode不一致')
                archive=entry['archive'];expect_moves=list(dict.fromkeys(row['move_id'] for row in rows if not catalog[family,row['move_id']]))
                need(archive['offset']==archive_cursor,'archive gap/overlap')
                ar=payloads[family+'_archive'][archive_cursor:archive_cursor+archive['size']];archive_cursor+=len(ar)
                need([x[0] for x in struct.iter_unpack('<H',ar)]==expect_moves,'独立archive decode不一致')
            elif family=='egg':
                decoded=[x[0] for x in struct.iter_unpack('<H',raw)]
                expect=[20000+sid]+[row['move_id'] for row in rows if not row['conditional_egg']]
                need(decoded==expect,'条件付きegg混入/独立egg decode不一致')
            else:
                need([x[0] for x in struct.iter_unpack('<H',raw)]==list(dict.fromkeys(row['move_id'] for row in rows)), '独立専用consumer decode不一致')
        if family in ('pre_evolution_carry','form_change'):continue
        suffix=payloads[family][cursor:]
        need(suffix==(b'\xff\xff' if family=='egg' else b''),'payload末尾の余剰/終端不一致')
        if family in ('machine','tutor'):need(archive_cursor==len(payloads[family+'_archive']),'archive余剰')
    need(seen==set(ledger) and original==128288 and added==64 and blocked==9 and preserved==188*9 and corrected==33321,'全数監査不一致')
    return {'status':'PASS_INDEPENDENT_ALL_ROWS_AND_PAYLOAD_BYTES','source_rows':original,'explicit_binding_rows':added,
            'consumer_counts':dict(audited),'identity_only_species':188,'blocking_species':[1029],
            'wiki_one_based_to_bit_rows':corrected,'conditions_retained_by_source_hash':True,
            'rom_changes':0,'native_runs':0,'install_ready':False}


def verify():
    from pr16_learnset_binding_verify import restore
    WORK.mkdir(parents=True,exist_ok=False)
    head=git('rev-parse','HEAD').decode().strip();need(head==os.environ['GITHUB_SHA'],'実行HEAD不一致');current_pr(head)
    lock=s.read_json(ROOT/LOCK)
    for name,ident in lock['inputs'].items():s.bound(ROOT/name,ident)
    proof=WORK/'proof';proof.mkdir()
    for label,pattern,count in [('species','test_pr16_learnset_species_binding.py',30),('payload','test_pr16_learnset_payloads.py',24)]:
        run=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p',pattern,'-v'],cwd=ROOT,capture_output=True,text=True)
        text=run.stdout+run.stderr;(proof/('unit-'+label+'.txt')).write_text(text)
        need(run.returncode==0 and re.findall(r'^Ran (\d+) tests? in ',text,re.M)==[str(count)] and re.search(r'\nOK\s*$',text),'新規試験未成功')
    tables,receipt,reused=restore();need(tables==TABLES,'復元先不一致')
    watched=list(tables.iterdir())+[ROOT/name for name in receipt['inputs'] if '/' in name]+[ROOT/name for name in lock['inputs']]
    before=snapshot(watched)
    for seed in (11,29):
        dest=WORK/('build'+str(seed))
        subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'build',str(dest)],cwd=ROOT,
                       env=dict(os.environ,PYTHONHASHSEED=str(seed)),check=True,timeout=240)
        actual={x.name:s.identity(x) for x in dest.iterdir()}
        need(actual==lock['expected_outputs'],'独立プロセス/ローカルhash不一致: '+str(seed))
    audit=independent_audit(WORK/'build11')
    need(snapshot(watched)==before,'source byte/mtime変化')
    for name in PROOF[:4]:shutil.copyfile(WORK/'build11'/name,proof/name)
    (proof/'audit.json').write_bytes(s.encode(audit))
    report={'task':TASK,'source_head':head,'run_id':int(os.environ['GITHUB_RUN_ID']),
            'status':'PASS_NEW_BINDING_AND_PAYLOAD_SCOPE','focused_tests':54,
            'independent_processes':2,'local_actions_all_output_hashes_match':True,
            'readonly_source_byte_mtime_unchanged':True,'accepted_source_generations_rerun':0,
            'accepted_native_runs_rerun':0,'accepted_hatch_tests_rerun':0,'runtime_applied':False,
            'reused_successor':reused,'inputs_lock':s.identity(ROOT/LOCK),
            'proof_files':{x.name:s.identity(x) for x in proof.iterdir()},
            'payload_files':lock['expected_outputs']}
    (proof/'verification.json').write_bytes(s.encode(report))
    subprocess.run([sys.executable,'-B','scripts/pr16_resume.py','check'],cwd=ROOT,check=True)
    subprocess.run(['git','diff','--exit-code'],cwd=ROOT,check=True)
    print(json.dumps(audit,ensure_ascii=False))


def completed_run(rid,head,path,jobname):
    from pr16_wiki_reconcile import fetch
    run=fetch(f'actions/runs/{rid}');jobs=fetch(f'actions/runs/{rid}/jobs?per_page=100')
    need(run['head_sha']==head and run['head_branch']==BRANCH and run['path']==path
         and run['status']=='completed' and run['conclusion']=='success','Actions完了条件不一致')
    need(jobs['total_count']==len(jobs['jobs'])==1,'job件数/ページ不一致')
    job=jobs['jobs'][0]
    need(job['name']==jobname and job['head_sha']==head and job['status']=='completed' and job['conclusion']=='success'
         and all(x['status']=='completed' and x['conclusion']=='success' for x in job['steps']), 'job/step未成功')
    return {'id':rid,'head_sha':head,'status':run['status'],'conclusion':run['conclusion'],
            'path':path,'jobs':[{'id':job['id'],'name':jobname,'status':job['status'],'conclusion':job['conclusion'],
                              'steps':[{'name':x['name'],'status':x['status'],'conclusion':x['conclusion']} for x in job['steps']]}]}


def record():
    from pr16_wiki_reconcile import fetch
    request=s.read_json(ROOT/REQUEST);head=git('rev-parse','HEAD').decode().strip();current_pr(head)
    done=completed_run(request['run_id'],request['source_head'],'.github/workflows/pr16-learnset-payload.yml','payload-verify')
    for name,ident in s.read_json(ROOT/LOCK)['inputs'].items():s.bound(ROOT/name,ident)
    artifacts=fetch(f"actions/runs/{request['run_id']}/artifacts?per_page=100")
    need(artifacts['total_count']==len(artifacts['artifacts'])==2,'artifact集合不一致')
    by_name={a['name']:a for a in artifacts['artifacts']}
    for item in request['artifacts']:
        actual=by_name[item['name']]
        need(all(actual[k]==item[k] for k in ('id','name','digest','size_in_bytes','workflow_run'))
             and actual['expired'] is False,'artifact binding不一致')
    artifact=by_name['pr16-learnset-payload-proof'];raw=fetch(f"actions/artifacts/{artifact['id']}/zip",binary=True)
    need(hashlib.sha256(raw).hexdigest()==artifact['digest'].removeprefix('sha256:') and len(raw)==artifact['size_in_bytes'],'proof外側hash不一致')
    with zipfile.ZipFile(io.BytesIO(raw)) as archive:
        need(len(archive.infolist())==len(PROOF) and set(archive.namelist())==set(PROOF),'proof集合/重複不一致')
        files={}
        for name in PROOF:
            info=archive.getinfo(name);need(info.file_size<=1000000 and info.external_attr>>28!=0xA and not info.is_dir(),'proof size/symlink不正')
            data=archive.read(name);data.decode('utf-8');need(b'\0' not in data,'binaryをtracked証拠へ入れない');files[name]=data
    verification=json.loads(files['verification.json']);receipt=json.loads(files['receipt.json']);audit=json.loads(files['audit.json'])
    need(verification['source_head']==request['source_head'] and verification['run_id']==request['run_id']
         and verification['status']=='PASS_NEW_BINDING_AND_PAYLOAD_SCOPE' and verification['focused_tests']==54
         and verification['inputs_lock']==s.identity(ROOT/LOCK),'proof検証identity不一致')
    need(set(verification['proof_files']) == set(PROOF)-{'verification.json'}
         and verification['independent_processes']==2
         and verification['local_actions_all_output_hashes_match'] is True
         and verification['readonly_source_byte_mtime_unchanged'] is True
         and all(verification[k]==0 for k in ('accepted_source_generations_rerun','accepted_native_runs_rerun','accepted_hatch_tests_rerun'))
         and verification['runtime_applied'] is False, 'proof受入境界不一致')
    for name,ident in verification['proof_files'].items():need(b.identity(files[name])==ident,'proof内側hash不一致')
    need(b.identity(files['receipt.json']) == s.read_json(ROOT/LOCK)['expected_outputs']['receipt.json'], 'receipt固定hash不一致')
    need(verification['payload_files']==s.read_json(ROOT/LOCK)['expected_outputs'],'payload固定hash不一致')
    need(audit['status']=='PASS_INDEPENDENT_ALL_ROWS_AND_PAYLOAD_BYTES' and audit['source_rows']==128288
         and audit['explicit_binding_rows']==64 and audit['blocking_species']==[1029],'監査完了条件不一致')
    old=completed_run(35656548503,'1fa45557c6ad1ae4ed0c976f84b84e953abf37ee','.github/workflows/pr16-learnset-binding.yml','binding-verify')
    snapshot_done=completed_run(35657130145,'7f53d58e0357c9172b6838a6e51f840008e64508','.github/workflows/pr16-learnset-adapter-sources.yml','adapter-sources')
    dest=ROOT/EVIDENCE;need(not dest.exists() and not (ROOT/CHECKPOINT).exists(),'同工程の重複記録禁止');dest.mkdir()
    for name,data in files.items():(dest/name).write_bytes(data)
    cp={'task':TASK,'status':'ACCEPTED_BINDING_PAYLOADS_ONLY_ROM_PENDING','source_head':request['source_head'],
        'run_id':request['run_id'],'focused_tests':54,'actions_completion_confirmed':True,
        'completed_actions':done,'payload_artifact':by_name['pr16-learnset-payload-data'],
        'proof_artifact':artifact,'summary':receipt,'audit':audit,'source_snapshot_actions':snapshot_done,
        'prior_hatch_actions':old,'runtime_applied':False,'issue19_complete':False,'release_ready':False,
        'proof_bindings':{name:b.identity(data) for name,data in files.items()},
        'superseded_diagnostic':{'run_id':35659288132,'head':'3eb9f551603c55752060f59c92f62f85c3d216fe',
            'status':'FAILURE_IN_AUDIT_OWNER_LOOKUP','reason':'1262 is already official-selected, not one of 191 unselected bindings',
            'source_or_payload_changes_required':False},
        'superseded_record_attempt':{'run_id':35659771966,'reason':'resume observed_head_checks.reason_ja missing; no remote record was committed',
            'accepted_tests_rerun_for_record_fix':0}}
    (ROOT/CHECKPOINT).write_bytes(s.encode(cp))
    prior_path=ROOT/(BASE+'pr16_learnset_binding_checkpoint.json');prior=s.read_json(prior_path)
    need(prior['run_id']==35656548503 and prior['source_head']==old['head_sha'],'既受入孵化scope不一致')
    prior['actions_completion_confirmed']=True;prior['completed_actions']=old;prior_path.write_bytes(s.encode(prior))
    state=s.read_json(ROOT/STATE)
    need(not state['pr_merged'] and not state['release_ready'] and not state['active_baseline_changed'],'受入境界違反')
    state['learnset_binding']=prior;state['learnset_payloads']=cp
    state.setdefault('observed_head_history',[]).append({'head':state['observed_head'],
        'semantics':state['observed_head_semantics'],'checks':state['observed_head_checks'],
        'reason_ja':'191枠明示bindingと配置前payloadの完了Actionsへ表示を更新。旧受入範囲は保全。'})
    state['observed_head']=request['source_head'];state['observed_head_semantics']='191枠binding/配置前payloadの完了検証入力HEAD。branch最新HEAD/native受入HEADではない。現在HEADはremoteから取得する。'
    state['observed_head_checks']={'scope_head':request['source_head'],'runs':[done],
        'reason_ja':'今回の新54試験・独立2プロセス・全128352経路と全byte監査は完了Actionsで照合済み。静的binding/配置前payloadだけの受入で、全PR checksやROM/native全回帰の成功ではない。'}
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    goal='Issue19: Floette Eternal(1029)のgift入手契約とP01 learnset apply=falseを明示裁定し、既存贈呈先を消さず固定referenceを採用する。受入payloadを再利用し、188非学習/戦闘姿のruntime owner処理、条件付きconsumer、後継ROMの配置・別Wiki・影響nativeを接続する。'
    state['next_action']=dict(state['next_action'],id='LEARNSET_FLOETTE_ADOPTION_AND_RUNTIME_LINK',goal_ja=goal,
        read_paths=[GUIDE,CHECKPOINT,EVIDENCE+'/species-bindings.jsonl','tools/pr16_learnset_payloads.py','config/modernization_floette_gift.json','content/modernization/identity_contract.json'],
        stop_rule_ja='旧表fallback/191枠一括削除は禁止。配置前payloadはROM受入ではない。531孵化差分・原本裁定を再実行しない。Issue19/18全体、merge/releaseは未完。')
    state['bp']['next_step']=goal
    state['bp']['current_stop']='191枠を188保全/2明示owner/1採用待ちへ分類。64追加経路、元128288経路を配置前payloadと全行台帳へ変換。Wikiの1始まりslotを33321経路で補正し54新試験/独立全byte照合PASS。ROM/native未変更。'
    state['do_not_repeat'].append('learnset payload: 191 binding、531孵化差分、64明示経路、33321 slot補正は証拠固定済み。配置前payload artifactを再利用。受入54/24試験・原本生成は影響変更がない限り再実行せず、1029採用裁定とruntime接続から続行。')
    state['logs_synchronized']=True
    (ROOT/STATE).write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n');(ROOT/DOC).write_text(render(state))
    (ROOT/GUIDE).write_text('# Issue19 明示bindingと配置前payload\n\n'
        '正本: `'+CHECKPOINT+'`。最新実行原本とartifactを参照し、原本生成・既受入nativeをやり直さない。\n\n'
        '## 完了範囲\n191枠は188のidentity/戦闘時持越し保全、Caterpie649の4経路、Own Tempo1670の60経路、Floette Eternal1029の採用待ち1枠へ分類。'
        '元128288経路は不変で、明示64経路を別層に保持。54新試験・独立2プロセス・ローカル/Actions全hash一致、旧Wikiから別計算した全byte監査を完了。\n\n'
        '後継表の `candidate_slots_zero_based` は旧Wiki `slot=slot+1` 由来の1始まり番号だった。33321経路をbinary bit用の0始まりへ明示補正した。'
        '凍結済み後継表を直接変更せず、旧欄をruntimeへ直結することは禁止する。上限はmachine128/tutor64。\n\n'
        '## 成果物と境界\nlevel/egg/進化時/reminder/shared egg/互換bit/不足技archiveの配置前binaryとconsumer index、全経路SHA台帳をartifactに保存。'
        'shared egg・進化前持越し・フォーム条件・特殊孵化を通常level/eggへ統合しない。188枠は空表ではなくIDENTITY_ONLY_NO_REPLACEMENT、1029はBLOCKED_SOURCE_ADOPTION。'
        '保存済み4技は変更しない。選択済みUltra Necrozmaの既存P02解除先2通りも変更しない。\n\n'
        '## 次の未完\n1029はStage69で入手可能だがP01の習得元はapply=false。旧候補の技表や通常Floetteへのfallbackを避け、固定reference legendsza:0670.05の明示採用裁定を行う。'
        'その後、非学習/戦闘姿owner、条件付きconsumer、配置とpointer/容量、実供給を接続し、後継ROM・別Wiki・影響nativeを検証する。'
        '今回のartifactはインストール不可の配置前成果物であり、ROM受入/Issue19全体完了/merge/releaseではない。\n')
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 191枠bindingと配置前payload\n- Version: learnset-payload-v1\n- Status: DONE（静的binding/配置前payload限定。1029採用裁定・ROM接続未完）\n- Summary: 188枠identity保全、2owner64経路を明示接続、1枠は採用待ち。128288原経路を保全し33321経路のWiki slot 1始まりを補正。\n- Files changed: Species/payload実装、54新試験、限定Actionsと固定入力、checkpoint/証拠/guide、固定MD/JSON、両ログ。\n- Verify: 54新試験PASS、独立2プロセス全hash一致、旧Wikiからの独立全byte/128352行監査PASS、原本byte/mtime不変。run={request["run_id"]} head={request["source_head"]}。受入孵化run35656548503/source snapshot run35657130145の全step完了も照合。\n- Prior attempt: run35659288132は1262の監査参照先誤りで停止。元表とpayloadは不変のまま監査だけを訂正。\n- Commit: 本記録を含む同branch非force commit。自己SHAは記載せずgit logで照合。\n- Network: GitHub Actions受入artifact再利用、原本/旧Wiki再生成0、native0、ROM変更0。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a') as stream:stream.write(entry)
    print(json.dumps({'status':cp['status'],'run_id':request['run_id'],'tests':54},ensure_ascii=False))


def guard():
    import pr16_learnset_binding_verify as old
    old.OWNED=old.OWNED|set(CODE)|{CHECKPOINT,GUIDE}|{EVIDENCE+'/'+name for name in PROOF}
    old.guard()


if __name__=='__main__':
    args=sys.argv[1:]
    if len(args)==2 and args[0]=='build':p.compile_tables(ROOT,TABLES,Path(args[1]))
    elif args==['verify']:verify()
    elif args==['record']:record()
    elif args==['guard']:guard()
    else:raise SystemExit('usage: pr16_learnset_payload_verify.py build DEST | verify | record | guard')
