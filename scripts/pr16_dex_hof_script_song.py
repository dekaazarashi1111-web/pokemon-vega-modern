"""明示Factory mapの有限consumer連鎖からJP song306を追加する候補。"""
from pathlib import Path
import collections,hashlib,json,re,struct
import pr16_dex_hof_reference_gaps_song as gaps
import pr16_dex_hof_remaining_song as retained
import pr16_dex_hof_remaining_references as remaining
base,extended,previous,delta=gaps.base,gaps.extended,gaps.previous,gaps.delta
need,identity,chunk=base.need,base.identity,base.chunk
ROOT=Path(__file__).resolve().parents[1]
REVIEW='content/modernization/pr16_dex_hof_script_song_review.json'
REVIEW_ID={'size':20113,'sha256':'2ab324ab62ac216247d327092ca497027614e1aa2a78e86e5dc6a0ffee3c8005'}
HITS=[0x848d6a4,0x848d702,0x848d83e,0x848d848,0x848d91b,0x848da6a,0x848dc8c]
PAIRS=[[96,5],[96,22],[96,23],[96,4],[97,88]]
u=lambda raw,a:base.u32(raw,a)
def b(raw,a):return chunk(raw,a,1)[0]
def half(raw,a):return int.from_bytes(chunk(raw,a,2),'little')
def imm_load(raw,a,kind,rt,rn,offset):
 op=half(raw,a);scale,pattern={'word':(4,0x6800),'byte':(1,0x7800),'half':(2,0x8800)}[kind]
 need(op&0xf800==pattern and op&7==rt and(op>>3)&7==rn and((op>>6)&31)*scale==offset,'actual '+kind+' load field/register at '+str(a))
def literal(raw,a,reg,field):
 op=half(raw,a);need(op&0xf800==0x4800 and(op>>8)&7==reg and((a+4)&~3)+4*(op&255)==field,'actual literal address/register')
def root_windows(value):
 out={}
 def visit(x):
  if isinstance(x,dict):
   if all(k in x for k in('address','size','sha256')):
    a,n=x['address'],x['size'];need(type(a)is int and type(n)is int and base.BASE<=a<a+n<=base.BASE+base.CANDIDATE['size'],'finite positive in-ROM root role')
    w={k:x[k]for k in('address','size','sha256')};need((a,n)not in out or out[a,n]==w,'shared root identity agreement');out[a,n]=w
   for v in x.values():visit(v)
  elif isinstance(x,list):
   for v in x:visit(v)
 visit(value);return out

def bind_sources(review,sources):
 need([r['local']for r in review['sources']]==['factory-config','BPRJ.ld','pret-overworld.c','gaps-pret-fieldmap.c','gaps-pret-global.fieldmap.h','pret-field_control_avatar.c'],'closed six source roots')
 for row in review['sources']:
  value=sources[row['local']]
  need(identity(value)=={k:row[k]for k in('size','sha256')}and hashlib.sha1(b'blob '+str(len(value)).encode()+b'\0'+value).hexdigest()==row['git_blob_sha'],'whole pinned semantic source and Git blob')
  need(row['commit']==({'kapibarasan000/CFRU-JP':'e24a16fe39e27ae162faf5b78596d1f3df18489d','pret/pokefirered':'c75f352304d529f6ba92d4f74b9cf8b5c3810788','dekaazarashi1111-web/pokemon-vega-modern':'5bbb4448249a940610e6af25059c0e6fb916fd75'}[row['repository']]),'fixed accepted upstream/project commit')
 binding=json.loads(sources['factory-config'])['physical_binding'];need((binding['map_group'],binding['map_num'],int(binding['map_header'],0))==(96,5,0x092bfdd4),'explicit project physical map seed, no US extent')
 bprj=sources['BPRJ.ld'].decode()
 for name,a in [('CB2_NewGame',0x8055f04),('Overworld_GetMapHeaderByGroupAndId',0x8054af8),('SetupWarp',0x806d448),('GetWarpEventAtMapPosition',0x806d424),('GetLocationMusic',0x805562c)]:
  need(re.search(r'\b'+name+r'\s*=\s*0x0*'+format(a,'x')+r'\s*\|\s*1',bprj,re.I),'explicit pinned JP engine symbol '+name)

def bind_roots(raw,review,sources):
 need(review['schema_version']==1 and review['required_candidate']==base.CANDIDATE and review['song_id']==306 and review['expected_hit_addresses']==HITS,'fixed finite song306 scope')
 need(review['claims']==dict(finite_static_consumer_root=True,actual_playback=False,natural_story_path=False,global_map_extent=False,indirect_completeness=False,donor_leased=False),'limited static typed root claims only')
 bind_sources(review,sources)
 complete_map_slices(raw);complete_map_callers(raw)
 accepted_raw=(ROOT/previous.REVIEW).read_bytes();need(identity(accepted_raw)==previous.REVIEW_ID,'independent immutable previously accepted map consumer review')
 accepted=json.loads(accepted_raw);trusted=[w for w in accepted['windows']if w['name']in('Overworld_GetMapHeaderByGroupAndId','GetLocationMusic')]
 need(len(trusted)==2,'both previously accepted exact map getters retained');base.prior.signed(raw,trusted)
 for w in root_windows(review).values():base.prior.signed(raw,w)
 roots={x['name']:x for x in review['roots']};need(set(roots)=={'map_groups','map_load_switch','map_load_case0','InitMap_gMapHeader','SetupWarp_gMapHeader','loaded_header_destination','loaded_header_saveblock1','warp_destination_writer','warp_destination_reader','map_connection_flags','dummy_connection_flags'},'exact eleven actual root literals')
 for w in roots.values():need(w['size']==4 and u(raw,w['address'])==w['value'],'whole finite root word')
 need(roots['map_groups']['address']==0x8054b0c and roots['map_load_switch']['address']==0x8056450 and roots['map_load_switch']['value']==roots['map_load_case0']['address']==0x8056454 and roots['map_load_case0']['value']==0x8056490,'actual selector table and finite state0 entry')
 need(roots['InitMap_gMapHeader']['address']==0x80582a4 and roots['SetupWarp_gMapHeader']['address']==0x806d468 and roots['InitMap_gMapHeader']['value']==roots['SetupWarp_gMapHeader']['value']==0x2036d30,'same actual gMapHeader')
 need(roots['loaded_header_destination']['address']==0x8054b74 and roots['loaded_header_destination']['value']==0x2036d30 and roots['loaded_header_saveblock1']['address']==0x8054b78 and roots['loaded_header_saveblock1']['value']==0x03005048,'actual SaveBlock1 location source and whole gMapHeader copy destination')
 need(roots['warp_destination_writer']['address']==0x8054c84 and roots['warp_destination_reader']['address']==0x8055674 and roots['warp_destination_writer']['value']==roots['warp_destination_reader']['value']==0x02031cf0,'same destination struct written and read for music')
 need(roots['map_connection_flags']['address']==0x80583bc and roots['map_connection_flags']['value']==0x02036d58 and roots['dummy_connection_flags']['address']==0x80583c0 and roots['dummy_connection_flags']['value']==0x08316f9c,'connection flag writes distinct from whole map header')
 calls={(0x8055f34,0x805671c),(0x8056724,0x8056438),(0x805649a,0x80551e0),(0x8055250,0x8058294),(0x8058298,0x80582c0),(0x805830a,0x8058388),(0x80583a4,0x8058284),(0x805828c,0x8054af8),(0x806d43a,0x806d52c),(0x806d48c,0x8054af8)}
 need(len(review['edges'])==len(calls)and{(x['address'],x['target'])for x in review['edges']}==calls,'closed actual direct-call chain')
 for row in review['edges']:need(gaps.code.thumb_bl(chunk(raw,row['address'],4),row['address'])==row['target'],'complete actual Thumb BL')
 for a,reg,field in[(0x8054afc,2,0x8054b0c),(0x8056448,1,0x8056450),(0x8058296,0,0x80582a4),(0x806d44c,0,0x806d468)]:literal(raw,a,reg,field)
 # JP map table really computes independent four-byte indices without a guessed extent.
 need(half(raw,0x8054af8)==0x0400 and half(raw,0x8054afa)==0x0409 and half(raw,0x8054afe)==0x0b80 and half(raw,0x8054b04)==0x0b89,'actual two u16 indices times four')
 for a,kind,rt,rn,off in[(0x8054b02,'word',0,0,0),(0x8054b08,'word',0,1,0),(0x805838c,'word',0,6,12),(0x805838e,'word',1,0,0),(0x8058390,'word',5,0,4),(0x8058286,'byte',2,0,8),(0x8058288,'byte',1,0,9),(0x806d44e,'word',0,0,4),(0x806d456,'word',0,0,8),(0x806d45a,'byte',0,4,6),(0x806d488,'byte',0,4,7),(0x806d48a,'byte',1,4,6),(0x806d53a,'word',0,0,4),(0x806d53c,'word',1,0,8),(0x806d53e,'byte',3,0,1)]:imm_load(raw,a,kind,rt,rn,off)
 need(half(raw,0x8056440)==0x280e and half(raw,0x8056446)==0x0080 and half(raw,0x805644e)==0x4687,'source state0 switch with bounded table selection')
 need(half(raw,0x8058402)==0x350c and half(raw,0x8058400)==0x3f01 and half(raw,0x8058404)==0x2f00,'actual counted connection stride12')
 need(half(raw,0x806d454)==0x00fe and half(raw,0x806d45c)==0x287f and half(raw,0x806d564)==0x3108 and half(raw,0x806d562)==0x3201,'actual warp stride8 and distinct dynamic127 sentinel')
 need(review['selection']==dict(source='factory-config',json_path=['physical_binding'],map=[96,5],map_header=0x92bfdd4),'fixed explicit first map selection')
 need([r['map']for r in review['maps']]==PAIRS,'only reviewed finite map chain')
 for row in review['maps']:
  g,n=row['map'];gr,sr,h=row['group_row'],row['header_row'],row['header']
  need(0<=g<127 and 0<=n<127 and gr['address']==roots['map_groups']['value']+4*g and gr['size']==4 and gr['value']==u(raw,gr['address'])and sr['address']==gr['value']+4*n and sr['size']==4 and sr['value']==u(raw,sr['address'])==h['address']and h['size']==28,'exact selected source indices, two-stage actual pointer rows, complete MapHeader')
 need(review['maps'][0]['header']['address']==review['selection']['map_header'],'source physical header agrees with actual root')
 need(len(review['routes'])==4,'three connections plus one warp')
 for i,row in enumerate(review['routes']):
  need(row['source_map']==PAIRS[i]and row['target_map']==PAIRS[i+1],'continuous explicit graph edge')
  h=review['maps'][i]['header']['address'];f,ah,arr,rec=row['header_field'],row['array_header'],row['array'],row['row'];idx=row['index'];count=row['count']
  need(type(count)is int and type(idx)is int and 0<=idx<count,'selected index within actual count')
  need(f['size']==4 and f['address']==h+(12 if i<3 else 4)and u(raw,f['address'])==f['value']==ah['address']and ah['size']==(8 if i<3 else 20),'actual MapHeader->array header root')
  if i<3:
   need(row['kind']=='connection'and idx==[1,1,0][i]and count==[2,2,3][i]and u(raw,ah['address'])==count and u(raw,ah['address']+4)==arr['address']and arr['size']==12*count and rec['address']==arr['address']+12*idx and rec['size']==12,'complete bounded connection row')
   need([b(raw,rec['address']+8),b(raw,rec['address']+9)]==row['target_map']and b(raw,rec['address'])==row['direction']in(1,2,3,4),'actual direct cardinal connection target')
  else:
   need(row['kind']=='warp'and idx==0 and count==6 and b(raw,ah['address']+1)==count and u(raw,ah['address']+8)==arr['address']and arr['size']==8*count and rec['address']==arr['address']and rec['size']==8,'complete first bounded warp row')
   need([b(raw,rec['address']+7),b(raw,rec['address']+6)]==row['target_map']and b(raw,rec['address']+6)!=127 and b(raw,rec['address']+5)==row['destination_warp']==1 and list(struct.unpack('<hhB',chunk(raw,rec['address'],5)))==row['position']==[18,6,0],'actual selected ordinary warp and matching coordinate/elevation case')
 h=review['maps'][-1]['header']['address'];e=review['destination_events'];w=review['destination_warp_row'];music=review['music_field']
 need(u(raw,h+4)==e['address']and e['size']==20 and b(raw,e['address']+1)>1 and w['address']==u(raw,e['address']+8)+8 and w['size']==8 and b(raw,w['address']+6)!=127,'destination warp consumed by SetupWarp is valid and ordinary')
 need(music['address']==h+16 and music['size']==2 and half(raw,music['address'])==306,'actual selected MapHeader u16 music306')
 return{306:[dict(name='JP_EXPLICIT_FACTORY_MAP_GRAPH_306',source_review=REVIEW)]}

def all_song_regions(raw, inherited, engine, sources, review, typed_regions=(), additional_protected_windows=()):
    new_ids = bind_roots(raw, review, sources)
    ids = extended.selected_song_ids(raw, sources, engine)
    parent_raw=(ROOT/previous.REVIEW).read_bytes();need(identity(parent_raw)==previous.REVIEW_ID,'whole prior130 roots')
    old_roots=previous.bind_roots(raw,json.loads(parent_raw),sources)
    need(len(ids)==126 and not set(ids)&set(old_roots),'original126 plus prior4 roots')
    ids.update(old_roots)
    old_extra=(ROOT/gaps.REVIEW).read_bytes();need(identity(old_extra)==gaps.REVIEW_ID,'whole prior132 roots');ids.update(gaps.bind_roots(raw,json.loads(old_extra),sources))
    need(len(ids)==132 and set(new_ids)=={306} and not set(ids)&set(new_ids),'retained132 plus only306')
    ids.update(new_ids)
    readers = []
    old_reader = extended.Reader
    class CapturedReader(old_reader):
        def __init__(self, value):
            super().__init__(value)
            readers.append(self)
    extended.Reader = CapturedReader
    try:
        regions, songs, diagnostics = extended.song_regions(raw, dict(sorted(ids.items())), engine, inherited['hits'])
    finally:
        extended.Reader = old_reader
    need(len(songs) == len(ids)==133 and {s['id']for s in songs}==set(ids) and not any(r.get('scope') in ('whole_song_rejected', 'conflicting_sample_role')
         for r in diagnostics), 'all inherited and new songs complete without shared role conflicts')
    roots_protected=root_windows(review)
    roots_protected.update(gaps.root_windows(json.loads(parent_raw)))
    roots_protected.update(gaps.root_windows(json.loads(old_extra)))
    extra_roots={(w['address'],w['size']):w for w in remaining.protected_windows()}
    extra_roots.update({(w['address'],w['size']):w for w in additional_protected_windows})
    base.prior.signed(raw,list(extra_roots.values()))
    base.prior.signed(raw,list(roots_protected.values()))
    protections = {(a,n,'finite-root'):w for (a,n),w in roots_protected.items()}
    for engine_proof in (engine.get('proof', {}), engine.get('extended_proof', {})):
        for window in engine_proof.get('windows', []):
            protections[(window['address'], window['size'], 'engine')] = {k: window[k] for k in ('address', 'size', 'sha256')}
    for song_row in songs:
        for key in ('song_row', 'header', 'player_row'):
            window = song_row[key]
            protections[(window['address'], window['size'], key)] = window
    for reader in readers:
        for (address, size, role), witness in reader.structures.items():
            protections[(address, size, role)] = witness
        for witness in reader.windows():
            protections[(witness['address'], witness['size'], 'command')] = witness
    # 新songのreadが過去にdataと分類された4byteを覆う場合、旧受入を黙って残さない。
    for hit in inherited['hits']:
        if hit['accepted']:
            need(not any(a < hit['address'] + hit['size'] and hit['address'] < a + size
                         for a, size, _ in protections), 'new cross-song reads do not contradict any prior accepted hit')
    for region in typed_regions:
        need(not any(a < region.end and region.start < a + size for a, size, _ in protections),
             'new typed data/code does not overlap any complete song read role')
    for typed in typed_regions:
        need(not any(typed.start < region.end and region.start < typed.end for region in regions),'every new typed data/code role disjoint from all133 sound payloads')
    for region in regions:
        need(not any(a < region.end and region.start < a+n for a,n in roots_protected),'every sound payload disjoint from new and inherited finite root roles')
    retained.protect_root_roles(raw,regions,list(extra_roots.values()))
    old_witnesses=retained.retained_sample_witnesses(inherited)
    retained.preserve_assets(regions,old_witnesses)
    unknown = [h for h in inherited['hits'] if not h['accepted']]
    selected = [r for r in regions if any(base.contains(r.start, r.end, h['address'], h['size']) for h in unknown)]
    need([h['address']for h in unknown if any(base.contains(r.start,r.end,h['address'],h['size'])for r in selected)]==HITS,'only the exact seven inherited unknown song306 hits')
    proof = dict(status='PASS_FINITE_JP_ROOTS_WITH_COMPLETE_CROSS_SONG_ROLE_CHECK',
        fixed_review=REVIEW, inherited_song_count=132, additional_song_ids=sorted(new_ids),
        combined_song_count=len(ids), complete_modeled_songs=len(songs),
        full_rom_inventory_runs=0, previous_accepted_hits_unchanged=True,
        old_sample_witnesses_preserved=len(old_witnesses),
        extra_finite_root_role_count=len(extra_roots),extra_finite_root_roles_identity=identity(delta.canonical(list(extra_roots.values()))),
        protected_read_windows=len(protections), finite_root_windows=len(roots_protected), protected_read_identity=identity(delta.canonical(
            [dict(role=role, **witness) for (a, size, role), witness in sorted(protections.items())])),
        new_songs=[s for s in songs if s['id'] in new_ids],
        diagnostics_by_scope=dict(collections.Counter(r.get('scope', 'unknown') for r in diagnostics)),
        jp_song_table_extent_claimed=False, actual_playback_claimed=False,
        complete_runtime_read_footprint_claimed=False, donor_leased=False)
    return selected, proof



def song_regions(raw,inherited,engine,sources,typed_regions=(),additional_protected_windows=()):
    need(identity(raw)==inherited['candidate']==base.CANDIDATE,'whole current0641 required')
    need((inherited['classified'],inherited['unclassified'])==(694,180),'exact inherited694 frontier')
    reviewed=(ROOT/REVIEW).read_bytes();need(identity(reviewed)==REVIEW_ID,'complete fixed song306 review')
    return all_song_regions(raw,inherited,engine,sources,json.loads(reviewed),typed_regions,additional_protected_windows)

import pr16_dex_hof_donor as d
import pr16_dex_hof_reference_code as code
class Consumer:
 def __init__(self,raw):self.raw=raw
 def opcode(self,a,v,label):d.need(int.from_bytes(d.chunk(self.raw,a,2),'little')==v,'complete map consumer '+label+' at '+str(a))
 def shift(self,a,kind,rd,rs,n):self.opcode(a,{'lsl':0,'lsr':0x800,'asr':0x1000}[kind]|(n<<6)|(rs<<3)|rd,kind)
 def imm(self,a,kind,rd,n):self.opcode(a,{'mov':0x2000,'cmp':0x2800,'add':0x3000,'sub':0x3800}[kind]|rd<<8|n,kind)
 def add(self,a,rd,rs,rt):self.opcode(a,0x1800|rt<<6|rs<<3|rd,'register ADD')
 def subreg(self,a,rd,rs,rt):self.opcode(a,0x1a00|rt<<6|rs<<3|rd,'register SUB')
 def small(self,a,rd,rs,n,sub=False):self.opcode(a,(0x1e00 if sub else 0x1c00)|n<<6|rs<<3|rd,'small ADD/SUB')
 def mem(self,a,kind,rd,rb,off):
  p,scale={'ldrw':(0x6800,4),'strw':(0x6000,4),'ldrb':(0x7800,1),'strb':(0x7000,1),'ldrh':(0x8800,2),'strh':(0x8000,2)}[kind]
  d.need(off%scale==0,'aligned field');self.opcode(a,p|((off//scale)<<6)|(rb<<3)|rd,kind)
 def regmem(self,a,kind,rd,rb,ro):self.opcode(a,{'ldrsb':0x5600,'ldrsh':0x5e00}[kind]|ro<<6|rb<<3|rd,kind)
 def compare(self,a,rn,rm):self.opcode(a,0x4280|rm<<3|rn,'register CMP')
 def stack(self,a,pop,mask,lr=False):self.opcode(a,(0xbc00 if pop else 0xb400)|int(lr)<<8|mask,'PUSH/POP exact frame')
 def sp(self,a,amount):self.opcode(a,0xb000|(0x80 if amount<0 else 0)|(abs(amount)//4),'stack local adjustment')
 def spmem(self,a,load,rd,off):self.opcode(a,(0x9800 if load else 0x9000)|rd<<8|(off//4),'SP relative field')
 def multi(self,a,load,rn,mask):self.opcode(a,(0xc800 if load else 0xc000)|rn<<8|mask,'multiple word copy')
 def bx(self,a,reg):self.opcode(a,0x4700|reg<<3,'BX return register')
 def highmov(self,a,rd,rs):self.opcode(a,0x4600|rs<<3|(rd&7)|((rd&8)<<4),'high register MOV')
 def alu(self,a,kind,rd,rs):self.opcode(a,{'orr':0x4300,'mul':0x4340,'neg':0x4240,'and':0x4000}[kind]|rs<<3|rd,kind)
 def branch(self,a,cond,target):
  off=(target-a-4)//2;d.need(-128<=off<128,'bounded condition offset');self.opcode(a,0xd000|cond<<8|(off&255),'conditional branch')
 def jump(self,a,target):
  off=(target-a-4)//2;d.need(-1024<=off<1024,'bounded branch');self.opcode(a,0xe000|(off&2047),'unconditional branch')
 def pointer(self,a,rd,slot):
  off=slot-((a+4)&~3);d.need(0<=off<=1020 and off%4==0,'literal field bounds');self.opcode(a,0x4800|rd<<8|off//4,'literal load')
 def call(self,a,target):d.need(code.thumb_bl(d.chunk(self.raw,a,4),a)==target,'complete map consumer BL')

def complete_map_slices(raw,cls=Consumer):
 s=cls(raw)
 # Both table index arithmetic and return, without gaps.
 s.shift(0x8054af8,'lsl',0,0,16);s.shift(0x8054afa,'lsl',1,1,16);s.pointer(0x8054afc,2,0x8054b0c);s.shift(0x8054afe,'lsr',0,0,14)
 s.add(0x8054b00,0,0,2);s.mem(0x8054b02,'ldrw',0,0,0);s.shift(0x8054b04,'lsr',1,1,14);s.add(0x8054b06,1,1,0);s.mem(0x8054b08,'ldrw',0,1,0);s.bx(0x8054b0a,14)
 # Map location byte arguments, signed promotion, header music read, caller return.
 s.stack(0x805562c,False,0,True);s.small(0x805562e,1,0,0);s.imm(0x8055630,'mov',0,0);s.regmem(0x8055632,'ldrsb',0,1,0)
 s.shift(0x8055634,'lsl',0,0,16);s.shift(0x8055636,'lsr',0,0,16);s.mem(0x8055638,'ldrb',1,1,1)
 s.shift(0x805563a,'lsl',1,1,24);s.shift(0x805563c,'asr',1,1,24);s.shift(0x805563e,'lsl',1,1,16);s.shift(0x8055640,'lsr',1,1,16)
 s.call(0x8055642,0x8054af8);s.mem(0x8055646,'ldrh',0,0,16);s.stack(0x8055648,True,2);s.bx(0x805564a,1)
 # LoadCurrentMapData copies all seven header words. Only layout word0 is later replaced.
 s.stack(0x8054b34,False,0x70,True);s.pointer(0x8054b36,4,0x8054b74);s.pointer(0x8054b38,5,0x8054b78);s.mem(0x8054b3a,'ldrw',1,5,0)
 s.imm(0x8054b3c,'mov',0,4);s.regmem(0x8054b3e,'ldrsb',0,1,0);s.shift(0x8054b40,'lsl',0,0,16);s.shift(0x8054b42,'lsr',0,0,16);s.mem(0x8054b44,'ldrb',1,1,5)
 s.shift(0x8054b46,'lsl',1,1,24);s.shift(0x8054b48,'asr',1,1,24);s.shift(0x8054b4a,'lsl',1,1,16);s.shift(0x8054b4c,'lsr',1,1,16);s.call(0x8054b4e,0x8054af8)
 s.small(0x8054b52,1,4,0)
 for a,load,rn in[(0x8054b54,True,0),(0x8054b56,False,1),(0x8054b58,True,0),(0x8054b5a,False,1)]:s.multi(a,load,rn,0x4c)
 s.mem(0x8054b5c,'ldrw',0,0,0);s.mem(0x8054b5e,'strw',0,1,0);s.mem(0x8054b60,'ldrw',1,5,0);s.mem(0x8054b62,'ldrh',0,4,18);s.mem(0x8054b64,'strh',0,1,50)
 s.call(0x8054b66,0x8054a30);s.mem(0x8054b6a,'strw',0,4,0);s.stack(0x8054b6c,True,0x70);s.stack(0x8054b6e,True,1);s.bx(0x8054b70,0)
 # The switch's argument, bound, row arithmetic/load, transfer, and selected case0 call.
 s.stack(0x8056438,False,0x30,True);s.small(0x805643a,4,0,0);s.small(0x805643c,5,1,0);s.mem(0x805643e,'ldrb',0,4,0);s.imm(0x8056440,'cmp',0,14)
 s.branch(0x8056442,9,0x8056446);s.jump(0x8056444,0x8056590);s.shift(0x8056446,'lsl',0,0,2);s.pointer(0x8056448,1,0x8056450);s.add(0x805644a,0,0,1);s.mem(0x805644c,'ldrw',0,0,0);s.highmov(0x805644e,15,0)
 s.call(0x8056490,0x8055b70);s.call(0x8056494,0x805627c);s.small(0x8056498,0,5,0);s.call(0x805649a,0x80551e0);s.jump(0x805649e,0x805658a)
 # The source call reaches InitMap before return, then forwards the same global header.
 s.stack(0x80551e0,False,0x10,True);s.call(0x80551e2,0x8054b34)
 s.call(0x8055250,0x8058294);s.stack(0x8055254,True,0x10);s.stack(0x8055256,True,1);s.bx(0x8055258,0)
 s.stack(0x8058294,False,0,True);s.pointer(0x8058296,0,0x80582a4);s.call(0x8058298,0x80582c0)
 s.stack(0x80582c0,False,0x70,True);s.sp(0x80582c2,-4);s.small(0x80582c4,6,0,0)
 s.small(0x8058308,0,6,0);s.call(0x805830a,0x8058388);s.sp(0x805830e,4);s.stack(0x8058310,True,0x70);s.stack(0x8058312,True,1);s.bx(0x8058314,0)
 # Complete connection getter, including input forwarding and its exact return.
 s.stack(0x8058284,False,0,True);s.mem(0x8058286,'ldrb',2,0,8);s.mem(0x8058288,'ldrb',1,0,9);s.small(0x805828a,0,2,0);s.call(0x805828c,0x8054af8);s.stack(0x8058290,True,2);s.bx(0x8058292,1)
 # Complete counted connection walker: no unexplained instruction between array root, index and getter.
 s.stack(0x8058388,False,0xf0,True);s.small(0x805838a,6,0,0);s.mem(0x805838c,'ldrw',0,6,12);s.mem(0x805838e,'ldrw',1,0,0);s.mem(0x8058390,'ldrw',5,0,4)
 s.pointer(0x8058392,2,0x80583bc);s.pointer(0x8058394,0,0x80583c0);s.mem(0x8058396,'ldrw',0,0,0);s.mem(0x8058398,'strw',0,2,0);s.imm(0x805839a,'cmp',1,0);s.branch(0x805839c,13,0x8058408)
 s.small(0x805839e,4,2,0);s.small(0x80583a0,7,1,0);s.small(0x80583a2,0,5,0);s.call(0x80583a4,0x8058284);s.small(0x80583a8,1,0,0);s.mem(0x80583aa,'ldrw',2,5,4);s.mem(0x80583ac,'ldrb',0,5,0)
 s.imm(0x80583ae,'cmp',0,2);s.branch(0x80583b0,0,0x80583da);s.imm(0x80583b2,'cmp',0,2);s.branch(0x80583b4,12,0x80583c4);s.imm(0x80583b6,'cmp',0,1);s.branch(0x80583b8,0,0x80583ce);s.jump(0x80583ba,0x8058400)
 s.imm(0x80583c4,'cmp',0,3);s.branch(0x80583c6,0,0x80583e6);s.imm(0x80583c8,'cmp',0,4);s.branch(0x80583ca,0,0x80583f2);s.jump(0x80583cc,0x8058400)
 for a,target,flag in[(0x80583ce,0x8058474,1),(0x80583da,0x80584dc,2),(0x80583e6,0x805853c,4),(0x80583f2,0x805859c,8)]:
  s.small(a,0,6,0);s.call(a+2,target);s.mem(a+6,'ldrb',0,4,0);s.imm(a+8,'mov',1,flag)
  if a!=0x80583f2:s.jump(a+10,0x80583fc)
 s.alu(0x80583fc,'orr',0,1);s.mem(0x80583fe,'strb',0,4,0);s.imm(0x8058400,'sub',7,1);s.imm(0x8058402,'add',5,12);s.imm(0x8058404,'cmp',7,0);s.branch(0x8058406,1,0x80583a2);s.stack(0x8058408,True,0xf0);s.stack(0x805840a,True,1);s.bx(0x805840c,0)
 # Complete normal SetupWarp selection up to its destination writer. No later callbacks are assumed.
 s.stack(0x806d448,False,0xf0,True);s.small(0x806d44a,5,2,0);s.pointer(0x806d44c,0,0x806d468);s.mem(0x806d44e,'ldrw',0,0,4)
 s.shift(0x806d450,'lsl',1,1,24);s.shift(0x806d452,'asr',7,1,24);s.shift(0x806d454,'lsl',6,7,3);s.mem(0x806d456,'ldrw',0,0,8);s.add(0x806d458,4,0,6);s.mem(0x806d45a,'ldrb',0,4,6);s.imm(0x806d45c,'cmp',0,127);s.branch(0x806d45e,1,0x806d46c)
 for a,rd,off in[(0x806d46c,0,7),(0x806d470,1,6),(0x806d474,2,5)]:s.imm(a,'mov',rd,off);s.regmem(a+2,'ldrsb',rd,4,rd)
 s.call(0x806d478,0x8054c88)
 # The constructor forwards sign-extended group/number/warp and -1 coordinates.
 s.stack(0x8054c88,False,0,True);s.sp(0x8054c8a,-4)
 for a,r in[(0x8054c8c,0),(0x8054c90,1),(0x8054c94,2)]:s.shift(a,'lsl',r,r,24);s.shift(a+2,'asr',r,r,24)
 s.imm(0x8054c98,'mov',3,1);s.alu(0x8054c9a,'neg',3,3);s.spmem(0x8054c9c,False,3,0);s.call(0x8054c9e,0x8054c4c);s.sp(0x8054ca2,4);s.stack(0x8054ca4,True,1);s.bx(0x8054ca6,0)
 s.stack(0x8054c4c,False,0x70,True);s.sp(0x8054c4e,-8);s.small(0x8054c50,4,0,0);s.small(0x8054c52,5,1,0);s.small(0x8054c54,6,2,0);s.spmem(0x8054c56,True,1,24);s.pointer(0x8054c58,0,0x8054c84)
 for a,r in[(0x8054c5a,4),(0x8054c5e,5),(0x8054c62,6),(0x8054c66,3)]:s.shift(a,'lsl',r,r,24);s.shift(a+2,'asr',r,r,24)
 s.spmem(0x8054c6a,False,3,0);s.shift(0x8054c6c,'lsl',1,1,24);s.shift(0x8054c6e,'asr',1,1,24);s.spmem(0x8054c70,False,1,4)
 s.small(0x8054c72,1,4,0);s.small(0x8054c74,2,5,0);s.small(0x8054c76,3,6,0);s.call(0x8054c78,0x8054a9c);s.sp(0x8054c7c,8);s.stack(0x8054c7e,True,0x70);s.stack(0x8054c80,True,1);s.bx(0x8054c82,0)
 s.stack(0x8054a9c,False,0x30,True);s.spmem(0x8054a9e,True,4,12);s.spmem(0x8054aa0,True,5,16);s.mem(0x8054aa2,'strb',1,0,0);s.mem(0x8054aa4,'strb',2,0,1);s.mem(0x8054aa6,'strb',3,0,2)
 s.shift(0x8054aa8,'lsl',4,4,24);s.shift(0x8054aaa,'asr',4,4,24);s.mem(0x8054aac,'strh',4,0,4);s.shift(0x8054aae,'lsl',5,5,24);s.shift(0x8054ab0,'asr',5,5,24);s.mem(0x8054ab2,'strh',5,0,6);s.stack(0x8054ab4,True,0x30);s.stack(0x8054ab6,True,1);s.bx(0x8054ab8,0)
 # Destination music consumes precisely the same sWarpDestination written above.
 s.stack(0x8055664,False,0,True);s.pointer(0x8055666,0,0x8055674);s.call(0x8055668,0x805562c);s.shift(0x805566c,'lsl',0,0,16);s.shift(0x805566e,'lsr',0,0,16);s.stack(0x8055670,True,2);s.bx(0x8055672,1)
 return s

def complete_map_callers(raw,cls=Consumer):
 s=cls(raw)
 # CB2_NewGame: actual complete code body, literal pools excluded.
 s.stack(0x8055f04,False,0,True)
 s.call(0x8055f06,134570620)
 s.call(0x8055f0a,134681144)
 s.call(0x8055f0e,134569184)
 s.call(0x8055f12,134562596)
 s.call(0x8055f16,134566564)
 s.call(0x8055f1a,134562044)
 s.call(0x8055f1e,134648640)
 s.call(0x8055f22,134648332)
 s.pointer(0x8055f26,1,134569804)
 s.pointer(0x8055f28,0,134569808)
 s.mem(0x8055f2a,'strw',0,1,0)
 s.pointer(0x8055f2c,1,134569812)
 s.imm(0x8055f2e,'mov',0,0)
 s.mem(0x8055f30,'strw',0,1,0)
 s.pointer(0x8055f32,0,134569816)
 s.call(0x8055f34,134571804)
 s.call(0x8055f38,134570692)
 s.pointer(0x8055f3c,0,134569820)
 s.call(0x8055f3e,134569632)
 s.pointer(0x8055f42,0,134569824)
 s.call(0x8055f44,134219076)
 s.stack(0x8055f48,True,1,False)
 s.bx(0x8055f4a,0)
 # DoMapLoadLoop: actual complete code body, literal pools excluded.
 s.stack(0x805671c,False,16,True)
 s.small(0x805671e,4,0,0,False)
 s.small(0x8056720,0,4,0,False)
 s.imm(0x8056722,'mov',1,0)
 s.call(0x8056724,134571064)
 s.imm(0x8056728,'cmp',0,0)
 s.branch(0x805672a,0,134571808)
 s.stack(0x805672c,True,16,False)
 s.stack(0x805672e,True,1,False)
 s.bx(0x8056730,0)
 # LoadMapFromWarp: actual complete code body, literal pools excluded.
 s.stack(0x80551e0,False,16,True)
 s.call(0x80551e2,134564660)
 s.call(0x80551e6,134563880)
 s.pointer(0x80551ea,0,134566492)
 s.mem(0x80551ec,'ldrb',0,0,23)
 s.call(0x80551ee,134568600)
 s.small(0x80551f2,4,0,0,False)
 s.shift(0x80551f4,'lsl',4,4,24)
 s.shift(0x80551f6,'lsr',4,4,24)
 s.call(0x80551f8,135316216)
 s.call(0x80551fc,134666500)
 s.call(0x8055200,135051308)
 s.call(0x8055204,134664156)
 s.pointer(0x8055208,0,134566496)
 s.mem(0x805520a,'ldrw',1,0,0)
 s.imm(0x805520c,'mov',0,4)
 s.regmem(0x805520e,'ldrsb',0,1,0)
 s.shift(0x8055210,'lsl',0,0,16)
 s.shift(0x8055212,'lsr',0,0,16)
 s.mem(0x8055214,'ldrb',1,1,5)
 s.shift(0x8055216,'lsl',1,1,24)
 s.shift(0x8055218,'asr',1,1,24)
 s.shift(0x805521a,'lsl',1,1,16)
 s.shift(0x805521c,'lsr',1,1,16)
 s.call(0x805521e,135319632)
 s.call(0x8055222,134719648)
 s.call(0x8055226,134568396)
 s.imm(0x805522a,'cmp',4,0)
 s.branch(0x805522c,0,134566452)
 s.pointer(0x805522e,0,134566500)
 s.call(0x8055230,134667932)
 s.call(0x8055234,134567288)
 s.call(0x8055238,134567748)
 s.call(0x805523c,134649092)
 s.call(0x8055240,135662500)
 s.call(0x8055244,135537872)
 s.call(0x8055248,135537912)
 s.call(0x805524c,135337068)
 s.call(0x8055250,134578836)
 s.stack(0x8055254,True,16,False)
 s.stack(0x8055256,True,1,False)
 s.bx(0x8055258,0)
 # InitMapLayoutData: actual complete code body, literal pools excluded.
 s.stack(0x80582c0,False,112,True)
 s.sp(0x80582c2,-4)
 s.small(0x80582c4,6,0,0,False)
 s.mem(0x80582c6,'ldrw',5,6,0)
 s.pointer(0x80582c8,0,134578968)
 s.spmem(0x80582ca,False,0,0)
 s.pointer(0x80582cc,4,134578972)
 s.pointer(0x80582ce,2,134578976)
 s.highmov(0x80582d0,0,13)
 s.small(0x80582d2,1,4,0,False)
 s.call(0x80582d4,136084100)
 s.pointer(0x80582d8,2,134578980)
 s.mem(0x80582da,'strw',4,2,8)
 s.mem(0x80582dc,'ldrw',1,5,0)
 s.imm(0x80582de,'add',1,15)
 s.mem(0x80582e0,'strw',1,2,0)
 s.mem(0x80582e2,'ldrw',0,5,4)
 s.imm(0x80582e4,'add',0,14)
 s.mem(0x80582e6,'strw',0,2,4)
 s.alu(0x80582e8,'mul',1,0)
 s.imm(0x80582ea,'mov',0,160)
 s.shift(0x80582ec,'lsl',0,0,6)
 s.compare(0x80582ee,1,0)
 s.branch(0x80582f0,13,134578942)
 s.pointer(0x80582f2,0,134578984)
 s.pointer(0x80582f4,2,134578988)
 s.imm(0x80582f6,'mov',1,158)
 s.imm(0x80582f8,'mov',3,1)
 s.call(0x80582fa,136084024)
 s.mem(0x80582fe,'ldrw',0,5,12)
 s.mem(0x8058300,'ldrh',1,5,0)
 s.mem(0x8058302,'ldrh',2,5,4)
 s.call(0x8058304,134578992)
 s.small(0x8058308,0,6,0,False)
 s.call(0x805830a,134579080)
 s.sp(0x805830e,4)
 s.stack(0x8058310,True,112,False)
 s.stack(0x8058312,True,1,False)
 s.bx(0x8058314,0)
 # GetWarpEventAtMapPosition: actual complete code body, literal pools excluded.
 s.stack(0x806d424,False,0,True)
 s.small(0x806d426,3,1,0,False)
 s.mem(0x806d428,'ldrh',1,3,0)
 s.imm(0x806d42a,'sub',1,7)
 s.shift(0x806d42c,'lsl',1,1,16)
 s.shift(0x806d42e,'lsr',1,1,16)
 s.mem(0x806d430,'ldrh',2,3,2)
 s.imm(0x806d432,'sub',2,7)
 s.shift(0x806d434,'lsl',2,2,16)
 s.shift(0x806d436,'lsr',2,2,16)
 s.mem(0x806d438,'ldrb',3,3,4)
 s.call(0x806d43a,134665516)
 s.shift(0x806d43e,'lsl',0,0,24)
 s.shift(0x806d440,'asr',0,0,24)
 s.stack(0x806d442,True,2,False)
 s.bx(0x806d444,1)
 # GetWarpEventAtPosition: actual complete code body, literal pools excluded.
 s.stack(0x806d52c,False,112,True)
 s.shift(0x806d52e,'lsl',1,1,16)
 s.shift(0x806d530,'lsr',6,1,16)
 s.shift(0x806d532,'lsl',2,2,16)
 s.shift(0x806d534,'lsr',5,2,16)
 s.shift(0x806d536,'lsl',3,3,24)
 s.shift(0x806d538,'lsr',4,3,24)
 s.mem(0x806d53a,'ldrw',0,0,4)
 s.mem(0x806d53c,'ldrw',1,0,8)
 s.mem(0x806d53e,'ldrb',3,0,1)
 s.imm(0x806d540,'mov',2,0)
 s.compare(0x806d542,2,3)
 s.branch(0x806d544,10,134665578)
 s.mem(0x806d546,'ldrh',0,1,0)
 s.compare(0x806d548,0,6)
 s.branch(0x806d54a,1,134665570)
 s.mem(0x806d54c,'ldrh',0,1,2)
 s.compare(0x806d54e,0,5)
 s.branch(0x806d550,1,134665570)
 s.mem(0x806d552,'ldrb',0,1,4)
 s.compare(0x806d554,0,4)
 s.branch(0x806d556,0,134665564)
 s.imm(0x806d558,'cmp',0,0)
 s.branch(0x806d55a,1,134665570)
 s.shift(0x806d55c,'lsl',0,2,24)
 s.shift(0x806d55e,'asr',0,0,24)
 s.jump(0x806d560,134665582)
 s.imm(0x806d562,'add',2,1)
 s.imm(0x806d564,'add',1,8)
 s.compare(0x806d566,2,3)
 s.branch(0x806d568,11,134665542)
 s.imm(0x806d56a,'mov',0,1)
 s.alu(0x806d56c,'neg',0,0)
 s.stack(0x806d56e,True,112,False)
 s.stack(0x806d570,True,2,False)
 s.bx(0x806d572,1)
 # FillNorthConnection: actual complete code body, literal pools excluded.
 s.stack(0x80584dc,False,240,True)
 s.sp(0x80584de,-12)
 s.small(0x80584e0,5,1,0,False)
 s.imm(0x80584e2,'cmp',5,0)
 s.branch(0x80584e4,0,134579504)
 s.mem(0x80584e6,'ldrw',0,5,0)
 s.mem(0x80584e8,'ldrw',4,0,0)
 s.mem(0x80584ea,'ldrw',0,0,4)
 s.imm(0x80584ec,'add',2,7)
 s.small(0x80584ee,7,0,7,True)
 s.imm(0x80584f0,'cmp',2,0)
 s.branch(0x80584f2,10,134579468)
 s.alu(0x80584f4,'neg',6,2)
 s.add(0x80584f6,2,2,4)
 s.pointer(0x80584f8,0,134579464)
 s.mem(0x80584fa,'ldrw',3,0,0)
 s.compare(0x80584fc,2,3)
 s.branch(0x80584fe,10,134579458)
 s.small(0x8058500,3,2,0,False)
 s.imm(0x8058502,'mov',2,0)
 s.jump(0x8058504,134579484)
 s.imm(0x805850c,'mov',6,0)
 s.add(0x805850e,0,2,4)
 s.pointer(0x8058510,1,134579512)
 s.mem(0x8058512,'ldrw',1,1,0)
 s.subreg(0x8058514,3,1,2)
 s.compare(0x8058516,0,1)
 s.branch(0x8058518,10,134579484)
 s.small(0x805851a,3,4,0,False)
 s.spmem(0x805851c,False,7,0)
 s.spmem(0x805851e,False,3,4)
 s.imm(0x8058520,'mov',0,7)
 s.spmem(0x8058522,False,0,8)
 s.small(0x8058524,0,2,0,False)
 s.imm(0x8058526,'mov',1,0)
 s.small(0x8058528,2,5,0,False)
 s.small(0x805852a,3,6,0,False)
 s.call(0x805852c,134579216)
 s.sp(0x8058530,12)
 s.stack(0x8058532,True,240,False)
 s.stack(0x8058534,True,1,False)
 s.bx(0x8058536,0)
 # FillWestConnection: actual complete code body, literal pools excluded.
 s.stack(0x805853c,False,240,True)
 s.sp(0x805853e,-12)
 s.small(0x8058540,5,1,0,False)
 s.imm(0x8058542,'cmp',5,0)
 s.branch(0x8058544,0,134579600)
 s.mem(0x8058546,'ldrw',0,5,0)
 s.mem(0x8058548,'ldrw',1,0,0)
 s.mem(0x805854a,'ldrw',4,0,4)
 s.imm(0x805854c,'add',2,7)
 s.small(0x805854e,7,1,7,True)
 s.imm(0x8058550,'cmp',2,0)
 s.branch(0x8058552,10,134579564)
 s.alu(0x8058554,'neg',6,2)
 s.add(0x8058556,1,2,4)
 s.pointer(0x8058558,0,134579560)
 s.mem(0x805855a,'ldrw',3,0,4)
 s.compare(0x805855c,1,3)
 s.branch(0x805855e,10,134579554)
 s.small(0x8058560,3,1,0,False)
 s.imm(0x8058562,'mov',2,0)
 s.jump(0x8058564,134579580)
 s.imm(0x805856c,'mov',6,0)
 s.add(0x805856e,0,2,4)
 s.pointer(0x8058570,1,134579608)
 s.mem(0x8058572,'ldrw',1,1,4)
 s.subreg(0x8058574,3,1,2)
 s.compare(0x8058576,0,1)
 s.branch(0x8058578,10,134579580)
 s.small(0x805857a,3,4,0,False)
 s.spmem(0x805857c,False,6,0)
 s.imm(0x805857e,'mov',0,7)
 s.spmem(0x8058580,False,0,4)
 s.spmem(0x8058582,False,3,8)
 s.imm(0x8058584,'mov',0,0)
 s.small(0x8058586,1,2,0,False)
 s.small(0x8058588,2,5,0,False)
 s.small(0x805858a,3,7,0,False)
 s.call(0x805858c,134579216)
 s.sp(0x8058590,12)
 s.stack(0x8058592,True,240,False)
 s.stack(0x8058594,True,1,False)
 s.bx(0x8058596,0)
 # LoadMapConnection: actual complete code body, literal pools excluded.
 s.stack(0x8058410,False,240,True)
 s.highmov(0x8058412,7,8)
 s.stack(0x8058414,False,128,False)
 s.spmem(0x8058416,True,5,24)
 s.mem(0x8058418,'ldrw',4,2,0)
 s.mem(0x805841a,'ldrw',7,4,0)
 s.small(0x805841c,2,7,0,False)
 s.alu(0x805841e,'mul',2,5)
 s.add(0x8058420,2,2,3)
 s.shift(0x8058422,'lsl',2,2,1)
 s.mem(0x8058424,'ldrw',3,4,12)
 s.add(0x8058426,6,3,2)
 s.pointer(0x8058428,3,134579308)
 s.mem(0x805842a,'ldrw',2,3,0)
 s.alu(0x805842c,'mul',1,2)
 s.add(0x805842e,1,1,0)
 s.shift(0x8058430,'lsl',1,1,1)
 s.mem(0x8058432,'ldrw',0,3,8)
 s.add(0x8058434,5,0,1)
 s.spmem(0x8058436,True,0,32)
 s.imm(0x8058438,'cmp',0,0)
 s.branch(0x805843a,13,134579298)
 s.small(0x805843c,4,0,0,False)
 s.pointer(0x805843e,3,134579312)
 s.highmov(0x8058440,8,3)
 s.small(0x8058442,0,6,0,False)
 s.small(0x8058444,1,5,0,False)
 s.spmem(0x8058446,True,2,28)
 s.highmov(0x8058448,3,8)
 s.alu(0x805844a,'and',2,3)
 s.call(0x805844c,136084104)
 s.pointer(0x8058450,0,134579308)
 s.mem(0x8058452,'ldrw',0,0,0)
 s.shift(0x8058454,'lsl',0,0,1)
 s.add(0x8058456,5,5,0)
 s.shift(0x8058458,'lsl',0,7,1)
 s.add(0x805845a,6,6,0)
 s.imm(0x805845c,'sub',4,1)
 s.imm(0x805845e,'cmp',4,0)
 s.branch(0x8058460,1,134579266)
 s.stack(0x8058462,True,8,False)
 s.highmov(0x8058464,8,3)
 s.stack(0x8058466,True,240,False)
 s.stack(0x8058468,True,1,False)
 s.bx(0x805846a,0)
 return s
