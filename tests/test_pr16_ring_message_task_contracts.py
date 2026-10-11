"""新規1231結合条件は一回だけ実行し、境界/順序/状態/出自の改変を検査する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_task_contracts as m


class JoinedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=m.saved_inputs();cls.e=m.evaluated();cls.r=m.build_result(cls.c,cls.e)
        cls.by={r['case']:r for r in cls.e['cases']}
    def group(self,name):return [r for r in self.e['cases'] if r['group']==name]
    def test_groups(self):self.assertEqual(self.e['groups'],m.EXPECTED_GROUPS)
    def test_counts(self):self.assertEqual((self.r['contract_cases'],self.r['conditional_return_cases'],self.r['pending_stop_cases']),(1231,914,317))
    def test_single_evaluation(self):m.evaluated();self.assertEqual(m.evaluated.cache_info().misses,1)
    def test_unique_labels(self):self.assertEqual(len(self.by),1231)
    def test_busy_domain(self):self.assertEqual([int(r['case'].split('-')[1]) for r in self.group('upstream-busy')],list(range(1,256)))
    def test_busy_no_write(self):self.assertTrue(all(r['nonstack_write_count']==0 and r['call_count']==0 and r['return_value']==0 for r in self.group('upstream-busy')))
    def test_script_busy_cursor(self):self.assertTrue(all(r['nonstack_write_count']==4 and r['return_value']==0 for r in self.group('script-busy')))
    def test_upstream_return(self):self.assertTrue(all(r['returned'] and r['return_value']==1 for r in self.group('upstream-producer')))
    def test_script_return(self):self.assertTrue(all(r['returned'] and r['return_value']==0 for r in self.group('script-producer')))
    def test_direct_and_fallback(self):self.assertEqual({r['operand_is_null'] for r in self.group('script-producer')},{False,True})
    def test_task_full_not_allocated(self):
        rows=[r for r in self.group('upstream-producer') if r['task_layout']=='full']
        self.assertEqual(len(rows),2);self.assertTrue(all(not r['task_allocated'] for r in rows))
        self.assertEqual(self.r['task_full_boundary']['busy_after'],2);self.assertFalse(self.r['task_full_boundary']['liveness_proven'])
    def test_partial_cursor_consumption(self):
        for n in range(4):self.assertEqual(self.by['short-script-operand-'+str(n)]['nonstack_write_count'],n)
    def test_fallback_short_after_cursor(self):self.assertEqual(self.by['short-script-fallback']['nonstack_write_count'],4)
    def test_source_failure_before_busy(self):self.assertEqual(self.by['short-script-source']['nonstack_write_count'],4)
    def test_task_ids(self):self.assertEqual(self.r['task_ids'],list(range(16)))
    def test_noop_signed_representatives(self):
        self.assertIn(32768,self.r['task_noop_state_representatives']);self.assertIn(65535,self.r['task_noop_state_representatives'])
        self.assertTrue(all(r['nonstack_write_count']==r['call_count']==0 for r in self.group('task-noop')))
    def test_not_exhaustive_uint16(self):self.assertFalse(self.r['all_uint16_states_exhaustively_executed'])
    def test_id_aliases(self):self.assertEqual(len(self.group('task-id-alias')),48)
    def test_out_of_range_stops(self):self.assertTrue(all(not r['returned'] and r['nonstack_write_count']==0 for r in self.group('task-bounds')))
    def test_delete_links(self):self.assertEqual(len(self.group('destroy-links')),64)
    def test_inactive_delete_no_write(self):self.assertTrue(all(r['nonstack_write_count']==0 for r in self.group('destroy-inactive')))
    def test_broken_links_partial(self):self.assertEqual(self.by['delete-bad-link-1-16']['nonstack_write_count'],2)
    def test_sequence_count(self):self.assertEqual(len(self.e['sequences']),96)
    def test_sequence_input_scope(self):self.assertTrue(all(r['initial_task_state']==2 and not r['state01_execution_claimed'] for r in self.e['sequences']))
    def test_sequence_successors(self):self.assertTrue(all(r['same_ram_successor'] and len(r['cases'])==3 for r in self.e['sequences']))
    def test_wait_retains_task(self):self.assertTrue(all(not r['task_completed'] for name in ('poll-countdown','poll-delay-finished') for r in self.group(name)))
    def test_termination_deletes_task(self):self.assertTrue(all(r['task_completed'] for r in self.group('poll-terminated')))
    def test_fast_queue_only_on_finish(self):self.assertEqual(sum(r['queue_requests'] for r in self.e['cases'] if 'queue_requests'in r),48)
    def test_nonbool_active_unaccepted(self):
        rows=self.group('poll-active-boundary');self.assertEqual({r['input_active_byte'] for r in rows},{0,2,127,128,255})
        self.assertTrue(all(not r['active_boolean_precondition'] for r in rows if r['input_active_byte']!=0))
    def test_renderer_prefix_preserved(self):self.assertEqual(self.by['poll-short-pool-last-slot']['nonstack_write_count'],1)
    def test_readonly_busy_prevents_delete(self):self.assertEqual(self.by['poll-readonly-busy']['nonstack_write_count'],0)
    def test_readonly_task_after_busy(self):self.assertEqual(self.by['poll-readonly-task']['nonstack_write_count'],1)
    def test_broken_link_after_busy(self):self.assertEqual(self.by['poll-bad-next']['nonstack_write_count'],2)
    def test_window_flags_domain(self):self.assertEqual(self.r['window_flag_byte_values'],list(range(256)))
    def test_window_flags_partial(self):self.assertTrue(all(r['nonstack_write_count']==1 and not r['returned'] for r in self.group('window-flags')))
    def test_window_setup_unresolved(self):self.assertTrue(all(not r['returned'] and r['task_state_after']==0 for r in self.group('window-setup')))
    def test_window_frame_not_executed(self):self.assertTrue(all(r['frame_callback']==0x080f8185 and not r['frame_callback_execution_proven'] for r in self.group('window-frame')))
    def test_window_short_no_write(self):self.assertTrue(all(r['nonstack_write_count']==0 for r in self.group('window-short')))
    def test_state2_only(self):self.assertTrue(self.r['task_state2_conditional_cleanup_proven']);self.assertFalse(self.r['task_state01_complete_proven'])
    def test_no_native_promotion(self):
        for k in ('task_runtime_observed','task_scheduler_execution_observed','normal_story_observed','initializer_runtime_observed',
                  'actual_callback_table_observed','dma_execution_observed','ring_acquisition_accepted','release_ready'):
            with self.subTest(key=k):self.assertIs(self.r[k],False)
    def test_no_replay_or_restore(self):
        for k in ('rom_changes','new_emulator_processes','candidate_reconstructions','saved_nodes_redecoded',
                  'new_node_count','new_window_bytes','accepted_native_cases_replayed','accepted_standalone_contracts_replayed','successful_callee_stubs'):
            with self.subTest(key=k):self.assertEqual(self.r[k],0)
    def test_return_abi(self):self.assertTrue(all(r['return_sp_r4_r11_proven']==r['returned'] for r in self.e['cases']))
    def test_critical_opcode_rejection(self):
        for at in (0x08068c42,0x08068c4a,0x08068cb4,0x08002e44,0x08068d10):
            with self.subTest(site=at):
                c=copy.deepcopy(self.c);next(n for n in c['nodes'] if n['address']==at)['hex']='0000'
                with self.assertRaises(ValueError):m.validate_inputs(c)
    def test_candidate_rejection(self):
        c=copy.deepcopy(self.c);c['window_bytes']['candidate']={}
        with self.assertRaises(ValueError):m.validate_inputs(c)
    def test_prior_acceptance_rejection(self):
        c=copy.deepcopy(self.c);c['window_bytes']['ring_acquisition_accepted']=True
        with self.assertRaises(ValueError):m.validate_inputs(c)
    def test_prior_node_count_rejection(self):
        c=copy.deepcopy(self.c);c['nodes'].pop()
        with self.assertRaises(ValueError):m.validate_inputs(c)
    def test_wrong_count_rejection(self):
        e=dict(self.e,cases=self.e['cases'][:-1])
        with self.assertRaises(ValueError):m.build_result(self.c,e)


class HarnessTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.nodes=m.saved_inputs()['nodes']
    def test_wrong_expected_return_rejected(self):
        with self.assertRaises(ValueError):m.Cases(self.nodes).run('wrong-return',m.UPSTREAM,[(m.BUSY,b'\1',False)],(0,),value=1)
    def test_expected_stop_cannot_hide_return(self):
        with self.assertRaises(ValueError):m.Cases(self.nodes).run('wrong-stop',m.UPSTREAM,[(m.BUSY,b'\1',False)],(0,),stop=('保存node境界で停止',0))
    def test_wrong_write_rejected(self):
        with self.assertRaises(ValueError):m.Cases(self.nodes).run('wrong-write',m.UPSTREAM,[(m.BUSY,b'\1',True)],(0,),writes=[(m.BUSY,1,0)])
    def test_task_input_ranges(self):
        for task_id,state in ((-1,0),(16,0),(0,-1),(0,65536)):
            with self.subTest(task_id=task_id,state=state):
                with self.assertRaises(ValueError):m.task_fixture(task_id,state)
    def test_cursor_range(self):
        for count in (-1,5,True):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):m.cursor_writes(count)
    def test_delete_input_size(self):
        with self.assertRaises(ValueError):m.destroy_expected(bytes(639),0)
    def test_trim_requires_existing_object(self):
        with self.assertRaises(ValueError):m.trim([(m.BUSY,b'\1',False)],0,0)
    def test_script_context_range(self):
        with self.assertRaises(ValueError):m.script_segments(0,length=105)


if __name__=='__main__':unittest.main()
