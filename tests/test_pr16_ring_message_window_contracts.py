"""724新規条件を一度だけ評価し、帰還・不足・非native境界を独立検査する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_message_window_contracts as m

class WindowContractsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=m.saved_inputs();cls.result=m.evaluated();cls.rows={r['case']:r for r in cls.result['cases']}
        cls.report=m.build_result(cls.c,cls.result)
    def mutate_context(self,change):
        c=copy.deepcopy(self.c);change(c)
        with self.assertRaises(ValueError):m.validate_inputs(c)
    def mutate_result(self,change):
        r=copy.deepcopy(self.result);change(r)
        with self.assertRaises(ValueError):m.build_result(self.c,r)
    def test_total(self):self.assertEqual(self.report['contract_cases'],724)
    def test_partition(self):self.assertEqual((self.report['conditional_return_cases'],self.report['pending_stop_cases']),(587,137))
    def test_groups(self):self.assertEqual(self.result['groups'],m.EXPECTED_GROUPS)
    def test_one_evaluation(self):self.assertEqual(m.evaluated.cache_info().misses,1)
    def test_same_ram_count(self):self.assertEqual(self.report['same_ram_state01_sequences'],9)
    def test_same_ram_no_writes(self):self.assertTrue(all(s['host_writes_between_calls']==0 for s in self.result['sequences']))
    def test_same_ram_states(self):self.assertTrue(all(s['states']==[0,1,1]for s in self.result['sequences']))
    def test_26_rectangles(self):self.assertTrue(all(r['frame_rectangle_calls']==26 for r in self.rows.values()if r['group']=='frame-ram'))
    def test_frame_max_stack(self):self.assertEqual(self.report['maximum_stack_bytes'],252)
    def test_mode2_state1(self):self.assertTrue(all(r['task_state_after']==1 for r in self.rows.values()if r['group']=='state0-mode2'))
    def test_full_and_disabled_no_reservation(self):
        rows=[r for r in self.rows.values()if r['group']=='state0-mode2'and r['case'].endswith(('-full','-disabled'))]
        self.assertEqual(len(rows),32);self.assertTrue(all(r['queue_reserved'] is False for r in rows))
    def test_queue_partial_lock(self):
        r=self.rows['state0-short-queue-mode'];self.assertEqual((r['queue_lock_after'],r['task_state_after'],r['partial_write_count']),(1,0,5))
    def test_readonly_task_keeps_resource_writes(self):self.assertEqual(self.rows['state0-readonly-task']['partial_write_count'],8)
    def test_frame_fault_preserves_prefix(self):
        self.assertEqual([self.rows['frame-protected-'+str(i)]['nonstack_write_count']for i in (0,1,28,50,77)],[0,1,28,50,77])
    def test_pixel_pointer_fault_after_frame(self):
        for size in range(8,12):
            r=self.rows['state1-pixel-pointer-short-'+str(size)]
            self.assertEqual((r['nonstack_write_count'],r['task_state_after']),(78,1));self.assertFalse(r['state0_execution_claimed'])
    def test_partial_count(self):self.assertEqual(sum(self.result['groups'][g]for g in ('attribute-short','frame-short','state0-short','state1-short','tile-leaf-short')),60)
    def test_bios_known_prefix_not_resampled(self):self.assertIs(self.report['bios_prefix_resampling_needed'],False)
    def test_palette_pre_bios(self):self.assertEqual(self.rows['palette-224-20']['bios_arguments'],[0x083e30ac,0x020372ec,10])
    def test_palette_byte_truncation(self):self.assertEqual(self.rows['palette-65536-65536']['bios_arguments'],[0x083e30ac,0x0203712c,0])
    def test_bios_stops(self):
        self.assertTrue(all(r['stop'][1]==m.BIOS_COPY for r in self.rows.values()if r['group']in ('palette-bios','state0-palette')))
    def test_unaccepted(self):
        for k in (*m.prior.FALSE,'task_state1_to2_proven','bios_execution_observed','palette_copy_effects_proven','window_fill_effects_proven'):
            with self.subTest(flag=k):self.assertIs(self.report[k],False)
    def test_zero_replay(self):
        for k in ('new_node_count','new_window_bytes','rom_changes','new_emulator_processes','candidate_reconstructions','saved_nodes_redecoded',
            'accepted_native_cases_replayed','accepted_standalone_contracts_replayed','full_rom_scans','successful_callee_stubs'):
            with self.subTest(flag=k):self.assertEqual(self.report[k],0)
    def test_task_full_liveness_not_promoted(self):self.assertFalse(self.report['task_full_boundary']['liveness_proven'])
    def test_bad_node_count(self):self.mutate_context(lambda c:c['nodes'].pop())
    def test_candidate_mismatch(self):self.mutate_context(lambda c:c['tile_leaves'].update(candidate={}))
    def test_wrong_selector_word(self):self.mutate_context(lambda c:c['window_frontier']['selector0'].update(hex='00000000'))
    def test_wrong_frame_thunk(self):self.mutate_context(lambda c:next(n for n in c['nodes']if n['address']==0x081c7ae8).update(hex='3847'))
    def test_wrong_bios_identity(self):self.mutate_context(lambda c:c['analysis']['bios_prefix'].update(identity={}))
    def test_bios_promoted(self):self.mutate_context(lambda c:c['analysis']['audio_bios_prefix'].update(executed=True))
    def test_task_full_promoted(self):self.mutate_context(lambda c:c['task_contracts']['task_full_boundary'].update(liveness_proven=True))
    def test_prior_native_promoted(self):self.mutate_context(lambda c:c['tile_leaves'].update(ring_acquisition_accepted=True))
    def test_duplicate_result_case(self):self.mutate_result(lambda r:r['cases'].__setitem__(0,r['cases'][1]))
    def test_wrong_group_count(self):self.mutate_result(lambda r:r['groups'].update(**{'tile-value':29}))
    def test_host_write_in_sequence(self):self.mutate_result(lambda r:r['sequences'][0].update(host_writes_between_calls=1))
    def test_false_state2_completion(self):self.mutate_result(lambda r:r['sequences'][0].update(whole_state01_completed=True))
    def test_missing_sequence_case(self):self.mutate_result(lambda r:r['sequences'][0].update(state1_case='missing'))
    def test_success_stub_rejected(self):self.mutate_result(lambda r:r['cases'][0].update(successful_callee_stubs=1))
    def test_model_index_corners(self):
        self.assertEqual([m.tile_index(32,32,s)for s in range(4)],[0,1024,1024,3072])
        self.assertEqual(m.tile_index(63,63,3),4095);self.assertEqual(m.tile_index(64,64,3),0)
    def test_model_index_bounds(self):
        for shape in range(4):
            self.assertEqual(m.tile_index(0xffffffff,0xffffffff,shape),(1024,2048,2048,4096)[shape]-1)
    def test_model_value_palette16(self):self.assertEqual(m.tile_value(0x3ff,0xfc00,16,1,0),0xfc00)
    def test_model_value_signed_palette(self):self.assertEqual(m.tile_value(0xabcd,0,0xffffffff,1,0),0xabce)
    def test_model_value_low12(self):self.assertEqual(m.tile_value(0x1fff,0,15,1,0),0xf000)
    def test_models_reject_invalid(self):
        for args in ((-1,0,0),(0,0,4),(0,0,True)):
            with self.subTest(args=args),self.assertRaises(ValueError):m.tile_index(*args)
        with self.assertRaises(ValueError):m.tile_value(65536,0,0,0,0)
        with self.assertRaises(ValueError):m.palette_request(True,0,0)
    def test_rectangles_layout(self):
        r=m.rectangles(3,5,27);self.assertEqual(len(r),26);self.assertEqual(r[0],(0x200,1,4,1,1,15))
        self.assertEqual(sum(x[3]*x[4]for x in r),78)
        self.assertEqual(r[13][0],0xa0a);self.assertEqual(m.rectangles(3,5,27,True)[13][0],0xa05)
    def test_readonly_split_no_byte_change(self):
        seg=[(0x02001000,b'abc',True)];out=m.protect_byte(seg,0x02001001)
        self.assertEqual(b''.join(x[1]for x in out),b'abc');self.assertEqual([x[2]for x in out],[True,False,True])
    def test_no_implicit_stack(self):
        with self.assertRaisesRegex(ValueError,'非live stack read'):
            m.strict.Machine(self.c['nodes'],[]).read(m.b.vm.SP-4,4)
    def test_reserved_stack_cannot_be_seeded(self):
        with self.assertRaisesRegex(ValueError,'予約stack重複'):
            m.strict.Machine(self.c['nodes'],[(m.b.vm.SP-4,bytes(4),True)])
    def test_fifth_argument_explicit(self):
        self.assertTrue(all(self.rows[f'tile-arg-short-{entry}-{size}']['read_fault']['address']==m.b.vm.SP
            for entry in (0x08002805,0x0800283d)for size in range(4)))
    def test_local_harness_rejects_wrong_write(self):
        # 検査器自体の負対照。既存受入集合は実行しない。
        cases=m.task.Cases(self.c['nodes']);seg=[(m.TABLE,bytes.fromhex('58490008'),False),(m.b.WINDOWS,m.b.template(3),False)]
        with self.assertRaises(ValueError):cases.run('bad-getter-expectation',m.GETTER,seg,(0,0),value=4)
    def test_summaries_keep_next_boundary(self):
        current,next_step=m.summaries(self.report)
        self.assertIn('724',current);self.assertIn('prefix再採取は不要',next_step);self.assertIn('020376ECは未到達',next_step)

if __name__=='__main__':unittest.main()
