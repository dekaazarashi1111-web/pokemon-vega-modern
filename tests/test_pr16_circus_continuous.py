"""連続入場validatorの合成敵対テスト。合成30勝は実機受入の証拠に数えない。"""
from copy import deepcopy
from pathlib import Path
import importlib.util
import json
import struct
import unittest
import zlib
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('continuous',ROOT/'scripts/pr16_circus_continuous.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
p=m.probe

def own(current,best,phase,prepared,settled,session,outcome=0):
    raw=bytearray(struct.pack('<IIHHIIIIIHHBBBBI',0x31534356,0x31534356^0xffffffff,
        1,64,0,1,session,prepared,settled,current,best,phase,0,outcome,0,1234)+bytes(20))
    struct.pack_into('<I',raw,12,zlib.crc32(raw)&0xffffffff);return raw.hex()

def fixture(loss_at=None):
    battles=loss_at or 30;wins=battles-(loss_at is not None);losses=int(loss_at is not None)
    party=bytes(600);pool=b''.join(bytes([i])+bytes(99) for i in range(1,7));chosen=pool[:300]+bytes(300)
    events=[];row=dict(label='fixture',frame=0,battle=0,callback2=1,script=0,newbs=0,outcome=0,flags=0,types=0,count=1,bp=0,
        save_counter=2,pending=0,snapshot=0,marker=0,order=[0,0,0],owner=own(0,0,0,0,0,0),party=party.hex(),factory=bytes(104).hex())
    def add(label,**values):
        nonlocal row
        row=dict(row,**values,label=label,frame=0 if not events else row['frame']+10);events.append(deepcopy(row))
    add('fixture');observed=0
    for admission in range((battles+2)//3):
        session=admission+1;base=observed
        add('selected',battle=base,count=6,bp=admission*9,pending=0,snapshot=1,marker=1,order=[1,2,3],party=pool.hex(),
            owner=own(base,base,1,base,base,session,1 if base else 0))
        for local in range(min(3,battles-observed)):
            n=observed;armed=own(n,n,2,n+1,n,session,1 if n else 0)
            add('confirmation',battle=n,count=3,script=p.LAUNCH[local],newbs=0,marker=2,party=chosen.hex(),owner=armed)
            add('action',script=p.LAUNCH[local]+43,newbs=123,types=0x04000000)
            outcome=2 if loss_at and n==battles-1 else 1
            add('outcome',outcome=outcome)
            best=n+(outcome==1);ending=outcome==2 or local==2
            add('settled',newbs=0,owner=own(best if outcome==1 else 0,best,0 if ending else 1,n+1,n+1,session,outcome))
            observed+=1
        best=observed-losses if observed==battles else observed
        current=0 if losses and observed==battles else observed
        add('returned',battle=observed,count=1,bp=(best//3)*9,pending=0,snapshot=0,marker=0,party=party.hex(),owner=own(current,best,0,observed,observed,session,2 if not current else 1))
    add('saved',save_counter=3);add('reloaded')
    result=dict(schema_version=1,status='PASS_CIRCUS_CONTINUOUS_LIFECYCLE',case=p.CASE,candidate_sha256=p.SHA,target_wins=30,
        save_counter_before=2,save_counter_after=3,manual_saves=1,fresh_cores=2,owner_bytes_verified=64,party_bytes_verified=600,
        host_write_barriers=7,input_only_after_guard=True,physical_admission_accepted=False,suppression_accepted=False,release_ready=False,warnings_errors=0,
        wins=wins,losses=losses,battles=battles,turns=battles,switches=0,forced_identity_checks=0,total_frames=row['frame'],events=len(events),
        admissions=(battles+2)//3,completed_batches=wins//3,bp_earned=(wins//3)*9)
    return events,result

def validate(events,result):
    err=b'\n'.join(b'CIRCUS_CONTINUOUS '+json.dumps(e).encode() for e in events)
    return p.validate(json.dumps(result).encode(),err,0,p.CASE)

class ContinuousTests(unittest.TestCase):
    def test_synthetic_target_structure_not_native_acceptance(self):
        events,result=fixture();self.assertEqual(len(events),143);validate(events,result);p.require_target(result)
        self.assertEqual(p.analyze(events,result)['bp_earned'],90)
    def test_first_loss_is_not_thirty(self):
        for ordinal in (1,3,4,6,7,29,30):
            with self.subTest(ordinal=ordinal):
                events,result=fixture(ordinal);validate(events,result)
                self.assertFalse(p.analyze(events,result)['genuine_30_wins_verified'])
                with self.assertRaises(ValueError):p.require_target(result)
    def test_counter_types_and_reported_target_forgery(self):
        events,result=fixture()
        for field in result:
            if type(result[field]) is int:
                bad=dict(result,**{field:True})
                with self.subTest(field=field),self.assertRaises(ValueError):validate(events,bad)
        events,result=fixture(4);result.update(wins=30,losses=0,battles=30,admissions=10,completed_batches=10,bp_earned=90)
        with self.assertRaises((ValueError,IndexError)):validate(events,result)
    def test_independent_owner_currency_identity_lifecycle_rejections(self):
        events,result=fixture()
        mutants=[(15,'owner',own(0,0,1,3,3,2)),(15,'bp',0),(15,'owner',own(3,3,1,3,3,1)),
            (16,'owner',own(3,3,2,4,3,2,2)),(18,'outcome',2),(19,'owner',own(5,5,1,4,4,2,1)),
            (17,'party',bytes(600).hex()),(17,'factory',(bytes(103)+b'\1').hex()),(17,'script',p.LAUNCH[1]+43),
            (17,'save_counter',3),(142,'bp',81),(142,'owner',own(0,30,0,30,30,10,1)),(142,'save_counter',2)]
        # A previous battle outcome in an armed record is allowed, so do not mutate that non-authoritative field.
        mutants=[v for v in mutants if not (v[0]==16 and v[1]=='owner')]
        for index,key,value in mutants:
            copy=deepcopy(events);copy[index][key]=value
            with self.subTest(index=index,key=key),self.assertRaises(ValueError):validate(copy,result)
    def test_json_crc_and_order_fail_closed(self):
        with self.assertRaises(ValueError):p.strict('{"a":1,"a":2}')
        with self.assertRaises(ValueError):p.strict('{"a":NaN}')
        with self.assertRaises(ValueError):p.owner(bytes(64))
        events,result=fixture();events[5]['frame']=events[4]['frame']
        with self.assertRaises(ValueError):validate(events,result)
    def test_policy_fixed_boundaries(self):
        headers={path:(ROOT/path).read_text() for path in m.HEADERS}
        text=m.policy_text('slot=wx_move_slot(c);',headers)
        self.assertEqual(text.count('(read16(c,0x0203DB20U)%3U)'),4)
        self.assertIn('CIRCUS_ACCURACY_VARIANT 1U',text)
        self.assertNotIn('#include "mgba_pr16_circus_matchup.h"',text)
        with self.assertRaises(ValueError):m.policy_text('',headers)
    def test_host_writes_remain_before_guard(self):
        text=(ROOT/m.SOURCE).read_text();main=text[text.index('int main('):]
        guarded=main[main.index('a_guard(c);'):]
        for token in ('write8(', 'write16(', 'write32(', 'call_preserving(', 'loadState('):self.assertNotIn(token,guarded)
        self.assertIn('admission<10U',guarded);self.assertIn('if(sc_losses)break',guarded)
        old=(ROOT/'tools/mgba_pr16_streak_native.c').read_text()
        a=old[old.index('    g_prefix=argv[6]'):old.index('    sc_event(c,"fixture"')]
        b=text[text.index('    g_prefix=argv[6]'):text.index('    sc_event(c,"fixture"')]
        self.assertEqual(a,b)
    def test_prefix_must_be_identical(self):
        old=[dict(label='x',frame=i) for i in range(17)];old[14]['label']='returned'
        raw=b'\n'.join(b'CIRCUS_STREAK '+json.dumps(e).encode() for e in old)
        m.verify_prefix(old[:15],raw)
        changed=deepcopy(old[:15]);changed[3]['frame']+=1
        with self.assertRaises(ValueError):m.verify_prefix(changed,raw)
    def test_visual_review_has_reward_and_continue(self):
        review=json.loads((ROOT/m.REVIEW).read_bytes())
        self.assertEqual(review['run_id'],35425237415);self.assertTrue(review['completed']);self.assertEqual(len(review['screens']),5)
        self.assertTrue(any('14-settled' in n for n in review['screens']))
        self.assertTrue(any('17-reloaded' in n for n in review['screens']))
if __name__=='__main__':unittest.main()
