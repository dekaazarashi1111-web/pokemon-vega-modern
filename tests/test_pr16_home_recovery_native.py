"""母親回復の新規原本と型/保存/時計/入力/画面の拒否検証。旧受入は実行しない。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_home_recovery_native as m

class HomeRecoveryNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dev=ROOT/m.DEV
        cls.raw=(dev/'progress.stdout.txt').read_bytes();cls.cold=(dev/'continue.stdout.txt').read_bytes()
        cls.parent=m.load((ROOT/m.PARENT).read_bytes());cls.visual=m.load((dev/'visual-review.json').read_bytes())
        cls.commands=(dev/'commands.txt').read_text();cls.cold_commands=(dev/'continue-commands.txt').read_text()

    def verify(self,raw=None,cold=None,parent=None,save=None,visual=None):
        return m.verify(self.raw if raw is None else raw,self.cold if cold is None else cold,
                        self.parent if parent is None else parent,m.OUTPUT_SAVE if save is None else save,
                        self.visual if visual is None else visual)

    def test_positive_complete_scope(self):
        actual=self.verify();expected=m.load((ROOT/m.DEV/'result.json').read_bytes())
        self.assertEqual(actual,expected)
        self.assertTrue(actual['ordinary_recovery_accepted']);self.assertFalse(actual['travel_native_accepted'])

    def test_complete_progress_commands(self):m.command_trace(self.commands,self.raw)
    def test_complete_cold_commands(self):m.command_trace(self.cold_commands,self.cold,True)

    def test_saved_clock_minute32_sha(self):
        self.assertEqual(m.identity(m.ledger(32))['sha256'],'8a96b5fea1de1cd063092537ceb3841175fd6065f59e960b09c07612d031c877')

    def test_cold_clock_minute33_sha(self):
        self.assertEqual(m.identity(m.ledger(33))['sha256'],'8e4b77c9acd97c5e65fadb0c856ba81d247d11da288c652e1088a3bd860f7103')

    def test_clock_only5bytes(self):
        a,b=m.ledger(32),m.ledger(33)
        self.assertEqual([i for i,(x,y) in enumerate(zip(a,b)) if x!=y],[8,9,10,11,0x746])

    def test_clock_bool_rejected(self):
        with self.assertRaises(ValueError):m.ledger(True)

    def test_clock_undeclared_minute_rejected(self):
        with self.assertRaises(ValueError):m.ledger(34)

    def test_save_identity_rejected(self):
        with self.assertRaises(ValueError):self.verify(save={'size':131088,'sha256':'0'*64})

    def test_save_bytes_mutable_rejected(self):
        with self.assertRaises(ValueError):m.saved_bytes(bytearray(),b'',b'')

    def test_save_bytes_wrong_identity_rejected(self):
        with self.assertRaises(ValueError):m.saved_bytes(b'x'*131088,b'x'*131088,b'x'*131088)

    def test_unconfirmed_parent_rejected(self):
        p=copy.deepcopy(self.parent);p['actions_completion_confirmed']=False
        with self.assertRaises(ValueError):self.verify(parent=p)

    def test_wrong_parent_run_rejected(self):
        p=copy.deepcopy(self.parent);p['run_id']+=1
        with self.assertRaises(ValueError):self.verify(parent=p)

    def test_promoted_parent_rejected(self):
        p=copy.deepcopy(self.parent);p['release_ready']=True
        with self.assertRaises(ValueError):self.verify(parent=p)

    def test_fake_parent_save_rejected(self):
        p=copy.deepcopy(self.parent);p['output_save']['sha256']='0'*64
        with self.assertRaises(ValueError):self.verify(parent=p)

    def test_visual_anchor_swap_rejected(self):
        v=copy.deepcopy(self.visual);v['anchors']['stats']['sha256']='0'*64
        with self.assertRaises(ValueError):self.verify(visual=v)

    def test_visual_anchor_missing_rejected(self):
        v=copy.deepcopy(self.visual);del v['anchors']['stats']
        with self.assertRaises(ValueError):self.verify(visual=v)

    def test_fake_ocr_review_rejected(self):
        v=copy.deepcopy(self.visual);v['method']='OCR'
        with self.assertRaises(ValueError):self.verify(visual=v)

    def test_unknown_command_rejected(self):
        with self.assertRaises(ValueError):m.command_trace('inject\n'+self.commands,self.raw)

    def test_missing_command_rejected(self):
        with self.assertRaises(ValueError):m.command_trace(self.commands.replace('key 64 16\n','',1),self.raw)

    def test_added_save_rejected(self):
        with self.assertRaises(ValueError):m.command_trace(self.commands.replace('quit\n','save\nquit\n'),self.raw)

    def test_cold_save_rejected(self):
        with self.assertRaises(ValueError):m.command_trace(self.cold_commands.replace('quit\n','save\nquit\n'),self.cold,True)

    def test_swapped_command_rejected(self):
        with self.assertRaises(ValueError):m.command_trace(self.commands.replace('key 64 16','key 32 16'),self.raw)

    def test_missing_observation_command_rejected(self):
        with self.assertRaises(ValueError):m.command_trace(self.commands.replace('observe 5\n',''),self.raw)

    def test_duplicate_json_key_rejected(self):
        with self.assertRaises(ValueError):self.verify(raw=self.raw.replace(b'"fixture_calls":0',b'"fixture_calls":0,"fixture_calls":0'))

    def test_truncated_terminal_rejected(self):
        with self.assertRaises(ValueError):self.verify(raw=b'\n'.join(self.raw.splitlines()[:-1]))

    def test_extra_row_rejected(self):
        with self.assertRaises(ValueError):self.verify(raw=self.raw+b'{"unbound":1}\n')

    def test_new_game_mode_rejected(self):
        with self.assertRaises(ValueError):self.verify(raw=self.raw.replace(b'INDEPENDENT_CONTINUE',b'NEW_GAME_STORY_DEVELOPMENT'))


def mutation(which,kind,index,key,value):
    def test(self):
        rows=[json.loads(x) for x in (self.cold if which=='cold' else self.raw).splitlines()]
        targets=[r for r in rows if kind in r]
        targets[index][key]=value
        raw=('\n'.join(json.dumps(x,separators=(',',':')) for x in rows)+'\n').encode()
        with self.assertRaises(ValueError):self.verify(**{which:raw})
    return test

mutants=[
 ('raw','begin',0,'candidate_sha256','0'*64),('raw','begin',0,'initial_save_sha256','0'*64),
 ('cold','begin',0,'initial_save_sha256','0'*64),('raw','begin',0,'host_write_barriers',6),
 ('raw','end',0,'warnings_errors',1),('raw','end',0,'warnings_errors',False),
 ('raw','end',0,'fixture_calls',1),('raw','end',0,'fixture_calls',False),
 ('raw','end',0,'guarded_host_writes',1),('raw','end',0,'guarded_host_writes',False),
 ('raw','end',0,'natural_research_arrival_accepted',True),('raw','end',0,'natural_research_arrival_accepted',0),
 ('raw','end',0,'inputs',80),('cold','end',0,'frames',2573),
 ('raw','observe',2,'xy',[8,6]),('raw','observe',6,'party_sha256','0'*64),
 ('raw','observe',5,'party_sha256',m.AFTER_PARTY),('raw','observe',17,'flash_sha256',m.AFTER_FLASH),
 ('raw','observe',18,'save_counter',5),('raw','observe',6,'rp',1),('raw','observe',6,'party_count',2),
 ('raw','observe',6,'battle_flags',4),('raw','observe',6,'battle_outcome',1),
 ('raw','observe',3,'facing',1),('raw','observe',3,'lock',0),('raw','observe',17,'lock',1),
 ('raw','observe',17,'field',False),('raw','observe',6,'ledger_sha256','0'*64),
 ('cold','observe',3,'ledger_sha256',m.identity(m.ledger(32))['sha256']),
 ('cold','observe',0,'party_sha256','0'*64),('cold','observe',4,'flash_sha256','0'*64),
 ('cold','observe',6,'save_counter',7),('cold','observe',6,'rp',1),('cold','observe',6,'map',[3,0]),
 ('cold','observe',6,'facing',1),('cold','observe',6,'battle_outcome',1),('cold','observe',6,'lock',1),
 ('raw','ordinary_save',0,'after',7),('raw','ordinary_save',0,'before',4),('raw','ordinary_save',0,'ordinary_save',1),
 ('raw','input',13,'key',32),('raw','input',14,'frames',True),('raw','screen',13,'screen',True),
 ('raw','screen',15,'sha256','0'*64),('cold','screen',4,'sha256','0'*64)
]
for i,args in enumerate(mutants):setattr(HomeRecoveryNativeTests,'test_reject_%02d_%s_%s_%s'%(i,args[0],args[1],args[3]),mutation(*args))

if __name__=='__main__':unittest.main()
