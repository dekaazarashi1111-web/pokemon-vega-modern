"""交換単体選択の実Cをhostで検証。ゲーム状態への書込みはmockのみ。"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'tools/mgba_pr16_bp_win_exchange.c'

class ExchangeNavigationTests(unittest.TestCase):
    def test_actual_c_navigation_and_fail_closed_boundaries(self):
        text = SOURCE.read_text()
        helper = text[text.index('static void wx_single_confirm('):text.index('struct WXResult')]
        harness = r'''
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <setjmp.h>
#include <string.h>
#define BATTLE_CORE_MAIN_CALLBACK2 1U
#define SP_SCRIPT_PTR 2U
#define ADDR_NEW_BATTLE_STRUCT_POINTER 3U
#define SP_ORDER_CFRU 10U
#define SP_PARTY_SLOT 20U
#define P02S_CB2_PARTY 0x0811f3a9U
#define QOL_KEY_UP 64U
struct mCore {unsigned cursor,order[6],cb,ptr,bs,pulses,mutation,stuck;};
static unsigned b_frames;
static jmp_buf stop;
static void bp_require(struct mCore *c,bool ok,const char *msg){(void)c;(void)msg;if(!ok)longjmp(stop,1);}
static unsigned read8(struct mCore *c,unsigned p){return p==SP_PARTY_SLOT?c->cursor:c->order[p-SP_ORDER_CFRU];}
static unsigned read32(struct mCore *c,unsigned p){return p==BATTLE_CORE_MAIN_CALLBACK2?c->cb:p==SP_SCRIPT_PTR?c->ptr:c->bs;}
static void b_press(struct mCore *c,unsigned key,unsigned frames){
    bp_require(c,key==QOL_KEY_UP && frames==60U,"non-native key/timing");
    ++c->pulses;b_frames+=62U;
    if(!c->stuck)c->cursor=c->cursor?c->cursor-1U:6U;
    if(c->mutation==1)c->order[0]=0;
    if(c->mutation==2)c->order[1]=1;
    if(c->mutation==3)c->cb=0;
    if(c->mutation==4)c->ptr=0;
    if(c->mutation==5)c->bs=1;
}
'''
        vectors = r'''
static struct mCore c;
static void reset(void){memset(&c,0,sizeof(c));c.cursor=2;c.order[0]=3;c.cb=P02S_CB2_PARTY;c.ptr=0x092CF72CU;}
int main(void){
    reset();if(setjmp(stop))return 1;wx_single_confirm(&c,2);if(c.pulses!=3 || c.cursor!=6)return 2;
    reset();c.cursor=6;if(setjmp(stop))return 3;wx_single_confirm(&c,2);if(c.pulses)return 4;
    reset();c.stuck=1;if(!setjmp(stop)){wx_single_confirm(&c,2);return 5;}if(c.pulses!=8)return 6;
    for(unsigned m=1;m<=5;++m){reset();c.mutation=m;if(!setjmp(stop)){wx_single_confirm(&c,2);return 7;}if(c.pulses!=1)return 8;}
    reset();c.order[0]=0;if(!setjmp(stop)){wx_single_confirm(&c,2);return 9;}if(c.pulses)return 10;
    reset();c.order[5]=1;if(!setjmp(stop)){wx_single_confirm(&c,2);return 11;}if(c.pulses)return 12;
    reset();c.cursor=8;if(!setjmp(stop)){wx_single_confirm(&c,2);return 13;}if(c.pulses)return 14;
    reset();if(!setjmp(stop)){wx_single_confirm(&c,3);return 15;}if(c.pulses)return 16;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src, exe = Path(tmp)/'navigation.c', Path(tmp)/'navigation'
            src.write_text(harness + helper + vectors)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)

    def test_integration_keeps_single_order_and_exact_party_witness(self):
        text = SOURCE.read_text()
        self.assertIn('wx_single_confirm(c,w.slot);', text)
        self.assertNotIn('single selection did not reach Confirm', text)
        self.assertIn('memcmp(expected,actual,sizeof(actual))', text)
        self.assertIn('w.replaced=100U;w.preserved=500U;', text)
        for term in ('write8(', 'write16(', 'write32(', 'busWrite', 'rawWrite', 'call_preserving('):
            self.assertNotIn(term, text)

if __name__ == '__main__':
    unittest.main()
