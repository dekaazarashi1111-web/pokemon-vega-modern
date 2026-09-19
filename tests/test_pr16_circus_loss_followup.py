"""実観測のbattle-active markerをsnapshotと混同しない回帰契約。"""
import importlib.util
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('loss_followup',ROOT/'scripts/pr16_circus_loss_followup.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

class LossFollowupTests(unittest.TestCase):
    def sample(self):
        a=dict(label='outcome',frame=17060,outcome=2,marker=2,snapshot=1,script=0x09ff4d16,flags=32,newbs=1,owner='same')
        b=dict(a,label='timeout',frame=93902,newbs=0,callback2=0x08055e75)
        return a,b

    def encode(self,events):
        return ''.join('CIRCUS_STREAK '+json.dumps(e)+'\n' for e in events).encode()

    def test_actual_loss_is_diagnostic_not_acceptance(self):
        v=m.failed_witness(self.encode(self.sample()))
        self.assertEqual(v['active_marker'],2);self.assertEqual(v['original_conclusion'],'failure')
        self.assertIs(v['native_acceptance'],False)

    def test_snapshot_marker_cannot_replace_active_battle(self):
        for key,value in [('marker',1),('snapshot',0),('outcome',1),('script',0x092cf669),('newbs',0),('flags',0)]:
            a,b=self.sample();a[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):m.failed_witness(self.encode((a,b)))

    def test_missing_duplicate_and_changed_owner_rejected(self):
        a,b=self.sample()
        for events in ((a,), (a,a,b), (a,dict(b,owner='changed'))):
            with self.assertRaises(ValueError):m.failed_witness(self.encode(events))

    def test_repair_uses_authoritative_enum_and_is_not_repeatable(self):
        h='#include <stdint.h>\nreturn marker == 1u;\n'
        out=m.repair_text(m.HEADER,h)
        self.assertIn('marker == VEGA_FACTORY_BATTLE_ACTIVE',out)
        self.assertIn('../save_migration/save_migration.h',out)
        with self.assertRaises(ValueError):m.repair_text(m.HEADER,out)

    def test_all_five_markers_are_covered(self):
        text='for(unsigned marker=0;marker<3;++marker)\nexpected=marker==1;'
        out=m.repair_text(m.FIXTURE,text)
        self.assertIn('marker<5',out);self.assertIn('marker==VEGA_FACTORY_BATTLE_ACTIVE',out)
        self.assertEqual(3*3*5*3*8*256*8,2211840)

    def test_unknown_paths_and_ambiguous_anchors_rejected(self):
        with self.assertRaises(ValueError):m.repair_text('unrelated.h','marker == 1u')
        with self.assertRaises(ValueError):m.repair_text(m.HEADER,'#include <stdint.h>\nmarker == 1u; marker == 1u;')

if __name__=='__main__':unittest.main()
