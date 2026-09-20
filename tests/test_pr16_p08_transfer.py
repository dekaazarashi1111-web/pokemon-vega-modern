"""既存nativeを実行せず、候補移送の拒否境界と所有範囲を検証する。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('transfer', ROOT/'scripts/pr16_p08_transfer.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def load(path):
    return json.loads((ROOT/path).read_text())


def inputs():
    return load(m.IMPACT), {key:load(path) for key,path in m.PATHS.items()}


def projection_inputs():
    impact, reps = inputs()
    state = load('content/modernization/pr16_native_supply_resume_20260913.json')
    backlog = load('content/modernization/p08_remaining_work.json')
    # Synthetic pre-transfer boundary, independent of whether live task is finished.
    final = next(r for r in backlog['remaining_conditions'] if r['id'] == 'FINAL_NATIVE_ACCEPTANCE')
    final.update(complete=False, completed_representative_regression_ids=list(m.PATHS),
                 remaining_representative_regression_ids=[])
    for row in backlog['remaining_conditions']:
        if 'parent_scope_status' in row:
            row['status'] = row['parent_scope_status']
    result = dict(candidate=impact['candidate'], candidate_crc32=impact['candidate_crc32'],
                  final_native_acceptance_complete=True, release_ready=False,
                  domain_transfers=m.matrix(impact,reps))
    return state, backlog, result


class TransferTests(unittest.TestCase):
    def test_current_four_representatives_cover_six_domains(self):
        impact, reps = inputs()
        before = copy.deepcopy((impact,reps))
        out = m.matrix(impact,reps)
        self.assertEqual(set(out), m.DOMAINS)
        self.assertTrue(all(r['accepted'] for r in out.values()))
        self.assertEqual(out['CIRCUS']['decision'], 'SAME_CANDIDATE_INHERIT')
        self.assertEqual(out['BP']['parent'], impact['candidate_impacts']['BP']['parent'])
        self.assertEqual((impact,reps), before)
        self.assertIs(impact['final_native_acceptance_complete'],False)

    def test_missing_or_extra_representative(self):
        for extra in (False, True):
            impact, reps = inputs()
            reps['unknown'] = copy.deepcopy(next(iter(reps.values()))) if extra else reps.pop(next(iter(reps)))
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                m.matrix(impact,reps)

    def test_mixed_candidate_and_regression_id(self):
        for field,value in [('candidate',dict(size=33554432,sha256='0'*64)),('regression_id','OTHER')]:
            impact,reps = inputs()
            reps['P08_SHARED_SAVE_LOAD'][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                m.matrix(impact,reps)

    def test_unverified_and_integer_boolean_flags(self):
        for flag in ('representative_accepted','native_verified','visual_review_completed'):
            for value in (False,1):
                impact,reps = inputs()
                reps['P08_SHARED_SAVE_LOAD'][flag] = value
                with self.subTest(flag=flag,value=value), self.assertRaises(ValueError):
                    m.matrix(impact,reps)

    def test_replay_and_bool_counts_rejected(self):
        for field in ('new_emulator_processes','arm_compiles','arm_links','accepted_standalone_replays','prefix_wins_reexecuted'):
            for value in (1,False):
                impact,reps = inputs()
                reps['P08_BP_RETURN_PARTY'][field] = value
                with self.subTest(field=field,value=value), self.assertRaises(ValueError):
                    m.matrix(impact,reps)

    def test_original_core_accounting(self):
        for key in m.PATHS:
            impact,reps = inputs()
            reps[key]['original_fresh_cores'] += 1
            with self.subTest(key=key), self.assertRaises(ValueError):
                m.matrix(impact,reps)

    def test_unmapped_or_duplicate_hook(self):
        for hook in ('NEW_UNREVIEWED_HOOK','SAVE_DISPATCH'):
            impact,reps = inputs()
            impact['candidate_impacts']['BP']['shared_hooks'].append(hook)
            with self.subTest(hook=hook), self.assertRaises(ValueError):
                m.matrix(impact,reps)

    def test_parent_identity_cannot_be_relabelled(self):
        impact,reps = inputs()
        impact['candidate_impacts']['BP']['parent'] = copy.deepcopy(impact['candidate'])
        with self.assertRaises(ValueError):
            m.matrix(impact,reps)

    def test_changed_source_requires_new_review(self):
        impact,reps = inputs()
        impact['candidate_impacts']['RING']['source_review']['mismatches'] = 1
        with self.assertRaises(ValueError):
            m.matrix(impact,reps)

    def test_p07_content_and_full_rom_proof_required(self):
        for change in ('p07','rollback','full'):
            impact,reps = inputs()
            if change == 'p07':
                impact['p07_content_preservation'][0]['byte_preserved'] = False
            elif change == 'rollback':
                impact['reconstruction']['whole_chain_rollback_matches_parent'] = False
            else:
                impact['full_rom_sparse_comparison'] = False
            with self.subTest(change=change), self.assertRaises(ValueError):
                m.matrix(impact,reps)

    def test_projection_preserves_parent_authorities_and_queues_wiki(self):
        state,backlog,result = projection_inputs()
        before = copy.deepcopy((state,backlog,result))
        s,b = m.project(state,backlog,result)
        self.assertEqual((state,backlog,result),before)
        self.assertEqual(s['candidate'],state['candidate'])
        self.assertEqual(b['next_integration_candidate'],backlog['next_integration_candidate'])
        self.assertEqual(s['remaining_p08_gate_ids'],['RELEASE_DECISION'])
        self.assertEqual(s['next_action']['id'],'P08_CANDIDATE_WIKI')
        self.assertEqual(b['final_candidate']['sha256'],result['candidate']['sha256'])
        self.assertIs(b['final_candidate']['final_product_sha_fixed'],False)
        self.assertIs(b['release_ready'],False)
        self.assertIs(b['active_baseline_changed'],False)
        self.assertEqual(b['pre_transfer_final_candidate'],backlog['final_candidate'])

    def test_duplicate_or_unfinished_transfer_rejected(self):
        for mutation in ('duplicate','remaining','missing'):
            state,backlog,result = projection_inputs()
            final = next(r for r in backlog['remaining_conditions'] if r['id']=='FINAL_NATIVE_ACCEPTANCE')
            if mutation == 'duplicate':
                final['complete'] = True
            elif mutation == 'remaining':
                final['remaining_representative_regression_ids'] = ['P08_SHARED_SAVE_LOAD']
            else:
                final['completed_representative_regression_ids'].pop()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                m.project(state,backlog,result)

    def test_release_or_physical_gap_overclaim_rejected(self):
        for mutation in ('release','physical','parent'):
            state,backlog,result = projection_inputs()
            if mutation == 'release':
                result['release_ready'] = True
            elif mutation == 'physical':
                state['remaining_physical_gap_ids'] = ['PENDING']
            else:
                next(r for r in backlog['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')['complete'] = False
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                m.project(state,backlog,result)


if __name__ == '__main__':
    unittest.main()
