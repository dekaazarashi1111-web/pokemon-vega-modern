#!/usr/bin/env python3
"""Same-frame route observation; the accepted observer source stays frozen."""
import re
from pathlib import Path
from pr16_story_after_maori_session import Session
from pr16_story_after_maori import need,identity
import pr16_story_live_observer as live
ROOT=Path(__file__).resolve().parents[1]
SIZES=dict(battle_mons=352,party_indexes=8,controllers=16,battle_buffer=2048,battle_state=512,trainer_state=48,script_contexts=240,research_volatile=40)
SCALARS={'route_live','frame','schema','clock_state','trainer_id'}
def parse(row,observation):
    need(set(row)==set(SIZES)|SCALARS,'exact route observer schema')
    need(all(type(row[k])is int and 0<=row[k]<=0xffffffff for k in SCALARS),'route integers')
    need(row['schema']==1 and row['route_live']==observation['observe'] and row['frame']==observation['frame'] and row['clock_state']<=2 and row['trainer_id']<=65535,'same frame route scalar bounds')
    out={k:row[k]for k in SCALARS}
    for k,size in SIZES.items():
        v=row[k];need(type(v)is str and len(v)==2*size and re.fullmatch('[a-f0-9]+',v)is not None,'route region '+k)
        out[k]=bytes.fromhex(v)
    return out

def source_check(source):
    text=re.sub(r'/\*.*?\*/|//[^\n]*','',source,flags=re.S)
    calls=set(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*\(',text))
    need(calls<={'rv_hex','rv_emit','si_need','printf','read8','read16','read32','for'},'read-only route observer call graph')
    need(source.count('static void rv_emit(')==source.count('static void rv_hex(')==1,'unique route observer')

def generate():
    s=(ROOT/'tools/mgba_pr16_story_route_observer.h').read_text();source_check(s)
    base=live.generate().decode();needle='lv_emit(c,n,st_frames);st_screen(n);fflush(stdout);'
    need(base.count(needle)==1,'single route observation attachment')
    base=base.replace('static struct mCore *st_open(',s+'\nstatic struct mCore *st_open(',1)
    return base.replace(needle,'lv_emit(c,n,st_frames);rv_emit(c,n,st_frames);st_screen(n);fflush(stdout);').encode()

class RouteSession(Session):
    def _observation(self,index):
        o=None;l=None;r=None
        while True:
            row=self._next()
            if 'observe'in row:
                need(o is None and row['observe']==index,'unique route observation');o=row;self.observations.append(o)
            elif 'live'in row:
                need(o is not None and l is None,'unique live observation');l=live.parse(row,o)
            elif 'route_live'in row:
                need(l is not None and r is None,'unique route adjunct');r=parse(row,o)
            elif 'screen'in row:
                need(l is not None and r is not None and row['screen']==index and row['frame']==o['frame'],'four-way frame pairing')
                p=self.folder/f'screen-{index:04d}.ppm';need(identity(p.read_bytes())['sha256']==row['sha256'],'exact screenshot')
                self.screen_records.append(row);l['route']=r;self.live=l;return o
