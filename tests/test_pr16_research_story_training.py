"""新規入力原本への拒否試験。受入済みnativeや旧unitは呼ばない。"""
from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_story_training as m
DEV=ROOT/m.DEV
RAW=(DEV/'progress.stdout.txt').read_bytes()
COLD=(DEV/'continue.stdout.txt').read_bytes()
PARENT=m.load((ROOT/m.PARENT).read_bytes())
ROWS=m.old.prior.load_rows(RAW)
CROWS=m.old.prior.load_rows(COLD)
COMMAND=(DEV/'commands.txt').read_text()
CCOMMAND=(DEV/'continue-commands.txt').read_text()

def dump(rows):return ('\n'.join(json.dumps(x,ensure_ascii=False,separators=(',',':')) for x in rows)+'\n').encode()
def run(raw=RAW,cold=COLD,parent=PARENT,saved=m.OUTPUT_SAVE):return m.verify(raw,cold,parent,saved)
def obs(rows,index):return next(x for x in rows if x.get('observe')==index)
def image(rows,index):return next(x for x in rows if x.get('screen')==index)

class Training(unittest.TestCase):
    def test_complete_new_original(self):
        result=run()
        self.assertEqual(result['status'],'PASS_NATURAL_LV7_ABSORB_SAVE_SCOPED')
        self.assertEqual(result,m.load((DEV/'result.json').read_bytes()))
        self.assertEqual((result['level'],result['experience'],result['experience_gain']),(7,245,41))
        self.assertEqual(result['hp'],[13,23])
        self.assertEqual(result['moves_pp'],[31,30,25])
        self.assertIs(result['ordinary_recovery_accepted'],False)
        self.assertIs(result['natural_research_arrival_accepted'],False)
    def test_complete_command_bindings(self):
        m.command_trace(COMMAND,RAW);m.command_trace(CCOMMAND,COLD,True)
    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):run(RAW.replace(b'"host_write_barriers":7',b'"host_write_barriers":7,"host_write_barriers":7',1))
    def test_unknown_command(self):
        with self.assertRaises(ValueError):m.commands('write32 1 2\nquit\n')
    def test_reject_savestate(self):
        with self.assertRaises(ValueError):m.commands('loadState old\nquit\n')
    def test_command_input_mismatch(self):
        with self.assertRaises(ValueError):m.command_trace(COMMAND.replace('key 128 48','key 128 47',1),RAW)
    def test_command_observation_order(self):
        with self.assertRaises(ValueError):m.commands(COMMAND.replace('observe 1\n','observe 2\n',1))
    def test_extra_save(self):
        with self.assertRaises(ValueError):m.commands(COMMAND.replace('quit\n','save\nquit\n'))
    def test_cold_save_forbidden(self):
        with self.assertRaises(ValueError):m.commands(CCOMMAND.replace('quit\n','save\nquit\n'),True)
    def test_no_explicit_quit(self):
        with self.assertRaises(ValueError):m.commands(COMMAND[:-5])
    def test_raw_truncated(self):
        with self.assertRaises((ValueError,KeyError)):run(dump(ROWS[:-1]))
    def test_raw_unknown_row(self):
        x=deepcopy(ROWS);x.insert(-1,{'write32':123})
        with self.assertRaises(ValueError):run(dump(x))
    def test_missing_screen(self):
        x=deepcopy(ROWS);x.remove(image(x,30))
        with self.assertRaises(ValueError):run(dump(x))
    def test_extra_screen(self):
        x=deepcopy(ROWS);x.insert(-1,deepcopy(image(x,30)))
        with self.assertRaises(ValueError):run(dump(x))
    def test_output_rtc_identity(self):
        with self.assertRaises(ValueError):run(saved={**m.OUTPUT_SAVE,'size':131072})
    def test_output_digest(self):
        with self.assertRaises(ValueError):run(saved={**m.OUTPUT_SAVE,'sha256':'0'*64})
    def test_zero_rp_not_healed(self):
        self.assertEqual(obs(ROWS,31)['party_sha256'],obs(ROWS,42)['party_sha256'])
        self.assertNotEqual(obs(ROWS,0)['party_sha256'],obs(ROWS,42)['party_sha256'])
    def test_sparse_diagnostic_parser(self):
        # ROM全体ではなく、公開された固定pointer鎖の合成fixture。nativeの証拠にしない。
        raw=bytearray(33554432)
        def put(addr,body):raw[addr-0x08000000:addr-0x08000000+len(body)]=body
        def ptr(addr,value):put(addr,value.to_bytes(4,'little'))
        ptr(0x08054b0c,0x092c5194);ptr(0x092c51a4,0x083164ac);ptr(0x083164ac,0x08314e00)
        ptr(0x08314e04,0x0837d764);put(0x0837d764,b'\1');ptr(0x0837d768,0x0837d720)
        put(0x0837d720,bytes.fromhex('01580000080004000309000000000000d00c220900000000'))
        put(0x09220cd0,bytes.fromhex('6a5a235d0c22092b2c080601040d22092b24080600f80c22092b4b110600f80c220905040d2209'))
        put(0x09220cf8,bytes.fromhex('0f00af0c220909046c02'));put(0x09220caf,b'text\xff')
        source=(ROOT/m.BUILDER).read_text()
        data=bytes(raw)
        with patch.object(m,'CANDIDATE',m.identity(data)):
            result=m.diagnose(data,source)
            self.assertEqual(result['object']['xy'],[8,4])
            self.assertIs(result['native_recovery_accepted'],False)
            with self.assertRaises(ValueError):m.diagnose(data,source.replace('VEGA_PORTAL_MAP = (4, 0)','VEGA_PORTAL_MAP = (4, 3)'))
            raw[0x037d720]=2
            with self.assertRaises(ValueError):m.diagnose(bytes(raw),source)

# 各testは原本を複写し1要素だけ変える。全native処理・旧検査は実行しない。
def mutation(name,where,key,value,cold=False):
    def test(self):
        rows=deepcopy(CROWS if cold else ROWS)
        if where=='start':row=rows[0]
        elif where=='end':row=rows[-1]
        elif where=='save':row=next(x for x in rows if 'ordinary_save' in x)
        elif isinstance(where,tuple) and where[0]=='screen':row=image(rows,where[1])
        else:row=obs(rows,where)
        row[key]=value
        with self.assertRaises(ValueError):
            run(cold=dump(rows)) if cold else run(raw=dump(rows))
    test.__name__='test_reject_'+name
    setattr(Training,test.__name__,test)

for name,where,key,value in [
 ('candidate','start','candidate_sha256','0'*64),('parent_save','start','initial_save_sha256','0'*64),
 ('host_barriers','start','host_write_barriers',6),('input_count','end','inputs',193),('frame_count','end','frames',19043),
 ('host_write','end','guarded_host_writes',1),('fixture','end','fixture_calls',1),('warnings','end','warnings_errors',1),
 ('warnings_bool','end','warnings_errors',False),('writes_bool','end','guarded_host_writes',False),('fixture_bool','end','fixture_calls',False),
 ('research_claim','end','natural_research_arrival_accepted',True),('research_alias','end','natural_research_arrival_accepted',0),
 ('counter_start',0,'save_counter',3),('initial_party',0,'party_sha256','0'*64),('rp',20,'rp',1),('party_count',20,'party_count',2),
 ('trainer_flags',20,'battle_flags',12),('wild_position',20,'xy',[25,13]),('wild_lock',20,'lock',0),
 ('false_victory',26,'battle_outcome',1),('false_escape',31,'battle_outcome',4),('false_loss',31,'battle_outcome',2),
 ('home_owner',40,'map',[4,3]),('home_coordinate',40,'xy',[7,5]),('home_facing',40,'facing',1),
 ('invented_heal',42,'party_sha256',obs(ROWS,0)['party_sha256']),('wrong_save_map',48,'map',[96,0]),
 ('busy_save',48,'lock',1),('not_field',48,'field',False),('save_counter','save','after',6),
 ('save_bool','save','ordinary_save',1),('screen_bool',('screen',1),'screen',True),
 ('learned_anchor',('screen',30),'sha256','0'*64),('home_dialogue',('screen',40),'sha256','0'*64),
 ('pp_anchor',('screen',45),'sha256','0'*64),('screenshot_frame',('screen',30),'frame',0),
 ('map_route',12,'map',[96,5]),('extra_save_early',47,'save_counter',5),
 ]:mutation(name,where,key,value)
for key,value in [('party_sha256','0'*64),('flash_sha256','0'*64),('ledger_sha256','0'*64),('save_counter',4),
                  ('rp',1),('party_count',2),('map',[3,19]),('xy',[5,27]),('live_xy',[12,34]),('facing',2),
                  ('battle_flags',4),('battle_outcome',1)]:
    mutation('cold_'+key,6,key,value,True)
mutation('cold_wrong_save','start','initial_save_sha256',m.INPUT_SAVE['sha256'],True)
for i in range(2,6):mutation('cold_ui_'+str(i),('screen',i),'sha256','0'*64,True)

def parent_test(key,value):
    def test(self):
        parent=deepcopy(PARENT);parent[key]=value
        with self.assertRaises(ValueError):run(parent=parent)
    return test
for key,value in [('status','PASS'),('actions_completion_confirmed',False),('run_id',1),('source_head','0'*40),
                  ('retained_artifact_id',1),('trainer_victories',1),('trainer_victories',False),
                  ('native_bag_potion_count',1),('full_story_accepted',True),('natural_research_arrival_accepted',True),
                  ('release_ready',True),('active_baseline_changed',True)]:
    setattr(Training,'test_parent_'+key+'_'+str(value),parent_test(key,value))

if __name__=='__main__':unittest.main()
