"""通常のr12退避ABIを復元命令後まで検証。旧段階失敗を受入にしない。"""
from pathlib import Path
import copy
import json
import sys
import unittest
from unittest import mock
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parents[1])]
import pr16_p08_ordinary_abi as m
import tests.test_pr16_p08_ordinary_representative as old


def calls():
    rows=old.call_rows();d=rows[1];d.update(entry_r12=d['r3_before'],restored_pc=d['delegate']+2)
    d['pcs'].append(d['restored_pc']);return rows


def raw(rows):
    return b''.join(b'P08_ORDINARY_CALL '+json.dumps(x).encode()+b'\n' for x in rows)


class OrdinaryABITests(unittest.TestCase):
    def test_native_restore_proof(self):
        self.assertEqual(m.calls_proof(calls(),old.routes())['normal_dispatches'],1)
    def test_stage72_entry_is_not_restore_completed(self):
        rows=calls();rows[1]['pcs'].pop();rows[1]['restored_pc']-=2
        with self.assertRaises(ValueError):m.calls_proof(rows,old.routes())
    def test_r12_handoff_corruption(self):
        rows=calls();rows[1]['entry_r12']+=1
        with self.assertRaises(ValueError):m.calls_proof(rows,old.routes())
    def test_r3_after_instruction_corruption(self):
        rows=calls();rows[1]['r3_after']+=1
        with self.assertRaises(ValueError):m.calls_proof(rows,old.routes())
    def test_direct_normal_8byte_route(self):
        rows=calls();routes=old.routes();routes[0]['preserve_r3']=False
        rows[1].update(preserve_r3=False,entry_r12=0,restored_pc=rows[1]['delegate'],r3_after=rows[1]['delegate']+1)
        rows[1]['pcs'].pop();m.calls_proof(rows,routes)
    def test_typed_nonfacility_flag(self):
        for value in (0,4):
            rows=calls()
            for row in rows:row['types']=value
            m.calls_proof(rows,old.routes())
    def test_facility_or_unknown_flag_rejected(self):
        for value in (8,0x04000000,1,False):
            rows=calls();rows[0]['types']=value
            with self.subTest(value=value),self.assertRaises(ValueError):m.calls_proof(rows,old.routes())
    def test_unknown_call_field_rejected(self):
        rows=calls();rows[1]['extra']=1
        with self.assertRaises(ValueError):m.calls_proof(rows,old.routes())
    def test_missing_natural_predicate(self):
        with self.assertRaises(ValueError):m.calls_proof(calls()[1:],old.routes())
    def test_suppression_result_stays_false(self):
        rows=calls();rows[0]['result']=1
        with self.assertRaises(ValueError):m.calls_proof(rows,old.routes())
    def test_full_native_lifecycle(self):
        row,events,original=old.sample()
        result,proof=m.validate(m.e.stable(row),old.trace(events,calls()),dict(returncode=0,timed_out=False,spawn_error=None),
            dict(routes=old.routes(),normal_entry_abi={'synthetic_unit_only':True}),original)
        self.assertEqual(result,row);self.assertEqual(proof['events'],events)
    def test_host_main_input_preserved(self):
        original={'controller.c':b'original\n','getter_suppression.h':b'int main(int argc,char **argv){return 0;}'}
        output=m.adapt(original)['controller.c']
        self.assertIn(b'#include "mgba_pr16_p08_ordinary_abi.h"',output)
        source=(m.ROOT/m.m.HEADER).read_bytes()
        for name in (b'k_path(c,',b'n_step(c,',b'n_cursor(c,',b'n_return(c,',b'a_guard(c)',b'b_continue(c)'):
            self.assertEqual(source.count(name),output.count(name))
    def test_observer_has_no_injected_state_or_input(self):
        text=(m.ROOT/m.HEADER).read_bytes()
        for token in (b'write8(',b'write16(',b'write32(',b'writeRegister',b'call_preserving(',b'->setKeys(',b'loadState',b'saveState'):
            with self.subTest(token=token):self.assertNotIn(token,text)
        self.assertIn(b'read16(c,pc)==0x4663U',text)
    def test_wrong_source_derivation_rejected(self):
        with self.assertRaises(ValueError):m.adapt({'controller.c':b'','getter_suppression.h':b'fake'})
    def test_physical_seven_restore_instructions(self):
        routes=[dict(name=str(i),normal=0x08000000+2*i,preserve_r3=i<7) for i in range(29)]
        oracle=dict(routes=routes)
        with mock.patch.object(m,'PHYSICAL',return_value=(oracle,b'header')):
            proof,_=m.physical(b'\x63\x46'*29,{})
            self.assertEqual(len(proof['normal_entry_abi']),7)
            with self.assertRaises(ValueError):m.physical(b'\0\0'*29,{})
    def test_unmodified_input_prefix(self):
        previous=old.call_rows()[1];previous.update(name='AbilityBattleEffects',frame=4989,r3_before=65535)
        current=calls()[1];current.update(name='AbilityBattleEffects',frame=4989,r3_before=65535)
        p=b'unchanged state\n';self.assertEqual(m.prefix_proof(p+raw([previous]),p+raw([current]))['input_changes'],0)
    def test_changed_input_prefix_rejected(self):
        previous=old.call_rows()[1];previous.update(name='AbilityBattleEffects',frame=4989,r3_before=65535)
        with self.assertRaises(ValueError):m.prefix_proof(b'old\n'+raw([previous]),b'new\n'+raw([previous]))
    def test_changed_first_call_rejected(self):
        previous=old.call_rows()[1];previous.update(name='AbilityBattleEffects',frame=4989,r3_before=65535)
        current=copy.deepcopy(previous);current['frame']+=1
        with self.assertRaises(ValueError):m.prefix_proof(raw([previous]),raw([current]))


if __name__=='__main__':unittest.main()
