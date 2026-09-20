"""入力限定の修正・厳密prefix・方策逸脱拒否。合成traceはunit専用。"""
from pathlib import Path
import sys
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_p08_bp_loss_policy as m


def traces():
    previous=b'old unchanged input\n'
    marker=b'P08_BP_INPUT_CHANGE {"frame":3917,"old_slot":0,"new_slot":1}\n'
    row=b'P08_BP_POLICY frame=3917 chosen=1'
    for i in range(4):
        row+=f' move{i}={i+1} pp{i}=10 power{i}={40 if i==0 else 0} split{i}={0 if i==0 else 2}'.encode()
    return previous,previous+marker+row+b'\n'


class PolicyTests(unittest.TestCase):
    def test_status_before_damage(self):
        self.assertLess(m.rank(0,2),m.rank(1,0));self.assertLess(m.rank(40,1),m.rank(80,1))
    def test_invalid_move_metadata(self):
        for pair in [(True,0),(-1,0),(256,0),(20,3),(0,False)]:
            with self.subTest(pair=pair),self.assertRaises(ValueError):m.rank(*pair)
    def test_prefix_and_move_policy(self):
        self.assertEqual(m.policy_proof(*traces())['ordinary_move_decisions'],1)
    def test_changed_prefix(self):
        old,new=traces()
        with self.assertRaises(ValueError):m.policy_proof(old,b'x'+new)
    def test_missing_boundary(self):
        old,new=traces()
        with self.assertRaises(ValueError):m.policy_proof(old,new.replace(m.MARKER,b'not-a-marker '))
    def test_wrong_boundary(self):
        old,new=traces()
        for a,b in [(b'3917',b'3918'),(b'"old_slot":0',b'"old_slot":1'),(b'"new_slot":1',b'"new_slot":0')]:
            with self.subTest(a=a),self.assertRaises(ValueError):m.policy_proof(old,new.replace(a,b))
    def test_rejects_damage_over_available_status(self):
        old,new=traces()
        with self.assertRaises(ValueError):m.policy_proof(old,new.replace(b'chosen=1',b'chosen=0'))
    def test_missing_policy_record(self):
        old,new=traces()
        with self.assertRaises(ValueError):m.policy_proof(old,new.split(b'P08_BP_POLICY')[0])
    def test_exact_old_controller_derivation(self):
        import pr16_bp_loss_return_native as old
        raw=old.derived_driver().assemble_controller().encode()
        result=m.adapt(raw,(m.ROOT/m.m.HEADER).read_bytes())
        self.assertIn(b'slot=p08_loss_slot(c);',result)
        self.assertIn(b'struct BPProgress progress=bp_progress(c);',result)
        self.assertIn(b'p08_bp_lifecycle(&c,&original',result)
    def test_host_write_and_result_override_absent(self):
        text=(m.ROOT/m.HEADER).read_bytes()
        for token in (b'write8(',b'write16(',b'write32(',b'call_preserving(',b'saveState',b'loadState',b'->setKeys(',b'->runFrame('):
            with self.subTest(token=token):self.assertNotIn(token,text)
    def test_wrong_source_anchor(self):
        with self.assertRaises(ValueError):m.adapt(b'fake',b'fake')
    def test_duplicate_and_unknown_policy_fields(self):
        old,new=traces()
        for tail in (b' chosen=1',b' unknown=1'):
            with self.subTest(tail=tail),self.assertRaises(ValueError):m.policy_proof(old,new.rstrip()+tail+b'\n')


if __name__=='__main__':unittest.main()
