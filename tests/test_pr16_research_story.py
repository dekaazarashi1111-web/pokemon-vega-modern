"""新story protocolだけの独立oracle/拒否検査。native起動や旧受入再実行なし。"""
import copy
import json
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_story as m
BASE=ROOT/'content/modernization/pr16_research_story_development'
RAW=(BASE/'stdout.txt').read_bytes()
ROWS=[json.loads(x) for x in RAW.splitlines()]
C=(ROOT/m.C).read_text()

def encode(rows):return ('\n'.join(json.dumps(x) for x in rows)+'\n').encode()

class StoryTests(unittest.TestCase):
    def test_real_development_trace(self):
        v=m.observations(RAW);self.assertEqual((len(v['inputs']),len(v['observations']),len(v['saves'])),(421,18,1))
        self.assertEqual(v['observations'][-1]['party_count'],1)
    def test_source_and_generation(self):
        m.source_check(C);s=m.generate();self.assertEqual(s.count(b'int main(int argc,char**argv){'),1)
        self.assertIn(m.CANDIDATE['sha256'].encode(),s)
    def test_real_commands(self):self.assertEqual(len(m.commands((BASE/'commands.txt').read_text())),187)
    def test_schema_duplicate(self):
        with self.assertRaises(ValueError):m.observations(RAW.replace(b'"key":0',b'"key":0,"key":1',1))
    def test_truncated(self):
        with self.assertRaises((ValueError,KeyError)):m.observations(RAW.rsplit(b'\n',2)[0]+b'\n')
    def test_removed_screen(self):
        r=copy.deepcopy(ROWS);r.pop(next(i for i,x in enumerate(r) if 'screen' in x))
        with self.assertRaises(ValueError):m.observations(encode(r))
    def test_invalid_commands(self):
        for text in ('','key 1 601\nquit\n','key 3 2\nquit\n','key 1 -1\nquit\n','warp 4 3\nquit\n','quit\nquit\n','observe 2\nobserve 1\nquit\n','save\n','key 1 2 extra\nquit\n'):
            with self.subTest(text=text),self.assertRaises(ValueError):m.commands(text)
    def test_blank_video_rejected(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            for r in ROWS:
                if 'screen' in r:(p/f"screen-{r['screen']:04}.ppm").write_bytes(b'P6\n240 160\n255\n'+bytes(240*160*3))
            with self.assertRaises(ValueError):m.observations(RAW,screens=p)
    def test_unit_only_retention_positive(self):
        # 合成Continueはvalidator単体テスト専用。実測/受入件数には含めない。
        v=m.observations(RAW);b=copy.deepcopy(v);b['saves']=[];b['start']['initial_save_sha256']='a'*64
        self.assertTrue(m.retained(v,b)['natural_starter_accepted'])


def mutation(name,selector,field,value):
    def test(self):
        r=copy.deepcopy(ROWS);next(x for x in r if selector in x)[field]=value
        with self.assertRaises((ValueError,KeyError,TypeError)):m.observations(encode(r))
    setattr(StoryTests,'test_reject_'+name,test)
for name,sel,field,val in (
 ('candidate','begin','candidate_sha256','f'*64),('initial_fixture','begin','initial_save_sha256','f'*64),
 ('barrier','begin','host_write_barriers',0),('begin_claim','begin','begin','PASS'),
 ('input_id','input','input',1),('input_frame','input','frame',1),('key_combination','input','key',3),
 ('key_bool','input','key',True),('frames_zero','input','frames',0),('frames_overflow','input','frames',601),
 ('input_bool','input','input',False),('frame_bool','input','frame',False),
 ('observe_frame','observe','frame',4),('observe_schema','observe','unseen',3),
 ('party_overflow','observe','party_count',7),('RP_overflow','observe','rp',10000),
 ('coord_bool','observe','xy',[True,2]),('party_digest','observe','party_sha256','G'*64),
 ('field_bool','observe','field',1),('screen_frame','screen','frame',0),('screen_pair','screen','screen',3),
 ('save_jump','ordinary_save','after',2),('save_bool','ordinary_save','before',False),
 ('end_frame','end','frames',1),('end_count','end','inputs',1),('warning','end','warnings_errors',1),
 ('host_write','end','guarded_host_writes',1),('fixture','end','fixture_calls',1),('overclaim','end','natural_research_arrival_accepted',True)):
    mutation(name,sel,field,val)

def bad_call(token):
    def test(self):
        with self.assertRaises(ValueError):m.source_check(C.replace(' st_observe(c,0);',' '+token+'(c,0);st_observe(c,0);'))
    setattr(StoryTests,'test_source_reject_'+token,test)
for name in ('write8','write16','write32','write_register','call_preserving','si_call','si_restore','loadState','putPixels','system','accepted_newgame_main','qol_open'):
    bad_call(name)

def retention_mutation(key,value):
    def test(self):
        a=m.observations(RAW);b=copy.deepcopy(a);b['saves']=[];b['start']['initial_save_sha256']='a'*64;b['observations'][-1][key]=value
        with self.assertRaises(ValueError):m.retained(a,b)
    setattr(StoryTests,'test_continue_reject_'+key,test)
for key,value in (('map',[96,0]),('xy',[1,1]),('party_count',0),('save_counter',2),('rp',100),('flash_sha256','a'*64),('party_sha256','b'*64),('field',False),('lock',1)):
    retention_mutation(key,value)

if __name__=='__main__':unittest.main()
