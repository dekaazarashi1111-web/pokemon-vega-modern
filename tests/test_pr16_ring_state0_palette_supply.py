"""新しい32byte供給境界を、合成dataと独立write oracleで検査する。"""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_ring_state0_palette_supply as t

DATA=bytes(range(32))

class State0PaletteSupplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c=t.bios.context();cls.a=t.s.load(t.PRIOR)['analysis']
        cls.selector=t.s.load(t.selector.REPORT)['analysis']

    def reject(self,mutate):
        a=copy.deepcopy(self.a);mutate(a)
        with self.assertRaises(ValueError):t.plan(self.c,a)

    def test_exact_plan(self):
        self.assertEqual(t.plan(self.c,self.a),{'source':0x0843fa24,'length':32,
            'destinations':[0x0203730c,0x0203770c],'unit':2,'count':16})

    def test_changed_candidate_rejected(self):self.reject(lambda a:a['candidate'].update(size=1))
    def test_missing_state1_proof_rejected(self):self.reject(lambda a:a.update(task_state1_to2_proven=False))
    def test_overclaimed_state01_rejected(self):self.reject(lambda a:a.update(task_state01_complete_proven=True))
    def test_overclaimed_ring_rejected(self):self.reject(lambda a:a.update(ring_acquisition_accepted=True))
    def test_overclaimed_bios_rejected(self):self.reject(lambda a:a.update(bios_execution_observed=True))
    def test_overclaimed_release_rejected(self):self.reject(lambda a:a.update(release_ready=True))
    def test_wrong_fault_rejected(self):self.reject(lambda a:a['state0_remaining_read']['read_fault'].update(address=t.SOURCE+2))
    def test_wrong_count_rejected(self):self.reject(lambda a:a['state0_remaining_read']['bios_events'][2].update(source_bytes=30))
    def test_false_completed_rejected(self):self.reject(lambda a:a['state0_remaining_read']['bios_events'][2].update(completed=True))
    def test_partial_prefix_rejected(self):self.reject(lambda a:a['state0_remaining_read']['bios_events'][0].update(completed=False))
    def test_nonzero_actual_rejected(self):self.reject(lambda a:a['state0_remaining_read']['bios_events'][2].update(actually_written_units=1))

    def test_data_row_identity(self):
        row=t.data_row(DATA)
        self.assertEqual(row['identity'],t.s.identity(DATA));self.assertEqual(row['hex'],DATA.hex())
        self.assertEqual(row['candidate'],t.s.CANDIDATE)

    def test_data_row_width_and_type(self):
        for data in(b'',DATA[:-1],DATA+b'\0',bytearray(DATA)):
            with self.subTest(size=len(data)):
                with self.assertRaises(ValueError):t.data_row(data)

    def test_independent_pair_order_and_endian(self):
        rows=t.pair_writes(DATA)
        self.assertEqual(len(rows),32)
        self.assertEqual(rows[0],(t.DEST1,2,0x0100));self.assertEqual(rows[15],(t.DEST1+30,2,0x1f1e))
        self.assertEqual(rows[16],(t.DEST2,2,0x0100));self.assertEqual(rows[31],(t.DEST2+30,2,0x1f1e))

    def test_copy_matrix(self):
        rows=t.copy_contracts(DATA)
        self.assertEqual(len(rows),99);self.assertEqual(sum(r['returned']for r in rows),1)
        self.assertEqual(rows[0]['completed_copies'],2);self.assertTrue(rows[0]['return_sp_r4_r11_proven'])

    def test_odd_short_source_preserves_partial_writes(self):
        rows={r['case']:r for r in t.copy_contracts(DATA)}
        for n in range(32):
            r=rows[f'source_length-{n}'];self.assertEqual(r['writes'],n//2)
            self.assertEqual(r['read_fault'],{'address':t.SOURCE+n//2*2,'size':2,'site':t.w.BIOS_COPY})

    def test_short_first_destination(self):
        for r in t.copy_contracts(DATA):
            if r['case'].startswith('first-'):
                n=int(r['case'][6:]);self.assertEqual(r['writes'],n//2);self.assertEqual(r['completed_copies'],0)

    def test_short_second_keeps_first_copy(self):
        for r in t.copy_contracts(DATA):
            if r['case'].startswith('second-'):
                n=int(r['case'][7:]);self.assertEqual(r['writes'],16+n//2);self.assertEqual(r['completed_copies'],1)

    def test_readonly_is_not_success(self):
        rows=t.copy_contracts(DATA)[-2:]
        self.assertEqual([r['writes']for r in rows],[0,16]);self.assertTrue(all(not r['returned']for r in rows))

    def test_invalid_lengths_rejected(self):
        for length in(-1,33,True):
            with self.assertRaises(ValueError):t.copy_case(self.c,DATA,'bad',first=length)

    def test_invalid_readonly_rejected(self):
        with self.assertRaises(ValueError):t.copy_case(self.c,DATA,'bad',readonly=(3,))

    def test_task_suffix_matrix(self):
        rows=t.task_contracts(self.c,self.selector,bytes(range(20)),DATA)
        self.assertEqual(len(rows),21);self.assertEqual({r['task_id']for r in rows},set(range(16)))
        self.assertTrue(all(r['completed_bios_copies']==4 and r['task_state_after']==0 for r in rows))
        self.assertTrue(all(r['read_fault']=={'address':t.NEXT_POINTER,'size':4,'site':t.NEXT_PC}for r in rows))
        self.assertFalse(rows[-1]['queue_reservations']);self.assertEqual(rows[-1]['writes'],54)

    def test_scope_and_parent_model_unchanged(self):
        self.assertEqual(t.EXTRA_CODE,());self.assertEqual(t.MIN_TESTS,24)
        self.assertTrue(all(not r['bios_execution_observed']and not r['native_observation']for r in t.copy_contracts(DATA)))

    def test_invalid_task_and_mode_rejected(self):
        for opts in(dict(task_id=16),dict(task_id=-1),dict(mode=2)):
            with self.assertRaises(ValueError):t.task_case(self.c,self.selector,bytes(range(20)),DATA,'bad',**opts)

if __name__=='__main__':unittest.main()
