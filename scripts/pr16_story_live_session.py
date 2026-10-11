#!/usr/bin/env python3
"""通常key-only Sessionに同一frameのlive観測を追加する専用adapter。"""
from pr16_story_after_maori_session import Session
from pr16_story_after_maori import need, identity
import pr16_story_live_observer as live

class LiveSession(Session):
    def _observation(self,index):
        observation=None; snapshot=None
        while True:
            row=self._next()
            if 'observe' in row:
                need(observation is None and row['observe']==index,'unique exact observation')
                observation=row;self.observations.append(row)
            elif 'live' in row:
                need(observation is not None and snapshot is None,'one same-frame live row')
                snapshot=live.parse(row,observation)
            elif 'screen' in row:
                need(observation is not None and snapshot is not None and row['screen']==index and row['frame']==observation['frame'],'three-way frame identity')
                path=self.folder/f'screen-{index:04d}.ppm'
                need(identity(path.read_bytes())['sha256']==row['sha256'],'same-frame full screenshot')
                self.screen_records.append(row);self.live=snapshot
                return observation
