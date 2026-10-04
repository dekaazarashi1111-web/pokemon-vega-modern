#!/usr/bin/env python3
"""既存read-only observerに同frameのbattle-script PCだけを追加する。"""
import re
import pr16_story_route_session as route
import pr16_story_live_observer as live
from pr16_story_after_maori_session import Session
from pr16_story_after_maori import need,identity
SOURCE='''static void tv_emit(struct mCore *c, unsigned n, unsigned frame) {
    printf("{\\"trainer_live\\":%u,\\"frame\\":%u,\\"schema\\":1,\\"battle_script\\":%u}\\n", n, frame, read32(c, 0x02023CD4U));
}
'''
def generate():
    need(set(re.findall(r'\b([A-Za-z_][A-Za-z_0-9]*)\s*\(',SOURCE))=={'tv_emit','printf','read32'},'read-only trainer PC source')
    s=route.generate().decode();needle='rv_emit(c,n,st_frames);st_screen(n);fflush(stdout);'
    need(s.count(needle)==1,'one trainer PC observation site')
    s=s.replace('static struct mCore *st_open(',SOURCE+'\nstatic struct mCore *st_open(',1)
    return s.replace(needle,'rv_emit(c,n,st_frames);tv_emit(c,n,st_frames);st_screen(n);fflush(stdout);').encode()
def parse(row,o):
    need(set(row)=={'trainer_live','frame','schema','battle_script'} and all(type(v)is int and 0<=v<=0xffffffff for v in row.values()),'exact trainer adjunct schema')
    need(row['schema']==1 and row['trainer_live']==o['observe'] and row['frame']==o['frame'],'same-frame trainer script PC')
    return row
class RouteSession(Session):
    def _observation(self,index):
        o=None;l=None;r=None;t=None
        while True:
            row=self._next()
            if 'observe'in row:
                need(o is None and row['observe']==index,'unique trainer observation');o=row;self.observations.append(o)
            elif 'live'in row:
                need(o is not None and l is None,'unique live');l=live.parse(row,o)
            elif 'route_live'in row:
                need(l is not None and r is None,'unique route');r=route.parse(row,o)
            elif 'trainer_live'in row:
                need(r is not None and t is None,'unique trainer');t=parse(row,o)
            elif 'screen'in row:
                need(t is not None and row['screen']==index and row['frame']==o['frame'],'five-way same frame pairing')
                p=self.folder/f'screen-{index:04d}.ppm';need(identity(p.read_bytes())['sha256']==row['sha256'],'whole screenshot')
                self.screen_records.append(row);l['route']=r;l['trainer']=t;self.live=l;return o
