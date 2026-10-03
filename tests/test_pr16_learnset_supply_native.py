"""実ROM接続adapterだけの新規試験。既受入30/96試験を呼ばない。"""
from __future__ import annotations
import ctypes as c
from pathlib import Path
import subprocess
import tempfile
import unittest
from tools import pr16_learnset_supply as data
ROOT = Path(__file__).resolve().parents[1]
U8, U16 = c.c_uint8, c.c_uint16
HEADER = r'''
#include "pr16_learnset_runtime.h"
extern uint8_t ns_mode, ns_gate, ns_policy, ns_wrong, ns_special, ns_party[600];
extern uint16_t ns_selection, ns_result, ns_map[256];
extern const uint8_t *ns_image;
extern uint32_t ns_size;
uint32_t ns_get(void *, int, uint8_t *);
uint8_t ns_read(uint16_t, uint8_t, struct Pr16RuntimeView *);
uint8_t ns_parent(void *,uint16_t *);
uint8_t ns_original(void *,uint8_t);
#define PR16_SUPPLY_GET_MON_DATA ns_get
#define PR16_SUPPLY_READ_CONDITIONAL ns_read
#define PR16_SUPPLY_IMAGE ns_image
#define PR16_SUPPLY_IMAGE_SIZE ns_size
#define PR16_SUPPLY_FLAG_GET(f) (ns_gate && (f)==0x082cu)
#define PR16_SUPPLY_MEMORY_MODE (&ns_mode)
#define PR16_SUPPLY_PARENT_RELEARNER ns_parent
#define PR16_SUPPLY_GET_TUTOR_MOVE(n) (ns_map[n])
#define PR16_SUPPLY_SPECIAL_TUTOR ns_original
#define PR16_SUPPLY_PARTY_SELECTION (&ns_selection)
#define PR16_SUPPLY_RESULT (&ns_result)
#define PR16_SUPPLY_PARTY ns_party
'''
FIXTURE = r'''
#include "pr16_learnset_supply_bindings.h"
uint8_t ns_mode, ns_gate, ns_policy, ns_wrong, ns_special, ns_party[600], ns_bits[16];
uint16_t ns_selection, ns_result, ns_map[256], ns_calls, ns_last;
const uint8_t *ns_image;
uint32_t ns_size;
uint32_t ns_get(void *ptr,int field,uint8_t *out) {
 uint8_t *p=ptr; (void)out;
 if(field==11)return p[0]|((uint16_t)p[1]<<8);
 if(field==45)return p[2];
 if(field>=13 && field<17)return p[4+(field-13)*2]|((uint16_t)p[5+(field-13)*2]<<8);
 return 0;
}
uint8_t ns_read(uint16_t sid,uint8_t consumer,struct Pr16RuntimeView *v) {
 (void)consumer; v->owner=sid+ns_wrong;v->bytes=ns_bits;v->count=64;
 return ns_policy;
}
uint8_t ns_parent(void *mon,uint16_t *out){(void)mon;out[0]=777;return 1;}
uint8_t ns_original(void *mon,uint8_t id){(void)mon;++ns_calls;ns_last=id;return ns_special;}
'''

class NativeSupplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(); cls.addClassCleanup(cls.temp.cleanup)
        folder = Path(cls.temp.name)
        (folder/'pr16_learnset_supply_bindings.h').write_text(HEADER)
        (folder/'fixture.c').write_text(FIXTURE)
        library = folder/'native.so'
        subprocess.run(['cc','-std=c11','-shared','-fPIC','-O2','-Wall','-Wextra','-Werror',
            '-Isrc/modernization','-I'+str(folder),
            *['src/modernization/'+n+'.c' for n in ('pr16_learnset_supply','pr16_learnset_supply_game','pr16_learnset_supply_native')],
            str(folder/'fixture.c'),'-o',str(library)],cwd=ROOT,check=True,capture_output=True)
        cls.dll=c.CDLL(str(library))
        cls.dll.Pr16_GameCanLearnTutor.argtypes=[c.c_void_p,U8];cls.dll.Pr16_GameCanLearnTutor.restype=U8
        cls.dll.Pr16_GameSupplySelectedRowCount.restype=U16
        cls.dll.Pr16_GameSupplySelectedPageHasMoves.restype=None
        cls.dll.Pr16_GameSupplyRelearner.argtypes=[c.c_void_p,c.POINTER(U16)]
        cls.dll.Pr16_GameSupplyRelearner.restype=U8
        policies=bytearray([2]*1671)
        rows={(sid,f):None for sid in range(1671) for f in data.FAMILIES}
        for sid,machine,tutor in ((1,tuple(range(1,132)),(500,)),(1029,(63,76,80),(501,)),(1670,(),())):
            policies[sid]=1;rows[sid,'machine']=machine;rows[sid,'tutor']=tutor
        raw,_=data.compose(rows,bytes(policies))
        cls.image=(U8*len(raw)).from_buffer_copy(raw)
        c.c_void_p.in_dll(cls.dll,'ns_image').value=c.addressof(cls.image)
        c.c_uint32.in_dll(cls.dll,'ns_size').value=len(raw)

    def var(self,name,typ=U8): return typ.in_dll(self.dll,'ns_'+name)
    def setUp(self):
        for name in ('mode','gate','policy','special'):self.var(name).value=1
        self.var('wrong').value=0
        for name in ('calls','last','selection'):self.var(name,U16).value=0
        self.var('result',U16).value=0xcafe
        self.party=(U8*600).in_dll(self.dll,'ns_party');self.party[:]=bytes(600)
        self.bits=(U8*16).in_dll(self.dll,'ns_bits');self.bits[:]=bytes(16)
        self.map=(U16*256).in_dll(self.dll,'ns_map');self.map[:]=[0]*256
        self.party[0]=1;self.map[152]=500;self.map[160]=501
    def tutor(self,n):return self.dll.Pr16_GameCanLearnTutor(self.party,n)
    def test_normal_slots_stay_separate(self):
        self.bits[0]=1;self.bits[7]=128
        self.assertEqual([self.tutor(n) for n in (0,1,63,64,151)],[1,0,1,0,0])
        self.assertEqual(self.var('calls',U16).value,0)
    def test_special_exact_id_and_owner_archive(self):
        self.assertEqual(self.tutor(152),1);self.assertEqual(self.var('last',U16).value,152)
        self.assertEqual(self.tutor(160),0);self.assertEqual(self.var('calls',U16).value,1)
    def test_special_parent_restriction_is_preserved(self):
        self.var('special').value=0;self.assertEqual(self.tutor(152),0)
        self.assertEqual(self.var('calls',U16).value,1)
    def test_special_regular_catalog_membership_not_id_flattening(self):
        self.map[160]=222;self.map[4]=222;self.bits[0]=16
        self.assertEqual(self.tutor(160),1);self.assertEqual(self.var('last',U16).value,160)
        self.assertEqual(self.tutor(64),0)
    def test_all_other_tutor_ids_fail_closed(self):
        for n in (*range(64,152),*range(161,256)):self.assertEqual(self.tutor(n),0)
        self.assertEqual(self.var('calls',U16).value,0)
    def test_special_egg_policy_owner_and_null_rejected(self):
        for flag in ('wrong','policy'):
            self.var(flag).value=2;self.assertEqual(self.tutor(152),0);self.var(flag).value=0 if flag=='wrong' else 1
        self.party[2]=1;self.assertEqual(self.tutor(152),0)
        self.assertEqual(self.dll.Pr16_GameCanLearnTutor(None,152),0)
        self.assertEqual(self.var('calls',U16).value,0)
    def test_special_invalid_move_rejected(self):
        for move in (0,1063,65535):self.map[152]=move;self.assertEqual(self.tutor(152),0)
    def test_tutor_npc_does_not_inherit_archive_hof_gate(self):
        self.var('gate').value=0;self.assertEqual(self.tutor(152),1)
        self.assertEqual(self.dll.Pr16_GameSupplySelectedRowCount(),0)
    def test_selected_row_count_raw_before_known_filter(self):
        self.party[4:12]=bytes((1,0,2,0,3,0,4,0))
        self.assertEqual(self.dll.Pr16_GameSupplySelectedRowCount(),131)
    def test_selected_slot_not_species_slot_zero(self):
        self.var('selection',U16).value=5;self.party[500]=1029&255;self.party[501]=1029>>8
        self.assertEqual(self.dll.Pr16_GameSupplySelectedRowCount(),3)
        for n in (6,255,65535):self.var('selection',U16).value=n;self.assertEqual(self.dll.Pr16_GameSupplySelectedRowCount(),0)
    def test_callback_mode_boundaries_and_no_party_write(self):
        before=bytes(self.party)
        for mode in range(9):
            self.var('mode').value=mode;self.dll.Pr16_GameSupplySelectedPageHasMoves()
            self.assertEqual(self.var('result',U16).value,int(3<=mode<=6))
            self.assertEqual(self.var('mode').value,mode)
        self.assertEqual(bytes(self.party),before)
    def test_empty_selected_page_and_gate(self):
        self.party[0]=1029&255;self.party[1]=1029>>8;self.var('mode').value=4
        self.dll.Pr16_GameSupplySelectedPageHasMoves();self.assertEqual(self.var('result',U16).value,0)
        self.var('mode').value=3;self.var('gate').value=0
        self.dll.Pr16_GameSupplySelectedPageHasMoves();self.assertEqual(self.var('result',U16).value,0)
    def test_selected_identity_only_and_egg_have_no_rows(self):
        self.party[0]=887&255;self.party[1]=887>>8
        self.assertEqual(self.dll.Pr16_GameSupplySelectedRowCount(),0)
        self.party[0]=1;self.party[1]=0;self.party[2]=1
        self.assertEqual(self.dll.Pr16_GameSupplySelectedRowCount(),0)
    def test_normal_and_egg_reminder_delegate_and_canary(self):
        out=(U16*42)(*([0xbeef]*42))
        for mode in (0,1):
            self.var('mode').value=mode
            self.assertEqual(self.dll.Pr16_GameSupplyRelearner(self.party,out),1)
            self.assertEqual(list(out),[777]+[0xbeef]*41)
