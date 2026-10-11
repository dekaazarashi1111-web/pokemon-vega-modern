"""ROM断片なしの合成疎メモリfixtureで有限型根と拒否条件を検査。"""
from pathlib import Path
import copy,json,struct,sys,unittest
from unittest.mock import patch
from types import SimpleNamespace
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'scripts'),str(Path(__file__).resolve().parent)]
import pr16_dex_hof_script_song as m
FIXTURE=object()
class FiniteRootTests(unittest.TestCase):
 def setUp(self):
  self.review=json.loads((m.ROOT/m.REVIEW).read_bytes());self.mem={}
  self.sources={}
  def put(a,v,n):
   for i,b in enumerate(v.to_bytes(n,'little',signed=v<0)):self.mem[a+i]=b
  self.put=put
  for r in self.review['roots']:put(r['address'],r['value'],4)
  for row in self.review['maps']:
   for key in('group_row','header_row'):
    w=row[key];put(w['address'],w['value'],4)
  for i,row in enumerate(self.review['routes']):
   h=row['array_header']['address'];arr=row['array']['address'];a=row['row']['address'];g,n=row['target_map'];put(row['header_field']['address'],h,4)
   if i<3:put(h,row['count'],4);put(h+4,arr,4);put(a+8,g,1);put(a+9,n,1);put(a,row['direction'],1)
   else:
    put(h+1,row['count'],1);put(h+8,arr,4);put(a+7,g,1);put(a+6,n,1);put(a+5,row['destination_warp'],1);put(a,18,2);put(a+2,6,2);put(a+4,0,1)
  h=self.review['maps'][-1]['header']['address'];e=self.review['destination_events']['address'];w=self.review['destination_warp_row']['address'];put(h+4,e,4);put(e+1,4,1);put(e+8,w-8,4);put(w+6,4,1);put(h+16,306,2)
  for a,reg,field in[(0x8054afc,2,0x8054b0c),(0x8056448,1,0x8056450),(0x8058296,0,0x80582a4),(0x806d44c,0,0x806d468)]:put(a,0x4800|(reg<<8)|((field-((a+4)&~3))//4),2)
  for a,op in[(0x8054af8,0x0400),(0x8054afa,0x0409),(0x8054afe,0x0b80),(0x8054b04,0x0b89),(0x8056440,0x280e),(0x8056446,0x0080),(0x805644e,0x4687),(0x8058402,0x350c),(0x8058400,0x3f01),(0x8058404,0x2f00),(0x806d454,0x00fe),(0x806d45c,0x287f),(0x806d564,0x3108),(0x806d562,0x3201)]:put(a,op,2)
  for a,kind,rt,rn,off in[(0x8054b02,'word',0,0,0),(0x8054b08,'word',0,1,0),(0x805838c,'word',0,6,12),(0x805838e,'word',1,0,0),(0x8058390,'word',5,0,4),(0x8058286,'byte',2,0,8),(0x8058288,'byte',1,0,9),(0x806d44e,'word',0,0,4),(0x806d456,'word',0,0,8),(0x806d45a,'byte',0,4,6),(0x806d488,'byte',0,4,7),(0x806d48a,'byte',1,4,6),(0x806d53a,'word',0,0,4),(0x806d53c,'word',1,0,8),(0x806d53e,'byte',3,0,1)]:
   scale,pattern={'word':(4,0x6800),'byte':(1,0x7800)}[kind];put(a,pattern|rt|(rn<<3)|((off//scale)<<6),2)
  self.edge_targets={r['address']:r['target']for r in self.review['edges']}
  for a,target in self.edge_targets.items():
   off=target-(a+4);self.put(a,0xf000|((off>>12)&2047),2);self.put(a+2,0xf800|((off>>1)&2047),2)
  parent=self
  class Recorder(m.Consumer):
   def opcode(self,a,value,label):parent.put(a,value,2)
   def call(self,a,target):
    off=target-(a+4);parent.put(a,0xf000|((off>>12)&2047),2);parent.put(a+2,0xf800|((off>>1)&2047),2)
  m.complete_map_slices(FIXTURE,Recorder);m.complete_map_callers(FIXTURE,Recorder)

 def chunk(self,raw,a,n):
  assert raw is FIXTURE
  return bytes(self.mem.get(a+i,0)for i in range(n))
 def invoke(self):
  with patch.object(m,'bind_sources'),patch.object(m.base.prior,'signed'),patch.object(m,'chunk',side_effect=self.chunk),patch.object(m.base,'u32',side_effect=lambda raw,a:int.from_bytes(self.chunk(raw,a,4),'little')),patch.object(m.d,'chunk',side_effect=self.chunk):return m.bind_roots(FIXTURE,self.review,self.sources)
 def reject(self,change):
  change()
  with self.assertRaises(ValueError):self.invoke()
 def test_exact_root(self):self.assertEqual(set(self.invoke()),{306})
 def test_source_selection_change(self):self.reject(lambda:self.review['selection'].update(map=[64,0]))
 def test_source_header_change(self):self.reject(lambda:self.review['selection'].update(map_header=0x92bfdd8))
 def test_map_index(self):self.reject(lambda:self.review['maps'][-1].update(map=[97,89]))
 def test_group_stride(self):self.reject(lambda:self.review['maps'][-1]['group_row'].update(address=self.review['maps'][-1]['group_row']['address']+4))
 def test_header_stride(self):self.reject(lambda:self.review['maps'][-1]['header_row'].update(address=self.review['maps'][-1]['header_row']['address']+4))
 def test_header_size(self):self.reject(lambda:self.review['maps'][-1]['header'].update(size=32))
 def test_count_drift(self):self.reject(lambda:self.put(self.review['routes'][0]['array_header']['address'],1,4))
 def test_count_expansion(self):self.reject(lambda:self.review['routes'][0].update(count=3))
 def test_connection_index(self):self.reject(lambda:self.review['routes'][0].update(index=2))
 def test_connection_stride(self):self.reject(lambda:self.review['routes'][0]['row'].update(size=16))
 def test_connection_target(self):self.reject(lambda:self.put(self.review['routes'][0]['row']['address']+9,21,1))
 def test_connection_direction(self):self.reject(lambda:self.put(self.review['routes'][0]['row']['address'],5,1))
 def test_warp_count(self):self.reject(lambda:self.put(self.review['routes'][3]['array_header']['address']+1,0,1))
 def test_warp_stride(self):self.reject(lambda:self.review['routes'][3]['row'].update(size=12))
 def test_dynamic_warp_rejected(self):self.reject(lambda:self.put(self.review['routes'][3]['row']['address']+6,127,1))
 def test_destination_warp_invalid(self):self.reject(lambda:self.put(self.review['destination_events']['address']+1,1,1))
 def test_destination_dynamic_rejected(self):self.reject(lambda:self.put(self.review['destination_warp_row']['address']+6,127,1))
 def test_wrong_music(self):self.reject(lambda:self.put(self.review['music_field']['address'],305,2))
 def test_music_extent(self):self.reject(lambda:self.review['music_field'].update(size=4))
 def test_claims(self):self.reject(lambda:self.review['claims'].update(actual_playback=True))
 def test_edge_drift(self):self.reject(lambda:self.put(0x80583a4,0x2000,2))
 def test_wrong_ram_root(self):self.reject(lambda:self.put(0x80582a4,0x2036d34,4))
 def test_consumer_offset(self):self.reject(lambda:self.put(0x8058286,0x7a02+64,2))
 def test_consumer_stride(self):self.reject(lambda:self.put(0x8058402,0x3508,2))
 def test_consumer_index_size(self):self.reject(lambda:self.put(0x8054af8,0x0600,2))
 def test_engine_window_drift(self):
  with patch.object(m,'bind_sources'),patch.object(m,'complete_map_slices'),patch.object(m,'complete_map_callers'),patch.object(m.base.prior,'signed',side_effect=ValueError('drift')):
   with self.assertRaises(ValueError):m.bind_roots(FIXTURE,self.review,{})
 def test_whole_current_entry(self):
  with self.assertRaisesRegex(ValueError,'whole current0641'):m.song_regions(b'not-current',dict(candidate=m.base.CANDIDATE),{}, {})
 def test_frontier(self):
  with patch.object(m,'identity',return_value=m.base.CANDIDATE):
   with self.assertRaisesRegex(ValueError,'exact inherited694'):m.song_regions(FIXTURE,dict(candidate=m.base.CANDIDATE,classified=693,unclassified=181),{}, {})

class ModelGuards(unittest.TestCase):
 def setUp(self):
  self.raw=bytes(128);self.B=0x8000000;self.old={1000+i:[]for i in range(126)};self.old4={98:[],160:[],182:[],294:[]};self.old2={86:[],123:[]};self.new={306:[]};self.diags=[];self.truncate=False;self.duplicate=False;self.read_at=None;self.sample_at=self.B+64;self.typed=[];self.extras=[];self.review={};self.engine={};self.lost=False
  self.inherited=dict(hits=[dict(address=self.B+32,size=4,accepted=True),dict(address=self.B+64,size=4,accepted=False)])
  self.asset=dict(address=self.B+48,size=20,sha256='synthetic')
 def model(self,raw,ids,engine,hits):
  reader=m.extended.Reader(raw)
  if self.read_at is not None:reader.structure(self.read_at,4,'key-map')
  songs=[dict(id=i,**{k:dict(address=self.B+8,size=4,sha256='synthetic')for k in('song_row','header','player_row')})for i in ids]
  if self.truncate:songs.pop()
  if self.duplicate:songs[-1]=songs[0]
  regions=[m.base.prior.TypedRegion(self.sample_at,self.sample_at+4,'pcm8',dict(asset=self.asset))]
  if self.lost:regions=[]
  return regions,songs,self.diags
 def invoke(self):
  with patch.object(m.base.prior,'signed'),patch.object(m.previous,'bind_roots',return_value=self.old4),patch.object(m.gaps,'bind_roots',return_value=self.old2),patch.object(m,'bind_roots',return_value=self.new),patch.object(m.extended,'selected_song_ids',return_value=self.old),patch.object(m.extended,'song_regions',side_effect=self.model),patch.object(m.remaining,'protected_windows',return_value=[]),patch.object(m.gaps,'root_windows',return_value={}),patch.object(m.retained,'retained_sample_witnesses',return_value=[dict(kind='pcm8',asset=self.asset)]),patch.object(m,'HITS',[self.B+64]):return m.all_song_regions(self.raw,self.inherited,self.engine,{},self.review,self.typed,self.extras)
 def test_complete133(self):self.assertEqual(self.invoke()[1]['combined_song_count'],133)
 def test_prior132_id_change(self):
  self.old2={86:[],160:[]}
  with self.assertRaises(ValueError):self.invoke()
 def test_newzero_song_rejected(self):
  self.new[43]=[]
  with self.assertRaises(ValueError):self.invoke()
 def test_incomplete_model(self):
  self.truncate=True
  with self.assertRaises(ValueError):self.invoke()
 def test_duplicate_model(self):
  self.duplicate=True
  with self.assertRaises(ValueError):self.invoke()
 def test_whole_song_reject(self):
  self.diags=[dict(scope='whole_song_rejected')]
  with self.assertRaises(ValueError):self.invoke()
 def test_sample_role_conflict(self):
  self.diags=[dict(scope='conflicting_sample_role')]
  with self.assertRaises(ValueError):self.invoke()
 def test_old_hit_read_conflict(self):
  self.read_at=self.B+32
  with self.assertRaises(ValueError):self.invoke()
 def test_new_typed_command_conflict(self):
  self.read_at=self.B+96;self.typed=[SimpleNamespace(start=self.B+96,end=self.B+100)]
  with self.assertRaises(ValueError):self.invoke()
 def test_new_typed_sample_conflict(self):
  self.typed=[SimpleNamespace(start=self.B+64,end=self.B+68)]
  with self.assertRaises(ValueError):self.invoke()
 def test_newroot_sample_conflict(self):
  self.review={'window':dict(address=self.B+64,size=4,sha256='synthetic')}
  with self.assertRaises(ValueError):self.invoke()
 def test_extra_root_sample_conflict(self):
  self.extras=[dict(address=self.B+64,size=4,sha256='synthetic')]
  with self.assertRaises(ValueError):self.invoke()
 def test_lost_old_sample(self):
  self.lost=True
  with self.assertRaises(ValueError):self.invoke()
 def test_restore_reader(self):
  orig=m.extended.Reader;self.read_at=self.B+32
  with self.assertRaises(ValueError):self.invoke()
  self.assertIs(m.extended.Reader,orig)
if __name__=='__main__':unittest.main(verbosity=2)

class SourceBindingsTests(unittest.TestCase):
 def setUp(self):
  import hashlib
  self.review=json.loads((m.ROOT/m.REVIEW).read_bytes())
  bprj='\n'.join(f'{name} = 0x{a:X} | 1;'for name,a in [('CB2_NewGame',0x8055f04),('Overworld_GetMapHeaderByGroupAndId',0x8054af8),('SetupWarp',0x806d448),('GetWarpEventAtMapPosition',0x806d424),('GetLocationMusic',0x805562c)])
  self.sources={r['local']:b'synthetic fixed public source'for r in self.review['sources']};self.sources['BPRJ.ld']=bprj.encode();self.sources['factory-config']=json.dumps({'physical_binding':{'map_group':96,'map_num':5,'map_header':'0x092BFDD4'}}).encode()
  for r in self.review['sources']:
   val=self.sources[r['local']];r.update(size=len(val),sha256=hashlib.sha256(val).hexdigest(),git_blob_sha=hashlib.sha1(b'blob '+str(len(val)).encode()+b'\0'+val).hexdigest())
 def test_exact(self):m.bind_sources(self.review,self.sources)
 def test_each_source_content_changed(self):
  for row in self.review['sources']:
   sources=dict(self.sources);sources[row['local']]+=b'changed'
   with self.subTest(source=row['local']),self.assertRaises(ValueError):m.bind_sources(self.review,sources)
 def test_each_git_identity_changed(self):
  for i in range(6):
   review=copy.deepcopy(self.review);review['sources'][i]['git_blob_sha']='0'*40
   with self.subTest(source=i),self.assertRaises(ValueError):m.bind_sources(review,self.sources)
 def test_commit_changed(self):
  self.review['sources'][2]['commit']='0'*40
  with self.assertRaises(ValueError):m.bind_sources(self.review,self.sources)
 def test_dropped_source(self):
  self.review['sources'].pop()
  with self.assertRaises(ValueError):m.bind_sources(self.review,self.sources)


class CompleteConsumerMutationTests(unittest.TestCase):
 setUp=FiniteRootTests.setUp
 chunk=FiniteRootTests.chunk
 invoke=FiniteRootTests.invoke
 def test_all_asserted_halfwords_fail_closed(self):
  parent=self;seen={}
  class Recorder(m.Consumer):
   def opcode(self,a,value,label):seen[a]=(value,label)
   def call(self,a,target):
    off=target-(a+4);seen[a]=(0xf000|((off>>12)&2047),'BL prefix');seen[a+2]=(0xf800|((off>>1)&2047),'BL suffix')
  m.complete_map_slices(FIXTURE,Recorder);m.complete_map_callers(FIXTURE,Recorder)
  for a,(value,label) in seen.items():
   self.put(a,value^1,2)
   with self.subTest(address=a,meaning=label),self.assertRaises(ValueError):self.invoke()
   self.put(a,value,2)
  self.assertGreater(len(seen),400)
 def test_reviewer_adversarial_replacements(self):
  for a,value in[(0x8054b00,0x2000),(0x8054b06,0x2100),(0x8054b0a,0x4708),(0x805562c,0x4770),(0x805644a,0x2000),(0x805838a,0x2600),(0x806d458,0x2400),(0x8054b56,0x2000)]:
   before=int.from_bytes(self.chunk(FIXTURE,a,2),'little');self.put(a,value,2)
   with self.subTest(address=a),self.assertRaises(ValueError):self.invoke()
   self.put(a,before,2)

CURRENT_FIXTURE=None
CURRENT_FIXTURE_SOURCES=None
class CurrentCandidateFixtureTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  if CURRENT_FIXTURE is None or CURRENT_FIXTURE_SOURCES is None:raise unittest.SkipTest('Actions producer injects current0641 and bound source bytes')
  m.need(m.identity(CURRENT_FIXTURE)==m.base.CANDIDATE,'injected actual current0641')
 def test_current_root_bound(self):
  review=json.loads((m.ROOT/m.REVIEW).read_bytes());self.assertEqual(set(m.bind_roots(CURRENT_FIXTURE,review,CURRENT_FIXTURE_SOURCES)),{306})
 def test_each_finite_window_byte_mutation_rejected(self):
  review=json.loads((m.ROOT/m.REVIEW).read_bytes());mut=bytearray(CURRENT_FIXTURE)
  for a,n in m.root_windows(review):
   at=a-m.base.BASE;mut[at]^=1
   with self.subTest(address=a,size=n),self.assertRaises(ValueError):m.bind_roots(mut,review,CURRENT_FIXTURE_SOURCES)
   mut[at]^=1
