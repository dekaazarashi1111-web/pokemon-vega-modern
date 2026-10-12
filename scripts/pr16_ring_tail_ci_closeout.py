#!/usr/bin/env python3
"""保存済み末尾ABIを再実行せず、BP受入後のP05所有権テストを整合させる。"""
from __future__ import annotations
import copy
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pr16_ring_followup_v2 as s

BASE='dce59195dd99b8b85f5dd953862e78663e8c5458'
SLUG='pr16-ring-tail-ci-closeout'
TASK='PR-P08-7-RING-TAIL-CI-CLOSEOUT'
TITLE='保存末尾ABI成功照合とBP受入後のP05残件テスト修正'
SELF='scripts/pr16_ring_tail_ci_closeout.py'
TEST='tests/test_pr16_ring_tail_ci_closeout.py'
WORKFLOW='.github/workflows/pr16-ring-tail-ci-closeout.yml'
PRIOR='content/modernization/pr16_ring_external3_tail_abi.json'
REPORT='content/modernization/pr16_ring_tail_ci_closeout.json'
LEGACY='tests/test_modernization_p08_forgetting_evidence.py'
KEY='ring_tail_ci_closeout'
SOURCES=(LEGACY,)
EXTRA_CODE=(LEGACY,)
MIN_TESTS=12
OLD_BLOB='be55ec7824da0d29fcbd0ada89faf7d7d0af762d'
FAILURE_RUN=35054872496
FAILURE_JOB=104662809736
ABI_RUN=35054868301
ABI_HEAD='e64d6c86224905b21f108a57a3e5be00a226f001'
OLD_BLOCK="""        self.assertEqual(
            p05['status'], 'PENDING_THREE_BOUND_NATIVE_SUPPLY_ACCEPTANCES')
        self.assertEqual(p05['remaining_supply_gap_ids'], [
            'P05_NATIVE_RING_ACQUISITION_PHYSICAL',
            'P05_NATIVE_BP_EARNING_PHYSICAL',
            'P05_ORDINARY_POLICY_SELECTION_PHYSICAL',
        ])
"""
NEW_BLOCK="""        # BP受入原本を保持し、Ring/policyの未完を消去しない。
        self.assertEqual(
            p05['status'], 'PENDING_TWO_BOUND_NATIVE_SUPPLY_ACCEPTANCES')
        self.assertEqual(p05['remaining_supply_gap_ids'], [
            'P05_NATIVE_RING_ACQUISITION_PHYSICAL',
            'P05_ORDINARY_POLICY_SELECTION_PHYSICAL',
        ])
        bp_ref = current['bp_chooser_checkpoint']
        self.assertEqual(bp_ref['path'],
                         'content/modernization/pr16_bp_chooser_checkpoint.json')
        bp = record.load((ROOT/bp_ref['path']).read_bytes())
        self.assertEqual(bp_ref['latest_native_run'], 34946969126)
        self.assertEqual(bp_ref['accepted_case_count'], 3)
        self.assertEqual(bp['accepted_case_count'], 3)
        self.assertEqual(bp['accepted_case_ids'], [
            'rental-cancel-save-continue',
            'native-three-win-reward-9bp',
            'native-bp-spending-save-continue',
        ])
        self.assertEqual(bp['candidate']['sha256'],
                         'ceddbe91ecba0d81f6148b82d24771cced2d269f9474400bfed7a0938156934b')
        self.assertIs(current['full_p05_acceptance'], False)
"""
NO_REPEAT=('run35054868301の末尾43testsと条件付き合成は保存原本で成功照合済み。'
    'P05所有権テストの旧3件期待をBP受入原本に結び直した。旧failure run35054872496はfailureのまま保持。'
    'BP/P03 native、末尾ABI、prefix/bodyを再実行せず実caller非aliasと旧18ownerへ進む。')


def expected_source(original):
    s.need(original.count(OLD_BLOCK)==1,'修正前blockが一意でない')
    return original.replace(OLD_BLOCK,NEW_BLOCK)


def validate_prior(prior):
    s.need(prior['task']=='PR-P08-7-RING-EXTERNAL3-TAIL-ABI'
           and prior['run_id']==ABI_RUN and prior['source_head']==ABI_HEAD,'末尾原本identity差分')
    s.need(prior['focused_tests']==dict(tests_run=43,failures=0,errors=0,skips=0,successful=True),'末尾検証原本差分')
    a=prior['analysis']; c=a['conditional_composition']
    s.need(a['candidate']==s.CANDIDATE and a['instructions_verified']==3 and a['instruction_bytes_verified']==6,'末尾candidate差分')
    s.need(c['net_sp_delta_under_contract']==0 and c['body_tail_r0_is_function_return_value'] is False
           and c['caller_frame_integrity_discharged'] is False,'条件付き帰還境界差分')
    s.need(len(a['remaining_unread_targets'])==18 and a['remaining_unread_targets']==a['old_unread_targets'],'旧owner差分')
    for key in ('callee_return_proven','callee_return_observed','saved_slot_preservation_proven',
                'return_pointer_non_alias_proven','all_runtime_owners_excluded','ring_acquisition_accepted','release_ready'):
        s.need(a[key] is False,'受入過大化')
    for key in ('rom_changes','new_emulator_processes','candidate_reconstructions',
                'new_graph_decodes','accepted_native_cases_replayed','prior_abi_classifications_replayed'):
        s.need(a[key]==0,'原本scope差分')
    return a


def validate_failure(run):
    s.need(run['id']==FAILURE_RUN and run['head_sha']==ABI_HEAD
           and run['status']=='completed' and run['conclusion']=='failure','失敗原本の改称/取り違え')
    return {k:run[k] for k in ('id','head_sha','status','conclusion')}


def analyze(prior,out):
    a=validate_prior(prior)
    s.need(s.cmd('git','rev-parse',BASE+':'+LEGACY)==OLD_BLOB,'修正前test blob差分')
    original=s.cmd('git','show',BASE+':'+LEGACY)+'\n'
    s.need((s.ROOT/LEGACY).read_text(encoding='utf-8')==expected_source(original),'対象外test差分')
    failure=validate_failure(s.api('actions/runs/'+str(FAILURE_RUN)))
    return {'classification':'SAVED_TAIL_ABI_SUCCESS_REUSED_AND_STALE_P05_TEST_REPAIRED',
        'candidate':copy.deepcopy(s.CANDIDATE),
        'tail_abi_reused':{'path':PRIOR,'run_id':ABI_RUN,'source_head':ABI_HEAD,
            'tests_run':43,'reexecuted':False,'complete_commit':BASE},
        'original_failure':{**failure,'job_id':FAILURE_JOB,
            'test':'CurrentRemainingWorkOwnershipTests.test_current_snapshot_preserves_later_checkpoint_fields',
            'expected_at_failure':'PENDING_THREE_BOUND_NATIVE_SUPPLY_ACCEPTANCES',
            'actual_at_failure':'PENDING_TWO_BOUND_NATIVE_SUPPLY_ACCEPTANCES',
            'cause':'BP受入済みの現在正本へ旧3件snapshotを要求したtest期待の陳腐化。native不良ではない。'},
        'test_repair':{'path':LEGACY,'old_blob':OLD_BLOB,'changed_blocks':1,
            'bp_checkpoint_bound':True,'bp_accepted_case_count':3,'bp_run_id':34946969126,
            'remaining_p05_gaps':['P05_NATIVE_RING_ACQUISITION_PHYSICAL','P05_ORDINARY_POLICY_SELECTION_PHYSICAL'],
            'full_p05_acceptance':False},
        'old_unread_targets':copy.deepcopy(a['old_unread_targets']),
        'remaining_unread_targets':copy.deepcopy(a['remaining_unread_targets']),
        'conditional_composition':copy.deepcopy(a['conditional_composition']),
        'unresolved_indirect_edges':copy.deepcopy(a['unresolved_indirect_edges']),
        'prior_external_indirect_edges_preserved':copy.deepcopy(a['prior_external_indirect_edges_preserved']),
        'callee_return_proven':False,'callee_return_observed':False,'saved_slot_preservation_proven':False,
        'return_pointer_non_alias_proven':False,'all_runtime_owners_excluded':False,
        'ring_acquisition_accepted':False,'release_ready':False,'side_effects_excluded':False,
        'rom_changes':0,'new_emulator_processes':0,'candidate_reconstructions':0,'new_graph_decodes':0,
        'accepted_native_cases_replayed':0,'prior_abi_classifications_replayed':0}


def summaries(a):
    return ('external3末尾ABIの43tests成功・完了commitを保存原本で照合。P05残件テストの旧3件期待を'
        'BP正式3case/run34946969126と未完Ring/policy2件へ結び直し、誤再開・誤完了の拒否を検証。'
        '旧CI failure原本を保持。末尾ABI/受入native再実行0。',
        '次は保存external1/2/3契約と外側callerを結び、実frame/record/global非alias・帰還先条件を限定検証する。'
        '末尾byte/ABI・BP受入・修正済みP05期待テストを同一入力で再実行しない。旧18ownerとRing通常取得・policy/Circus・P08最終判定は未完。')


if __name__=='__main__':
    s.run(sys.modules[__name__])
