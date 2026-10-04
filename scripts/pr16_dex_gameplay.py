#!/usr/bin/env python3
"""候補の通常Save/独立Continue。新規raw ABI呼出し・fixture書込はしない。"""
from __future__ import annotations
import hashlib,json,re,struct,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_dex_lifecycle as lifecycle
need,identity=lifecycle.need,lifecycle.identity
CANDIDATE=dict(size=33554432,sha256='71a1131dae058f568bc5537d21bb8c85dfa551c956c4ac36d9e52293eaf5915c')
HEADER='tools/mgba_pr16_dex_gameplay.h'
LAYOUT=[0xF24]+[0xF80]*3+[0xEC0]+[0xF80]*8+[0x7D0]
def record(legacy=None):
 out=bytearray(522);out[:4]=b'MDX1';out[8]=1
 if legacy is not None:need(len(legacy)==208,'exact legacy evidence');out[10]=1;out[314:]=legacy
 struct.pack_into('<I',out,4,zlib.crc32(out));return bytes(out)
def physical(save,counter):
 need(len(save)in(131072,131088),'Flash with optional RTC');bank=counter&1;rows={}
 for i in range(14):
  raw=save[(bank*14+i)*4096:(bank*14+i+1)*4096];sid,check,sig,gen=struct.unpack_from('<HHII',raw,0xFF4)
  need(sid<14 and sid not in rows and sig==0x08012025 and gen==counter,'same complete bank identity')
  total=sum(struct.unpack_from('<'+'I'*(LAYOUT[sid]//4),raw))&0xffffffff
  need(check==((total>>16)+(total&65535))&65535,'all14 stock checksums');rows[sid]=raw
 s1=b''.join(rows[i][:LAYOUT[i]]for i in range(1,5));s2=rows[0][:LAYOUT[0]]
 legacy=s1[0x5F8:0x5F8+52]+s1[0x3A18:0x3A18+52]+s2[0x5C:0x5C+52]+s2[0x28:0x28+52]
 return dict(mdx=rows[13][0xDE6:0xFF0],legacy=legacy,party=s1[56:656],save1=s1,save2=s2)
def generate():
 import pr16_research_story as story
 source=story.generate().decode();pattern=r'^#define NG_ROM "[a-f0-9]{64}"$';need(len(re.findall(pattern,source,re.M))==1,'one inherited ROM identity')
 source=re.sub(pattern,'#define NG_ROM "'+CANDIDATE['sha256']+'"',source,flags=re.M)
 need(source.count('static struct mCore *st_open(')==1 and source.count('st_screen(n);fflush(stdout);')==1,'one observation entry')
 source=source.replace('static struct mCore *st_open(', (ROOT/HEADER).read_text()+'\nstatic struct mCore *st_open(')
 source=source.replace('st_screen(n);fflush(stdout);','dx_observe(c,n,st_frames);st_screen(n);fflush(stdout);')
 # 旧fixtureのmainは名前を変えた非到達関数。唯一mainのwrite barrierは原本のまま。
 need(source.count('int main(int argc,char**argv){')==1,'one key-only main')
 return source.encode()
def validate_trace(raw,folder,mode,initial,expected,counter,location,save_expected):
 rows=[json.loads(line)for line in raw.decode().splitlines()];need(rows and rows[0]['candidate_sha256']==CANDIDATE['sha256']and rows[0]['initial_save_sha256']==identity(initial)['sha256'],'exact input identities')
 need(rows[0]['begin']==('NEW_GAME_STORY_DEVELOPMENT'if mode=='new-game-story'else 'INDEPENDENT_CONTINUE')and rows[0]['host_write_barriers']==7,'input-only mode')
 inputs=[];observed=[];mdx=[];screens=[];saves=[];frame=0;pending=None
 for row in rows[1:-1]:
  if 'input'in row:
   need(pending is None and row['input']==len(inputs)and row['frame']==frame and row['key']in(0,1,2,8,16,32,64,128)and 0<row['frames']<=600,'bounded ordered key');inputs.append(row);frame+=row['frames']
  elif 'observe'in row:
   need(pending is None and row['observe']==len(observed)and row['frame']==frame,'ordered observation');observed.append(row);pending='mdx'
  elif 'mdx'in row:
   need(pending=='mdx'and row['mdx']==len(mdx)and row['frame']==frame,'same-frame MDX');mdx.append(row);pending='screen'
  elif 'screen'in row:
   need(pending=='screen'and row['screen']==len(screens)and row['frame']==frame,'same-frame real screen');p=folder/f"screen-{len(screens):04d}.ppm";b=p.read_bytes();need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n')and identity(b)['sha256']==row['sha256'],'full screenshot bytes');screens.append(row);pending=None
  elif 'ordinary_save'in row:
   need(pending is None and row==dict(ordinary_save=True,before=counter,after=counter+1,frame=frame),'exact ordinary save +1');saves.append(row)
  else:raise ValueError('unknown trace schema')
 end=rows[-1];need(end==dict(end='STORY_INPUT_CHECKPOINT',frames=frame,inputs=len(inputs),warnings_errors=0,host_write_barriers=7,guarded_host_writes=0,fixture_calls=0,natural_research_arrival_accepted=False),'no fixture or guarded host writes')
 need(pending is None and len(observed)==len(mdx)==len(screens)==(2 if save_expected else 1)and len(saves)==int(save_expected),'complete expected stages')
 for i,(o,d)in enumerate(zip(observed,mdx)):
  wantcounter=counter+int(save_expected and i==1)
  need(o['map']==location['map']and o['xy']==location['xy']and o['party_count']==location['party_count']and o['save_counter']==wantcounter and o['rp']==0 and o['field']and o['lock']==0,'stable specified field only')
  need(d['valid']is True and d['live_sha256']==identity(expected)['sha256']and d['legacy_sha256']==identity(expected[314:])['sha256']and d['legacy_snapshot']==expected[10]and d['seen_count']==d['caught_count']==0,'complete canonical MDX with no invented registration')
  need(d['physical_matches_current_generation']==(0 if save_expected and i==0 else 1),'physical MDX appears only after ordinary Save')
 for key in ('party_sha256','map','xy','facing','party_count'):
  need(all(o[key]==observed[0][key]for o in observed),'Save retains '+key)
 for key in ('bag_sha256','stock_flags_vars_sha256'):
  need(all(d[key]==mdx[0][key]for d in mdx),'Save preserves all '+key)
 if mode=='new-game-story':
  import pr16_research_new_game as newgame
  prefix=b''.join(struct.pack('<IH',x['frames'],x['key'])for x in inputs[:233]);need(identity(prefix)['sha256']==newgame.trace()['trace_sha256'],'exact existing introduction only')
 return dict(observations=observed,mdx=mdx,screens=screens,saves=saves,inputs=len(inputs),frames=frame,end=end)
