#!/usr/bin/env python3
"""大きな成功原本の再実行なしで、小さなGitHub再開用checkpointを作る。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_followup_v2 as s

BASE='5a489a17e2908dee43fab62b98d078be92d61edb'
SLUG='pr16-ring-message-task-checkpoint'
TASK='PR-P08-7-RING-MESSAGE-TASK-CHECKPOINT'
TITLE='成功1231条件を再実行せず軽量再開点と証拠取得経路を固定'
SELF='scripts/pr16_ring_message_task_checkpoint.py'
TEST='tests/test_pr16_ring_message_task_checkpoint.py'
WORKFLOW='.github/workflows/pr16-ring-message-task-checkpoint.yml'
PRIOR='content/modernization/pr16_ring_message_task_contracts.json'
REPORT='content/modernization/pr16_ring_message_task_checkpoint.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=20
EXTRA_CODE=()
SOURCES=('scripts/pr16_ring_message_task_contracts.py',)
SOURCE='a87bd4e4a027d684d0f84d27ee4bd0f7decfb158'
SOURCE_TASK='PR-P08-7-RING-MESSAGE-TASK-CONTRACTS'
RUN=35301261393
JOB=105464195485
ARTIFACT=10530291611
DIGEST='sha256:72dc385bc53b24b152db97d430681b1d7c03d8b5c39214f9097da9d0e8331c11'
NO_REPEAT=('55tests/1231条件の原本run35301261393と完了5a489a17はこの軽量checkpointから再利用。'
    '大きなJSON本文が空なら権限不足/内容不在と推測せず、記載artifactと分割exportをhash照合して読む。'
    '今回記録だけで契約/native/byte採取を再実行しない。次はwindow状態0/1の未読境界。')
need=s.need
FALSE_FLAGS=('task_state01_complete_proven','task_state_transitions_proven','task_runtime_observed',
    'task_scheduler_execution_observed','normal_story_observed','initializer_runtime_observed',
    'actual_callback_table_observed','dma_execution_observed','ring_acquisition_accepted','release_ready')
ZERO_FLAGS=('new_node_count','new_window_bytes','rom_changes','new_emulator_processes','candidate_reconstructions',
    'saved_nodes_redecoded','accepted_native_cases_replayed','accepted_standalone_contracts_replayed',
    'full_rom_scans','successful_callee_stubs')


def compact(previous):
    need(previous['task']==SOURCE_TASK and previous['source_head']==SOURCE and previous['run_id']==RUN,'成功原本identity')
    need(previous['focused_tests']==dict(tests_run=55,failures=0,errors=0,skips=0,successful=True),'成功55tests')
    a=previous['analysis'];rows=a['cases'];by={r['case']:r for r in rows}
    need(a['candidate']==s.CANDIDATE and a['saved_node_count']==8251,'candidate/8251命令')
    need(a['contract_cases']==len(rows)==len(by)==1231 and a['evaluation_cache_misses']==1,'1231一回原本')
    need(a['conditional_return_cases']==sum(r['returned'] for r in rows)==914 and a['pending_stop_cases']==317,'帰還/停止原本')
    need(all((r['stop'] is None)==r['returned'] and r['native_observation'] is False
        and r['successful_callee_stubs']==0 for r in rows),'caseの停止/非native境界')
    groups={k:sum(r['group']==k for r in rows) for k in a['groups']}
    need(groups==a['groups'] and sum(groups.values())==1231,'保存group集合')
    sequences=a['state2_sequences']
    need(a['same_ram_state2_sequences']==len(sequences)==96 and a['state2_sequence_calls']==288,'保存96列')
    for seq in sequences:
        need(seq['same_ram_successor'] is True and seq['initial_task_state']==2
            and seq['state01_execution_claimed'] is False and len(seq['cases'])==3,'state2開始の条件境界')
        selected=[by.get(label) for label in seq['cases']]
        need(all(r is not None for r in selected),'連続列case参照')
        need([r['phase'] for r in selected]==['countdown','delay-finished','terminated']
            and [r['task_completed'] for r in selected]==[False,False,True],'連続列の順序')
        need(all((r['task_id'],r['font'],r['fast'])==(seq['task_id'],seq['font'],seq['fast']) for r in selected),'連続列object同一性')
    need(a['upstream_busy_byte_values']==list(range(1,256)) and a['window_flag_byte_values']==list(range(256))
        and a['task_ids']==list(range(16)),'保存domain')
    need(a['task_state2_conditional_cleanup_proven'] is True,'state2帰還')
    for key in FALSE_FLAGS:need(a[key] is False,'未受入境界 '+key)
    for key in ZERO_FLAGS:need(a[key]==0,'新実行禁止 '+key)
    full=a['task_full_boundary']
    need(full['busy_after']==2 and full['task_allocated'] is False and full['liveness_proven'] is False
        and full['normal_play_reproduction_observed'] is False,'task満杯を成功へ昇格しない')
    keep=('groups','cleanup_order','task_full_boundary','active_byte_boundary','task_noop_state_representatives',
        'all_uint16_states_exhaustively_executed','all_live_slot_bounds_proven','pending_window_attribute',
        'pending_palette_entry','pending_frame_thunk','saved_frame_callback','remaining_unread_callees','maximum_stack_bytes','boundary_ja')
    result={key:copy.deepcopy(a[key]) for key in keep}
    result.update({key:False for key in FALSE_FLAGS});result.update({key:0 for key in ZERO_FLAGS})
    result.update({'classification':'SAVED_MESSAGE_TASK_PROOF_CHECKPOINT_NO_REPLAY','candidate':dict(s.CANDIDATE),
        'saved_node_count':8251,'task_state2_conditional_cleanup_proven':True,'reused_contract_cases':1231,
        'reused_conditional_return_cases':914,'reused_pending_stop_cases':317,'reused_same_ram_state2_sequences':96,
        'reused_source_tests':55,'new_contract_cases_executed':0,'original_evaluation_cache_misses':1,
        'source_record_commit':BASE,'source_head':SOURCE,'source_run_id':RUN,'source_job_id':JOB,
        'source_report':PRIOR,'busy_domain':'1..255; zeroは生成経路で別検証','window_flags_domain':'0..255','task_ids':list(range(16)),
        'implementation_read_paths':[SOURCES[0],'content/modernization/pr16_ring_message_window_bytes.json'],
        'evidence_access':{'artifact_id':ARTIFACT,'run_id':RUN,'artifact_name':'pr16-ring-message-task-contracts',
            'archive_sha256':DIGEST.split(':',1)[1],'analysis_member':'analysis.json','receipt_member':'recorded-result.json',
            'manifest_member':'export/manifest.json','manifest_identity':copy.deepcopy(a['export_manifest']),
            'logical_context':'saved-context.json','text_format':'utf8-text-chunks-v1',
            'method_ja':'GitHub.download_workflow_artifactで取得しarchive SHA→manifest→各chunk→logical fileのsize/SHAを照合。'
                '本文空の大きいJSONを内容不在や権限不足と推測しない。artifact失効時もtracked原本を改変しない。'}})
    need(len(s.stable(result))<16000,'checkpoint size上限')
    return result


def verify_actions(job,artifact):
    need(job['id']==JOB and job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='success','成功job原本')
    need(job['steps'] and all(step['status']=='completed' and step['conclusion']=='success' for step in job['steps']),'job全step')
    need(artifact['id']==ARTIFACT and artifact['name']=='pr16-ring-message-task-contracts'
        and artifact['expired'] is False and artifact['digest']==DIGEST,'artifact原本')
    run=artifact['workflow_run']
    need(run['id']==RUN and run['head_sha']==SOURCE and run['head_branch']==s.BRANCH,'artifact source binding')
    return {'job_status':'completed','job_conclusion':'success','steps':len(job['steps']),
        'artifact_id':ARTIFACT,'artifact_digest':DIGEST,'artifact_expired':False}


def analyze(previous,out):
    result=compact(previous)
    result['source_report_identity']=s.identity((s.ROOT/PRIOR).read_bytes())
    result['actions_verified_without_replay']=verify_actions(s.api('actions/jobs/'+str(JOB)),s.api('actions/artifacts/'+str(ARTIFACT)))
    (out/'analysis.json').write_bytes(s.stable(result))
    return result


def summaries(r):
    return ('run35301261393/完了5a489a17の55tests・1231条件（914帰還/317停止、状態2開始96列）を再実行せず照合。'
        '大きいJSONの本文空応答を避ける軽量checkpointとhash付きartifact取得経路を固定。新byte/契約/native実行0。',
        '軽量checkpointのimplementation_read_pathsとevidence_accessから保存証拠を読む。次はwindow状態0/1の'
        'GetWindowAttribute selector0表08004938の必要word/分岐body、palette0806FB91、r8 frame thunk081C7AE9を限定する。'
        '上流/状態2の1231条件、旧採取/391条件/BP/nativeは再実行しない。task満杯busy2・live初期化/通常story/Ring取得は未受入。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
