"""低HPで無効技を選ぶ原本回帰。過去の2勝をnative再実行せず照合。"""
import importlib.util
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('effective',ROOT/'scripts/pr16_circus_effective.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class EffectiveTests(unittest.TestCase):
    def test_host_policy_112_conditions(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'policy'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/m.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS_CIRCUS_EFFECTIVE_POLICY checks=112',result.stdout)
    def test_only_selector_changes(self):
        source='static void test(void){slot=wx_move_slot(c);br_trace(c,"turn-start");}'
        changed=m.adapt_policy(source)
        self.assertTrue(changed.startswith('static unsigned ef_move_slot(struct mCore *c);'))
        self.assertEqual(changed.split('\n',1)[1].replace('ef_move_slot','wx_move_slot'),source)
    def test_anchor_drift_rejected(self):
        for text in ('','slot=wx_move_slot(c);'*2,'slot=wx_move_slot(c); ef_move_slot'):
            with self.assertRaises(ValueError):m.adapt_policy(text)
    def test_acceptance_or_same_policy_never_replayed(self):
        old=dict(classification='CIRCUS_THREE_WIN_DIAGNOSTIC_OPEN',recording_run=42)
        run=dict(id=42,status='completed',conclusion='failure')
        m.prior_allowed(old,run)
        for changes in ({'classification':'CIRCUS_THREE_WIN_CONTINUATIONS_9BP_SAVE_CONTINUE_VERIFIED'},
                        {'input_policy_id':m.POLICY},{'recording_run':41}):
            with self.assertRaises(ValueError):m.prior_allowed(dict(old,**changes),run)
        for changes in ({'status':'in_progress'},{'conclusion':'success'},{'conclusion':'action_required'}):
            with self.assertRaises(ValueError):m.prior_allowed(old,dict(run,**changes))
    def test_read_only_and_preserves_existing_policy(self):
        text=(ROOT/m.HEADER).read_text()
        for bad in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', 'SC_OWNER', '0x03000EB8', 'wx_team'):
            self.assertNotIn(bad,text)
        self.assertIn('selected=su_move_slot(c)',text)
        self.assertIn('BATTLE_CORE_MON_STATUS1',text)
        self.assertIn('!wx_effect(type,t1)',text)
    def test_original_trace_first_intervention_after_two_wins(self):
        name='evidence/pr16_circus_three_win/35418010512/circus-streak-batch-save.stderr'
        last=None;attempts=0;scores={};overrides=[]
        for line in (ROOT/name).read_text().splitlines():
            if line.startswith('BP_WIN_MOVE '):
                d=dict(re.findall(r'(\w+)=(\S+)',line))
                scores[(int(d['frame']),int(d['slot']))]=int(d['score'])
            if not line.startswith('CIRCUS_SUSTAIN '):continue
            d=dict(re.findall(r'(\w+)=(\S+)',line));raw=bytes.fromhex(d['battle']);own=raw[:len(raw)//2]
            key=(d['player'],d['enemy'])
            if key!=last:attempts=0;last=key
            if int(d['move'])==92:attempts+=1
            types=[int(x) for x in d['types'].split(',')]
            moves=struct.unpack_from('<4H',own,12);pp=own[0x24:0x28]
            toxic=next((i for i in range(4) if moves[i]==92 and pp[i]),4)
            if scores.get((int(d['frame']),int(d['slot'])),1)==0 and toxic<4 and attempts<2 \
                and int(d['status1'],16)==0 and all(t not in (3,8) for t in types):
                overrides.append(int(d['frame']))
        self.assertEqual(overrides,[50972,51748,52354,53413,54263,54934,56055])
if __name__=='__main__':unittest.main()
