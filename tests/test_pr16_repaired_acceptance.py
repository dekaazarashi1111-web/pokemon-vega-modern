"""Projection/negative evidence tests only; native acceptance is Actions output."""
from pathlib import Path
import json
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_repaired_acceptance as m

class RepairedAcceptance(unittest.TestCase):
    def test_all_parent_sources_are_pinned_and_only_explicit_paths_are_projected(self):
        for name,(sha,count) in m.PINS.items():
            before=m.layer.source.checked(ROOT/'scripts'/f'{name}.py',sha).decode()
            after=m.substituted_source(name)
            self.assertEqual(before.count(m.OLD),count)
            self.assertEqual(after.count(m.ROM),count)
            self.assertNotIn(m.OLD,after)
            if name!='pr16_integrated_domains':self.assertEqual(after.replace(m.ROM,m.OLD),before)
    def test_separate_native_module_never_mutates_parent_identity(self):
        import pr16_integrated_native as old
        new=m.native_module()
        self.assertEqual(old.ROM_SHA,m.repair.PARENT_SHA)
        self.assertEqual(new.ROM_SHA,m.ROM_SHA)
        self.assertNotEqual(old.ROM_SHA,new.ROM_SHA)
        self.assertEqual(new.SPECS,old.SPECS)
    def test_evolution_uses_same_required_move_and_parent_success_is_rejected(self):
        native=m.native_module();child=m.load('pr16_native_learning');child.native=native
        import pr16_native_learning as parent
        self.assertEqual(child.CASES,parent.CASES)
        case=child.CASES[-1]
        self.assertEqual(child.expected(case)['moves_after'],[33,81,366,0])
        value=child.expected(case);value['witness']={k:0 for k in child.WITNESS}
        value['witness'].update(bag_party=10,level=20,evo_begin=30,evo_update=40,field=1000)
        process={'schema_version':1,'returncode':0,'timed_out':False,'spawn_error':None}
        child.validate(json.dumps(value).encode(),case,process)
        value['rom_sha256']=m.repair.PARENT_SHA
        with self.assertRaises(ValueError):child.validate(json.dumps(value).encode(),case,process)
    def test_p06_path_projection_retains_the_immutable_native_phase_validator(self):
        child=m.load('pr16_integrated_p06');child.new=m.native_module()
        self.assertIn(m.ROM,child.NEW_CHILD)
        original=(ROOT/'scripts/run_modernization_p06_phase_e2e.py').read_text()
        projected=child.path_adapter(original)
        self.assertEqual(projected.replace(child.NEW_CHILD,child.OLD_CHILD),original)
    def test_domain_composition_is_explicit_and_old_domain_validators_are_unchanged(self):
        child=m.domain_module()
        self.assertEqual(child.ROM,m.ROM)
        self.assertEqual(child.REPORT,m.REPORT)
        self.assertEqual(len(child.DOMAINS),7)
        self.assertIs(child.compose_candidate,m.compose_candidate)
        self.assertEqual(child.native.ROM_SHA,m.ROM_SHA)
if __name__=='__main__':unittest.main()
