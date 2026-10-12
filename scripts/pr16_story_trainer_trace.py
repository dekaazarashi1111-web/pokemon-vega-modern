#!/usr/bin/env python3
"""保存済み5way trainer証跡を全byte再照合する。nativeを起動しない。"""
import json
import pr16_story_live_observer as observer
import pr16_story_route_session as route_reader
import pr16_story_trainer_session as trainer_reader
import pr16_story_live_probe as transport
from pr16_story_after_maori import need,identity
def trace(folder):
    rows=[json.loads(x)for x in(folder/'stdout.txt').read_text().splitlines()]
    need(rows[0]==dict(begin='INDEPENDENT_CONTINUE',candidate_sha256=observer.CANDIDATE,initial_save_sha256=transport.SEED['sha256'],host_write_barriers=7),'original fixed Continue')
    obs=[];live=[];adjunct=[];screens=[];inputs=[];frame=0;next_kind=None
    for row in rows[1:-1]:
        if 'input'in row:
            need(next_kind is None and row['input']==len(inputs) and row['frame']==frame,'input ordering')
            need(type(row['key'])is int and row['key']in(0,1,2,8,16,32,64,128) and type(row['frames'])is int and 0<row['frames']<=600,'bounded normal input')
            inputs.append((row['key'],row['frames']));frame+=row['frames']
        elif 'observe'in row:
            need(next_kind is None and row['observe']==len(obs) and row['frame']==frame,'observation ordering');obs.append(row);next_kind='live'
        elif 'live'in row:
            need(next_kind=='live','same-frame live ordering');live.append(observer.parse(row,obs[-1]));next_kind='route'
        elif 'route_live'in row:
            need(next_kind=='route','same-frame route ordering');adjunct.append(route_reader.parse(row,obs[-1]));live[-1]['route']=adjunct[-1];next_kind='trainer'
        elif 'trainer_live'in row:
            need(next_kind=='trainer','same-frame trainer order');live[-1]['trainer']=trainer_reader.parse(row,obs[-1]);next_kind='screen'
        elif 'screen'in row:
            need(next_kind=='screen' and row['screen']==len(screens) and row['frame']==frame,'same-frame screenshot')
            raw=(folder/f"screen-{row['screen']:04d}.ppm").read_bytes();need(identity(raw)['sha256']==row['sha256'] and len(raw)==115215 and raw.startswith(b'P6\n240 160\n255\n'),'whole screenshot hash');screens.append(row);next_kind=None
        else:raise ValueError('unexpected trace row')
    ending=dict(end='STORY_INPUT_CHECKPOINT',frames=frame,inputs=len(inputs),warnings_errors=0,host_write_barriers=7,guarded_host_writes=0,fixture_calls=0,natural_research_arrival_accepted=False)
    need(next_kind is None and len(obs)==len(live)==len(adjunct)==len(screens) and rows[-1]==ending and not(folder/'stderr.txt').read_bytes(),'clean exact four-way trace')
    need(inputs[:12]==[(0,600),(8,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(1,2),(0,120),(0,180)],'retained boot sequence')
    commands=(folder/'commands.txt').read_text().splitlines();need(commands[-1]=='quit' and commands.count('quit')==1 and not any(x=='save'for x in commands),'unsaved diagnostic')
    keys=[tuple(map(int,x.split()[1:]))for x in commands if x.startswith('key ')];need(keys==inputs[12:] and all(x[0]!=8 for x in keys),'no field Save menu')
    execution=json.loads((folder/'execution.json').read_bytes());need(execution==dict(returncode=0,initial_save=transport.SEED,final_save=transport.SEED,native_end=ending,observations=len(obs)),'all Save/RTC unchanged')
    return dict(observations=obs,live=live,screens=screens,inputs=inputs,execution=execution)
