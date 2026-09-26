"""通常frameとreadRegisterだけの限定CPU診断。受入条件を書き換えない。"""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_win_return_cpu as t
class CpuTests(unittest.TestCase):
    def rows(self):
        main=bytearray(16);main[4:8]=(0x08055e75).to_bytes(4,'little')
        return [dict(frame=1000+e-1,elapsed=e,pc=0x08079542,lr=0x08079547,sp=0x03007f00,cpsr=0x30,
                     weather_id=3,weather_init=0x0807a001,main=main.hex(),weather='00'*64,script='00'*124,
                     tasks='00'*640,stack='00'*128) for e in [1,*range(30,601,30)]]
    def raw(self,rows):return b'\n'.join(b'CIRCUS_WIN_CPU '+json.dumps(r).encode() for r in rows)+b'\nbounded win CPU diagnostic complete\n'
    def test_exact_bounded_samples(self):self.assertEqual(t.parse(self.raw(self.rows())),self.rows())
    def test_missing_or_extra_sample_rejected(self):
        rows=self.rows()
        for v in (rows[:-1],rows+rows[-1:]):
            with self.assertRaises(ValueError):t.parse(self.raw(v))
    def test_bad_cpu_fields_rejected(self):
        for k,v in [('frame',0),('elapsed',599),('sp',0x02000000),('weather_id',32),('pc',True),('tasks','00')]:
            rows=self.rows();rows[-1][k]=v
            with self.assertRaises(ValueError):t.parse(self.raw(rows))
    def test_field_callback_change_rejected(self):
        rows=self.rows();rows[-1]['main']='00'*16
        with self.assertRaises(ValueError):t.parse(self.raw(rows))
    def test_real_diagnostic_exit_required(self):
        with self.assertRaises(ValueError):t.parse(self.raw(self.rows()).replace(b'bounded win CPU diagnostic complete',b''))
    def test_no_game_state_or_input_injection(self):
        text=(ROOT/t.HEADER).read_text()
        for token in ('write8(', 'write16(', 'write32(', 'writeRegister(', 'loadState(', '#define b_frame','call_preserving('):self.assertNotIn(token,text)
        self.assertEqual(text.count('b_frame(c,keys);'),1)
        self.assertIn('c->readRegister',text)
    def test_readonly_header_strict_host_compilation(self):
        text=r'''#include <stdint.h>
#include <stdbool.h>
#include <stdio.h>
struct mCore {bool (*readRegister)(struct mCore*,const char*,void*);};
enum {BATTLE_CORE_BATTLE_OUTCOME=1,SP_SCRIPT_PTR=2,BATTLE_CORE_MAIN_CALLBACK2=3,ADDR_NEW_BATTLE_STRUCT_POINTER=4};
static unsigned frames;
static unsigned read8(struct mCore*c,uint32_t a){(void)c;(void)a;return 0;}
static unsigned read16(struct mCore*c,uint32_t a){(void)c;(void)a;return 0;}
static uint32_t read32(struct mCore*c,uint32_t a){(void)c;(void)a;return 0;}
static void b_frame(struct mCore*c,uint32_t k){(void)c;(void)k;++frames;}
#define b_frames frames
static void bp_require(struct mCore*c,bool ok,const char*s){(void)c;(void)ok;(void)s;}
static void g_shot(const char*s){(void)s;}
#include "HEADER"
int main(void){struct mCore c={0};wr_frame(&c,1U);return frames!=1U || wc_rows!=0U;}
'''.replace('HEADER',(ROOT/t.HEADER).as_posix())
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.c').write_text(text)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            subprocess.run([str(p/'test')],check=True,capture_output=True)
if __name__=='__main__':unittest.main()
