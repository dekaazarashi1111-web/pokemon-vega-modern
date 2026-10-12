"""PPフィードバック・通常交代証拠・native前setup失敗の限定修復。"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('matchup',ROOT/'scripts/pr16_circus_matchup.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def rows():
    return [dict(label='begin',frame=44000,**{'from':1},target=0,pid=123,ot=456,species=2,type=12),
            dict(label='done',frame=45500,**{'from':1},target=0,pid=123,ot=456,species=2,type=12)]
def raw(value,start=41181,end=55000):
    def native(label,frame):return ('CIRCUS_STREAK '+json.dumps(dict(label=label,frame=frame,battle=2))+'\n').encode()
    return native('action',start)+b''.join(('CIRCUS_MATCHUP '+json.dumps(r)+'\n').encode() for r in value)+native('outcome',end)

class MatchupTests(unittest.TestCase):
    def test_host_policy_100_conditions(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'policy'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/m.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS_CIRCUS_MATCHUP_POLICY checks=100',result.stdout)
    def test_one_and_multiple_switch_proofs(self):
        self.assertEqual(m.events(raw(rows()))['voluntary_matchup_switches'],1)
        extra=deepcopy(rows())
        for row in extra:row['frame']+=3000
        self.assertEqual(m.events(raw(rows()+extra))['voluntary_matchup_switches'],2)
    def test_identity_and_types(self):
        for key,value in [('pid',9),('ot',7),('target',True),('type',11),('species',0),('target',3),('extra',0),('frame',1)]:
            mutated=rows();mutated[1][key]=value
            with self.assertRaises(ValueError):m.events(raw(mutated))
    def test_exactly_paired_and_bounded(self):
        for value in ([],rows()[:1],list(reversed(rows())),rows()+rows(),rows()*7):
            with self.assertRaises(ValueError):m.events(raw(value))
    def test_third_battle_only(self):
        for start,end in ((45000,55000),(41181,45000)):
            with self.assertRaises(ValueError):m.events(raw(rows(),start,end))
    def test_duplicate_json_fields_rejected(self):
        blob=raw(rows()).replace(b'"pid": 123',b'"pid": 123, "pid": 124',1)
        with self.assertRaises(ValueError):m.events(blob)
    def test_only_selector_changes(self):
        source='static void test(void){slot=wx_move_slot(c);br_trace(c,"turn-start");}'
        changed=m.adapt_policy(source)
        self.assertEqual(changed.split('\n',1)[1].replace('mt_move_slot','wx_move_slot'),source)
        for bad in ('',source+source,changed):
            with self.assertRaises(ValueError):m.adapt_policy(bad)
    def test_read_only_and_no_retroactive_win_injection(self):
        text=(ROOT/m.HEADER).read_text()
        for bad in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', '0x03000EB8'):
            self.assertNotIn(bad,text)
        self.assertIn('if(streak!=2U)return selected;',text)
        self.assertIn('n_cursor(c,2U)',text)
        self.assertIn('read32(c,mon+0x48U)==pid',text)
        self.assertIn('mt_memory.last_pp',text)
    def test_setup_repair_is_bounded_and_rejects_reapplication(self):
        source="TASK='USER-20260919-CIRCUS-INTERRUPTION'\ndef configure():\n    return b\n\n\ndef checkpoint():\n    pass\n"
        changed=m.repair_interruption_text(source)
        self.assertIn('b.OUT.mkdir(parents=True,exist_ok=True)',changed)
        self.assertEqual(changed.replace('    b.OUT.mkdir(parents=True,exist_ok=True)\n','').replace(m.INTERRUPTION_TASK,'USER-20260919-CIRCUS-INTERRUPTION'),source)
        for bad in ('',source+source,changed):
            with self.assertRaises(ValueError):m.repair_interruption_text(bad)
    def test_setup_repair_physically_creates_parent_before_pipeline(self):
        source="TASK='USER-20260919-CIRCUS-INTERRUPTION'\ndef configure():\n    return b\n\n\ndef checkpoint():\n    pass\n"
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)/'new/setup';b=SimpleNamespace(OUT=target)
            ns={'b':b};exec(source,ns);ns['configure']();self.assertFalse(target.exists())
            ns={'b':b};exec(m.repair_interruption_text(source),ns);ns['configure']();self.assertTrue(target.is_dir())
            (target/'toolchain.log').write_text('host test only\n')
    def test_actual_source_repair_preserves_native(self):
        source=(ROOT/m.INTERRUPTION).read_text()
        if "TASK='"+m.INTERRUPTION_TASK+"'" in source:
            source=source.replace("TASK='"+m.INTERRUPTION_TASK+"'","TASK='USER-20260919-CIRCUS-INTERRUPTION'").replace('    b.OUT.mkdir(parents=True,exist_ok=True)\n','')
        changed=m.repair_interruption_text(source)
        for name in ('native','finish','pack'):
            before=source.split('\ndef '+name+'():\n',1)[1].split('\n\ndef ',1)[0]
            after=changed.split('\ndef '+name+'():\n',1)[1].split('\n\ndef ',1)[0]
            self.assertEqual(before,after)
if __name__=='__main__':unittest.main()
