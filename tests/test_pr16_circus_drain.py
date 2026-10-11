"""実毒/PP/低HPの限定入力。原本を合成の勝利として扱わない。"""
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('drain',ROOT/'scripts/pr16_circus_drain.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
PREFIX='evidence/pr16_circus_three_win/35420622910/'
REC='evidence/pr16_circus_interruption/35420622910/circus-interrupt-second-battle.stderr'
class DrainTests(unittest.TestCase):
    def test_c_selection_contract(self):
        code=r'''
#define CIRCUS_DRAIN_HOST_TEST
#include "mgba_pr16_circus_drain.h"
#include <assert.h>
#include <stdio.h>
int main(void){unsigned checks=0;
for(unsigned type=0;type<25;++type)for(unsigned slot=0;slot<4;++slot){
 assert(cd_choose(2,73,slot,type,0x380,81,171)==(type==12?slot:2));++checks;}
for(unsigned move=0;move<=1062;++move){assert(cd_choose(2,move,0,12,0x80,81,171)==(move==73?0:2));++checks;}
assert(cd_choose(2,73,0,12,0,81,171)==2);++checks;
assert(cd_choose(2,73,0,12,0x10,81,171)==2);++checks;
assert(cd_choose(2,73,4,12,0x80,81,171)==2);++checks;
assert(cd_choose(2,73,0,12,0x80,86,171)==2);++checks;
assert(cd_choose(2,73,0,12,0x80,85,171)==0);++checks;
assert(cd_choose(2,73,0,12,0x80,0,171)==2);++checks;
assert(cd_choose(2,73,0,12,0x80,1,0)==2);++checks;
printf("PASS_CIRCUS_DRAIN checks=%u\n",checks);return 0;}
'''
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'fixture.c';source.write_text(code);exe=Path(folder)/'test'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-I'+str(ROOT/'tools'),str(source),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS_CIRCUS_DRAIN checks=1170',result.stdout)
    def test_exact_controller_adaptation(self):
        source='static unsigned mt_move_slot(struct mCore *c);\nvoid test(void){slot=mt_move_slot(c);}'
        changed=m.adapt(source);self.assertEqual(changed.replace('cd_move_slot','mt_move_slot'),source)
        for bad in ('',source+source,changed):
            with self.assertRaises(ValueError):m.adapt(bad)
    def test_first_intervention_after_menu_repair_and_two_wins(self):
        overrides=[]
        for line in (ROOT/(PREFIX+'circus-streak-batch-save.stderr')).read_text().splitlines():
            if not line.startswith('CIRCUS_SUSTAIN '):continue
            d=dict(re.findall(r'(\w+)=(\S+)',line));data=bytes.fromhex(d['battle']);own=data[:88]
            moves=struct.unpack_from('<4H',own,12);pp=own[0x24:0x28];hp,maxhp=map(int,d['enemy_hp'].split('/'))
            if int(d['frame'])>=41181 and d['move']=='73' and own[0x21]==12 and int(d['status1'],16)&0x88 and 0<hp*2<=maxhp:
                if any(move==202 and pp[i] for i,move in enumerate(moves)):overrides.append(int(d['frame']))
        self.assertEqual(overrides,[48229])
    def test_controller_input_read_only(self):
        text=(ROOT/m.HEADER).read_text()
        for word in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', 'loadState(', 'saveState(', 'setKeys('):self.assertNotIn(word,text)
        self.assertIn('selected=mt_move_slot(c)',text);self.assertIn('!=2U)return selected',text)
        self.assertIn('mt_memory.last_pp',text)
    def test_recovery_raw_not_a_pass(self):
        value=m.recovery_diagnosis((ROOT/REC).read_bytes())
        self.assertFalse(value['accepted']);self.assertEqual(value['terminal_best'],0)
        self.assertEqual(value['standard_save_counter_chain'],[2,3,4])
    def test_recovery_changed_owner_or_counter_rejected(self):
        raw=(ROOT/REC).read_bytes()
        for bad in (raw.replace(b'"sequence":21',b'"sequence":20'),
                    raw.replace(b'"save_counter":3',b'"save_counter":2'),raw.replace(b'"frame_boundary":25805',b'"frame_boundary":25806')):
            with self.assertRaises(ValueError):m.recovery_diagnosis(bad)
if __name__=='__main__':unittest.main()
