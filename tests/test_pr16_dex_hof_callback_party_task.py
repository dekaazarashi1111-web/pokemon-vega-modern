"""新party task局所診断の変異試験。旧suite、native実行、ROM再構成は行わない。"""
import copy
import unittest
import pr16_dex_hof_callback_party_task as v

FIXTURE = None


class PartyTaskDiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 親runnerが明示注入するfixtureだけを使用する。
        if FIXTURE is None:
            raise RuntimeError('FIXTURE=(raw, review)の明示注入が必要です')
        cls.original, cls.review = FIXTURE

    def setUp(self):
        self.raw = bytearray(self.original)

    def reject_at(self, address, replacement, refresh=True):
        off = address - 0x08000000
        old = self.raw[off:off + len(replacement)]
        self.assertNotEqual(old, replacement, '変異は実際に入力を変更する')
        try:
            self.raw[off:off + len(replacement)] = replacement
            review = v.make_review(self.raw) if refresh else self.review
            with self.assertRaises(ValueError):
                v.check_local(self.raw, review)
        finally:
            self.raw[off:off + len(replacement)] = old

    def change(self, address, kind, *args):
        self.reject_at(address, v.encoded(v.Ins(address, kind, args)))

    def test_01_positive_diagnostic_retains_unknown(self):
        result = v.check_local(self.raw, self.review)
        self.assertEqual(result['newly_classified'], 0)
        self.assertFalse(result['donor_eligible'])
        self.assertFalse(result['current_acceptance_claimed'])
        self.assertFalse(result['full_root_to_hit_lifetime_proven'])
        self.assertTrue(result['actual_special_registration_bound'])
        self.assertTrue(result['sixth_stack_argument_local_flow_bound'])
        self.assertEqual(result['unresolved_obligations'], list(v.BLOCKERS))

    def test_02_regions_cannot_promote_diagnostic(self):
        with self.assertRaisesRegex(ValueError, 'unknown retained'):
            v.regions(self.raw, self.review)

    def test_03_fixed_manifest_matches_windows(self):
        self.assertEqual(self.review, v.make_review(self.raw))

    def test_04_all_instruction_halfwords_reject_refreshed_hashes(self):
        # BLの後半も含める。SHAを更新しても意味別encoderが拒否する。
        count = 0
        for label, rows in v.BLOCKS.items():
            for ins in rows:
                for part in range(0, ins.size, 2):
                    a = ins.address + part
                    off = a - 0x08000000
                    value = int.from_bytes(self.raw[off:off + 2], 'little') ^ 1
                    with self.subTest(block=label, address=a):
                        self.reject_at(a, value.to_bytes(2, 'little'))
                    count += 1
        self.assertGreater(count, 509)

    def test_05_all_literal_words_reject_refreshed_hashes(self):
        for a, value in v.LITERALS.items():
            with self.subTest(address=a):
                self.reject_at(a, (value ^ 2).to_bytes(4, 'little'))

    def test_06_hash_drift_without_refresh(self):
        self.reject_at(0x08128166, v.encoded(v.Ins(0x08128166, 'spmem', (False, 0, 8))), False)

    def test_07_caller_sixth_argument_slot(self):
        self.change(0x08128166, 'spmem', False, 0, 8)

    def test_08_callee_sixth_argument_slot(self):
        self.change(0x0811F2C2, 'spmem', True, 0, 0x2C)

    def test_09_constructor_stack_frame_size(self):
        self.change(0x0811F256, 'spadd', -8)

    def test_10_constructor_task_field_not_exit_field(self):
        self.change(0x0811F2C4, 'mem', False, 'word', 0, 5, 4)

    def test_11_task_consumer_field_not_exit_field(self):
        self.change(0x0811F5C0, 'mem', True, 'word', 0, 0, 4)

    def test_12_create_task_actual_call(self):
        self.change(0x0811F5C4, 'call', 0x08000544)

    def test_13_create_task_field_and_active(self):
        self.change(0x08076BCE, 'mem', False, 'word', 2, 4, 4)
        self.change(0x08076BE8, 'mem', False, 'byte', 0, 4, 5)

    def test_14_create_task_stride(self):
        self.change(0x08076BC4, 'shift', 'lsl', 5, 0, 2)

    def test_15_scheduler_calls_run_tasks(self):
        self.change(0x0811F3AA, 'call', 0x08076D40)

    def test_16_scheduler_same_task_field0(self):
        self.change(0x08076D28, 'mem', True, 'word', 1, 4, 4)
        self.change(0x08076D24, 'shift', 'lsl', 4, 4, 2)

    def test_17_scheduler_interwork_register(self):
        self.change(0x081C7ACC, 'bx', 2)

    def test_18_special397_root_pointer(self):
        self.reject_at(0x0816369C, (0x081281C1).to_bytes(4, 'little'))

    def test_19_special_table_index_stride(self):
        self.change(0x080697C4, 'shift', 'lsr', 0, 0, 15)

    def test_20_tutor_argument_guard_and_action(self):
        self.change(0x0812815C, 'imm', 'cmp', 0, 15)
        self.change(0x08128170, 'imm', 'mov', 2, 0)

    def test_21_actual_hook_bias_and_branch(self):
        self.change(0x09097A84, 'imm', 'sub', 0, 2)
        self.change(0x09097A8C, 'branch', 8, 0x09097A9E)

    def test_22_action_selector_table_slot(self):
        self.reject_at(0x08120418, (0x08120496).to_bytes(4, 'little'))

    def test_23_tutor_call_preserves_task_id(self):
        self.change(0x0812048E, 'addi', 0, 5, 0)

    def test_24_input_is_signed_not_unsigned(self):
        self.change(0x08126710, 'shift', 'lsr', 1, 0, 24)
        self.change(0x08126AD2, 'shift', 'lsr', 5, 0, 24)

    def test_25_tutor_full_moves_branch(self):
        self.change(0x0812777A, 'branch', 1, 0x081277BC)

    def test_26_each_task_rewrite_uses_function_field0(self):
        for a,rd,rb in [(0x081277CE,1,0),(0x081266F2,0,1),(0x08126A5E,1,0),(0x08126AA6,0,1)]:
            with self.subTest(address=a):
                self.change(a, 'mem', False, 'word', rd, rb, 4)

    def test_27_each_task_rewrite_stride(self):
        for a,rd,rs in [(0x081277C8,0,0),(0x081266EC,1,1),(0x08126A58,0,0),(0x08126AA0,1,1)]:
            with self.subTest(address=a):
                self.change(a, 'shift', 'lsl', rd, rs, 2)

    def test_28_final_yes_branch(self):
        self.change(0x08126AD6, 'branch', 1, 0x08126AF6)

    def test_29_complete_hit_call_target(self):
        self.change(0x08126B0A, 'call', 0x08008B48)

    def test_30_hit_following_literal_register(self):
        self.change(0x08126B0E, 'literal', 5, 0x08126B44)

    def test_31_manifest_missing_instruction_block(self):
        review = copy.deepcopy(self.review)
        del review['instruction_windows']['tutor_root_normal_constructor']
        with self.assertRaises(ValueError): v.check_local(self.raw, review)

    def test_32_manifest_missing_literal(self):
        review = copy.deepcopy(self.review)
        del review['literal_words'][str(0x0816369C)]
        with self.assertRaises(ValueError): v.check_local(self.raw, review)

    def test_33_manifest_relocated_window(self):
        review = copy.deepcopy(self.review)
        review['minimal_instruction_window']['address'] += 2
        with self.assertRaises(ValueError): v.check_local(self.raw, review)

    def test_34_manifest_cannot_add_acceptance(self):
        review = copy.deepcopy(self.review)
        review['newly_classified'] = 1
        with self.assertRaises(ValueError): v.check_local(self.raw, review)

    def test_35_record_disallows_bytes_and_paths(self):
        for forbidden in ('raw', 'hex', 'path', 'value'):
            review = copy.deepcopy(self.review)
            review['hit'][forbidden] = 'untrusted'
            with self.subTest(field=forbidden):
                with self.assertRaises(ValueError): v.check_local(self.raw, review)

    def test_36_unbound_setup_cannot_turn_into_acceptance(self):
        # 未拘束state0を変えても局所診断は変わらないが、分類/lease発行は拒否し続ける。
        self.raw[0x0811F488 - 0x08000000] ^= 1
        result = v.check_local(self.raw, self.review)
        self.assertEqual(result['newly_classified'], 0)
        self.assertFalse(result['full_root_to_hit_lifetime_proven'])
        with self.assertRaises(ValueError): v.regions(self.raw, self.review)


if __name__ == '__main__':
    unittest.main()
