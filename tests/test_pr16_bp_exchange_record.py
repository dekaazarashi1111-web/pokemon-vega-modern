"""交換ABI証拠の境界・固定上流getterのhost契約。emulatorなし。"""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('exchange_record',ROOT/'scripts/pr16_bp_exchange_record.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.c=json.loads((ROOT/m.EVIDENCE/'candidate.json').read_bytes())
        self.u=json.loads((ROOT/m.EVIDENCE/'upstream-abi.json').read_bytes())
    def test_recorded_build_and_source(self):
        m.validate_build(self.c);m.validate_upstream(self.u)
    def test_cannot_promote_native_or_release(self):
        for key in ('native_exchange_accepted','native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready','clean_rom_dual_build_verified'):
            c=copy.deepcopy(self.c);c[key]=True
            with self.subTest(key=key),self.assertRaises(ValueError):m.validate_build(c)
    def test_exact_two_operands(self):
        c=copy.deepcopy(self.c);c['changes'].append(copy.deepcopy(c['changes'][0]))
        with self.assertRaises(ValueError):m.validate_build(c)
        c=copy.deepcopy(self.c);c['changes'][0]['after']='2f00'
        with self.assertRaises(ValueError):m.validate_build(c)
    def test_parent_and_candidate_are_not_interchangeable(self):
        c=copy.deepcopy(self.c);c['candidate']=copy.deepcopy(c['parent'])
        with self.assertRaises(ValueError):m.validate_build(c)
        c=copy.deepcopy(self.c);c['new_emulator_processes']=False
        with self.assertRaises(ValueError):m.validate_build(c)
    def test_comment_is_not_active_ram_binding(self):
        u=copy.deepcopy(self.u)
        u['selected_order_declarations']=[u['selected_order_declarations'][0]]
        with self.assertRaises(ValueError):m.validate_upstream(u)
    def test_no_duplicate_log_section(self):
        old='# original\nKEEP\n';section='\n\n## '+m.TASK+'\n'
        once=m.append_once(old,section)
        self.assertTrue(once.startswith(old))
        with self.assertRaises(ValueError):m.append_once(once,section)
    def test_changed_artifact_rejected_before_extract(self):
        with self.assertRaises(ValueError):m.archive_members(b'not the bound artifact')
    def test_actual_getter_and_ui_max_allow_one(self):
        functions='\n'.join(self.u['functions'][name]['text'] for name in ('GetNumMonsOnTeamInFrontier','ChoosePokemon_LoadMaxPKMNStr'))
        header=r'''
#include <stdint.h>
#include <stddef.h>
#include <assert.h>
typedef uint8_t u8;
typedef uint8_t bool8;
#define FLAG_BATTLE_FACILITY 1
#define VAR_BATTLE_FACILITY_POKE_NUM 1
#define PARTY_SIZE 6
#define MathMin(a,b) ((a)<(b)?(a):(b))
#define MathMax(a,b) ((a)>(b)?(a):(b))
static unsigned flag,count;
static unsigned FlagGet(unsigned x) {(void)x;return flag;}
static unsigned VarGet(unsigned x) {(void)x;return count;}
static const u8 text[6]={1,2,3,4,5,6};
static const u8 *sChoosePokemonMaxStrings[6]={text,text+1,text+2,text+3,text+4,text+5};
static const u8 *gOtherText_NoMoreThreePoke=text+2;
'''
        main=r'''
int main(void) {
    const u8 *p=NULL;
    flag=1;
    const unsigned inputs[]={0,1,2,3,6,7};
    const unsigned expected[]={1,1,2,3,6,6};
    for(unsigned i=0;i<6;i++) {
        count=inputs[i];assert(GetNumMonsOnTeamInFrontier()==expected[i]);
        assert(ChoosePokemon_LoadMaxPKMNStr(&p,1)==expected[i]);
        if(expected[i]==1)assert(p==text);
    }
    flag=0;count=1;
    assert(GetNumMonsOnTeamInFrontier()==3);
    assert(ChoosePokemon_LoadMaxPKMNStr(&p,1)==3 && p==gOtherText_NoMoreThreePoke);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);(p/'test.c').write_text(header+functions+main)
            subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            result=subprocess.run([str(p/'test')],capture_output=True)
            self.assertEqual(result.returncode,0)


if __name__=='__main__':unittest.main()
