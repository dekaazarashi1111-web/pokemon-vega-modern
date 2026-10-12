"""保存済み新規原本に対する4陽性と改変拒否。native/compileは一切起動しない。"""
from copy import deepcopy
import json
import os
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_connection_oracle as o
BASE=ROOT/'content/modernization/pr16_research_connection_evidence'

class OracleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture=(ROOT/os.environ.get('PR16_CONNECTION_FIXTURE','.local/pr16-research-connection-accept/fixture.srm')).read_bytes()
        cls.proof={}
        for case in o.COMMANDS:
            p=BASE/'36285051878' if case=='ecology' else BASE/'36284847516'/case
            cls.proof[case]=dict(raw=(p/'stdout.txt').read_bytes(),commands=(p/'commands.txt').read_bytes(),screens=o.load((p/'measurement.json').read_bytes())['screens'])
    def run_case(self,case='lab',raw=None,commands=None,fixture=None,screens=None):
        p=self.proof[case]
        return o.validate(p['raw'] if raw is None else raw,case,p['commands'] if commands is None else commands,self.fixture if fixture is None else fixture,p['screens'] if screens is None else screens)
    def mutate(self,selector,key,value):
        rows=[o.load(line) for line in self.proof['lab']['raw'].splitlines()]
        found=[r for r in rows if all(r.get(k)==v for k,v in selector.items())]
        self.assertEqual(len(found),1);found[0][key]=value
        return b''.join((json.dumps(r,separators=(',',':'))+'\n').encode() for r in rows)
    def rejected(self,**kwargs):
        with self.assertRaises(ValueError):self.run_case(**kwargs)
    def test_raw_requires_bytes(self):self.rejected(raw=self.proof['lab']['raw'].decode())
    def test_missing_newline(self):self.rejected(raw=self.proof['lab']['raw'].rstrip(b'\n'))
    def test_missing_terminal(self):self.rejected(raw=b'\n'.join(self.proof['lab']['raw'].splitlines()[:-1])+b'\n')
    def test_extra_row(self):self.rejected(raw=self.proof['lab']['raw']+b'{}\n')
    def test_unknown_row(self):self.rejected(raw=b'{}\n'+self.proof['lab']['raw'])
    def test_duplicate_json_key(self):
        raw=self.proof['lab']['raw'].replace(b'"state":"fixture"',b'"state":"fixture","state":"fixture"',1)
        self.assertNotEqual(raw,self.proof['lab']['raw']);self.rejected(raw=raw)
    def test_nonfinite_json(self):self.rejected(raw=b'{"bad":NaN}\n'+self.proof['lab']['raw'])
    def test_oversized_raw(self):self.rejected(raw=b' '*100000+b'\n')
    def test_changed_command_file(self):self.rejected(commands=self.proof['lab']['commands']+b'0 0 end\n')
    def test_changed_input_keys(self):self.rejected(raw=self.mutate({'input':1},'keys',32))
    def test_changed_input_duration(self):self.rejected(raw=self.mutate({'input':1},'frames',41))
    def test_input_boolean(self):self.rejected(raw=self.mutate({'input':1},'input',True))
    def test_input_extra_field(self):self.rejected(raw=self.mutate({'input':1},'warp',True))
    def test_missing_screen(self):
        screens=deepcopy(self.proof['lab']['screens']);del screens['counter_balance.ppm'];self.rejected(screens=screens)
    def test_screen_extra_member(self):
        screens=deepcopy(self.proof['lab']['screens']);screens['unreviewed.ppm']=screens['end.ppm'];self.rejected(screens=screens)
    def test_screen_size(self):
        screens=deepcopy(self.proof['lab']['screens']);screens['end.ppm']['size']=1;self.rejected(screens=screens)
    def test_screen_boolean_size(self):
        screens=deepcopy(self.proof['lab']['screens']);screens['end.ppm']['size']=True;self.rejected(screens=screens)
    def test_screen_digest(self):
        screens=deepcopy(self.proof['lab']['screens']);screens['end.ppm']['sha256']='0'*64;self.rejected(screens=screens)
    def test_screen_frame(self):self.rejected(raw=self.mutate({'screen':'counter_balance'},'frame',1))
    def test_screen_extra_claim(self):self.rejected(raw=self.mutate({'screen':'counter_balance'},'balance_displayed',True))
    def test_live_player_position(self):
        rows=[o.load(line) for line in self.proof['lab']['raw'].splitlines()];rows[3]['objects'][0][4]+=1
        self.rejected(raw=b''.join((json.dumps(r)+'\n').encode() for r in rows))
    def test_live_host_position(self):
        rows=[o.load(line) for line in self.proof['lab']['raw'].splitlines()]
        i=next(i for i,r in enumerate(rows) if r.get('state')=='counter_intro')
        host=next(v for v in rows[i+3]['objects'] if v[1]==4);host[4]+=1
        self.rejected(raw=b''.join((json.dumps(r)+'\n').encode() for r in rows))
    def test_old_ecology_non_observation_rejected(self):
        p=BASE/'36284847516/ecology'
        self.rejected(case='ecology',raw=(p/'stdout.txt').read_bytes(),commands=(p/'commands.txt').read_bytes(),screens=o.load((p/'measurement.json').read_bytes())['screens'])

# Separate unittest IDs make all 64 owner-byte boundaries and all promoted claims visible.
def positive(case):
    def test(self):
        result=self.run_case(case=case)
        self.assertEqual(result['status'],'PASS_PHYSICAL_DOOR_AND_STATIC_GUIDE_SCOPED')
        self.assertFalse(result['counter_numeric_display_accepted'])
        self.assertFalse(result['natural_story_progress_accepted'])
        self.assertFalse(result['naturally_earned_spending_accepted'])
    return test
for case in o.COMMANDS:setattr(OracleTests,'test_positive_'+case,positive(case))

def owner_mutation(index):
    def test(self):
        rows=[o.load(line) for line in self.proof['lab']['raw'].splitlines()]
        owner=bytearray.fromhex(rows[1]['owner']);owner[index]^=1
        self.rejected(raw=self.mutate({'event':'fixture'},'owner',owner.hex()))
    return test
for index in range(64):setattr(OracleTests,f'test_owner_byte_{index:02d}',owner_mutation(index))

def field_mutation(selector,key,value):
    def test(self):self.rejected(raw=self.mutate(selector,key,value))
    return test
MUTATIONS={
 'state':('counter_intro',{'frame':True,'command':False,'map':[98,3,6,5],'facing':1,'field':True,'callback':0,'result':1,'shop_active':True,'eligible':1,'window':0,'flash_sha256':'0'*64,'text':'ff','extra':0}),
 'event':('fixture',{'counter':3,'item_quantity':1,'inventory_sha256':'0'*64,'other_inventory_sha256':'0'*64,'party_sha256':'0'*64,'party_count':1,'extra':0}),
 'ledger_event':('fixture',{'version':1,'size':2047,'checksum_valid':1,'ledger_sha256':'0'*64,'unrelated_ledger_sha256':'0'*64,'migration_dirty':1,'recovery_blocked':1,'extra':0}),
 'status':('MEASURED',{'status':'PASS','scope':'NATURAL_STORY','case':True,'fresh_cores':2,'commands':1,'screens':1,'guarded_host_writes':1,'manual_saves':1,'transaction_saves':1,'accepted_case_reruns':1,'natural_story_progress_accepted':True,'naturally_earned_spending_accepted':True,'warnings_errors':1,'extra':0})}
for selector,(label,fields) in MUTATIONS.items():
    for key,value in fields.items():setattr(OracleTests,'test_reject_'+selector+'_'+key,field_mutation({selector:label},key,value))

def fixture_mutation(index):
    def test(self):
        raw=bytearray(self.fixture);raw[index]^=1;self.rejected(fixture=bytes(raw))
    return test
for index in (0,1,0x1f064,0x1f064+8,0x1f064+0x73f,0x1f064+2047,131071):setattr(OracleTests,'test_fixture_byte_'+str(index),fixture_mutation(index))

if __name__=='__main__':unittest.main()
