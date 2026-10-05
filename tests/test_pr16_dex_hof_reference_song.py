"""ROMを含めず、有限JP root条件と新旧role競合を合成して検査。"""
import copy,json,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_reference_song as m

class RootTests(unittest.TestCase):
 def setUp(self):
  self.review=json.loads((m.ROOT/m.REVIEW).read_bytes());self.review['sources']=[]
  self.words={r['address']:r['value']for r in self.review['roots']}
  self.edges={r['address']:r['target']for r in self.review['edges']}
  self.sources={'BPRJ.ld':b'Task_Hof_PaletteFadeAndPrintWelcomeText = 0x80F3474 | 1;','cfru-moves.h':b'#define MOVE_PSYBEAM 0x3C\n#define MOVE_TAILWHIP 39\n'}
  roots=self.review['selected_song_roots'];self.blocks={roots[0]['constant_site']['address']:(0x2062).to_bytes(2,'little'),roots[1]['script_prefix']['address']:bytes([0,0,0,25,182,0,0]),roots[2]['script_prefix']['address']:bytes([28,160,0,0,0,0]),roots[3]['music_field']['address']:(294).to_bytes(2,'little')}
 def invoke(self):
  with patch.object(m.base.prior,'signed'),patch.object(m.base,'u32',side_effect=lambda raw,a:self.words[a]),patch.object(m,'chunk',side_effect=lambda raw,a,n:self.blocks.get(a,bytes(n))),patch.object(m.code,'thumb_bl',side_effect=lambda raw,a:self.edges[a]):
   return m.bind_roots(b'synthetic',self.review,self.sources)
 def test_four_finite_roots(self):self.assertEqual(set(self.invoke()),{98,182,160,294})
 def test_wrong_candidate(self):
  self.review['required_current_sha256']='wrong'
  with self.assertRaises(ValueError):self.invoke()
 def test_wrong_root_value(self):
  self.review['roots'][0]['value']+=2
  with self.assertRaises(ValueError):self.invoke()
 def test_wrong_bl_target(self):
  self.review['edges'][0]['target']+=2
  with self.assertRaises(ValueError):self.invoke()
 def test_extra_song(self):
  self.review['selected_song_roots'].append(copy.deepcopy(self.review['selected_song_roots'][0]))
  with self.assertRaises(ValueError):self.invoke()
 def test_immediate_wrong_register(self):
  self.blocks[self.review['selected_song_roots'][0]['constant_site']['address']]=(0x2162).to_bytes(2,'little')
  with self.assertRaises(ValueError):self.invoke()
 def test_immediate_wrong_id(self):
  self.blocks[self.review['selected_song_roots'][0]['constant_site']['address']]=(0x2063).to_bytes(2,'little')
  with self.assertRaises(ValueError):self.invoke()
 def test_missing_named_jp_root(self):
  self.sources['BPRJ.ld']=b''
  with self.assertRaises(ValueError):self.invoke()
 def test_different_move_constant(self):
  self.sources['cfru-moves.h']=b'#define MOVE_PSYBEAM 61\n#define MOVE_TAILWHIP 39\n'
  with self.assertRaises(ValueError):self.invoke()
 def test_duplicate_move_define(self):
  self.sources['cfru-moves.h']+=b'#define MOVE_PSYBEAM 60\n'
  with self.assertRaises(ValueError):self.invoke()
 def test_script_wrong_opcode(self):
  a=self.review['selected_song_roots'][1]['script_prefix']['address'];self.blocks[a]=bytes([0,0,0,26,182,0,0])
  with self.assertRaises(ValueError):self.invoke()
 def test_script_wrong_song(self):
  a=self.review['selected_song_roots'][1]['script_prefix']['address'];self.blocks[a]=bytes([0,0,0,25,183,0,0])
  with self.assertRaises(ValueError):self.invoke()
 def test_loop_wrong_opcode(self):
  a=self.review['selected_song_roots'][2]['script_prefix']['address'];self.blocks[a]=bytes([25,160,0,0,0,0])
  with self.assertRaises(ValueError):self.invoke()
 def test_unobserved_map(self):
  self.review['selected_song_roots'][3]['map_number']=25
  with self.assertRaises(ValueError):self.invoke()
 def test_wrong_map_music(self):
  a=self.review['selected_song_roots'][3]['music_field']['address'];self.blocks[a]=(295).to_bytes(2,'little')
  with self.assertRaises(ValueError):self.invoke()
 def test_wrong_map_context(self):
  self.review['selected_song_roots'][3]['selection_evidence']['binding']['sha256']='wrong'
  with self.assertRaises(ValueError):self.invoke()
 def test_wrong_music_storage_join(self):
  row=next(r for r in self.review['roots']if r['name']=='PlayNewMapMusic_current');row['value']+=2;self.words[row['address']]=row['value']
  with self.assertRaises(ValueError):self.invoke()

class CrossSongTests(unittest.TestCase):
 def setUp(self):
  self.raw=bytes(128);self.base=0x08000000;self.new={98:[],160:[],182:[],294:[]};self.old={1000+i:[]for i in range(126)}
  self.inherited=dict(hits=[dict(address=self.base+32,size=4,accepted=True),dict(address=self.base+64,size=4,accepted=False)],song_extension=dict(asset_witnesses=[]),song_extended_extension=dict(asset_witnesses=[]))
  self.diagnostics=[];self.protect=False;self.truncate=False;self.engine={};self.typed=[];self.header_conflict=False
 def model(self,raw,ids,engine,hits):
  reader=m.extended.Reader(raw)
  if self.protect:reader.structure(self.base+32,4,'new-keymap')
  songs=[dict(id=i,**{key:dict(address=self.base+(32 if self.header_conflict else 8),size=4,sha256='synthetic')for key in('song_row','header','player_row')})for i in ids]
  if self.truncate:songs.pop()
  return [m.base.prior.TypedRegion(self.base+64,self.base+68,'pcm8',dict(asset=dict(address=self.base+48,size=20,sha256='synthetic')))],songs,self.diagnostics
 def invoke(self):
  with patch.object(m,'bind_roots',return_value=self.new),patch.object(m.extended,'selected_song_ids',return_value=self.old),patch.object(m.extended,'song_regions',side_effect=self.model):
   return m.all_song_regions(self.raw,self.inherited,self.engine, {},{},self.typed)
 def test_complete_union(self):self.assertEqual(self.invoke()[1]['combined_song_count'],130)
 def test_old_hit_role_conflict(self):
  self.protect=True
  with self.assertRaises(ValueError):self.invoke()
 def test_incomplete_song_rejected(self):
  self.truncate=True
  with self.assertRaises(ValueError):self.invoke()
 def test_model_failure_rejected(self):
  self.diagnostics=[dict(scope='whole_song_rejected')]
  with self.assertRaises(ValueError):self.invoke()
 def test_sample_conflict_rejected(self):
  self.diagnostics=[dict(scope='conflicting_sample_role')]
  with self.assertRaises(ValueError):self.invoke()
 def test_old_sample_removed_rejected(self):
  self.inherited['song_extension']['asset_witnesses']=[dict(kind='pcm8',asset=dict(address=1,size=2,sha256='lost'))]
  with self.assertRaises(ValueError):self.invoke()
 def test_song_header_old_hit_conflict(self):
  self.header_conflict=True
  with self.assertRaises(ValueError):self.invoke()
 def test_engine_old_hit_conflict(self):
  self.engine={'proof':{'windows':[dict(address=self.base+32,size=4,sha256='synthetic')]}}
  with self.assertRaises(ValueError):self.invoke()
 def test_new_data_and_header_conflict(self):
  self.typed=[m.base.prior.TypedRegion(self.base+8,self.base+12,'synthetic',{})]
  with self.assertRaises(ValueError):self.invoke()
 def test_reader_restored_on_failure(self):
  old=m.extended.Reader;self.protect=True
  with self.assertRaises(ValueError):self.invoke()
  self.assertIs(m.extended.Reader,old)
if __name__=='__main__':unittest.main()
