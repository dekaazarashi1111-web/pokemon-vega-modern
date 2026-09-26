"""新規30戦目同点選択の契約。合成prefix試験はnative勝利証明ではない。"""
from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_battle30_pp_policy as p
BASE=ROOT/'evidence/pr16_circus_reserve_fallback/35478473681/execution'

class Battle30PPTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(BASE/'circus-continuous-30-save.stderr').read_bytes()
        cls.source=(BASE/'policy.c').read_text()

    def test_actual29_wins_and_equal_score(self):
        value=p.original(self.raw)
        self.assertEqual((value['events'],value['wins'],value['losses']),(143,29,1))
        self.assertEqual(value['original_conclusion'],'failure')

    def test_two_insertions_only(self):
        amended=p.amend(self.source)
        self.assertEqual(amended.replace(p.PURE+'\n','',1).replace(p.DECISION,'',1),self.source)
        self.assertEqual(amended.count('CIRCUS_PP_TIE '),1)

    def test_source_drift_rejected(self):
        with self.assertRaises(ValueError):p.amend(self.source+'\n')

    def test_original_mutation_rejected(self):
        with self.assertRaises(ValueError):p.original(self.raw.replace(b'pp=32 power=60',b'pp=31 power=60',1))

    def test_compiled_scope_rank_and_blocked_contracts(self):
        program='#include <stdint.h>\n#include <assert.h>\n'+p.PURE+r'''
int main(void){
    uint64_t score[4]={305824,458737,458737,0};unsigned acc[4]={100,100,100,0},pp[4]={40,16,32,16};
    assert(pc_pick(28,1,0,score,acc,pp)==1);
    assert(pc_pick(29,1,0,score,acc,pp)==2);
    assert(pc_pick(29,1,4,score,acc,pp)==1);
    assert(pc_pick(29,1,2,score,acc,pp)==1);
    assert(pc_pick(29,4,0,score,acc,pp)==4);
    assert(pc_pick(29,3,0,score,acc,pp)==3);
    acc[2]=90;assert(pc_pick(29,1,0,score,acc,pp)==1);acc[2]=100;
    score[2]--;assert(pc_pick(29,1,0,score,acc,pp)==1);score[2]++;
    pp[2]=16;assert(pc_pick(29,1,0,score,acc,pp)==1);
    pp[2]=0;assert(pc_pick(29,1,0,score,acc,pp)==1);
    pp[1]=0;assert(pc_pick(29,1,0,score,acc,pp)==1);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as d:
            source=Path(d)/'contract.c';exe=Path(d)/'contract';source.write_text(program)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(source),'-o',str(exe)],check=True,capture_output=True)
            subprocess.run([str(exe)],check=True,capture_output=True)

    def synthetic(self):
        first=dict(frame=482072,streak=29,selected=1,actual=2,blocked=0,score=458737,
                   accuracy=100,old_pp=16,new_pp=32,old_move=58,new_move=352)
        anchor=b'CIRCUS_REENTRY frame=482072 streak=29 selected=1 actual=1 move=58 blocked=0 pp=16 foe_hp=167\n'
        self.assertEqual(self.raw.count(anchor),1)
        return self.raw.replace(anchor,p.MARKER+json.dumps(first).encode()+b'\n'+anchor.replace(
            b'actual=1 move=58',b'actual=2 move=352').replace(b'pp=16',b'pp=32'),1)

    def test_prefix_contract_not_native_success(self):
        proof=p.prefix_proof(self.raw,self.synthetic())
        self.assertEqual(proof['exact_event_count'],138)
        self.assertEqual(proof['continuation_prefix_wins'],29)
        self.assertNotIn('genuine_30_wins_verified',proof)

    def test_prior_input_corruption_rejected(self):
        with self.assertRaises(ValueError):p.prefix_proof(self.raw,b'x'+self.synthetic())

    def test_wrong_tie_rejected(self):
        with self.assertRaises(ValueError):p.prefix_proof(self.raw,self.synthetic().replace(b'"new_pp": 32',b'"new_pp": 16',1))

    def test_marker_without_actual_move_rejected(self):
        with self.assertRaises(ValueError):p.prefix_proof(self.raw,self.synthetic().replace(
            b'actual=2 move=352 blocked=0 pp=32',b'actual=1 move=58 blocked=0 pp=16',1))

    def test_no_native_state_shortcuts(self):
        for token in ('write8','write16','write32','rawWrite','busWrite','setRegister','loadState','saveState','species','rand('):
            self.assertNotIn(token,p.PURE+p.DECISION)
        self.assertNotIn('482072',p.PURE+p.DECISION)

if __name__=='__main__':unittest.main()
