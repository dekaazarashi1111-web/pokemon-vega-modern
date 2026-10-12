"""共有fixtureの通常A入力だけ追加し、既存55unitとnative2caseは継承。"""
import json
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_exp_share_input as i
from tests.test_pr16_exp_share_route import example
from tests.test_pr16_exp_evolution_sync import PP,ROWS


def sample():
    value,err,case=example()
    for key in ('boundary','encounter','pp_spent','level_frame','reserve_level_frame','returned','evolution_begin','evolution_update'):value[key]*=10
    err=re.sub(rb'frame=(\d+)',lambda m:b'frame='+str(int(m[1])*10).encode(),err)
    return value,err+b'ESHARE_FIELD_KEY frame=120 key=1 callback=08055e75 lock=1\n',case


def accept(value,err,case):return i.validate(json.dumps(value).encode(),err,case,ROWS,PP)


class FieldInputTests(unittest.TestCase):
    def test_existing_native_and_save_contract_is_preserved(self):
        result=accept(*sample());self.assertEqual(result['party_preserved_bytes'],200);self.assertEqual(result['ordinary_field_event_pulses'],1)
    def test_key_callback_lock_and_time_are_strict(self):
        value,err,case=sample()
        for old,new in ((b'key=1 callback',b'key=2 callback'),(b'callback=08055e75',b'callback=08055e74'),(b'lock=1',b'lock=0'),(b'frame=120 key',b'frame=90 key'),(b'frame=120 key',b'frame=210 key'),(b'frame=120 key',b'frame=121 key')):
            with self.subTest(new=new),self.assertRaises(ValueError):accept(value,err.replace(old,new),case)
    def test_missing_duplicate_unbounded_inputs_rejected(self):
        value,err,case=sample();line=err.splitlines(keepends=True)[-1]
        for bad in (err.replace(line,b''),err+line,err+line*120):
            with self.subTest(size=len(bad)),self.assertRaises(ValueError):accept(value,bad,case)
    def test_only_ordinary_keys_are_added_before_native_encounter(self):
        for token in ('write8(','write16(','write32(','call_preserving(','create_mon(','p02s_set_data('):self.assertNotIn(token,i.PATCH)
        for token in ('e_field_keys<120','lb_frames%30==0','P02S_FIELD_LOCK','P02S_CB2_FIELD','!e_field_encounter','c->setKeys(c,QOL_KEY_A)'):self.assertIn(token,i.PATCH)
        derived=i.derived_source();self.assertEqual(derived,(i.e.ROOT/i.C).read_text());self.assertEqual(derived.count('a_guard(c);'),3)
        source=(i.e.ROOT/i.s.C).read_text();self.assertEqual(derived.replace(i.PATCH,i.ANCHOR),source)
    def test_old_55_unit_sources_and_processes_are_unchanged(self):
        value=i.original_units();self.assertEqual(value['new_unit_tests'],4);self.assertEqual(value['native_processes'],1)
    def test_encounter_disables_field_scheduler(self):
        self.assertLess(i.PATCH.index('e_field_encounter=true'),i.PATCH.index('if(!e_field_encounter'))
        self.assertEqual(i.PATCH.count('c->setKeys'),1)


if __name__=='__main__':unittest.main()
