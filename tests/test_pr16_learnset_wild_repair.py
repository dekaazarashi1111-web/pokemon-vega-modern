"""New wild-only wrapper: gate before writes, only slots/PP/PP Ups change."""
import ctypes as c
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
HEADER=r'''
#include <stdint.h>
struct Pr16RuntimeView { const uint8_t *bytes; uint16_t count,owner; };
#define PR16_CONSUMER_LEVEL_UP 3u
#define PR16_OWNER_PREPARED_LOOKUP 1u
#define PR16_IMAGE ((const uint8_t *)0)
#define PR16_IMAGE_SIZE 108008u
int Wild(void *);
uint32_t Get(const void *,int,uint8_t *);
uint8_t Read(const uint8_t *,uint32_t,uint16_t,uint8_t,struct Pr16RuntimeView *);
uint8_t Level(const void *);
void Set(void *,int,const void *);
void Initial(void *);
#define PR16_WILD_SLOT Wild
#define PR16_GET_MON_DATA Get
#define PR16_READ_VIEW Read
#define PR16_GET_BOX_LEVEL Level
#define PR16_SET_MON_DATA Set
#define PR16_INITIAL Initial
'''
FIXTURE=r'''
#include "pr16_wild_bindings.h"
#include <string.h>
static unsigned fields[64],saved[64],order[20],writes,called;
static unsigned wild,policy,level,violation;
static const uint16_t expect[4]={92,537,76,147};
void reset(unsigned w,unsigned p,unsigned lv,unsigned egg){
    for(unsigned i=0;i<64;++i)fields[i]=1000+i;
    fields[11]=838;fields[45]=egg;wild=w;policy=p;level=lv;
    memcpy(saved,fields,sizeof(fields));writes=called=violation=0;
}
void observe_again(void){memcpy(saved,fields,sizeof(fields));writes=called=violation=0;}
void *mon(void){return fields;}
int Wild(void *x){return x==fields && wild;}
uint32_t Get(const void *x,int f,uint8_t *unused){(void)unused;if(x!=fields)violation=1;return fields[f];}
uint8_t Read(const uint8_t *image,uint32_t size,uint16_t sid,uint8_t kind,struct Pr16RuntimeView *out){
    if(image || size!=108008 || sid!=838 || kind!=3)violation=1;
    out->bytes=0;out->count=4;out->owner=sid;return policy;
}
uint8_t Level(const void *x){if(x!=fields)violation=1;return level;}
void Set(void *x,int f,const void *zero){
    if(x!=fields || f<13 || f>21 || *(const uint32_t *)zero!=0 || writes>=9)violation=1;
    if(writes<20)order[writes]=f;++writes;fields[f]=*(const uint32_t *)zero;
}
void Initial(void *x){
    if(x!=fields || writes!=9)violation=1;
    for(unsigned i=13;i<=21;++i)if(fields[i])violation=1;
    for(unsigned i=0;i<4;++i){fields[13+i]=expect[i];fields[17+i]=10+i;}
    ++called;
}
unsigned query(unsigned q){
    if(q==0)return writes;if(q==1)return called;if(q==2)return violation;
    if(q==3){for(unsigned i=0;i<64;++i)if((i<13 || i>21) && fields[i]!=saved[i])return 0;return 1;}
    if(q==4)return memcmp(saved,fields,sizeof(fields))==0;
    if(q==5){for(unsigned i=0;i<9;++i)if(order[i]!=13+i)return 0;return 1;}
    if(q==6)return fields[21];return 0;
}
'''
class WildRepairTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();p=Path(cls.tmp.name)
        (p/'pr16_wild_bindings.h').write_text(HEADER);(p/'fixture.c').write_text(FIXTURE)
        subprocess.run(['cc','-std=c11','-O2','-fPIC','-shared','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-I'+str(p),str(ROOT/'src/modernization/pr16_learnset_wild_game.c'),str(p/'fixture.c'),'-o',str(p/'wild.so')],check=True,capture_output=True)
        cls.lib=c.CDLL(str(p/'wild.so'));cls.lib.mon.restype=c.c_void_p
        cls.lib.Pr16_GameApplyWildInitialMoves.argtypes=[c.c_void_p];cls.lib.Pr16_GameApplyWildInitialMoves.restype=c.c_uint8
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()
    def run_case(self,w=1,p=1,level=76,egg=0,null=False):
        self.lib.reset(w,p,level,egg);ret=self.lib.Pr16_GameApplyWildInitialMoves(None if null else self.lib.mon())
        self.assertEqual(self.lib.query(2),0);self.assertEqual(self.lib.query(3),1);return ret
    def rejected(self,**kwargs):
        self.assertEqual(self.run_case(**kwargs),0);self.assertEqual(self.lib.query(0),0);self.assertEqual(self.lib.query(1),0);self.assertEqual(self.lib.query(4),1)
    def test_null(self):self.rejected(null=True)
    def test_player_or_box(self):self.rejected(w=0)
    def test_egg(self):self.rejected(egg=1)
    def test_invalid_owner(self):self.rejected(p=0)
    def test_identity_owner(self):self.rejected(p=2)
    def test_carry_owner(self):self.rejected(p=3)
    def test_condition_owner(self):self.rejected(p=4)
    def test_unlinked_owner(self):self.rejected(p=5)
    def test_unknown_policy(self):self.rejected(p=255)
    def test_level_zero(self):self.rejected(level=0)
    def test_level_101(self):self.rejected(level=101)
    def test_level_255(self):self.rejected(level=255)
    def test_reset_only_nine_fields_then_original_initializer(self):
        self.assertEqual(self.run_case(),1);self.assertEqual([self.lib.query(i) for i in (0,1,5,6)],[9,1,1,0])
    def test_level_one(self):self.assertEqual(self.run_case(level=1),1)
    def test_level_hundred(self):self.assertEqual(self.run_case(level=100),1)
    def test_repeat_wild_normalization_is_stable(self):
        self.assertEqual(self.run_case(),1);a=[self.lib.query(i) for i in (0,1,2,3,5,6)]
        self.lib.observe_again();self.assertEqual(self.lib.Pr16_GameApplyWildInitialMoves(self.lib.mon()),1)
        self.assertEqual(a,[self.lib.query(i) for i in (0,1,2,3,5,6)])
if __name__=='__main__':unittest.main(verbosity=2)
