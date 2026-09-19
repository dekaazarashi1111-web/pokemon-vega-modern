"""空loader修復のscope/書込2byte/独立build/実native完了の回帰。"""
import copy
import inspect
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_drought as t
class DroughtTests(unittest.TestCase):
    def test_strict_native_header_fixture_527104_combinations(self):
        with tempfile.TemporaryDirectory() as d:
            exe=Path(d)/'test'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/t.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('combinations=527104',result.stdout)
    def test_actual_cpu_diagnosis(self):
        rows=json.loads((ROOT/t.ROWS).read_bytes());r=t.diagnosis(rows)
        self.assertEqual(r['weather'],12);self.assertEqual(r['state'],2)
    def test_changed_cpu_source_rejected(self):
        original=json.loads((ROOT/t.ROWS).read_bytes())
        for key,value in [('weather_id',11),('weather_init',0x0807AD39),('elapsed',0),('weather','00'*64)]:
            rows=copy.deepcopy(original);rows[-1][key]=value
            with self.assertRaises(ValueError):t.diagnosis(rows)
    def fixture_rom(self):
        data=bytearray(t.TABLE+4)
        for at,text in ((0x7A350,'70470000'),(t.TABLE,'09ad0708'),(0x389940,'687e0302'),(0x7AD08,'10b5fff7e3ff'),(0x7AD90,'fff7e0fa')):data[at:at+len(bytes.fromhex(text))]=bytes.fromhex(text)
        return data
    def test_preimage_checks_own_hash_and_all_five_native_anchors(self):
        raw=self.fixture_rom()
        with self.assertRaises(ValueError):t.verify_preimage(raw)
        with patch.object(t,'identity',return_value=t.PARENT):
            self.assertEqual(len(t.verify_preimage(raw)),5)
            for at in (0x7A350,t.TABLE,0x389940,0x7AD08,0x7AD90):
                changed=bytearray(raw);changed[at]^=1
                with self.assertRaises(ValueError):t.verify_preimage(changed)
    def test_runtime_uses_existing_native_steps_and_valid_owner(self):
        source=(ROOT/t.SOURCE).read_text();header=(ROOT/t.HEADER).read_text()
        for token in ('VegaSaveValidate(', 'CIRCUS_DROUGHT_ARMED','0x0807AD09u','0x0807ACD5u','0x0807AD39u'):self.assertIn(token,source)
        self.assertIn('w[0x74D] = 32u;',header);self.assertIn('w[0x74E] = 32u;',header)
        self.assertNotRegex(source+header,r'w\[0x6(?:D2|CC)\]\s*=(?!=)')
        for token in ('SaveFinalize(', 'RuntimeRecord(', 'RestoreParty(', 'DestroyTask('):self.assertNotIn(token,source+header)
    def test_changed_candidate_has_two_independent_links_and_full_rollback(self):
        source=inspect.getsource(t.reconstruct)
        self.assertIn('for i in (1,2)',source)
        self.assertIn('builds[0]==builds[1]',source)
        self.assertIn('bounded_patch(raw,patches)',source)
        self.assertIn("for row in allocation['allocations']",source)
        self.assertNotIn('c.native()',source)
    def witness(self):return dict(frame=284900,state=5,complete=1,index=32,offset=32,brightness=6,current=16,outcome=1,script=0x09FF4D77)
    def test_native_witness_not_injected_completion(self):
        raw=b'CIRCUS_DROUGHT_RETURN '+json.dumps(self.witness()).encode()
        self.assertEqual(t.return_witness(raw),self.witness())
        for key,value in [('state',2),('complete',0),('index',1),('offset',1),('outcome',2),('current',17),('brightness',99)]:
            row=self.witness();row[key]=value
            with self.assertRaises(ValueError):t.return_witness(b'CIRCUS_DROUGHT_RETURN '+json.dumps(row).encode())
        with self.assertRaises(ValueError):t.return_witness(raw+b'\n'+raw)
    def test_watch_is_input_unchanged_readonly(self):
        source=(ROOT/t.WATCH).read_text()
        self.assertEqual(source.count('b_frame(c,keys);'),1)
        for token in ('write8(', 'write16(', 'write32(', 'writeRegister(', 'loadState(', 'call_preserving(', '#define b_frame'):self.assertNotIn(token,source)
    def test_strict_watcher_host_compilation(self):
        source=r'''#include <stdint.h>
#include <stdio.h>
struct mCore {int unused;};
enum {BATTLE_CORE_BATTLE_OUTCOME=1,BATTLE_CORE_MAIN_CALLBACK2=2,SP_SCRIPT_PTR=3};
static unsigned b_frames;
static unsigned read8(struct mCore*c,uint32_t a){(void)c;(void)a;return 0;}
static unsigned read16(struct mCore*c,uint32_t a){(void)c;(void)a;return 0;}
static unsigned read32(struct mCore*c,uint32_t a){(void)c;(void)a;return 0;}
static void b_frame(struct mCore*c,uint32_t k){(void)c;(void)k;++b_frames;}
#include "WATCH"
int main(void){struct mCore c={0};wr_frame(&c,0);return b_frames!=1 || dw_seen!=0;}
'''.replace('WATCH',str(ROOT/t.WATCH))
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.c').write_text(source)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            subprocess.run([str(p/'test')],check=True,capture_output=True)
    def test_unchanged_seventeen_outcomes_required(self):
        old=(ROOT/t.RAW).read_bytes();events=t.probe.parse(old)
        with patch.object(t.previous,'verify_prefix'):
            t.verify_prefix(events,b'')
            changed=copy.deepcopy(events);changed[78]['outcome']=2
            with self.assertRaises(ValueError):t.verify_prefix(changed,b'')
if __name__=='__main__':unittest.main()
