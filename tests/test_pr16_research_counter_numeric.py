"""新受付数値だけの陽性/改変拒否。旧native/旧test suiteは呼ばない。"""
import copy
import json
import os
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_research_counter_numeric as patch
import pr16_research_counter_oracle as oracle
import pr16_research_counter_probe as probe


class EventTests(unittest.TestCase):
    def test_normal_event(self):
        code,_=patch.script()
        for rp,rank in ((0,1),(9,2),(10,3),(99,4),(100,5),(999,6),(1000,7),(9999,7)):
            with self.subTest(rp=rp):
                r=oracle.walk(code,0,rp,rank)
                self.assertEqual(r['result'],0)
                self.assertEqual(r['calls'],[0x093be8a1,0x093be033,0x093be057])
                self.assertEqual(r['messages'],[0x093c003d,0x093c004b,0x093c005a,0x093c006d,0x093c008e])
                self.assertEqual(r['buffers'],{0:(oracle.digits(rp)+b'\xff').hex(),1:(oracle.digits(rank)+b'\xff').hex()})

    def test_failure_branches_preserve_result(self):
        code,_=patch.script()
        for outcome,extra in ((4,[0x093c007e]),(13,[0x093c009e]),(1,[]),(2,[]),(3,[]),(65535,[])):
            with self.subTest(result=outcome):
                r=oracle.walk(code,outcome,9999,7)
                self.assertEqual(r,dict(result=outcome,messages=[0x093c003d]+extra,calls=[0x093be8a1],buffers={}))

    def test_format_is_two_native_placeholders(self):
        self.assertEqual(patch.TEXT_AFTER,bytes.fromhex('ccca00fd02fe777e5800fd03ffffff'))
        self.assertEqual(len(patch.SCRIPT_BEFORE),132)
        self.assertEqual(len(patch.TEXT_BEFORE),15)
        self.assertEqual(len(patch.script()[0])+len(patch.TEXT_AFTER),147)

    def test_independent_physical_input(self):
        self.assertEqual(len(probe.PROGRAM),17)
        self.assertEqual(probe.PROGRAM[-1],(0,0,'end'))
        self.assertNotIn(b'shop',probe.commands())
        self.assertEqual(sum(n for _,n,_ in probe.PROGRAM),1160)

    def test_getters_cannot_be_replaced_with_other_calls(self):
        code,_=patch.script();code=code.replace(bytes.fromhex('2333e03b09'),bytes.fromhex('2301000008'))
        with self.assertRaises(ValueError): oracle.walk(code,0,10,1)

    def test_outside_jump_rejected(self):
        code=bytearray(patch.script()[0]);code[0:5]=bytes.fromhex('0500000008')
        with self.assertRaises(ValueError): oracle.walk(bytes(code),0,10,1)

    def test_missing_release_rejected(self):
        code=patch.script()[0].replace(b'\x6c\x02',b'\x00\x02')
        with self.assertRaises(ValueError): oracle.walk(code,0,10,1)

    def test_truncated_event_rejected(self):
        with self.assertRaises(ValueError): oracle.walk(patch.script()[0][:-1],0,10,1)

    def test_result_not_restore_detected(self):
        code=patch.script()[0].replace(bytes.fromhex('160d800000'),bytes.fromhex('160d800100'))
        self.assertNotEqual(oracle.walk(code,0,9999,7)['result'],0)

    def test_reversed_slots_detected(self):
        code=patch.script()[0].replace(bytes.fromhex('83000d80'),bytes.fromhex('83010d80'))
        with self.assertRaises(ValueError): oracle.walk(code,0,9999,7)

    def test_display_values_closed(self):
        for n in (-1,10000,True,'1',1.5):
            with self.subTest(n=n),self.assertRaises(ValueError): oracle.digits(n)

    def test_fixture_indices_closed(self):
        for n in (-1,2,True,'0'):
            with self.subTest(n=n),self.assertRaises(ValueError): probe.fixture(b'',n)

    def test_duplicate_json_rejected(self):
        with self.assertRaises(ValueError): oracle.load(b'{"x":0,"x":1}')

    def test_nonfinite_json_rejected(self):
        with self.assertRaises(ValueError): oracle.load(b'{"x":NaN}')

    def test_booleans_are_not_integers(self):
        self.assertFalse(oracle.exact({'a':True},{'a':1}))


class NativeEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory=os.environ.get('PR16_COUNTER_EVIDENCE')
        if not directory: raise unittest.SkipTest('専用Actionsの原本/fixtureが必要。nativeは起動しない。')
        cls.directory=Path(directory)

    def inputs(self,index):
        path=self.directory/str(index)
        m=oracle.load((path/'measurement.json').read_bytes())
        return [(path/'stdout.txt').read_bytes(),index,(path/'commands.txt').read_bytes(),
                (self.directory.parent/(str(index)+'.srm')).read_bytes(),m['screens']]

    def test_two_real_transcripts(self):
        for i in (0,1):
            result=oracle.validate(*self.inputs(i))
            self.assertTrue(result['counter_numeric_display_accepted'])
            self.assertTrue(result['counter_rank_number_accepted'])
            self.assertFalse(result['standard_list_accepted'])
            self.assertFalse(result['naturally_earned_spending_accepted'])


def mutation_test(kind,index):
    def test(self):
        args=self.inputs(index);rows=[oracle.load(line) for line in args[0].splitlines()]
        first=lambda key:next(r for r in rows if key in r)
        if kind=='drop': rows.pop(3)
        elif kind=='duplicate': rows.insert(3,copy.deepcopy(rows[3]))
        elif kind=='trailing': rows.append({'status':'PASS'})
        elif kind=='truncate': args[0]=args[0][:-1]
        elif kind=='commands': args[2]=args[2].replace(b'0 120 counter_balance',b'1 120 counter_balance')
        elif kind=='fixture': args[3]=args[3][:-1]+bytes([args[3][-1]^1])
        elif kind=='screens': args[4]=dict(args[4]);args[4].pop('counter_balance.ppm')
        elif kind=='balance_text': next(r for r in rows if r.get('state')=='counter_balance')['text']='ff'
        elif kind=='buffer': next(r for r in rows if r.get('numeric')=='counter_balance')['buffers'][0]='ff'
        elif kind=='rank': first('numeric')['rank']=8
        elif kind=='rp_bool': first('numeric')['rp']=False
        elif kind=='lifetime': first('numeric')['lifetime']+=1
        elif kind=='owner': first('owner')['owner']='00'*64
        elif kind=='bag': first('inventory_sha256')['inventory_sha256']='0'*64
        elif kind=='party': first('party_sha256')['party_sha256']='0'*64
        elif kind=='ledger': first('ledger_sha256')['ledger_sha256']='0'*64
        elif kind=='counter': first('counter')['counter']+=1
        elif kind=='flash': first('flash_sha256')['flash_sha256']='0'*64
        elif kind=='position': next(r for r in rows if r.get('state')=='counter_balance')['map'][2]+=1
        elif kind=='object': first('objects')['objects']=[]
        elif kind=='result': next(r for r in rows if r.get('state')=='counter_balance')['result']=7
        elif kind=='field': next(r for r in rows if r.get('state')=='counter_balance')['field']=True
        elif kind=='key': first('input')['keys']=1
        elif kind=='frame': first('screen')['frame']+=1
        elif kind=='screen_hash': first('screen')['sha256']='0'*64
        elif kind=='extra_field': first('numeric')['accepted']=True
        elif kind=='scope': rows[-1]['scope']='STANDARD_LIST_COMPLETE'
        elif kind=='host_write': rows[-1]['guarded_host_writes']=1
        elif kind=='save': rows[-1]['transaction_saves']=1
        elif kind=='promotion': rows[-1]['naturally_earned_spending_accepted']=True
        else: raise AssertionError(kind)
        if kind not in ('truncate','commands','fixture','screens'):
            args[0]=b''.join(json.dumps(r).encode()+b'\n' for r in rows)
        with self.assertRaises(ValueError): oracle.validate(*args)
    return test

for _i in (0,1):
    for _kind in ('drop','duplicate','trailing','truncate','commands','fixture','screens','balance_text',
                  'buffer','rank','rp_bool','lifetime','owner','bag','party','ledger','counter','flash',
                  'position','object','result','field','key','frame','screen_hash','extra_field',
                  'scope','host_write','save','promotion'):
        setattr(NativeEvidenceTests,'test_reject_'+_kind+'_'+str(_i),mutation_test(_kind,_i))

if __name__=='__main__': unittest.main()
