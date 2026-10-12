"""新しい保存Continue区間だけの陽性/拒否試験。native再起動なし。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_research_story_continue as m
BASE = ROOT/m.DEV
RAW = (BASE/'progress.stdout.txt').read_bytes()
COLD = (BASE/'continue.stdout.txt').read_bytes()
PARENT = m.load((ROOT/m.PARENT).read_bytes())

def encode(rows):return ('\n'.join(json.dumps(r) for r in rows)+'\n').encode()

class ContinueTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 陽性前提が壊れた状態で負例だけをPASSと数えない。
        m.verify(RAW,COLD,PARENT,m.ROUTE_SAVE)
    def test_real_new_segment_and_cold_continue(self):
        v=m.verify(RAW,COLD,PARENT,m.ROUTE_SAVE)
        self.assertEqual(v['rival_result'],'LOSS_THEN_NORMAL_RECOVERY')
        self.assertEqual(v['first_save']['save_counter'],2)
        self.assertFalse(v['natural_research_arrival_accepted'])
        self.assertFalse(v['rival_victory_accepted'])
    def test_real_closed_commands(self):self.assertEqual(len(m.commands((BASE/'commands.txt').read_text())),101)
    def test_output_identity_not_only_flash(self):
        with self.assertRaises(ValueError):m.verify(RAW,COLD,PARENT,dict(size=131072,sha256=m.ROUTE_SAVE['sha256']))
    def test_output_sha_not_sufficient(self):
        with self.assertRaises(ValueError):m.verify(RAW,COLD,PARENT,dict(size=True,sha256=m.ROUTE_SAVE['sha256']))
    def test_parent_unconfirmed(self):
        p=copy.deepcopy(PARENT);p['actions_completion_confirmed']=False
        with self.assertRaises(ValueError):m.verify(RAW,COLD,p,m.ROUTE_SAVE)
    def test_parent_wrong_run(self):
        p=copy.deepcopy(PARENT);p['run_id']+=1
        with self.assertRaises(ValueError):m.verify(RAW,COLD,p,m.ROUTE_SAVE)
    def test_parent_wrong_artifact(self):
        p=copy.deepcopy(PARENT);p['retained_artifact_id']+=1
        with self.assertRaises(ValueError):m.verify(RAW,COLD,p,m.ROUTE_SAVE)
    def test_parent_overclaim(self):
        p=copy.deepcopy(PARENT);p['natural_research_arrival_accepted']=True
        with self.assertRaises(ValueError):m.verify(RAW,COLD,p,m.ROUTE_SAVE)
    def test_duplicate_json_key(self):
        with self.assertRaises(ValueError):m.verify(RAW.replace(b'"rp":0',b'"rp":0,"rp":10',1),COLD,PARENT,m.ROUTE_SAVE)
    def test_terminal_truncation(self):
        with self.assertRaises((ValueError,KeyError)):m.verify(RAW.rsplit(b'\n',2)[0]+b'\n',COLD,PARENT,m.ROUTE_SAVE)
    def test_missing_screen(self):
        rows=[json.loads(x) for x in RAW.splitlines()];rows.pop(next(i for i,r in enumerate(rows) if 'screen' in r))
        with self.assertRaises(ValueError):m.verify(encode(rows),COLD,PARENT,m.ROUTE_SAVE)
    def test_command_duplicate_observe_zero(self):
        with self.assertRaises(ValueError):m.commands('observe 0\n'+(BASE/'commands.txt').read_text())
    def test_extra_save(self):
        with self.assertRaises(ValueError):m.commands('save\n'+(BASE/'commands.txt').read_text())
    def test_command_injection(self):
        with self.assertRaises(ValueError):m.commands('warp 96 0\n'+(BASE/'commands.txt').read_text())
    def test_command_oversized_key_interval(self):
        with self.assertRaises(ValueError):m.commands('key 1 601\n'+(BASE/'commands.txt').read_text())
    def test_saved_empty(self):
        with self.assertRaises(ValueError):m.verify(RAW,COLD,PARENT,m.identity(b''))


def mutate(name,stream,kind,index,field,value):
    def test(self):
        rows=[json.loads(x) for x in (RAW if stream=='progress' else COLD).splitlines()]
        selected=[r for r in rows if kind in r][index];selected[field]=value
        bad=encode(rows)
        with self.assertRaises((ValueError,KeyError,TypeError)):
            m.verify(bad if stream=='progress' else RAW,bad if stream=='continue' else COLD,PARENT,m.ROUTE_SAVE)
    setattr(ContinueTests,'test_reject_'+name,test)

for args in (
 ('new_game','progress','begin',0,'begin','NEW_GAME_STORY_DEVELOPMENT'),
 ('wrong_starter','progress','begin',0,'initial_save_sha256','a'*64),
 ('wrong_candidate','progress','begin',0,'candidate_sha256','b'*64),
 ('barrier_false','progress','begin',0,'host_write_barriers',False),
 ('injected_RP','progress','observe',8,'rp',10),
 ('extra_party','progress','observe',3,'party_count',2),
 ('extra_save_counter','progress','observe',9,'save_counter',2),
 ('starter_map','progress','observe',0,'map',[96,0]),
 ('starter_party_hash','progress','observe',0,'party_sha256','b'*64),
 ('rival_not_battle','progress','observe',6,'battle_flags',0),
 ('false_victory','progress','observe',11,'battle_outcome',1),
 ('no_recovery','progress','observe',11,'field',False),
 ('recovery_party','progress','observe',11,'party_sha256','c'*64),
 ('wrong_route','progress','observe',14,'map',[96,0]),
 ('tree_warp','progress','observe',16,'xy',[12,70]),
 ('tree_not_message','progress','observe',16,'lock',0),
 ('tree_not_closed','progress','observe',17,'field',False),
 ('counter_reset','progress','ordinary_save',0,'before',0),
 ('counter_jump','progress','ordinary_save',0,'after',3),
 ('wrong_saved_position','progress','observe',20,'xy',[1,15]),
 ('no_new_flash','progress','observe',20,'flash_sha256',PARENT['continued']['flash_sha256']),
 ('input_boolean','progress','input',0,'key',False),
 ('input_gap','progress','input',2,'input',500),
 ('frame_gap','progress','input',2,'frame',3000),
 ('host_write','progress','end',0,'guarded_host_writes',1),
 ('warning','progress','end',0,'warnings_errors',1),
 ('fixture','progress','end',0,'fixture_calls',1),
 ('boolean_terminal','progress','end',0,'fixture_calls',False),
 ('research_overclaim','progress','end',0,'natural_research_arrival_accepted',True),
 ('cold_wrong_input','continue','begin',0,'initial_save_sha256',m.STARTER['sha256']),
 ('cold_wrong_map','continue','observe',0,'map',[4,3]),
 ('cold_wrong_xy','continue','observe',0,'xy',[1,15]),
 ('cold_wrong_live_xy','continue','observe',0,'live_xy',[8,22]),
 ('cold_wrong_facing','continue','observe',0,'facing',1),
 ('cold_wrong_party','continue','observe',0,'party_sha256','d'*64),
 ('cold_wrong_flash','continue','observe',0,'flash_sha256','e'*64),
 ('cold_wrong_ledger','continue','observe',0,'ledger_sha256','f'*64),
 ('cold_wrong_RP','continue','observe',0,'rp',1),
 ('cold_wrong_counter','continue','observe',0,'save_counter',3),
 ('cold_not_idle','continue','observe',0,'lock',1),
 ('cold_stale_battle','continue','observe',0,'battle_flags',12),
 ('cold_stale_result','continue','observe',0,'battle_outcome',2),
 ('cold_screen_pair','continue','screen',0,'screen',1),
):mutate(*args)

if __name__=='__main__':unittest.main()
