"""実メニュー並替え停止の回帰と、入力非変更の復旧observerを検証。"""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('menu_recovery',ROOT/'scripts/pr16_circus_menu_recovery.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
ORIGINAL='tools/mgba_pr16_circus_interruption.c'
OLD='evidence/pr16_circus_three_win/35420040412/circus-streak-batch-save.stderr'
REF='evidence/pr16_circus_three_win/35418424222/circus-streak-batch-save.stderr'

class MenuRecoveryTests(unittest.TestCase):
    def test_all_six_permutations_and_identity_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            exe=Path(folder)/'test'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(ROOT/m.FIXTURE),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS_CIRCUS_MENU_IDENTITY checks=45',result.stdout)
    def original_header(self):
        text=(ROOT/m.MATCHUP).read_text()
        if 'mi_find' in text:
            text=text.replace('\n#include "mgba_pr16_circus_menu_identity.h"','').replace(m.MENU_CODE,'    b_frames_run(c,0U,60U);wx_cursor(c,target);')
        return text
    def test_exact_menu_repair(self):
        text=self.original_header();fixed=m.repair_menu(text)
        self.assertEqual(fixed.replace('\n#include "mgba_pr16_circus_menu_identity.h"','').replace(m.MENU_CODE,'    b_frames_run(c,0U,60U);wx_cursor(c,target);'),text)
        self.assertIn('wx_cursor(c,menu_slot)',fixed)
        self.assertIn('pid,ot,species);',fixed)
        for bad in ('',text+text,fixed):
            with self.assertRaises(ValueError):m.repair_menu(bad)
    def test_repair_never_injects_game_state(self):
        for text in ((ROOT/m.HEADER).read_text(),m.MENU_CODE):
            for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setRegister(', 'loadState(', 'saveState('):
                self.assertNotIn(forbidden,text)
    def test_real_prefix_is_not_a_third_victory(self):
        value=m.prior_partial((ROOT/OLD).read_bytes(),(ROOT/REF).read_bytes())
        self.assertEqual(value['real_wins'],2);self.assertFalse(value['third_outcome_observed'])
        self.assertEqual(value['original_conclusion'],'failure')
    def test_changed_prefix_or_unrelated_stop_rejected(self):
        raw=(ROOT/OLD).read_bytes();ref=(ROOT/REF).read_bytes()
        for bad in (raw.replace(b'"frame":0',b'"frame":1',1),raw.replace(b'"outcome":1',b'"outcome":2',1),
                    raw.replace(b'Circus matchup actual selected individual/type absent',b'unrelated'),b''):
            with self.assertRaises(ValueError):m.prior_partial(bad,ref)
    def observer(self):
        text=(ROOT/m.TRACE).read_text()
        start=text.index('/* RECOVERY_WATCH_BEGIN:');end=text.index('/* RECOVERY_WATCH_END */',start)+len('/* RECOVERY_WATCH_END */\n\n')
        return text,text[start:end]
    def test_trace_input_and_acceptance_source_unchanged(self):
        text,block=self.observer()
        text=text.replace(block,'').replace('a_guard(c);rt_watch(c);','a_guard(c);').replace('sizeof(party));rt_emit(c);','sizeof(party));')
        self.assertEqual(text,(ROOT/ORIGINAL).read_text())
        self.assertEqual((ROOT/m.TRACE).read_text().count('rt_watch(c);'),2)
    def test_observer_read_only_and_single_delegate(self):
        _,block=self.observer()
        for forbidden in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'setKeys(', 'loadState(', 'saveState(', 'setRegister('):
            self.assertNotIn(forbidden,block)
        self.assertEqual(block.count('rt_original_frame(c);'),1)
        self.assertIn('rt_rows++<512U',block)
    def test_real_observer_delegates_five_frames_without_keys_change(self):
        _,block=self.observer()
        fixture=r'''
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <assert.h>
struct mCore {void (*runFrame)(struct mCore *);unsigned frames,keys;};
static unsigned b_frames;
#define SC_OWNER 100U
#define P03_SAVE_COUNTER 1U
#define BATTLE_CORE_MAIN_CALLBACK2 2U
#define QOL_PLAYER_PARTY_COUNT 3U
#define QOL_PLAYER_PARTY 200U
#define BP_FACTORY 300U
#define BP_F(name) 400U
static void b_copy(struct mCore *c,unsigned address,void *out,unsigned n){(void)c;(void)address;memset(out,0,n);}
static uint32_t read32(struct mCore *c,unsigned address){(void)c;return address==1U?2U:0U;}
static unsigned read8(struct mCore *c,unsigned address){(void)c;(void)address;return 0U;}
static void bp_require(struct mCore *c,int ok,const char *message){(void)c;if(!ok){fprintf(stderr,"%s\n",message);exit(1);}}
'''+block+r'''
static void actual(struct mCore *c){++c->frames;}
int main(void){struct mCore c={.runFrame=actual,.keys=73};rt_watch(&c);
 for(unsigned i=0;i<5U;++i){c.runFrame(&c);++b_frames;assert(c.frames==i+1U);assert(c.keys==73U);}
 assert(rt_rows==1U);puts("PASS_RECOVERY_OBSERVER_FIVE_FRAMES");return 0;}
'''
        with tempfile.TemporaryDirectory() as folder:
            source=Path(folder)/'fixture.c';source.write_text(fixture);exe=Path(folder)/'test'
            subprocess.run(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
            self.assertIn('PASS_RECOVERY_OBSERVER_FIVE_FRAMES',result.stdout)
if __name__=='__main__':unittest.main()
