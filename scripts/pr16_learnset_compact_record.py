#!/usr/bin/env python3
"""四条件入口の完了証拠だけを保存。旧試験/ROM生成/nativeを再実行しない。"""
from __future__ import annotations
import datetime
import io
import zipfile
import json
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT),str(ROOT/'scripts')]
from pr16_learnset_runtime_record import need, identity, encode, git
from pr16_learnset_progress_record import unpack
import pr16_learnset_compact_reuse as reuse
import pr16_learnset_compact_bound as bound
START = 'd61d54443d5ac8d47c9807a8a042c1e4402073dd'
TASK = 'USER-20260922-LEARNSET-COMPACT'
PREFIX = 'content/modernization/'
INPUTS = PREFIX+'pr16_learnset_compact_record_inputs.json'
CP = PREFIX+'pr16_learnset_compact_checkpoint.json'
EVIDENCE = PREFIX+'pr16_learnset_compact_evidence'
STATE = PREFIX+'pr16_native_supply_resume_20260913.json'
DOC = 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md'
GUIDE = 'docs/PR16_LEARNSET_COMPACT_JA.md'
ENTRY = 'CHATGPT_RESUME.md'
DATA_TEXT = ('disassembly.txt','pr16_learnset_conditional_bindings.h')
CODE = set(reuse.CODE) | set(reuse.m.CODE) | (set(bound.CODE)-{'overlays/modernization_p07_preserved_layer/runtime.c'}) | {INPUTS, 'scripts/pr16_learnset_compact_record.py',
        'tests/test_pr16_learnset_compact_record.py', '.github/workflows/pr16-learnset-compact-record.yml'}


def inputs(): return json.loads((ROOT/INPUTS).read_bytes())


def owned():
    return {CP,STATE,DOC,GUIDE,ENTRY,'design/run_log.md','design/version_log.md'} | {
        EVIDENCE+'/'+name for name in (*inputs()['proof_files'],*DATA_TEXT)}


def validate(files, expected):
    need(set(files) == set(expected['proof_files']), 'proof集合不一致')
    for name,binding in expected['proof_files'].items():
        need(identity(files[name]) == binding, '証拠hash不一致: '+name)
    v = json.loads(files['verification.json'])
    need(v['status'] == 'PASS_FOUR_CONDITIONAL_ROM_ENTRYPOINTS'
         and v['scope'] == 'HOST_FIXTURE_DIRECT_ROM_CALL_NOT_GAMEPLAY_E2E', 'scope昇格禁止')
    need(v['source_head'] == expected['source_head'] and v['run_id'] == expected['run_id']
         and v['candidate'] == expected['candidate'] and v['candidate']['size'] == 33554432, '入力/候補不一致')
    need(set(v['proof_files']) == set(files)-{'verification.json'}, '内側proof集合不一致')
    for name,binding in v['proof_files'].items(): need(identity(files[name]) == binding, '内側hash不一致')
    for name in ('game_tutor_connected','archive_rebound','gameplay_e2e_accepted','release_ready','active_baseline_changed','issue19_complete'):
        need(v[name] is False, '未受入範囲の昇格: '+name)
    for name in ('independent_candidate_hashes_match','four_conditional_entrypoints_connected',
                 'p03_evolution_dispatch_unchanged','input_byte_mtime_unchanged','tracked_tree_unchanged'):
        need(v[name] is True, '受入条件欠落: '+name)
    for name in ('accepted_tests_rerun','accepted_native_reruns','accepted_payload_regenerations',
                 'accepted_source_regenerations','old_arm_compiles'):
        need(type(v[name]) is int and v[name] == 0, '重複/原本生成禁止: '+name)
    for name,value in {'focused_tests':6,'native_processes':2,'new_arm_compiles':6,'new_arm_links':2,
                       'inherited_host_tests':41,'inherited_host_queries':622669,
                       'inherited_game_tests':18,'inherited_compact_tests':25,'inherited_compact_queries':15039,'inherited_compiler_tests':6}.items():
        need(type(v[name]) is int and v[name] == value, '実行計数不一致: '+name)
    need(v['inherited_game_run'] == 35716683381 and v['inherited_host_run'] == 35715106357
         and v['inherited_compact_run'] == 35720010554 and v['inherited_compiler_run'] == 35720416968, '継承元不一致')
    for name,count in (('compact-unit.txt',25),('bound-unit.txt',6),('inherited-compiler-unit.txt',6),('inherited-game-unit.txt',18)):
        need(files[name].count(b' ... ok\n') == count and b'\nOK\n' in files[name], 'unit成功原本不一致')
    audit = json.loads(files['compact-audit.json'])
    need(audit == v['compact_audit'] and audit['status'] == 'PASS' and audit['queries'] == 15039
         and audit['owner_consumer_pairs'] == 8355 and audit['owner_order_count_payload_actions_equal'] is True, 'PLC2全件不一致')
    receipt = json.loads(files['compact-receipt.json'])
    need(receipt == v['compact_receipt'] and receipt['image'] == {
        'size':31014,'sha256':'3fb75ac95022f2cfa9ea1a0bda13dd57f8ed883564b95271e97ba45489b7aa90'}
         and receipt['source'] == {'size':115282,'sha256':'d112866d8424f52ce3aaec00bc1517567943bae2cf6e7115725b26685dcd221d'}
         and receipt['unique_records'] == 842 and receipt['semantic_rows_equal'] is True
         and receipt['owner_policy_equal'] is True and receipt['source_regenerations'] == receipt['archive_moves_granted'] == 0,
         'PLC1/PLC2同値変換不一致')
    inherited = json.loads(files['inherited-compact.json'])
    need(inherited['run_conclusion'] == 'failure' and inherited['focused_tests_executed'] == 0
         and inherited['host_queries_executed'] == 0 and inherited['prior_native_processes'] == 0,
         '失敗履歴/再実行境界不一致')
    link = json.loads(files['link.json'])
    need(link['candidate'] == v['candidate'] and link['format'] == 'PLC2' and link['image'] == receipt['image']
         and link['outside_declared_ranges'] == 0 and link['prior_image_unchanged'] is True
         and link['p03_evolution_dispatch_unchanged'] is True and link['p07_archive_wrapper_preserved'] is True
         and link['p07_archive_delegate'] == 0x095DDBE9 and link['compiler_options_added'] == ['-fno-jump-tables'], '配置保全違反')
    need([p['offset'] for p in link['hooks']] == [0x1114120,0x11141D4,0x451EC,0x10EB970], '4入口範囲違反')
    need(len(link['segments']) == 2 and {x['file'] for x in link['segments']} == {'conditional.bin','compact-image.bin'}, '分割配置不一致')
    need(link['code_end']-link['code_start'] == link['bundle']['size'] <= 8192, 'code容量不一致')
    rows = sorted(link['allocation']['allocations'],key=lambda x:x['start'])
    need(all(a['end_exclusive'] <= b['start'] for a,b in zip(rows,rows[1:])), 'allocation重複')
    need(link['allocation']['summaries']['overlap_count'] == 0, 'overlap counter不一致')
    need(len(v['native_results']) == 2, '独立native process不足')
    for i,name in enumerate(('native11.json','native29.json')):
        native = json.loads(files[name])
        need(native == v['native_results'][i] == expected['native_results'][i]
             and native['status'] == v['status'] and native['scope'] == v['scope']
             and native['candidate_sha256'] == v['candidate']['sha256'] and native['samples'] == 15, 'native原本不一致')
        for key in ('new_code_pc_seen_for_every_call','stored_four_moves_and_pp_preserved','real_granted_pp_checked',
                    'p03_two_evolution_lr_paths_checked','floette_archive_denied'):
            need(native[key] is True, 'native保全/経路証拠欠落: '+key)
    return v


def record():
    from pr16_wiki_reconcile import fetch
    from pr16_learnset_payload_verify import completed_run, current_pr
    from pr16_resume import render, pending_ids
    config = inputs(); head = git('rev-parse','HEAD').decode().strip(); current_pr(head)
    need(not (ROOT/CP).exists() and not (ROOT/EVIDENCE).exists(), '受入記録の重複禁止')
    done = completed_run(config['run_id'],config['source_head'],'.github/workflows/pr16-learnset-compact-bound.yml','compact-bound')
    listing = fetch(f"actions/runs/{config['run_id']}/artifacts?per_page=100")
    need(listing['total_count'] == len(listing['artifacts']), 'artifactページ不足')
    artifacts = {x['name']:x for x in listing['artifacts']}
    need(set(artifacts) == set(config['artifacts']), 'artifact集合不一致')
    for name,binding in config['artifacts'].items():
        a = artifacts[name]
        need((a['id'],a['size_in_bytes'],a['digest']) == (binding['id'],binding['size'],'sha256:'+binding['sha256'])
             and not a['expired'] and a['workflow_run']['head_sha'] == config['source_head']
             and a['workflow_run']['id'] == config['run_id'], 'artifact/run/source不一致')
    artifact = config['artifacts']['pr16-learnset-compact-native-proof']
    raw = fetch(f"actions/artifacts/{artifact['id']}/zip",binary=True)
    need(identity(raw) == {key:artifact[key] for key in ('size','sha256')}, '外側ZIP不一致')
    files = unpack(raw,config['proof_files']); v = validate(files,config)
    data_artifact = config['artifacts']['pr16-learnset-compact-native-data']
    data_raw = fetch(f"actions/artifacts/{data_artifact['id']}/zip",binary=True)
    need(identity(data_raw) == {key:data_artifact[key] for key in ('size','sha256')}, '保存data ZIP不一致')
    data_text = {}
    with zipfile.ZipFile(io.BytesIO(data_raw)) as archive:
        members = archive.infolist()
        need(len(members) == len(v['data_files']) and {x.filename for x in members} == set(v['data_files']), '保存data集合不一致')
        for member in members:
            need(member.filename == Path(member.filename).name and member.file_size <= 1000000, '保存data範囲違反')
            need(identity(archive.read(member)) == v['data_files'][member.filename], '保存data hash不一致')
        need(archive.read('link.json') == files['link.json'], 'proof/data link不一致')
        for name in DATA_TEXT:
            value = archive.read(name); value.decode('utf-8')
            need(b'\0' not in value, 'data text内binary禁止')
            data_text[name] = value
    for name,binding in v['code_bindings'].items(): need(identity((ROOT/name).read_bytes()) == binding, '完了source変更: '+name)
    failures = []
    for number in (35716683381,35720010554,35720416968):
        run = fetch(f'actions/runs/{number}')
        need(run['status'] == 'completed' and run['conclusion'] == 'failure', '旧failure改作禁止')
        failures.append({key:run[key] for key in ('id','head_sha','status','conclusion')})
    state = json.loads((ROOT/STATE).read_bytes())
    backlog = json.loads((ROOT/(PREFIX+'p08_remaining_work.json')).read_bytes())
    bp = json.loads((ROOT/(PREFIX+'pr16_bp_chooser_checkpoint.json')).read_bytes())
    need(pending_ids(backlog) == (state['remaining_physical_gap_ids'],state['remaining_p08_gate_ids'])
         and bp['accepted_case_count'] == 3 and not state['pr_merged']
         and not state['release_ready'] and not state['active_baseline_changed'], '正式BP/P08/基準境界違反')
    checkpoint = {'task':TASK,'status':'ACCEPTED_FOUR_CONDITIONAL_DIRECT_ROM_PROBES_GAMEPLAY_PENDING',
        'source_head':config['source_head'],'run_id':config['run_id'],'record_source_head':head,
        'candidate':v['candidate'],'candidate_crc32':v['candidate_crc32'],'completed_actions':done,
        'artifacts':artifacts,'proof_bindings':config['proof_files'],
        'data_text_bindings':{name:identity(value) for name,value in data_text.items()},'verification':v,'preserved_failed_runs':failures,
        'game_tutor_connected':False,'archive_rebound':False,'gameplay_e2e_accepted':False,'issue19_complete':False,
        'active_baseline_changed':False,'release_ready':False}
    (ROOT/EVIDENCE).mkdir()
    for name,value in {**files,**data_text}.items(): (ROOT/EVIDENCE/name).write_bytes(value)
    (ROOT/CP).write_bytes(encode(checkpoint))
    state['learnset_conditional_compact'] = {key:checkpoint[key] for key in
        ('status','source_head','run_id','candidate','gameplay_e2e_accepted','issue19_complete')}
    state['learnset_conditional_compact']['path'] = CP
    state.setdefault('observed_head_history',[]).append({'head':state['observed_head'],
        'semantics':state['observed_head_semantics'],'checks':state['observed_head_checks'],
        'reason_ja':'四条件consumerの限定受入を追加。旧PLR1/通常level-up/正式BP/P08受入は不変。'})
    state['observed_head'] = config['source_head']
    state['observed_head_semantics'] = '進化/思い出し/egg/shared-eggの4入口直接ROM probe成功入力HEAD。通常操作E2E/記録commit/Issue19全完了ではない。'
    state['observed_head_checks'] = {'scope_head':config['source_head'],'runs':[done],
        'reason_ja':'PLC2同値圧縮・分割配置・2独立リンク・2native processを受入。41+18+25+6=90試験と622669+15039照合は継承し再実行0。'}
    state['observed_date_jst'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    goal = 'Issue19: 保存済みPLC2四条件入口の候補/ARM/data/linkを再利用し、残る実ゲームtutorとarchive供給境界を明示ownerへ接続する。新候補Wikiを別pathへ生成し、影響するBag/戦闘/習得選択/Save/Continueの通常操作E2Eへ進む。96host試験/4入口直接ROM probeの単純再実行は禁止。'
    state['next_action'] = dict(state['next_action'],id='LEARNSET_TUTOR_ARCHIVE_WIKI_AND_GAMEPLAY',goal_ja=goal,
        read_paths=[GUIDE,CP,'src/modernization/pr16_learnset_conditional_game.c',
                    'scripts/pr16_learnset_compact_bound.py','docs/PR16_LEARNSET_PAYLOADS_JA.md'],
        stop_rule_ja='P03進化LR分岐/通常level-up/保存4技/188保全ownerを維持。進化/思い出し/eggを通常levelへ平坦化しない。archive12件を実供給済みにせず、Floette独立ownerの旧archive fallbackを復活させない。旧Wiki/基準ROM/正式BP/P08受入不変。直接callを通常操作へ昇格せずmerge/releaseしない。')
    state['bp']['next_step'] = goal
    state['bp']['current_stop'] = 'PLC1 115282→PLC2 31014 bytesの同値圧縮と分割配置を採用し、新候補'+v['candidate']['sha256'][:8]+'へ進化/思い出し/egg/shared-eggの4入口を接続。15代表条件×2processでP03両進化LR/満杯/重複/実PP/4技不変/Floette archive拒否を受入。Tutor実接続・archive再束縛・新Wiki・通常操作E2Eは未完。'
    state['do_not_repeat'].append('四条件入口: run'+str(config['run_id'])+'の2独立ARM配置/2native processを再実行しない。run35715106357の41試験/622669照合、run35716683381の成功18試験、run35720010554の成功25試験/15039照合とrun35720416968の成功6 compiler-option試験を継承。旧failureを成功へ改作せず、固定2segmentと親e168c06fから再開。')
    state['logs_synchronized'] = True
    (ROOT/STATE).write_bytes(encode(state)); (ROOT/DOC).write_text(render(state),encoding='utf-8')
    former = (ROOT/GUIDE).read_text()
    guide = '# Issue19: 四条件consumerのPLC2接続\n\n'+state['bp']['current_stop']+'\n\n'
    guide += '候補SHA-256 `'+v['candidate']['sha256']+'`、33554432 bytes、CRC32 `'+v['candidate_crc32']+'`。run `'+str(config['run_id'])+'` / HEAD `'+config['source_head']+'`。\n\n'
    guide += '受入はhost fixtureからの実ROM call限定。通常の遭遇・戦闘・習得画面・Save/Continueは未受入。旧初期技/通常level-upの受入を再実行しない。90試験は成功原本を継承、新規6 ABIガード試験と2独立リンク・2native processを実行した。\n\n'
    guide += '4hook以外は新data/code segmentのみ。既存ownerの再利用/削除0、全差分rollback一致、P03 dispatch/PLR1/共有root不変。Thumb switch補助関数未解決は-fno-jump-tablesで除き、旧3失敗runは原本を保持。\n\n## 次工程\n\n'+goal+'\n\n## 初回WIP設計の記録\n\n'+former
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    entry = (ROOT/ENTRY).read_text(); title,rest = entry.split('\n',1)
    (ROOT/ENTRY).write_text(title+'\n\n## 最新の限定受入（2026-09-22）\n\n'
        +'`'+GUIDE+'` / `'+CP+'` を固定引継ぎと併読する。四条件入口のPLC2接続・直接ROM probeは受入済み。次はtutor/archive境界・別候補Wiki・変更影響の通常操作E2E。96host試験と2native processの重複は禁止。製品全体・Issue19・releaseは未完。以下の旧受入章の次工程は記録時点の履歴であり、この最新項目と状態JSONのnext_actionを優先する。\n'+rest,encoding='utf-8')
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = '\n## '+stamp+'\n- Timestamp: '+stamp+'\n- Task: '+TASK+' / 四条件consumerの接続と限定受入\n'
    log += '- Version: learnset-conditional-plc2-v1\n- Status: DONE（4入口直接ROM probe限定。tutor/archive/新Wiki/通常操作E2Eは未完）\n'
    log += '- Summary: PLC1 115282→PLC2 31014 bytes、8355行/842共有record同値、新候補'+v['candidate']['sha256'][:8]+'、4hookと2segment、全差分rollback/旧PLR1/P03/4技・PPを保全。\n'
    log += '- Files changed: PLC2配置器/C decoder/25試験、分割ARM配置・継承器/6試験、実測ABI/6試験、限定Actions、証拠/checkpoint/guide、固定入口/引継ぎMD・JSON、両ログ。\n'
    log += '- Verify: run'+str(config['run_id'])+' SUCCESS、15代表条件×2process。41+18+25+6=90試験/622669+15039照合を原本継承。新記録拒否試験・resume/task graph・diff --check・final index限定guard後のみcommit。\n'
    log += '- Commit: 本記録を含む同branch非force commit。自己SHAはgit logで照合。\n'
    log += '- Network: GitHub固定run/artifactのみ。原本再収集/旧ARM再compile/既存native再実行0。空間不足run35716683381とリンク失敗run35720010554・旧入口不一致run35720416968をfailureのまま保持。全履歴private guardのPASSは主張しない。\n'
    for name in ('design/run_log.md','design/version_log.md'):
        with (ROOT/name).open('a',encoding='utf-8') as stream: stream.write(log)
    print(json.dumps({'status':checkpoint['status'],'candidate':v['candidate'],'run_id':config['run_id'],'new_native_runs':0}))


def guard():
    import pr16_learnset_runtime_record as scoped
    scoped.START,scoped.CODE,scoped.OWNED = START,CODE,owned()
    scoped.guard()
    subprocess.run(['git','diff','--cached','--check',START],cwd=ROOT,check=True)


if __name__ == '__main__':
    if sys.argv[1:] == ['record']: record()
    elif sys.argv[1:] == ['guard']: guard()
    elif sys.argv[1:] == ['paths']: print('\n'.join(sorted(owned())))
    else: raise SystemExit('usage: pr16_learnset_compact_record.py record|guard|paths')
