"""交換2operandと実runtime関数のhost契約。native受入とは区別する。"""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('exchange',ROOT/'scripts/pr16_bp_exchange_successor.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def body(source, name):
    # exported/definition: declaration/callより先に実定義を要求する。
    import re
    match = re.search(r'^(?:FACILITY_EXPORT |static )?(?:void|uint\w+_t) '+re.escape(name)+r'\([^;]*?\)\s*\{', source, re.M)
    if not match:
        raise AssertionError('関数定義が見つからない: '+name)
    begin = source.index('{',match.start()); depth = 1; end = begin+1
    while depth:
        depth += (source[end]=='{')-(source[end]=='}'); end += 1
    return source[match.start():end].replace('FACILITY_EXPORT ','')


class ExchangePatchTests(unittest.TestCase):
    def test_two_only(self):
        raw = b'abc'+m.BEFORE+b'context'+m.BEFORE+b'end'
        changed = m.replace_operands(raw,(3,12))
        self.assertEqual(changed,b'abc'+m.AFTER+b'context'+m.AFTER+b'end')
        self.assertEqual(sum(a!=b for a,b in zip(raw,changed)),2)
        self.assertEqual(raw,b'abc'+m.BEFORE+b'context'+m.BEFORE+b'end')
    def test_partial_preimage_rejected(self):
        for raw in (b'xx'+m.BEFORE,b'\x2f\x01'+m.BEFORE,m.BEFORE+b'xx'):
            with self.assertRaises(ValueError):m.replace_operands(raw,(0,2))
    def test_reapply_rejected(self):
        with self.assertRaises(ValueError):m.replace_operands(m.AFTER*2,(0,2))
    def test_invalid_offsets(self):
        for offsets in ((-1,2),(2,0),(0,1),(0,4),(False,2),(0,),[0,2]):
            with self.subTest(offsets=offsets),self.assertRaises(ValueError):m.replace_operands(m.BEFORE*2,offsets)
    def test_mutable_rejected(self):
        with self.assertRaises(ValueError):m.replace_operands(bytearray(m.BEFORE*2),(0,2))
    def test_wrong_parent_rejected(self):
        with self.assertRaisesRegex(ValueError,'exact fcda'):m.binding(b'wrong')
    def test_no_false_native_claim(self):
        text = (ROOT/m.SELF).read_text()
        self.assertIn('new_emulator_processes=0',text)
        self.assertIn('native_exchange_accepted=False',text)
        self.assertIn('clean_rom_dual_build_verified=False',text)
    def test_fixed_scope(self):
        self.assertEqual(m.OFFSETS,(0x12CF729,0x12CF775))
        self.assertEqual(m.BEFORE.hex(),'2f00');self.assertEqual(m.AFTER.hex(),'2900')


class RuntimeContractTests(unittest.TestCase):
    def test_actual_runtime_functions(self):
        source = (ROOT/m.RUNTIME_SOURCE).read_text()
        self.assertEqual(hashlib.sha256(source.encode()).hexdigest(),m.RUNTIME_SHA)
        functions = '\n'.join(body(source,name) for name in ('copy_bytes','set_result','normalize_selected_order',
            'FacilityRuntime_SkipExchange','FacilityRuntime_BeginExchange','FacilityRuntime_CommitExchange'))
        header = r'''
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <assert.h>
#define FACILITY_PARTY_SIZE 6u
#define FACILITY_SELECTED_SIZE 3u
#define FACILITY_EXCHANGE_MAGIC 0x58434846u
typedef struct { uint8_t bytes[100]; } FacilityPokemon;
static FacilityPokemon party[6];
static struct { uint32_t magic; FacilityPokemon mon; } scratch;
static struct { struct { uint8_t snapshot_valid; } factory; } data;
#define gVegaModernSaveData (&data)
#define FACILITY_PLAYER_PARTY party
#define FACILITY_EXCHANGE_SCRATCH (&scratch)
static uint8_t order[6];
#define FACILITY_SELECTED_ORDER order
static uint16_t special_result;
#define FACILITY_SPECIAL_RESULT special_result
static uint8_t valid,configured;
static unsigned heals,persists;
static uint8_t ledger_valid(void) { return valid; }
static void configure_trial_vars(uint8_t n) { configured=n; }
static void heal_rental_party(void) { ++heals; }
static void persist_current(void) { ++persists; }
static void mark_seen(const FacilityPokemon *p) { (void)p; }
'''
        main = r'''
static void reset(void) {
    for(unsigned i=0;i<6;i++) memset(party[i].bytes,0x10+i,100);
    memset(scratch.mon.bytes,0xA5,100);scratch.magic=FACILITY_EXCHANGE_MAGIC;
    data.factory.snapshot_valid=valid=1;configured=3;special_result=0xFFFF;
    memset(order,0xFF,6);heals=persists=0;
}
int main(void) {
    for(unsigned slot=1;slot<=3;slot++) {
        reset();FacilityRuntime_BeginExchange();assert(configured==1 && special_result==1);
        for(unsigned i=0;i<6;i++) assert(order[i]==0);
        order[0]=slot;special_result=6; /* resultは選択slotではない */
        FacilityRuntime_CommitExchange();assert(special_result==1 && configured==3);
        assert(scratch.magic==0 && heals==1 && persists==1);
        for(unsigned i=0;i<6;i++) for(unsigned j=0;j<100;j++)
            assert(party[i].bytes[j]==(i==slot-1?0xA5:0x10+i));
        for(unsigned i=0;i<6;i++) assert(order[i]==(i<3?i+1:0));
    }
    const uint8_t rejected[]={0,4,5,6,255};
    for(unsigned k=0;k<5;k++) {
        reset();order[0]=rejected[k];special_result=1;
        FacilityRuntime_CommitExchange();assert(special_result==0 && configured==3 && scratch.magic==0);
        for(unsigned i=0;i<6;i++) for(unsigned j=0;j<100;j++) assert(party[i].bytes[j]==0x10+i);
    }
    for(unsigned k=0;k<3;k++) {
        reset();order[0]=2;
        if(k==0) valid=0; if(k==1)data.factory.snapshot_valid=0;if(k==2)scratch.magic=0;
        FacilityRuntime_CommitExchange();assert(special_result==0);
        for(unsigned i=0;i<6;i++) for(unsigned j=0;j<100;j++) assert(party[i].bytes[j]==0x10+i);
        reset();if(k==0)valid=0;if(k==1)data.factory.snapshot_valid=0;if(k==2)scratch.magic=0;
        FacilityRuntime_BeginExchange();assert(special_result==0 && configured==3);
    }
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);(p/'test.c').write_text(header+functions+main)
            subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-O2',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            proc = subprocess.run([str(p/'test')],capture_output=True,text=True)
            self.assertEqual(proc.returncode,0,proc.stderr)


if __name__=='__main__':unittest.main()
