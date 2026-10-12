"""敗北原本の非再実行照合と、paid無進展攻撃だけを避けるhost回帰。"""
from copy import deepcopy
from pathlib import Path
import importlib.util
import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_circus_reentry_probe as p
BASE=ROOT/'evidence/pr16_circus_continuous/35426278164/native'

def original():
    return ((BASE/(p.CASE+'.stdout')).read_bytes(),(BASE/(p.CASE+'.stderr')).read_bytes())

def changed_owner(raw,**changes):
    values=dict(current=(32,'H'),best=(34,'H'),phase=(36,'B'),outcome=(38,'B'),
                generation=(16,'I'),session=(20,'I'),prepared=(24,'I'),settled=(28,'I'),identity=(40,'I'))
    b=bytearray.fromhex(raw)
    for key,value in changes.items():
        at,fmt=values[key];struct.pack_into('<'+fmt,b,at,value)
    b[12:16]=bytes(4);struct.pack_into('<I',b,12,zlib.crc32(b)&0xffffffff)
    return b.hex()

def synthetic(loss_at=None):
    spec=importlib.util.spec_from_file_location('continuous_synthetic',ROOT/'tests/test_pr16_circus_continuous.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    events,result=m.fixture(loss_at);generation=1
    for i,e in enumerate(events):
        label=e['label'];local=e['battle']%3
        if label in ('selected','confirmation'):generation+=1
        if label=='settled':generation+=2 if e['outcome']==2 or local==2 else 1
        outcome=3 if label in ('settled','returned','saved','reloaded') and e['outcome']==2 else p.owner(bytes.fromhex(e['owner']))['outcome']
        e['owner']=changed_owner(e['owner'],generation=generation,outcome=outcome)
    return events,result

def validate(events,result):
    stderr=b'\n'.join(b'CIRCUS_CONTINUOUS '+json.dumps(e).encode() for e in events)
    return p.validate(json.dumps(result).encode(),stderr,0,p.CASE)

class ReentryTests(unittest.TestCase):
    def test_original_four_wins_loss_abort_and_save_not_thirty(self):
        raw,stderr=original();r=p.validate(raw,stderr,0,p.CASE);events=p.parse(stderr)
        self.assertEqual((r['wins'],r['losses'],r['events']),(4,1,27))
        self.assertEqual(p.owner(bytes.fromhex(events[23]['owner']))['outcome'],3)
        self.assertFalse(p.analyze(events,r)['genuine_30_wins_verified'])
        with self.assertRaises(ValueError):p.require_target(r)
    def test_all_terminal_ordinals_and_synthetic_target(self):
        for ordinal in (None,1,2,3,4,5,6,7,29,30):
            with self.subTest(ordinal=ordinal):
                e,r=synthetic(ordinal);validate(e,r)
                self.assertEqual(p.analyze(e,r)['genuine_30_wins_verified'],ordinal is None)
    def test_original_generation_outcome_and_return_mutants_rejected(self):
        raw,stderr=original();r=json.loads(raw);events=p.parse(stderr)
        mutations=[(15,dict(generation=9)),(16,dict(generation=12)),(19,dict(generation=13)),
            (23,dict(outcome=1)),(23,dict(outcome=2)),(23,dict(generation=14)),
            (24,dict(prepared=4,settled=4)),(24,dict(session=1)),(24,dict(identity=1)),
            (24,dict(generation=16)),(24,dict(outcome=2)),(26,dict(best=3))]
        for index,values in mutations:
            with self.subTest(index=index,values=values),self.assertRaises(ValueError):
                copy=deepcopy(events);copy[index]['owner']=changed_owner(copy[index]['owner'],**values);validate(copy,r)
    def test_actual_outcome_must_still_be_native_loss(self):
        raw,stderr=original();r=json.loads(raw);events=p.parse(stderr)
        for value in (0,1,3):
            copy=deepcopy(events);copy[22]['outcome']=value
            with self.subTest(value=value),self.assertRaises(ValueError):validate(copy,r)
    def test_pre_end_loss_snapshot_requires_exact_one_generation(self):
        raw,stderr=original();r=json.loads(raw);events=p.parse(stderr)
        events[23]['owner']=changed_owner(events[23]['owner'],phase=1,outcome=2,generation=14)
        validate(events,r)
        events[23]['owner']=changed_owner(events[23]['owner'],generation=15)
        with self.assertRaises(ValueError):validate(events,r)
    def test_abort_cannot_replace_any_genuine_win(self):
        e,r=synthetic()
        for i,row in enumerate(e):
            if row['label']=='settled':
                copy=deepcopy(e);copy[i]['owner']=changed_owner(row['owner'],outcome=3)
                with self.subTest(index=i),self.assertRaises(ValueError):validate(copy,r)
    def test_strict_types_and_double_settlement_are_rejected(self):
        e,r=synthetic()
        for key in r:
            if type(r[key]) is int:
                with self.subTest(key=key),self.assertRaises(ValueError):validate(e,dict(r,**{key:True}))
        copy=deepcopy(e);copy.insert(6,deepcopy(copy[5]));r=dict(r,events=len(copy))
        with self.assertRaises(ValueError):validate(copy,r)
    def test_exact_four_win_prefix_boundary(self):
        import pr16_circus_reentry as task
        raw,stderr=original();events=p.parse(stderr)
        task.verify_prefix(events,stderr)
        copy=deepcopy(events);copy[19]['frame']+=1
        with self.assertRaises(ValueError):task.verify_prefix(copy,stderr)
    def test_policy_inserts_only_one_later_input_wrapper(self):
        import pr16_circus_reentry as task
        headers={path:(ROOT/path).read_text() for path in task.c.HEADERS}
        text=task.policy_text('slot=wx_move_slot(c);',headers)
        self.assertEqual(text.count('slot=rr_move_slot(c);'),1)
        self.assertEqual(text.count('(read16(c,0x0203DB20U)%3U)'),4)
        self.assertEqual(text.count('#define CIRCUS_ACCURACY_VARIANT 1U'),1)
        with self.assertRaises(ValueError):task.policy_text('',headers)
    def test_configured_shared_module_cannot_double_wrap_on_reimport(self):
        import pr16_circus_reentry as first
        from unittest.mock import patch
        headers={path:(ROOT/path).read_text() for path in first.c.HEADERS}
        expected=first.policy_text('slot=wx_move_slot(c);',headers)
        with patch.object(first.c,'policy_text',first.policy_text),patch.object(first.c,'verify_prefix',first.verify_prefix):
            spec=importlib.util.spec_from_file_location('reentry_again',ROOT/'scripts/pr16_circus_reentry.py')
            again=importlib.util.module_from_spec(spec);spec.loader.exec_module(again)
            self.assertEqual(again.policy_text('slot=wx_move_slot(c);',headers),expected)
    def test_paid_progress_pure_c_contract(self):
        header=(ROOT/'tools/mgba_pr16_circus_reentry.h').as_posix()
        source='''#define CIRCUS_REENTRY_HOST_TEST
#include "HEADER"
#include <assert.h>
int main(void){
 assert(rr_stalls(0,16,16,106,106)==0);
 assert(rr_stalls(0,16,15,106,106)==1);
 assert(rr_stalls(1,15,14,106,106)==2);
 assert(rr_stalls(2,14,13,106,106)==2);
 assert(rr_stalls(1,15,14,106,80)==0);
 assert(rr_stalls(1,14,16,106,106)==1);
 uint64_t scores[4]={1000,300,0,0};
 assert(rr_pick(0,0,scores)==0);assert(rr_pick(0,1,scores)==1);
 assert(rr_pick(0,3,scores)==0);assert(rr_pick(3,1,scores)==3);
 assert(rr_pick(4,1,scores)==4);return 0;
}'''.replace('HEADER',header)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory);(path/'test.c').write_text(source)
            subprocess.run(['cc','-std=c11','-Wall','-Wextra','-Werror',str(path/'test.c'),'-o',str(path/'test')],check=True,capture_output=True)
            subprocess.run([str(path/'test')],check=True,capture_output=True)
    def test_controller_patch_cannot_write_game_state_or_change_prefix(self):
        text=(ROOT/'tools/mgba_pr16_circus_reentry.h').read_text()
        for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'loadState(', 'setKeys('):self.assertNotIn(token,text)
        self.assertIn('if(streak<4U)return selected;',text)
        self.assertIn('rr_memory.stalls[i]>=2U',text)
        self.assertIn('pp_after>=pp_before',text)

if __name__=='__main__':unittest.main()
