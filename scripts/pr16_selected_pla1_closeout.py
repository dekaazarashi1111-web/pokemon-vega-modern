#!/usr/bin/env python3
"""選定PLA1の成功原本を受領。ROM/実行測定を繰り返さず単親で記録する。"""
from __future__ import annotations
import datetime as dt
import io
import json
import os
from pathlib import Path
import sys
import traceback
import unittest
import zipfile
import pr16_selected_pla1_reader as m

SOURCE = '01aff6bdfde2cb8ab07bec612bfaa45adf9167cd'
RUN = 38203143951
ARTIFACT = 11726251879
ARCHIVE = dict(size=179708, sha256='eeafdc7cd027495e34ea8ece8d2c1c4ced038413284a6c76e044a815005111ae')
TASK = 'USER-20261012-SELECTED-PLA1-CLOSEOUT'
REPORT = 'content/modernization/pr16_selected_pla1_reader_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_selected_pla1_reader_evidence'
CODE = {'scripts/pr16_selected_pla1_closeout.py', 'tests/test_pr16_selected_pla1_receipt.py',
        '.github/workflows/pr16-selected-pla1-closeout.yml'}
ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / '.local/pr16-selected-pla1-closeout/public'
PHASE = 'preflight'


def validate(proof, result):
    """受領の意味検査。元JSONのhash/Actions/source拘束は呼出側で別に検査。"""
    m.need(proof['candidate'] == m.CANDIDATE and proof['image'] == m.IMAGE and proof['arm'] == m.ARM
           and proof['scope'] == 'ONE_PLA1_OWNER_FAMILY_ACTUAL_CONDITIONAL_DECODER'
           and proof['target'] == m.TARGET and proof['entry'] == m.ENTRY
           and proof['owner'] == m.OWNER and proof['family'] == m.FAMILY
           and proof['actual_conditional_reader_proven'] is True, '選定actual reader')
    for value in (proof, result):
        m.need(value['source_head'] == SOURCE and value['actions_run_id'] == RUN
               and [value[k] for k in ('formal_classified', 'formal_unclassified', 'selected_unknown_origins', 'donor_safe_bytes')] == [789,85,6,0]
               and [value[k] for k in ('accepted_measurement_reruns','accepted_test_reruns','native_processes','rom_reconstructions_started','new_reader_profiles_completed')] == [0,0,0,1,2], 'scope/原本の未受領値保持')
    m.need(proof['actions_completion_confirmed'] is False and proof['formal_classification_changes'] == 0
           and result['new_unit_tests'] == 36 and result['other_two_targets_reader_proven'] is False
           and result['status'] == 'MEASURED_PLA1_CONDITIONAL_READER_RECEIPT_PENDING', '測定と完了受領の区別')
    roles = m.cover(proof['chain'], m.TARGET-m.IMAGE_BASE, 4)
    m.need(roles == proof['target_roles'] and [r['role'] for r in roles] == result['roles']
           == ['selector_u8','xor_mask_u8','xor_mask_u8','xor_mask_u8']
           and [r['offset'] for r in proof['chain']] == [17227,14321,9440,9049,7490,7451,7376]
           and proof['chain'][0]['end_exclusive'] == 17239, '全4byteの一意な型/実鎖')
    m.need(len(proof['profiles']) == len(result['profiles']) == 2, '正常/容量不足の2条件のみ')
    for i, row in enumerate(proof['profiles']):
        m.need(row['callee_saved_and_sp_preserved'] is True and row['external_hooks'] == row['native_processes'] == 0
               and row['natural_entry_claimed'] is False and row['output_identity']['size'] == 320, '限定ABI')
        expected = dict(capacity=(160,31)[i], returned=(1,0)[i], output_count=(32,None)[i], instruction_count=(12728,12497)[i])
        m.need({k:row[k] for k in expected} == expected == result['profiles'][i], '帰値/出力/命令数')
        m.need(row['output_write_on_failure'] is (None if i == 0 else False), '失敗側の出力不変')
        reads = row['target_reads']
        m.need(len(reads) == 4 and [r['address'] for r in reads] == list(range(m.TARGET,m.TARGET+4))
               and [r['instruction'] for r in reads] == [0x09FFF2EC,0x09FFF328,0x09FFF328,0x09FFF328]
               and all(r['width'] == 1 and r['instruction_identity']['size'] == 2 for r in reads), '具体的LDRB全4byte')


def public(name, value):
    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC/name).write_bytes(m.encode(value) if isinstance(value,dict) else value)


def run():
    global PHASE
    import pr16_selected_compressed_asset_closeout as prior
    import pr16_selected_pla1_reader_actions as measured
    a, old, publication = prior.a, prior.old, prior.publication
    read, load, write, snapshot = prior.read, prior.load, prior.write, prior.snapshot
    STATE, GUIDE, BRANCH, LOGS = prior.STATE, prior.GUIDE, prior.BRANCH, prior.LOGS
    m.need(os.environ.get('GITHUB_REPOSITORY') == a.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/'+BRANCH
           and os.environ.get('GITHUB_RUN_ATTEMPT') == '1' and not PUBLIC.parent.exists()
           and not (ROOT/REPORT).exists(), '固定branch/初回/重複禁止')
    head = a.git('rev-parse','HEAD').decode().strip()
    m.need(head == os.environ['GITHUB_SHA'] and set(a.git('diff','--name-only',SOURCE,head).decode().splitlines()) == CODE
           and not a.git('status','--porcelain','--untracked-files=no').strip(), 'closeout3fileだけ')
    state = load(STATE); lane = state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need(state['next_action']['id'] == 'SAVE_CAPACITY_SELECTED_PLA1_AND_IPS_ACTUAL_READER'
           and [lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')] == [789,85,6,0], '固定next')
    owner = m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')})
    protected = {prior.REPORT, *measured.CODE, *measured.ENGINES}
    parent = load(prior.REPORT)
    for key in ('source_bindings','evidence_bindings','preserved_inputs'):
        for path, expected in parent[key].items():
            m.need(m.identity(read(path)) == expected, '既受入hash '+path)
            protected.add(path)
    baseline = snapshot(protected)
    PUBLIC.mkdir(parents=True)
    PHASE = 'receive-unchanged-success-original'
    completion = publication.accepted_run(RUN,SOURCE,['新PLA1全4byteの境界と実consumerのみ検証','Run actions/upload-artifact@v4'])
    meta = a.fetch('actions/artifacts/'+str(ARTIFACT))
    m.need(not meta['expired'] and meta['name'] == 'pr16-selected-pla1-reader-public-text'
           and meta['workflow_run']['id'] == RUN and meta['workflow_run']['head_sha'] == SOURCE
           and meta['size_in_bytes'] == ARCHIVE['size'] and meta['digest'] == 'sha256:'+ARCHIVE['sha256'], 'archive metadata')
    raw = a.fetch('actions/artifacts/'+str(ARTIFACT)+'/zip',binary=True)
    m.need(m.identity(raw) == ARCHIVE, 'archive全SHA')
    members = old.zip_members(raw)
    m.need(set(members) == {'attempt.json','pla1-reader.json','reader-tests.txt','result.json','saved-arm-reuse.json',
                           'scoped-context.zip','starting-head-checks.json','task-graph.txt'}, '閉8member')
    proof, result = json.loads(members['pla1-reader.json']), json.loads(members['result.json'])
    validate(proof,result)
    for path, expected in proof['source_bindings'].items():
        m.need(m.identity(read(path)) == expected, '測定source不変')
    for path, data in old.zip_members(members['scoped-context.zip']).items():
        m.need(a.git('show',SOURCE+':'+path) == read(path) == data, '測定時context byte不変')
    frontier = load(lane['unknown_frontier_path'])
    m.need(all(row['hit']['address'] != m.TARGET for row in frontier['rows']), 'PLA1は二次逆参照でformal originではない')
    PHASE = 'new-receipt-boundary-tests'
    fixture = PUBLIC.parent/'received';fixture.mkdir()
    for name in ('pla1-reader.json','result.json'):(fixture/name).write_bytes(members[name])
    stream = io.StringIO()
    test = unittest.TextTestRunner(stream=stream,verbosity=2).run(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern='test_pr16_selected_pla1_receipt.py'))
    public('receipt-tests.txt',stream.getvalue().encode())
    m.need(test.wasSuccessful() and test.testsRun == 14 and not test.skipped, '新14受領境界試験')
    completion.update(artifact={k:meta[k] for k in ('id','name','digest','size_in_bytes')},
        artifact_members={n:m.identity(b) for n,b in members.items()}, result=result,
        published_source_commit=SOURCE, accepted_test_reruns=0, accepted_measurement_reruns=0,
        additional_rom_reconstructions=0, conditional_reader_only=True, formal_classification_changes=0)
    data = {EVIDENCE+'/'+n:b for n,b in members.items() if n != 'scoped-context.zip'}
    data[EVIDENCE+'/actions-completion.json'] = m.encode(completion)
    data[EVIDENCE+'/receipt-tests.txt'] = stream.getvalue().encode()
    for path,body in data.items(): write(path,body)
    summary = ('選定二次逆参照0x095FE848はPLA1 owner530/family0のrecord17227..17239にあり、'
        '末尾selector1byteとXOR mask3byteを実ARM LDRB 0x09FFF2EC/0x09FFF328で全4byte消費。'
        '実配置の保存2788byte ARM/21383byte image/現候補全SHA一致。正常容量160で32件、'
        '容量31では出力/count無変更で拒否。明示ABIの条件付きdecoder実行であり自然入口の新受入ではない。')
    goal = ('PLA1二次逆参照の全4byte読取は受領済み。0x0880FA64のIPS記録11873から実asset境界とcallerを特定し、'
        '0x09673660はDPE予約envelope内の配置元/具体的asset readerを照合する。予約regionは実ownerではなく未所有は空き容量ではない。'
        'この二次参照の解決で主対象の全reader/正式分類を完了扱いにしない。新36境界試験/2実ARM profile/14受領試験と'
        '受入済みtype1/PCM/系譜/map/LZ/逆参照/Wikiを無変更再走しない。正式789/85・選定残6・安全容量0。'
        '保存controller/窓外跨り/間接参照/退役移管/heap/局所Saveは未完。')
    status = 'PLA1_SECONDARY_EDGE_CONDITIONAL_READER_ACCEPTED_TWO_ASSET_ORIGINS_PENDING'
    observed = a.live(head)
    report = dict(schema_version=1,task=TASK,status=status,source_head=head,measurement_source_head=SOURCE,
        measurement_run_id=RUN,measurement_completion_confirmed=True,candidate=m.CANDIDATE,
        actual_conditional_reader_proven=True,natural_entry_claimed=False,
        new_unit_tests=36,new_receipt_tests=14,measured_rom_reconstructions=1,additional_rom_reconstructions=0,
        new_reader_profiles=2,native_processes=0,accepted_test_reruns=0,accepted_measurement_reruns=0,
        formal_classification_changes=0,formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0,
        source_bindings={p:m.identity(read(p)) for p in sorted(CODE|measured.CODE|set(measured.ENGINES))},
        evidence_bindings={p:m.identity(read(p)) for p in sorted(data)},
        preserved_inputs={p:v[0] for p,v in baseline.items()},read_only_check_passed=True,
        task_graph_passed=True,observed_head_checks=observed,summary_ja=summary,next_ja=goal)
    write(REPORT,report)
    lane.update(status=status,checkpoint_path=REPORT,next_ja=goal)
    state['next_action'] = dict(id='SAVE_CAPACITY_IPS_AND_DPE_ASSET_READERS',goal_ja=goal,
        read_paths=[GUIDE,REPORT,EVIDENCE+'/pla1-reader.json',EVIDENCE+'/actions-completion.json',
            prior.prior.REPORT,prior.prior.EVIDENCE+'/provenance.json',
            'content/modernization/pr16_selected_asset_xrefs_evidence/inverse-references.json',
            'content/modernization/pr16_selected_asset_records_evidence/record-candidates.json'],
        done_ja='残る実asset全4byteを具体的読取命令に束縛したときだけ正式型差分へ進む。')
    state['observed_head_checks'] = observed
    state['recording']['last_execution'] = dict(task=TASK,source_head=head,measurement_run_id=RUN,
        measurement_source_head=SOURCE,actions_run_id=int(os.environ['GITHUB_RUN_ID']),
        measurement_completion_confirmed=True,closeout_actions_completion_confirmed=False,
        new_unit_tests=36,new_receipt_tests=14,new_rom_reconstructions=0,accepted_test_reruns=0,
        accepted_measurement_reruns=0,read_only_check_passed=True,task_graph_passed=True)
    state['recording'].update(task=TASK,status=status,source_head=head,selected_pla1_reader_checkpoint=REPORT,
        received_selected_pla1_completion=EVIDENCE+'/actions-completion.json')
    text = read('CHATGPT_RESUME.md').decode()
    left,rest = text.split('## 次の未完作業\n',1);_,right = rest.split('\n所有者が閲覧版で',1)
    text = left+'## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_IPS_AND_DPE_ASSET_READERS。'+goal+' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で'+right
    write('CHATGPT_RESUME.md',text.encode())
    state['bindings']['CHATGPT_RESUME.md'] = dict(git_blob_sha=old.m.blob(text.encode()),**m.identity(text.encode()))
    m.need(owner == m.encode({k:state['owner_execution_plan'][k] for k in ('wiki','wiki_readability','owner_review','scope')}), 'Wiki/承認/安全境界不変')
    write(STATE,state)
    guide = read(GUIDE).decode().replace('## 次の未完作業','## 以前の停止点（履歴）')
    guide += '\n## PLA1二次逆参照の条件付き実reader\n\n'+summary+'\n\n[checkpoint](../'+REPORT+') / [改作しない実測](../'+EVIDENCE+'/pla1-reader.json) / [完了受領](../'+EVIDENCE+'/actions-completion.json)。run38203143951の36試験・2profile成功を受領。新受領14試験のみ。正式origin分類の増減0、ROM/Save変更0。\n\n## 次の未完作業\n\n'+goal+'\n'
    write(GUIDE,guide.encode())
    stamp = dt.datetime.now(dt.timezone.utc).isoformat()
    block = ('\n## '+stamp+'\n- Timestamp: '+stamp+'\n- Task: '+TASK+' / 選定PLA1実readerの受領'
        '\n- Version: selected-pla1-reader-v1\n- Status: DONE（条件付き二次参照readerのみ。主asset/保存統合は未完）'
        '\n- Summary: '+summary+'\n- Files changed: 新reader/36境界試験/Actions、受領器/14試験、改作なしの測定原本/完了受領/JSON/引継ぎMD・両ログ。'
        '\n- Verify: run38203143951/job114660715809全必須step成功。ZIP179708byte SHA256 '+ARCHIVE['sha256']+
        '・8member・測定source/context全byte照合。新36試験、12728/12497命令の2条件、今回14受領試験、task graph、最終index読戻し。'
        '\n- Scope: 保存ARMとPLA1不変。実測時のみ候補復元1、受領時0。旧全owner/native/PCM/type1/系譜/map/LZ/Wiki再走0。正式789/85・残6・安全容量0。'
        '\n- Boundary: 全体private guardの歴史的違反・一般CI失敗は成功へ読み替えず別記録。自然UI/容量確保/保存統合未受入。'
        '\n- Next: '+goal+'\n- Commit: 両ログ込み単親通常commit。実SHAはActions result/Git履歴。'
        '\n- Network: 同repo Actions/artifact読取と同branch非force pushのみ。ROM/IPS/Saveの追加なし。\n')
    for path in LOGS:
        before = read(path);m.need(('- Task: '+TASK+' /').encode() not in before,'log重複禁止');write(path,before+block.encode())
    PHASE = 'final-index-and-nonforce-push'
    allowed = set(data)|set(LOGS)|{REPORT,STATE,GUIDE,'CHATGPT_RESUME.md'}
    publication.final_index(head,allowed,REPORT)
    m.need(baseline == snapshot(protected), '旧受入byte/mtime不変')
    # 次の未完作業で必要なtracked textだけを回収可能にする。測定や生成は実行しない。
    paths = {STATE,GUIDE,'CHATGPT_RESUME.md',REPORT,*allowed,
        'scripts/pr16_selected_asset_provenance_actions.py','scripts/pr16_selected_asset_provenance.py',
        'scripts/pr16_dex_hof_main_cow_actions.py','scripts/pr16_dex_hof_storage_actions.py',
        'scripts/pr16_selected_asset_xrefs_actions.py','scripts/pr16_selected_asset_records_actions.py',
        'scripts/pr16_selected_asset_actions.py',lane['reference_chain_path'],lane['unknown_frontier_path'],lane['window_progress_path'],
        'content/modernization/pr16_selected_asset_xrefs_evidence/inverse-references.json',
        'content/modernization/pr16_selected_asset_records_evidence/record-candidates.json'} - set(LOGS)
    with zipfile.ZipFile(PUBLIC/'next-context.zip','w',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(paths):
            body = read(path);body.decode();m.need(len(body)<1000000 and b'\0' not in body,'限定text');z.writestr(path,body)
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0] == head,'remote lease')
    a.git('config','user.name','github-actions[bot]');a.git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit','-m',TASK+': 全4byteのPLA1実読取・容量不足対照・固定引継ぎを記録')
    a.git('push','origin','HEAD:'+BRANCH)
    pushed = a.git('rev-parse','HEAD').decode().strip()
    m.need(a.git('ls-remote','origin','refs/heads/'+BRANCH).decode().split()[0] == pushed,'push後HEAD')
    for path in allowed:m.need(a.git('show','HEAD:'+path) == read(path),'commit読戻し')
    public('result.json',dict(status='DONE',task=TASK,commit=pushed,source_head=head,measurement_run=RUN,
        formal_classified=789,formal_unclassified=85,selected_unknown_origins=6,donor_safe_bytes=0))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+pushed)


if __name__ == '__main__':
    try: run()
    except Exception as exc:
        public('failure.json',dict(status='NOT_ACCEPTED',phase=PHASE,type=type(exc).__name__,
            frames=[{'file':Path(f.filename).name,'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__) if '/scripts/' in f.filename]))
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__)
        sys.exit(1)
