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
        helper = text[text.index('static void wx_single_confirm('):text.index('/* scratch消去')]
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
    if(!c->stuck)c->cursor=c->cursor?c->cursor-1U:7U;
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
    reset();if(setjmp(stop))return 1;wx_single_confirm(&c,2);if(c.pulses!=4 || c.cursor!=6)return 2;
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

    def test_commit_boundary_rejects_mid_heal_and_foreign_owner(self):
        text = SOURCE.read_text()
        helper = text[text.index('static bool wx_commit_returned('):text.index('struct WXResult')]
        harness = r'''
#include <stdbool.h>
#include <stdint.h>
#define VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS 1U
#define BATTLE_CORE_MAIN_CALLBACK2 2U
#define ADDR_NEW_BATTLE_STRUCT_POINTER 3U
#define SP_SCRIPT_PTR 4U
struct mCore {uint32_t magic,cb,bs,ptr;};
static uint32_t read32(struct mCore *c,unsigned p){return p==1?c->magic:p==2?c->cb:p==3?c->bs:c->ptr;}
'''
        vectors = r'''
int main(void){
    struct mCore c={.cb=0x08055e75U,.ptr=0x092cf731U};
    if(wx_commit_returned(&c))return 1;
    unsigned good[]={0x092cf680U,0x092cf686U,0x092cf688U,0x092cf68dU};
    for(unsigned i=0;i<4;++i){c.ptr=good[i];if(!wx_commit_returned(&c))return 2;}
    c.magic=1;if(wx_commit_returned(&c))return 3;c.magic=0;
    c.bs=1;if(wx_commit_returned(&c))return 4;c.bs=0;
    c.cb=0;if(wx_commit_returned(&c))return 5;c.cb=0x08055e75U;
    unsigned bad[]={0,0x092cf72cU,0x092cf731U,0x092cf73dU,0x092cf681U,0x092cf7a0U};
    for(unsigned i=0;i<6;++i){c.ptr=bad[i];if(wx_commit_returned(&c))return 6;}
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src, exe = Path(tmp)/'boundary.c', Path(tmp)/'boundary'
            src.write_text(harness + helper + vectors)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(src),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)
        self.assertIn('if(!w.commit && wx_commit_returned(c))', text)

    def test_partial_pp_heal_is_not_the_exact_expected_party(self):
        text = SOURCE.read_text()
        helper = text[text.index('static void wx_healed_expected('):text.index('/* 初手Protect')]
        harness = r'''
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <stdlib.h>
#define BATTLE_CORE_MOVE_TABLE_REPOINT 1U
struct mCore {int unused;};
static void bp_require(struct mCore *c,bool ok,const char *s){(void)c;(void)s;if(!ok)exit(1);}
static uint32_t read32(struct mCore *c,unsigned p){(void)c;(void)p;return 0x09000000U;}
static unsigned read8(struct mCore *c,unsigned p){(void)c;unsigned m=(p-0x09000004U)/12U;return m==55?25:m==352?20:10;}
'''
        vectors = r'''
int main(void){
    struct mCore c={0};uint8_t cached[100]={0},expected[100],actual[100];
    unsigned moves[]={55,58,352,182},spent[]={39,15,31,15},full[]={40,16,32,16};
    cached[0x28]=255;cached[0x58]=167;
    for(unsigned i=0;i<4;++i){cached[0x2c+i*2]=moves[i];cached[0x2d+i*2]=moves[i]>>8;cached[0x34+i]=spent[i];}
    memcpy(expected,cached,100);wx_healed_expected(&c,expected);
    for(unsigned i=0;i<4;++i)if(expected[0x34+i]!=full[i])return 2;
    memcpy(actual,cached,100);actual[0x56]=167;actual[0x34]=40;
    if(!memcmp(expected,actual,100))return 3;
    for(unsigned i=0;i<4;++i)actual[0x34+i]=full[i];
    if(memcmp(expected,actual,100))return 4;
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            src, exe = Path(tmp)/'heal.c', Path(tmp)/'heal'
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
