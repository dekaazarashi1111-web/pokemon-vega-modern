"""子機発行証拠の新しい陰性契約だけ。受入済み13profile/26試験は呼ばない。"""
import copy
import unittest
import pr16_berry_child as m


def fixture(full=True):
    value = dict(schema_version=1, native_processes=1, child_boot_fixtures=1, host_writes_after_entry=0,
        host_write_guards=7, mapped_bytes=m.COPY_SIZE, parent_game_boots=0, steps=20,
        all_issued_child_bytes_equal_source=True, target_byte_mask=15 if full else 7,
        status='CONDITIONAL_CHILD_READER_OBSERVED' if full else 'BOUNDED_CHILD_FRONTIER',
        stop_reason='TARGET_FOUR_BYTES_ISSUED' if full else 'FINITE_STEP_BUDGET',
        issued_spans=[dict(address=m.TARGET-1+i*2, width_mask=2, visits=1) for i in range(3 if full else 2)])
    value.update({k: False for k in m.FALSE_KEYS})
    return value


class ChildTests(unittest.TestCase):
    def test_complete(self): self.assertEqual(m.validate_native(fixture())['target_bytes_issued'], 4)
    def test_partial(self): self.assertFalse(m.validate_native(fixture(False))['all_four_bytes_issued'])
    def test_no_promotion(self): self.assertEqual(m.validate_native(fixture())['formal_classification_changes'], 0)
    def test_no_mutation(self):
        v=fixture(); old=copy.deepcopy(v); m.validate_native(v); self.assertEqual(v,old)
    def test_width_combination(self):
        v=fixture();v['issued_spans'][1]['width_mask']=6;self.assertTrue(m.validate_native(v)['all_four_bytes_issued'])
    def test_lied_mask(self):
        v=fixture(False);v['target_byte_mask']=15
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_lied_status(self):
        v=fixture(False);v['status']='CONDITIONAL_CHILD_READER_OBSERVED'
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_lied_stop(self):
        v=fixture();v['stop_reason']='FINITE_STEP_BUDGET'
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_duplicate(self):
        v=fixture();v['issued_spans'].append(v['issued_spans'][0])
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_unaligned_arm(self):
        v=fixture();v['issued_spans'][0]['width_mask']=4
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_unmapped(self):
        v=fixture();v['issued_spans'][0]['address']=m.CHILD-2
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_tail_not_code(self):
        v=fixture();v['issued_spans'][0]['address']=m.CHILD+m.LABEL_SIZE
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_missing_guards(self):
        v=fixture();v['host_write_guards']=6
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_host_mutation(self):
        v=fixture();v['host_writes_after_entry']=1
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_unbound_byte(self):
        v=fixture();v['all_issued_child_bytes_equal_source']=False
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_unobserved_transfer(self):
        v=fixture();v['natural_link_transfer_proven']=True
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_bool_count(self):
        v=fixture();v['native_processes']=True
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_budget(self):
        v=fixture();v['steps']=1000001
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_empty(self):
        v=fixture();v['issued_spans']=[]
        with self.assertRaises(ValueError):m.validate_native(v)
    def test_unknown_span_key(self):
        v=fixture();v['issued_spans'][0]['inferred']=True
        with self.assertRaises(ValueError):m.validate_native(v)


if __name__=='__main__':unittest.main()
