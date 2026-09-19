#!/usr/bin/env python3
"""724条件の成功原本を再実行せず、軽量の再開点とartifact出自を固定する。"""
from __future__ import annotations
import copy
import sys
import pr16_ring_followup_v2 as s

BASE='c16885a439f78860b0f2cf503d4615c2bcf039ee'
SLUG='pr16-ring-message-window-checkpoint'
TASK='PR-P08-7-RING-MESSAGE-WINDOW-CHECKPOINT'
TITLE='成功724条件の軽量再開点と次のBIOS供給境界を固定'
SELF='scripts/pr16_ring_message_window_checkpoint.py'
TEST='tests/test_pr16_ring_message_window_checkpoint.py'
WORKFLOW='.github/workflows/pr16-ring-message-window-checkpoint.yml'
PRIOR='content/modernization/pr16_ring_message_window_contracts.json'
REPORT='content/modernization/pr16_ring_message_window_checkpoint.json'
KEY='latest_ring_diagnostic'
MIN_TESTS=24
EXTRA_CODE=()
SOURCES=('scripts/pr16_ring_message_window_contracts.py','tests/test_pr16_ring_message_window_contracts.py')
SOURCE='cbc53699afa6ea8cc5d913fdba5d4bb451dd2833'
SOURCE_TASK='PR-P08-7-RING-MESSAGE-WINDOW-CONTRACTS'
RUN=35305255324
JOB=105476034868
ARTIFACT=10531358678
DIGEST='sha256:8d403a525cedc906fc7bbdd99aa556b7f316c14ad5ad75232d7db6adaab9fb99'
NO_REPEAT=('成功724条件/50testsの原本はこの軽量checkpointとhash付きartifactから再利用。'
    '今回checkpointはbyte採取/契約/nativeを実行しない。次は既知BIOS0B/0Cの根拠付き供給/効果境界。'
    'prefix/旧377命令836byte/724条件/1231条件/BP/nativeを重複実行しない。')
need=s.need
TRUE_FLAGS=('mode2_state0_to1_conditional_proven','r8_frame_callback_conditional_proven',
    'state0_progress_on_queue_failure','palette_pre_bios_arguments_proven','window_fill_pre_bios_arguments_proven')
FALSE_FLAGS=('queue_reservation_is_dma_completion','queue_failure_is_graphics_success','palette_copy_effects_proven',
    'window_fill_effects_proven','task_state01_complete_proven','task_state_transitions_proven','task_state1_to2_proven',
    'task_runtime_observed','task_scheduler_execution_observed','normal_story_observed','initializer_runtime_observed',
    'actual_callback_table_observed','bios_execution_observed','dma_execution_observed','ring_acquisition_accepted',
    'release_ready','bios_prefix_resampling_needed','implicit_ram_or_stack_values')
ZERO_FLAGS=('new_node_count','new_window_bytes','rom_changes','new_emulator_processes','candidate_reconstructions',
    'saved_nodes_redecoded','accepted_native_cases_replayed','accepted_standalone_contracts_replayed','full_rom_scans','successful_callee_stubs')
GROUPS={'attribute-byte':256,'attribute-id':48,'attribute-short':10,'frame-ram':93,'frame-short':13,
    'palette-bios':48,'state0-mode2':128,'state0-palette':20,'state0-short':14,'state01-sequence':9,
    'state1-short':4,'tile-index':32,'tile-leaf-short':19,'tile-value':30}


def compact(previous):
    need(previous['task']==SOURCE_TASK and previous['source_head']==SOURCE and previous['run_id']==RUN,'成功原本identity')
    need(previous['focused_tests']==dict(tests_run=50,failures=0,errors=0,skips=0,successful=True),'成功50tests')
    a=previous['analysis'];rows=a['cases'];by={r['case']:r for r in rows}
    need(a['candidate']==s.CANDIDATE and a['saved_node_count']==8628,'candidate/8628命令')
    need(a['contract_cases']==len(rows)==len(by)==724 and a['evaluation_cache_misses']==1,'724一回原本')
    need(a['conditional_return_cases']==sum(r['returned']for r in rows)==587 and a['pending_stop_cases']==137,'帰還/停止原本')
    need(all((r['stop'] is None)==r['returned'] and r['return_sp_r4_r11_proven']==r['returned']
        and r['native_observation'] is False and r['successful_callee_stubs']==0 for r in rows),'停止/非native境界')
    for row in rows:
        if row['group']=='state0-mode2':
            need(row['task_state_after']==1 and row['graphics_success_claimed'] is False
                and row['dma_execution_observed'] is False,'state0進行/未描画境界')
            if row['case'].endswith(('-full','-disabled')):need(row['queue_reserved'] is False,'queue失敗保持')
    need(a['groups']==GROUPS=={k:sum(r['group']==k for r in rows)for k in GROUPS},'group集合')
    seqs=a['state01_sequences'];pairs=set()
    need(a['same_ram_state01_sequences']==len(seqs)==9,'同一RAM9列')
    for seq in seqs:
        pair=(seq['task_id'],seq['queue_pattern']);need(pair not in pairs,'連続列重複');pairs.add(pair)
        first,second=by.get(seq['state0_case']),by.get(seq['state1_case'])
        need(first is not None and second is not None and first['group']=='state0-mode2'
            and second['group']=='state01-sequence' and first['returned'] is True
            and first['task_state_after']==1 and second['stop']==['保存node境界で停止',0x081c7a84], '連続列参照')
        need(seq['states']==[0,1,1] and seq['host_writes_between_calls']==0 and seq['bios_service']==12
            and seq['bios_executed'] is False and seq['whole_state01_completed'] is False,'連続列境界')
    need(pairs=={(t,p)for t in (0,7,15)for p in ('free','wrap','full')},'連続列domain')
    for k in TRUE_FLAGS:need(a[k] is True,'条件付き証明 '+k)
    for k in FALSE_FLAGS:need(a[k] is False,'未受入境界 '+k)
    for k in ZERO_FLAGS:need(a[k]==0,'新実行禁止 '+k)
    full=a['task_full_boundary']
    need(full['busy_after']==2 and full['task_allocated'] is False and full['liveness_proven'] is False
        and full['normal_play_reproduction_observed'] is False,'task満杯境界')
    bios=a['pending_bios']
    need([r['entry']for r in bios]==[0x081c7a89,0x081c7a85] and [r['service']for r in bios]==[11,12],'BIOS2境界')
    for r,raw in zip(bios,('0bdf7047','0cdf7047')):
        p=r['saved_prefix'];need(p['start']==r['entry']&~1 and p['hex']==raw
            and p['identity']==s.identity(bytes.fromhex(raw)) and p['executed'] is False
            and p['return_proven'] is False,'BIOS保存prefix')
    need(bios[0]['source_for_state0']==0x083e30ac and bios[0]['destination_for_state0']==0x020372ec
        and bios[0]['halfwords_for_state0']==10 and bios[0]['second_palette_destination']==0x020376ec
        and bios[0]['second_copy_reached'] is False,'palette供給/未到達')
    need(bios[1]['fill_word']==0x11111111 and bios[1]['fixture_control']==0x01000360,'fill前ABI')
    need(a['missing_readonly_and_partial_write_cases']==60 and a['tile_leaf_return_cases']==62
        and a['maximum_stack_bytes']==252 and a['frame_rectangle_count']==26,'局所境界件数')
    result={k:copy.deepcopy(a[k])for k in (*TRUE_FLAGS,*FALSE_FLAGS,*ZERO_FLAGS,
        'groups','task_full_boundary','pending_bios','remaining_window_attribute_selectors_unproven',
        'maximum_stack_bytes','frame_rectangle_count','missing_readonly_and_partial_write_cases','tile_leaf_return_cases','boundary_ja')}
    result.update({'classification':'SAVED_WINDOW_STATE01_PROOF_CHECKPOINT_NO_REPLAY','candidate':dict(s.CANDIDATE),
        'saved_node_count':8628,'reused_contract_cases':724,'reused_conditional_return_cases':587,
        'reused_pending_stop_cases':137,'reused_same_ram_state01_sequences':9,'reused_source_tests':50,
        'new_contract_cases_executed':0,'source_record_commit':BASE,'source_head':SOURCE,'source_run_id':RUN,
        'source_job_id':JOB,'source_report':PRIOR,'original_evaluation_cache_misses':1,
        'implementation_read_paths':list(SOURCES),
        'evidence_access':{'artifact_id':ARTIFACT,'run_id':RUN,'artifact_name':'pr16-ring-message-window-contracts',
            'archive_sha256':DIGEST.split(':',1)[1],'analysis_member':'analysis.json','receipt_member':'recorded-result.json',
            'manifest_member':'export/manifest.json','manifest_identity':copy.deepcopy(a['export_manifest']),
            'logical_context':'saved-context.json','text_format':'utf8-text-chunks-v1',
            'method_ja':'GitHub.download_workflow_artifactで取得しarchive SHA→manifest→各chunk→logical fileのsize/SHAを照合。'
                '大きいJSON本文の空応答を内容不在や権限不足と推測しない。失効時もtracked原本を改変しない。'}})
    need(len(s.stable(result))<14000,'checkpoint size上限');return result


def verify_actions(job,artifact):
    need(job['id']==JOB and job['run_id']==RUN and job['status']=='completed' and job['conclusion']=='success','成功job原本')
    need(job['steps'] and all(r['status']=='completed' and r['conclusion']=='success'for r in job['steps']),'全step成功')
    need(artifact['id']==ARTIFACT and artifact['name']=='pr16-ring-message-window-contracts'
        and artifact['expired'] is False and artifact['digest']==DIGEST,'artifact原本')
    r=artifact['workflow_run'];need(r['id']==RUN and r['head_sha']==SOURCE and r['head_branch']==s.BRANCH,'artifact source binding')
    return {'job_status':'completed','job_conclusion':'success','steps':len(job['steps']),
        'artifact_id':ARTIFACT,'artifact_digest':DIGEST,'artifact_expired':False}


def analyze(previous,out):
    result=compact(previous);result['source_report_identity']=s.identity((s.ROOT/PRIOR).read_bytes())
    result['actions_verified_without_replay']=verify_actions(s.api('actions/jobs/'+str(JOB)),s.api('actions/artifacts/'+str(ARTIFACT)))
    (out/'analysis.json').write_bytes(s.stable(result));return result


def summaries(r):
    return ('成功原本724条件/50tests(587帰還/137停止、9同一RAM列)を再実行せず照合し、軽量checkpointとhash付き取得経路を固定。'
        'mode2 state0進行・26矩形frame RAM帰還を確認済み。queue失敗と描画成功は区別。',
        '本checkpointのimplementation_read_paths/evidence_accessから継続。次は既知BIOS0B/0Cの根拠付き供給元/メモリ効果契約。'
        'palette083E30AC→020372ECの10半word、次の020376ECは未到達。state1はframe書込後fill11111111で停止。'
        '保存prefix/724条件/旧採取/1231条件/BP/nativeを再実行しない。task満杯busy2と通常story/Ring/live初期化の未受入を保持。')


if __name__=='__main__':
    need(sys.argv[1:]==['run'],'runだけを許可')
    s.assert_remote(s.cmd('git','rev-parse','HEAD'),attempts=12);s.run(sys.modules[__name__])
