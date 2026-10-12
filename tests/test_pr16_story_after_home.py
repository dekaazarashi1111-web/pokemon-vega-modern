"""新規区間だけ。各否定検査は元の陽性が通ることを先に確認する。"""
import copy
import json
import os
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_story_after_home as m


class AfterHome(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.environ.get('PR16_AFTER_HOME_PRIVATE'):
            raise unittest.SkipTest('専用workflowの固定private artifact供給時だけ検証。一般CIで受入済み区間を再実行しない。')
        cls.where=Path(os.environ.get('PR16_AFTER_HOME_EVIDENCE',str(m.ROOT/m.DEV)))
        cls.raw=(cls.where/'progress.stdout.txt').read_bytes()
        cls.cold=(cls.where/'continue.stdout.txt').read_bytes()
        cls.cmd=(m.ROOT/m.DEV/'commands.txt').read_bytes()
        cls.ccmd=(m.ROOT/m.DEV/'continue-commands.txt').read_bytes()
        cls.parent=m.load((m.ROOT/m.PARENT).read_bytes())
        cls.expected=m.load((cls.where/'expectations.json').read_bytes())

    def positive(self):
        return m.verify(self.raw,self.cold,self.cmd,self.ccmd,self.parent,self.expected)

    def test_positive_whole_scope(self):
        result=self.positive()
        self.assertEqual(result['trainer_victories'],0)
        self.assertEqual(result['ordinary_saves'],1)
        self.assertFalse(result['natural_research_arrival_accepted'])

    def test_positive_cold_has_no_resave(self):
        self.positive()
        t=m.trace(self.cold,self.ccmd,True)
        self.assertEqual({r['save_counter'] for r in t['observations']},{7})

    def test_duplicate_json(self):
        self.positive()
        with self.assertRaisesRegex(ValueError,'重複'):
            m.trace(self.raw.replace(b'"host_write_barriers":7',b'"host_write_barriers":7,"host_write_barriers":7',1),self.cmd)

    def test_nonfinite_json(self):
        self.positive()
        with self.assertRaises(ValueError):m.load('{"x":NaN}')

    def test_truncated_trace(self):
        self.positive()
        with self.assertRaises(ValueError):m.trace(self.raw.rsplit(b'\n',2)[0]+b'\n',self.cmd)

    def test_extra_trace(self):
        self.positive()
        with self.assertRaises(ValueError):m.trace(self.raw+b'{}\n',self.cmd)

    def test_helper_save_forbidden(self):
        self.positive()
        with self.assertRaises(ValueError):m.commands(self.cmd.replace(b'quit\n',b'save\nquit\n'))

    def test_blank_anchor_forbidden(self):
        self.positive()
        value=m.PPM_HEADER+b'\0'*(240*160*3);screen={'sha256':m.identity(value)['sha256']}
        m.screen_bytes(value,screen,True)
        with self.assertRaisesRegex(ValueError,'空画面'):m.screen_bytes(value,screen)

    def test_fake_pixel_hash(self):
        self.positive()
        value=m.PPM_HEADER+bytes(range(256))*450
        m.screen_bytes(value,{'sha256':m.identity(value)['sha256']})
        with self.assertRaisesRegex(ValueError,'SHA'):m.screen_bytes(value,{'sha256':'0'*64})

    def test_parent_not_terminal(self):
        self.positive();p=copy.deepcopy(self.parent);p['actions_completion_confirmed']=False
        with self.assertRaises(ValueError):m.verify(self.raw,self.cold,self.cmd,self.ccmd,p,self.expected)

    def test_wrong_parent_save(self):
        self.positive();p=copy.deepcopy(self.parent);p['output_save']=m.OUTPUT_SAVE
        with self.assertRaises(ValueError):m.parent_boundary(p)

    def test_no_victory_promotion(self):
        self.positive();e=copy.deepcopy(self.expected);e['claims']['trainer_victories']=1
        with self.assertRaisesRegex(ValueError,'昇格'):m.verify(self.raw,self.cold,self.cmd,self.ccmd,self.parent,e)

    def test_no_research_promotion(self):
        self.positive();e=copy.deepcopy(self.expected);e['claims']['research_arrival']=True
        with self.assertRaisesRegex(ValueError,'昇格'):m.verify(self.raw,self.cold,self.cmd,self.ccmd,self.parent,e)

    def test_ui_pair_swap(self):
        self.positive();e=copy.deepcopy(self.expected);e['ui_pairs'][0][1]=5
        with self.assertRaises(ValueError):m.verify(self.raw,self.cold,self.cmd,self.ccmd,self.parent,e)

    def test_anchor_changed(self):
        self.positive();e=copy.deepcopy(self.expected);next(iter(e['anchors'].values()))['sha256']='0'*64
        with self.assertRaises(ValueError):m.verify(self.raw,self.cold,self.cmd,self.ccmd,self.parent,e)

    def test_original_hash_changed(self):
        self.positive();e=copy.deepcopy(self.expected);e['files']['progress.stdout.txt']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'全原本'):m.verify(self.raw,self.cold,self.cmd,self.ccmd,self.parent,e)

    def test_saved_bytes_and_three_corruptions(self):
        self.positive()
        folder=Path(os.environ['PR16_AFTER_HOME_PRIVATE'])
        a=(folder/'recovery.srm').read_bytes();b=(folder/'story.srm').read_bytes();c=(folder/'cold.srm').read_bytes()
        proof=m.saved_bytes(a,b,c)
        self.assertEqual(proof['other_party_bytes_preserved'],597)
        for index in (90168+36,0x1f064+0x746,131087):
            with self.subTest(index=index):
                changed=bytearray(c);changed[index]^=1
                with self.assertRaises(ValueError):m.saved_bytes(a,b,bytes(changed))


def corruption(kind,key,value):
    def test(self):
        self.positive()
        rows=[m.load(x) for x in self.raw.splitlines()]
        index={'begin':0,'input':1,'observe':13,'screen':14,'end':len(rows)-1}[kind]
        rows[index][key]=value
        bad=('\n'.join(json.dumps(x,separators=(',',':')) for x in rows)+'\n').encode()
        with self.assertRaises(ValueError):m.trace(bad,self.cmd)
    return test


for i,(kind,key,value) in enumerate([
 ('begin','begin','NEW_GAME_STORY_DEVELOPMENT'),('begin','host_write_barriers',True),
 ('begin','candidate_sha256','0'*64),('begin','initial_save_sha256','0'*64),('begin','extra',0),
 ('input','input',True),('input','frame',1),('input','key',3),('input','frames',0),('input','extra',0),
 ('observe','observe',True),('observe','frame',1391),('observe','field',1),('observe','lock',2),
 ('observe','map',[4]),('observe','xy',[True,5]),('observe','live_xy',[8,5]),('observe','party_count',7),
 ('observe','rp',False),('observe','save_counter',True),('observe','battle_flags',False),
 ('observe','party_sha256','x'*64),('observe','extra',0),
 ('screen','screen',True),('screen','frame',1391),('screen','sha256','0'),('screen','extra',0),
 ('end','warnings_errors',1),('end','fixture_calls',1),('end','guarded_host_writes',1),
 ('end','host_write_barriers',6),('end','inputs',269),('end','frames',0),
 ('end','natural_research_arrival_accepted',True),('end','fixture_calls',False),('end','extra',0)
]):setattr(AfterHome,'test_corrupt_%02d_%s_%s'%(i,kind,key),corruption(kind,key,value))


if __name__=='__main__':unittest.main()
