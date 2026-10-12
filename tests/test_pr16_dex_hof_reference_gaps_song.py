"""合成prefix・callback境界と新旧132曲のrole競合を検査。ROMは収録しない。"""
import copy,json,struct,sys,unittest
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_dex_hof_reference_gaps_song as m

class RootTests(unittest.TestCase):
 def setUp(self):
  self.review=json.loads((m.ROOT/m.REVIEW).read_bytes());self.review['sources']=[]
  self.words={r['address']:r['value']for r in self.review['roots']};self.edges={r['address']:r['target']for r in self.review['edges']};self.blocks={}
  self.sources={'cfru-moves.h':b'#define MOVE_PHOTONGEYSER 662\n#define MOVE_POLTERGEIST 725\n'}
  for animation in self.review['selected_song_roots']:
   self.words[animation['table_row']['address']]=animation['script_prefix']['address']
   for row in animation['commands']:
    op=row['opcode'];raw=bytearray(row['size']);raw[0]=op
    if op in(2,3):
     raw[1:5]=row.get('task_callback',row.get('template')).to_bytes(4,'little');raw[5]=row.get('priority',0);raw[6]=row['argc'];raw[7:]=struct.pack('<'+'H'*row['argc'],*row['args'])
    if op==25:raw[1:3]=row['song_id'].to_bytes(2,'little')
    self.blocks[row['address']]=bytes(raw)
 def invoke(self):
  with patch.object(m.base.prior,'signed'),patch.object(m.base,'u32',side_effect=lambda raw,a:self.words[a]),patch.object(m,'chunk',side_effect=lambda raw,a,n:self.blocks.get(a,bytes(n))),patch.object(m.code,'thumb_bl',side_effect=lambda raw,a:self.edges[a]):return m.bind_roots(b'synthetic',self.review,self.sources)
 def reject(self,f):
  f()
  with self.assertRaises(ValueError):self.invoke()
 def test_finite_two(self):self.assertEqual(set(self.invoke()),{86,123})
 def test_candidate(self):self.reject(lambda:self.review.update(required_current_sha256='bad'))
 def test_root_target(self):self.reject(lambda:self.review['roots'][0].update(value=1))
 def test_call_target(self):self.reject(lambda:self.review['edges'][0].update(target=1))
 def test_source_move(self):self.reject(lambda:self.sources.update({'cfru-moves.h':b'#define MOVE_PHOTONGEYSER 661\n#define MOVE_POLTERGEIST 725\n'}))
 def test_source_duplicate(self):self.reject(lambda:self.sources.update({'cfru-moves.h':self.sources['cfru-moves.h']+b'#define MOVE_POLTERGEIST 725\n'}))
 def test_script_table_extent(self):self.reject(lambda:self.review['selected_song_roots'][0]['table_row'].update(address=0))
 def test_opcode(self):
  row=self.review['selected_song_roots'][0]['commands'][0];self.blocks[row['address']]=bytes([1,0,0])
  with self.assertRaises(ValueError):self.invoke()
 def test_prefix_gap(self):self.reject(lambda:self.review['selected_song_roots'][0]['commands'][1].update(address=1))
 def test_prefix_extra(self):self.reject(lambda:self.review['selected_song_roots'][0]['script_prefix'].update(size=43))
 def test_task_callback(self):
  row=self.review['selected_song_roots'][0]['commands'][2];data=bytearray(self.blocks[row['address']]);data[1:5]=(0x08000001).to_bytes(4,'little');self.blocks[row['address']]=bytes(data)
  with self.assertRaises(ValueError):self.invoke()
 def test_task_argcount_overflow(self):
  row=self.review['selected_song_roots'][0]['commands'][2];data=bytearray(self.blocks[row['address']]);data[6]=9;self.blocks[row['address']]=bytes(data)
  with self.assertRaises(ValueError):self.invoke()
 def test_task_delay_changed(self):
  row=self.review['selected_song_roots'][0]['commands'][2];data=bytearray(self.blocks[row['address']]);data[9:11]=(0).to_bytes(2,'little');self.blocks[row['address']]=bytes(data)
  with self.assertRaises(ValueError):self.invoke()
 def test_sprite_template(self):
  row=self.review['selected_song_roots'][0]['commands'][3];data=bytearray(self.blocks[row['address']]);data[1:5]=(0x08000000).to_bytes(4,'little');self.blocks[row['address']]=bytes(data)
  with self.assertRaises(ValueError):self.invoke()
 def test_sound_id(self):
  row=self.review['selected_song_roots'][1]['commands'][-1];self.blocks[row['address']]=bytes([25,124,0,0])
  with self.assertRaises(ValueError):self.invoke()
 def test_aliasing_tasks(self):self.reject(lambda:self.review['callback_noninterference']['tasks'].update(address=0x02037E08))
 def test_wrong_sprite_count(self):self.reject(lambda:self.review['callback_noninterference']['sprites'].update(count=128))

class MemsetTests(unittest.TestCase):
 def setUp(self):self.abi=json.loads((m.ROOT/m.REVIEW).read_bytes())['memset_noninterference']
 def test_exact_all16(self):self.assertTrue(m.memset_contract(self.abi))
 def test_short_long_clear(self):
  for length in(31,33):
   with self.subTest(length=length):
    abi=copy.deepcopy(self.abi);abi['register_contract']['r2']=length
    with self.assertRaises(ValueError):m.memset_contract(abi)
 def test_nonzero(self):
  self.abi['register_contract']['r1']=1
  with self.assertRaises(ValueError):m.memset_contract(self.abi)
 def test_id16(self):
  self.abi['task_id_max']=16
  with self.assertRaises(ValueError):m.memset_contract(self.abi)
 def test_boundary_overwrite(self):
  self.abi['destination_ranges'][-1]['end_exclusive']+=1
  with self.assertRaises(ValueError):m.memset_contract(self.abi)
 def test_missing_first(self):
  self.abi['destination_ranges'].pop(0)
  with self.assertRaises(ValueError):m.memset_contract(self.abi)

class CrossSongTests(unittest.TestCase):
 def setUp(self):
  self.raw=bytes(128);self.base=0x08000000;self.new={86:[],123:[]};self.prior4={98:[],160:[],182:[],294:[]};self.old={1000+i:[]for i in range(126)}
  self.inherited=dict(hits=[dict(address=self.base+32,size=4,accepted=True),dict(address=self.base+64,size=4,accepted=False)],song_extension=dict(asset_witnesses=[]),song_extended_extension=dict(asset_witnesses=[]),reference_delta=dict(witnesses=[]))
  self.diagnostics=[];self.protect=False;self.truncate=False;self.engine={};self.typed=[];self.header_conflict=False;self.review={}
 def model(self,raw,ids,engine,hits):
  reader=m.extended.Reader(raw)
  if self.protect:reader.structure(self.base+32,4,'new-keymap')
  songs=[dict(id=i,**{key:dict(address=self.base+(32 if self.header_conflict else 8),size=4,sha256='synthetic')for key in('song_row','header','player_row')})for i in ids]
  if self.truncate:songs.pop()
  return [m.base.prior.TypedRegion(self.base+64,self.base+68,'pcm8',dict(asset=dict(address=self.base+48,size=20,sha256='synthetic')))],songs,self.diagnostics
 def invoke(self):
  with patch.object(m.base.prior,'signed'),patch.object(m.previous,'bind_roots',return_value=self.prior4),patch.object(m,'bind_roots',return_value=self.new),patch.object(m.extended,'selected_song_ids',return_value=self.old),patch.object(m.extended,'song_regions',side_effect=self.model):
   return m.all_song_regions(self.raw,self.inherited,self.engine, {},self.review,self.typed)
 def test_complete_union(self):self.assertEqual(self.invoke()[1]['combined_song_count'],132)
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
 def test_new_data_and_any_sample_conflict(self):
  self.typed=[m.base.prior.TypedRegion(self.base+64,self.base+68,'synthetic',{})]
  with self.assertRaises(ValueError):self.invoke()
 def test_finite_root_sample_overlap(self):
  self.review={'windows':[dict(address=self.base+64,size=4,sha256='synthetic')]}
  with self.assertRaises(ValueError):self.invoke()
 def test_diagnostic_asset_is_not_control_role(self):
  self.review={'diagnostic_new_assets':[dict(address=self.base+64,size=4,sha256='synthetic')]}
  self.assertEqual(self.invoke()[1]['combined_song_count'],132)
 def test_parent_pcm_removed_rejected(self):
  self.inherited['reference_delta']['witnesses']=[dict(kind='pcm8',evidence=dict(asset=dict(address=1,size=20,sha256='lost-parent')))]
  with self.assertRaises(ValueError):self.invoke()
if __name__=='__main__':unittest.main()
