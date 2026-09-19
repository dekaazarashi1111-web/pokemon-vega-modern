from pathlib import Path
import inspect
import json
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_rental_drought as t

class RentalDroughtTests(unittest.TestCase):
    def test_ready_six_rental_guard_and_existing_delegates(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/'rental-drought'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/t.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            out=subprocess.check_output([str(exe)],text=True)
            self.assertIn('ready6-field-boundary PASS',out)
            self.assertIn('combinations=393472',out)
    def test_original_readonly_boundary_is_exact(self):
        r=t.diagnose((ROOT/t.RAW).read_bytes())
        self.assertEqual((r['wins'],r['bp'],r['events']),(21,63,100))
        self.assertEqual((r['weather_state'],r['cursor'],r['script']),(2,[1,1],0x09FF4CB5))
        self.assertEqual((r['owner_phase'],r['active_party_count'],r['saved_party_count']),(1,6,1))
    def test_changed_boundary_is_rejected(self):
        raw=(ROOT/t.RAW).read_bytes()
        for before,after in [(b'\"script\":167726261',b'\"script\":0'),(b'\"phase\":1',b'\"phase\":2'),(b'\"saved_count\":1',b'\"saved_count\":0')]:
            self.assertIn(before,raw)
            with self.subTest(before=before),self.assertRaises(ValueError):t.diagnose(raw.replace(before,after,1))
    def test_runtime_repair_is_exact_and_read_only_owner_predicate(self):
        source=(ROOT/t.SOURCE).read_text()
        if 'CircusDroughtInitializeRentalBoundary' not in source:source=t.repair(source)
        for token in ('circus_drought_rental.h','CircusStreakValid(OWNER)','OWNER->phase == CIRCUS_READY','CircusDroughtInitializeRentalBoundary'):
            self.assertIn(token,source)
        for token in ('CircusStreakBegin(', 'CircusStreakArm(', 'CircusStreakSettle(', 'CircusStreakEnd('):self.assertNotIn(token,source)
        with self.assertRaises(ValueError):t.repair(source)
    def test_header_does_not_widen_phase2_or_win_predicates(self):
        text=(ROOT/t.HEADER).read_text()
        self.assertIn('c->armed == 0u',text);self.assertIn('owner_ready == 1u',text)
        self.assertIn('active_count == 6u',text);self.assertIn('c->script == 0x09FF4CB5u',text)
        self.assertIn('CircusDroughtInitializeSelection(c, active_count',text)
        self.assertNotRegex(text,r'(?:w\[[^\]]+\]|c->\w+)\s*=(?!=)')
    def test_watcher_is_bounded_and_has_no_host_writes(self):
        text=(ROOT/t.WATCH).read_text()
        self.assertIn('rd_elapsed==600U',text);self.assertIn('sc_events>100U',text)
        self.assertEqual(text.count('b_frame(c,keys);'),1)
        for token in ('write8(', 'write16(', 'write32(', 'writeRegister(', 'setKeys('):self.assertNotIn(token,text)
    def test_build_relinks_only_new_bridge_not_old_runtime(self):
        source=inspect.getsource(t.reconstruct)
        self.assertIn('for i in (1,2)',source);self.assertIn('builds[0]==builds[1]',source)
        self.assertIn("old['entries']['CircusStreakRuntimeArmed']",source)
        self.assertNotIn('compile_runtime(',source)
        self.assertIn('independent_old_arm_links_replayed=0',source)
    def test_first_hundred_are_reused_only_inside_continuation(self):
        source=inspect.getsource(t.native)
        self.assertIn('same_without_frame',source);self.assertIn('events[:100]',source)
        self.assertNotIn('prior.native()',source);self.assertNotIn('s.native()',source)
    def test_prepare_checks_legacy_contract_before_candidate_contract(self):
        source=inspect.getsource(t.prepare)
        legacy="legacy_host_tests=r.tests(['test_pr16_circus_rental_boundary.py'])"
        repair="(ROOT/SOURCE).write_text(repair(before.decode()))"
        candidate="host_tests=r.tests([Path(TEST).name,'test_pr16_circus_selection.py','test_pr16_circus_drought.py'])"
        self.assertLess(source.index(legacy),source.index(repair))
        self.assertLess(source.index(repair),source.index(candidate))
        self.assertNotIn("'test_pr16_circus_rental_boundary.py']),\n        accepted_prefix",source)
    def test_witness_parser_requires_enter_and_cross(self):
        rows=[dict(label='entered',elapsed=0,frame=1,events=100,keys=0,current=21,phase=1,count=6,saved_count=1,marker=1,snapshot=1,callback2=0x08055E75,script=0x09FF4CB5,newbs=0,outcome=1,state=2,complete=0,index=1,offset=1),
              dict(label='event-crossed',elapsed=5,frame=6,events=101,keys=0,current=21,phase=2,count=3,saved_count=1,marker=2,snapshot=1,callback2=0x08055E75,script=0x09FF4CEB,newbs=0,outcome=0,state=5,complete=1,index=32,offset=32)]
        raw=b''.join(b'CIRCUS_RENTAL_DROUGHT '+json.dumps(r).encode()+b'\n' for r in rows)
        observed=t.witness(raw);self.assertTrue(observed['crossed']);self.assertFalse(observed['direct'])
        direct=dict(rows[-1],label='event-crossed-direct',elapsed=1)
        observed=t.witness(b'CIRCUS_RENTAL_DROUGHT '+json.dumps(direct).encode()+b'\n')
        self.assertTrue(observed['crossed']);self.assertTrue(observed['direct']);self.assertIsNone(observed['entered'])
        with self.assertRaises(ValueError):t.witness(raw.splitlines()[0]+b'\n')
    def test_configure_is_reentrant_and_scoped(self):
        for _ in range(2):
            d,b=t.configure();self.assertEqual(d.SELF,t.SELF);self.assertEqual(b.SELF,t.SELF)
            self.assertTrue(set(t.NEW)<=set(d.FILES));self.assertEqual(len(d.FILES),len(set(d.FILES)))

if __name__=='__main__':unittest.main()
