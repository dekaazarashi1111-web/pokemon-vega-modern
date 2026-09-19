"""WIN後の待機診断をnative受入に昇格させない限定検証。"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_win_return_trace as task

class WinReturnTraceTests(unittest.TestCase):
    def rows(self):
        raw=bytearray(640)
        for i,fn in ((2,0x0807951D),(6,0x0807D465)):
            raw[i*40:i*40+4]=fn.to_bytes(4,'little');raw[i*40+4]=1
        row=dict(frame=1000,callback2=0x08055E75,script=0x09FF4D77,ready=0,phase=2,newbs=0,marker=2,snapshot=1,
            waiting=30,count=3,outcome=1,current=16,best=16,types=0x04000000,tasks=raw.hex())
        other=copy.deepcopy(row);other['waiting']=180;other['frame']=1150
        return [row,other]
    def test_wait_is_diagnostic_not_save_or_streak_acceptance(self):
        value=task.waiting_witness(self.rows())
        self.assertEqual(value['real_winning_battles_observed'],17)
        self.assertEqual(value['settled_wins_before_stop'],16)
        self.assertTrue(value['diagnostic_complete'])
        for k in ('native_lifecycle_accepted','save_continue_verified','physical_admission_accepted','suppression_accepted','release_ready'):
            self.assertFalse(value[k])
    def test_wrong_waiter_callback_script_or_result_is_rejected(self):
        for k,v in [('callback2',0),('script',0x09FF4D16),('ready',1),('phase',1),('outcome',2),('current',17),
                ('best',17),('newbs',0x2000000),('marker',1),('snapshot',0),('count',6),('waiting',179),('types',0)]:
            rows=self.rows();rows[-1][k]=v
            with self.assertRaises(ValueError):task.waiting_witness(rows)
    def test_task_table_is_exact_active_not_stale_or_ambiguous(self):
        rows=self.rows();raw=bytearray.fromhex(rows[-1]['tasks']);raw[2*40+4]=0;rows[-1]['tasks']=raw.hex()
        with self.assertRaises(ValueError):task.waiting_witness(rows)
        rows=self.rows();raw=bytearray.fromhex(rows[-1]['tasks']);raw[:4]=(0x0807951D).to_bytes(4,'little');raw[4]=1;rows[-1]['tasks']=raw.hex()
        with self.assertRaises(ValueError):task.waiting_witness(rows)
        rows=self.rows();rows[-1]['tasks']='00'*639
        with self.assertRaises(ValueError):task.waiting_witness(rows)
    def test_persistent_wait_frames_are_required(self):
        for mutation in ('frame','early','ready'):
            rows=self.rows()
            if mutation=='frame':rows[-1]['frame']+=1
            elif mutation=='early':rows[0]['waiting']=29
            else:rows[0]['ready']=1
            with self.assertRaises(ValueError):task.waiting_witness(rows)
        with self.assertRaises(ValueError):task.waiting_witness([])
    def test_original_seventeen_win_outcomes_and_unsettled_black_return(self):
        events=task.probe.parse((ROOT/(task.RAW+'.stderr')).read_bytes())
        prefix=(ROOT/task.previous.previous.previous.previous.PREFIX).read_bytes();task.verify_prefix(events,prefix)
        self.assertEqual(len([e for e in events if e['label']=='outcome' and e['outcome']==1]),17)
        self.assertEqual(task.probe.owner(bytes.fromhex(events[-1]['owner']))['current'],16)
        self.assertFalse(any(e['label'] in ('saved','reloaded') for e in events))
        for at in (70,73,74,76,77,78):
            changed=copy.deepcopy(events);changed[at]['frame']+=1
            with self.assertRaises(ValueError):task.verify_prefix(changed,prefix)
    def test_policy_reimport_keeps_a_single_readonly_watcher(self):
        headers={p:(ROOT/p).read_text() for p in task.c.HEADERS}
        text=task.policy_text('slot=wx_move_slot(c);',headers)
        self.assertEqual(text.count('static void wr_frame('),1)
        with patch.object(task.c,'policy_text',task.policy_text):
            spec=importlib.util.spec_from_file_location('win_return_again',ROOT/task.SELF);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
            self.assertEqual(m.policy_text('slot=wx_move_slot(c);',headers),text)
    def test_readonly_header_compiles_without_write_apis(self):
        text=r'''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>
struct mCore {unsigned unused;};
enum {BATTLE_CORE_BATTLE_OUTCOME=0x2000000,BATTLE_CORE_MAIN_CALLBACK2=0x2000010,SP_SCRIPT_PTR=0x2000020,
 ADDR_NEW_BATTLE_STRUCT_POINTER=0x2000030,QOL_PLAYER_PARTY_COUNT=0x2000040,CF_TYPES=0x2000050};
#define BP_F(x) 0x2000060
static unsigned b_frames;
static void b_frame(struct mCore*c,uint32_t k){(void)c;(void)k;++b_frames;}
static unsigned read8(struct mCore*c,uint32_t p){(void)c;(void)p;return 0;}
static unsigned read16(struct mCore*c,uint32_t p){(void)c;(void)p;return 0;}
static uint32_t read32(struct mCore*c,uint32_t p){(void)c;(void)p;return 0;}
static void bp_require(struct mCore*c,bool ok,const char*s){(void)c;(void)ok;(void)s;}
static void g_shot(const char*s){(void)s;}
#include "HEADER"
int main(void){struct mCore c={0};wr_frame(&c,1U);return b_frames!=1U || wr_rows!=0U;}
'''.replace('HEADER',(ROOT/task.HEADER).as_posix())
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.c').write_text(text)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            subprocess.run([str(p/'test')],check=True,capture_output=True)
    def test_loss_watcher_calls_trace_without_redefining_frame_macro(self):
        old="b_frame(c,keys);\n#define b_frame fw_frame\n"
        self.assertEqual(task.chained_watch(old),"wr_frame(c,keys);\n#define b_frame fw_frame\n")
        self.assertEqual(task.chained_native_source().count('chained_watch('),1)
        for bad in ('',old+old,old.replace('b_frame(c,keys);','b_frame(c,0);')):
            with self.assertRaises(ValueError):task.chained_watch(bad)
    def test_no_fade_call_or_key_replacement_is_injected(self):
        text=(ROOT/task.HEADER).read_text()
        self.assertNotIn('#define b_frame',text)
        for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'loadState(', '0x0807D361'):self.assertNotIn(token,text)
        self.assertIn('b_frame(c,keys);',text)
        self.assertIn('wr_waiting==180U',text)
        self.assertEqual(task.probe.SHA,'3101772a3b91fe0461f200bbd3faf19f01064132bd3d8db9b0fe8f747445b399')

if __name__=='__main__':unittest.main()
