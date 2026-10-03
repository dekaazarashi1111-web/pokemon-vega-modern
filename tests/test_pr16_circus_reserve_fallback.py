"""実29戦目原本・生成差分・控え選択の新規契約だけを検証する。"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_reserve_fallback_policy as p
BASE=ROOT/'evidence/pr16_circus_battle29_recheck/35477541574/execution'

class ReserveFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(BASE/'circus-continuous-30-save.stderr').read_bytes()
        cls.source=(BASE/'policy.c').read_text()

    def test_actual_context_replaces_prediction(self):
        value=p.original(self.raw)
        self.assertEqual((value['wins'],value['losses'],len(value['holds'])),(28,1,6))
        self.assertEqual(value['next_foe_types'],[0,0])
        self.assertEqual(value['next_own_hp'],102)
        self.assertTrue(value['legacy_validator_failure_preserved'])

    def test_exact_saved_source_and_only_two_insertions(self):
        amended=p.amend(self.source)
        self.assertEqual(amended.replace(p.PURE+p.NATIVE+'\n','',1).replace(
            '    if(target==3U)target=rf_fallback(c,streak,wanted,attacks);\n','',1),self.source)
        self.assertEqual(amended.count('CIRCUS_RESERVE_FALLBACK '),1)

    def test_source_drift_rejected(self):
        with self.assertRaises(ValueError):p.amend(self.source+'\n')

    def test_original_mutation_rejected(self):
        with self.assertRaises(ValueError):p.original(self.raw.replace(b'"hp":113',b'"hp":114',1))

    def test_compiled_scope_and_health_ranking(self):
        program='#include <stdint.h>\n#include <assert.h>\n'+p.PURE+r'''
int main(void){
    assert(rf_needed(28,17,11,11,0,0,1U<<7));
    assert(!rf_needed(27,17,11,11,0,0,1U<<7));
    assert(!rf_needed(28,12,11,11,0,0,1U<<7));
    assert(!rf_needed(28,17,0,11,0,0,1U<<7));
    assert(!rf_needed(28,17,11,11,7,3,1U<<7));
    assert(!rf_needed(28,17,11,11,0,0,(1U<<7)|(1U<<10)));
    assert(!rf_rank(75,101,101,125,200,136,136));
    assert(!rf_rank(75,100,101,0,200,136,136));
    assert(!rf_rank(75,100,101,125,200,0,136));
    assert(!rf_rank(75,100,101,125,200,137,136));
    uint64_t scores[3]={0,rf_rank(90,100,115,90,100,163,163),rf_rank(75,100,101,125,200,136,136)};
    uint64_t active=rf_rank(90,100,105,90,100,102,182);
    assert(scores[1]==1150000 && scores[2]==1212000);
    assert(rf_pick(active,scores)==2);
    uint64_t weak[3]={0,100,125};assert(rf_pick(100,weak)==3);
    uint64_t ties[3]={200,200,0};assert(rf_pick(100,ties)==0);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'contract.c';exe=Path(d)/'contract';source.write_text(program)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)

    def synthetic(self):
        first=dict(frame=468129,streak=28,wanted=17,attacks=128,foe_types=[0,0],own_types=[11,11],
                   hp=102,maxhp=182,target=2,active_score=588461,scores=[0,1150000,1212000])
        before,found,after=self.raw.partition(b'BP_WIN_MOVE frame=468129 ')
        self.assertTrue(found)
        return before+p.MARKER+json.dumps(first).encode()+b'\nCIRCUS_TACTICAL begin frame=468129 streak=28 synthetic-only\n'+found+after

    def test_prefix_contract_not_native_success(self):
        proof=p.prefix_proof(self.raw,self.synthetic())
        self.assertEqual(proof['exact_event_count'],134)
        self.assertEqual(proof['accepted_standalone_replays'],0)
        self.assertNotIn('genuine_30_wins_verified',proof)

    def test_prefix_byte_corruption_rejected(self):
        with self.assertRaises(ValueError):p.prefix_proof(self.raw,b'x'+self.synthetic())

    def test_unobserved_boundary_rejected(self):
        with self.assertRaises(ValueError):p.prefix_proof(self.raw,self.synthetic().replace(b'"hp": 102',b'"hp": 91',1))

    def test_host_memory_and_species_shortcuts_absent(self):
        for token in ('write8','write16','write32','rawWrite','busWrite','setRegister','loadState','saveState','species=','rand('):
            self.assertNotIn(token,p.PURE+p.NATIVE)
        self.assertIn('if(!move || !pp)continue;',p.NATIVE)
        self.assertIn('read32(c,mon)==pid && read32(c,mon+4U)==ot',p.NATIVE)

    def test_wrong_reserve_rejected(self):
        with self.assertRaises(ValueError):p.prefix_proof(self.raw,self.synthetic().replace(b'"target": 2',b'"target": 1',1))

if __name__=='__main__':unittest.main()
