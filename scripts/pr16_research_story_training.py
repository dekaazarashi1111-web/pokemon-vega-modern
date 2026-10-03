#!/usr/bin/env python3
"""成長Save以後の自然Lv7/すいとる習得と非回復を区別する限定oracle。"""
from __future__ import annotations
from pathlib import Path
import ast
import struct
import pr16_research_story_growth as old
ROOT=Path(__file__).resolve().parents[1]
SOURCE='scripts/pr16_research_story_training.py'
TEST='tests/test_pr16_research_story_training.py'
DEV='content/modernization/pr16_research_story_training_development'
PARENT='content/modernization/pr16_research_story_growth_checkpoint.json'
BUILDER='tools/regression/rom_runtime.py'
CANDIDATE,INPUT_SAVE,RUNNER=old.CANDIDATE,old.OUTPUT_SAVE,old.RUNNER
OUTPUT_SAVE={'size':131088,'sha256':'e3ff50a1d88d24db28b4996440cf11c0114fa75f228c238f9e2e87fb122ac48a'}
need,identity,load=old.need,old.identity,old.load
screens=old.screens
RETAIN=old.RETAIN
ANCHORS={'wild_encounter': {'observe': 20, 'frame': 8026, 'sha256': 'e8683fc1da2c5c15908c38912f24eb5673b876b7a6eabe6b86fa9980b485555a'}, 'scratch_pp_before': {'observe': 21, 'frame': 8330, 'sha256': '98afe277a26d4373170c8350cbb1071422da493c271e1392cebe0c4fa1159b1c'}, 'wild_fainted': {'observe': 26, 'frame': 10748, 'sha256': 'a138de36f6c9352b5e1eebddfb9d35272a3ee02b756deddb4c48604ab1570cc4'}, 'experience41': {'observe': 27, 'frame': 10910, 'sha256': '70e1bfc168aac303e575309e6e48128f203206cea0698287fd6c5d3dd091dfdc'}, 'level7': {'observe': 28, 'frame': 11092, 'sha256': '677c58b9825d8c58974353250e06e91206d28b8ae627f7b49f56fa01cc502c25'}, 'levelup_stats': {'observe': 29, 'frame': 11216, 'sha256': 'e113adbc3dff691ca68094c2830d45a02417b306db111bc139612a7a21214b91'}, 'learned_absorb': {'observe': 30, 'frame': 11460, 'sha256': '654df9ee098559abfa2c415f797a82919d3dc82e4a526fd0f55b1c6bb5af6725'}, 'home_portal_locked': {'observe': 40, 'frame': 15674, 'sha256': '0755b5debf68b8fb07ea0a3184466aef6d821b94391763d2d3314a14395442e1'}, 'unhealed_party': {'observe': 42, 'frame': 16122, 'sha256': 'ddeeda0af492ece61fa702033fa0c95ebf0c6bb98237fdcdb51277ab407ae061'}, 'information': {'observe': 43, 'frame': 16306, 'sha256': '477eed6acb93d605ee30de820d3d15b7936a474ac9dc571e505dfa09b27ebdd2'}, 'stats_exp245_hp13_paralysis': {'observe': 44, 'frame': 16428, 'sha256': '070354d470074c000f38877293e1ff7a22f2ec5446606db42eb0048da4ad63c7'}, 'three_moves_pp': {'observe': 45, 'frame': 16550, 'sha256': 'e59c9ece97f1a2cb1a437313d28772d0611609c09f5463ff24eb42af2a62415d'}}
MAPS=[[3, 0], [3, 0], [3, 0], [3, 0], [3, 0], [3, 0], [3, 0], [3, 0], [3, 0], [3, 0], [3, 0], [3, 0], [3, 35], [3, 35], [3, 0], [3, 0], [3, 0], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 19], [3, 0], [3, 0], [3, 0], [3, 0], [4, 0], [4, 0], [4, 0], [4, 0], [4, 0], [4, 0], [4, 0], [4, 0], [4, 0], [3, 0], [3, 0]]


def read_trace(raw):
    result=old.read_trace(raw)
    for key in ('warnings_errors','guarded_host_writes','fixture_calls'):
        need(type(result['end'][key]) is int,'終端整数のbool別名拒否: '+key)
    need(result['end']['natural_research_arrival_accepted'] is False,'未到達のbool型')
    return result


def parent_boundary(parent):
    need(parent['status']=='PASS_NATURAL_STORY_GROWTH_SAVE_SCOPED' and
         parent['actions_completion_confirmed'] is True,'正式成長Saveだけ')
    need(type(parent['run_id']) is int and parent['run_id']==36358726444 and
         parent['source_head']=='52554a9b5eafe8743d87df57a4ba8565237fffae' and
         type(parent['retained_artifact_id']) is int and parent['retained_artifact_id']==10944976226,
         '親run/source/artifactの由来')
    cp=parent['checkpoint']
    need(parent['candidate']==cp['candidate']==CANDIDATE and
         parent['output_save']==cp['save']==INPUT_SAVE and cp['executable']==RUNNER,'全候補/save/runner')
    need(cp['runtime_artifact']==10898620034 and cp['data_artifact']==10898510128,'固定runtime/data')
    for key in ('natural_research_arrival_accepted','full_story_accepted','release_ready','active_baseline_changed'):
        need(parent[key] is False,'過大受入禁止: '+key)
    need(type(parent['trainer_victories']) is int and parent['trainer_victories']==0 and type(parent['native_bag_potion_count']) is int and parent['native_bag_potion_count']==0,'母親回復/道具を親から捏造しない')
    return parent['continued']


def commands(raw,cold=False):
    lines=old.prior.story.commands(raw)
    count=6 if cold else 48
    need([int(x.split()[1]) for x in lines if x.startswith('observe ')]==list(range(1,count+1)),
         '自動観測0を除く完全な観測順序')
    need(lines.count('save')==(0 if cold else 1),'新Save1回/cold0回')
    need(lines[-2:]==['observe 6','quit'] if cold else lines[-3:]==['save','observe 48','quit'],
         '新区間の明示終端')
    return lines


def command_trace(command,raw,cold=False):
    lines=commands(command,cold);trace=read_trace(raw);rows=old.prior.load_rows(raw);cursor=15
    for line in lines:
        need(cursor<len(rows),'実行原本欠落');row=rows[cursor];p=line.split()
        if p[0]=='key':
            need('input' in row and (row['key'],row['frames'])==(int(p[1]),int(p[2])),'key原本不一致');cursor+=1
        elif p[0]=='observe':
            need(row.get('observe')==int(p[1]) and cursor+1<len(rows) and rows[cursor+1].get('screen')==int(p[1]),'観測原本不一致');cursor+=2
        elif line=='save':
            start=cursor
            while cursor<len(rows) and 'input' in rows[cursor]:cursor+=1
            need(2<=cursor-start<=100 and cursor<len(rows) and rows[cursor].get('ordinary_save') is True,'通常Save命令');cursor+=1
        else:
            need(line=='quit' and cursor==len(rows)-1 and row==trace['end'],'一意終端');cursor+=1
    need(cursor==len(rows),'余剰操作')


def verify(raw,cold_raw,parent,output_save,where=None,cold_where=None):
    first,second=read_trace(raw),read_trace(cold_raw);initial=parent_boundary(parent)
    need(output_save==OUTPUT_SAVE,'全Flash+RTCの後継保存')
    need(first['start']['initial_save_sha256']==INPUT_SAVE['sha256'] and
         second['start']['initial_save_sha256']==OUTPUT_SAVE['sha256'],'成長Saveから後継Saveへ')
    a,b=first['observations'],second['observations']
    need([x['observe'] for x in a]==list(range(49)) and [x['observe'] for x in b]==list(range(7)),'全56観測')
    need((first['end']['inputs'],first['end']['frames'])==(194,19042) and
         (second['end']['inputs'],second['end']['frames'])==(34,2572),'完全入力会計')
    need(first['saves']==[dict(ordinary_save=True,before=4,after=5,frame=19042)] and not second['saves'],'Save4→5')
    for key in RETAIN+('field','lock','callback2','battle_flags','battle_outcome'):
        need(a[0][key]==initial[key],'成長親の実境界: '+key)
    need([x['map'] for x in a]==MAPS,'自然移動の全map履歴')
    for i,row in enumerate(a):
        need(row['party_count']==1 and row['rp']==0 and row['save_counter']==(5 if i==48 else 4),'party/RP/Save境界')
        need(row['battle_flags']==(0 if i<20 else 4) and row['battle_outcome']==(0 if i<31 else 1),'新しい野生戦1回のみ')
    for i in range(20,32):
        need(a[i]['map']==[3,19] and a[i]['xy']==[24,13] and not a[i]['field'] and a[i]['lock']==1,'自然野生戦の位置/lock')
    for anchor in ANCHORS.values():
        i=anchor['observe'];need(first['screens'][i]==dict(screen=i,frame=anchor['frame'],sha256=anchor['sha256']),
                               '実入力に対応した目視原本')
    # 訪問前・船運休会話・訪問後で全party不変。敗北時の自動回復を会話回復に転用しない。
    for i in range(32,49):
        need(a[i]['party_sha256']==a[31]['party_sha256'],'会話/移動で回復を捏造しない')
    need(a[40]['map']==[4,0] and a[40]['xy']==[8,5] and a[40]['facing']==2 and a[40]['lock']==1,'自宅local1に実会話')
    need(a[47]['map']==a[48]['map']==[3,0] and a[48]['xy']==[4,27] and
         a[47]['field'] and a[48]['field'] and a[47]['lock']==a[48]['lock']==0,'屋外idleの正常Save')
    for row in b:
        for key in RETAIN:need(row[key]==a[-1][key],'独立Continue保持: '+key)
        need(row['battle_flags']==0 and row['battle_outcome']==0,'cold一時戦闘状態reset')
    need(b[0]['field'] and b[-1]['field'] and b[-1]['lock']==0,'cold終端idle')
    for i,j in ((42,2),(43,3),(44,4),(45,5)):
        need(first['screens'][i]['sha256']==second['screens'][j]['sha256'],'独立のparty/情報/経験値/技PP画面')
    if where is not None:screens(first,where)
    if cold_where is not None:screens(second,cold_where)
    return dict(status='PASS_NATURAL_LV7_ABSORB_SAVE_SCOPED',candidate=CANDIDATE,input_save=INPUT_SAVE,
        output_save=OUTPUT_SAVE,first_save=a[-1],continued=b[-1],natural_learned_move_ja='すいとる',
        level=7,experience=245,experience_gain=41,hp=[13,23],status_condition_ja='まひ',
        learned_moves_ja=['ひっかく','しっぽをふる','すいとる'],moves_pp=[31,30,25],
        ordinary_recovery_accepted=False,home_portal_locked_observed=True,wild_victories=1,trainer_battles=0,
        trainer_victories=0,native_bag_potion_count=0,screen_count=56,independent_ui_pairs=4,
        natural_research_arrival_accepted=False,full_story_accepted=False,release_ready=False,active_baseline_changed=False)


def diagnose(candidate,source):
    """実ROMの自宅object→T17渡航→locked文言を読むだけ。旧scriptを推測しない。"""
    need(identity(candidate)==CANDIDATE,'診断候補全SHA')
    tree=ast.parse(source);constants={}
    for n in tree.body:
        if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name):
            if n.targets[0].id in ('VEGA_PORTAL_MAP','VEGA_PORTAL_LOCAL_ID'):
                constants[n.targets[0].id]=ast.literal_eval(n.value)
    need(constants==dict(VEGA_PORTAL_MAP=(4,0),VEGA_PORTAL_LOCAL_ID=1),'実builderの所有権')
    need('まだ ふねは うごいていません' in source and 'Hakuji research object local-id 1 portal script' in source,'実builderの誤ったラベル/会話')
    def get(p,n):
        need(type(p) is int and 0x08000000<=p<=0x0a000000-n,'ROM pointer境界')
        return candidate[p-0x08000000:p-0x08000000+n]
    def u(p):return struct.unpack('<I',get(p,4))[0]
    root=u(0x08054b0c);group=u(root+16);header=u(group);events=u(header+4);objects=u(events+4)
    need(get(events,1)==b'\x01','自宅object1件');record=get(objects,24)
    need(record[0]==1 and struct.unpack_from('<hh',record,4)==(8,4),'母親位置local1')
    script=u(objects+16);portal=get(script,39)
    need(portal==bytes.fromhex('6a5a235d0c22092b2c080601040d22092b24080600f80c22092b4b110600f80c220905040d2209'),'現配置の閉じたportal鎖')
    locked=u(script+21);need(u(script+30)==locked,'両early gateの同じlocked先')
    body=get(locked,10);need(body[:2]==b'\x0f\x00' and body[6:]==b'\x09\x04\x6c\x02','lockedはmsgbox/release/endだけ')
    text=u(locked+2);text_raw=get(text,64).split(b'\xff',1)[0]+b'\xff'
    return dict(status='CONFIRMED_HOME_NPC_PORTAL_LOCKED_NOT_RECOVERY',candidate=CANDIDATE,
        builder=BUILDER,builder_identity=identity(source.encode()),
        chain=dict(root=hex(root),group=hex(group),header=hex(header),events=hex(events),objects=hex(objects),
                   script=hex(script),locked=hex(locked),text=hex(text)),
        object=dict(local_id=1,xy=[8,4],identity=identity(record)),script_identity=identity(portal),
        locked_identity=identity(body),text_identity=identity(text_raw),
        dialogue_ja='まだ ふねは うごいていません',original_mother_script_verified=False,
        native_recovery_accepted=False,rom_changes=0,host_writes=0,
        next_step_ja='T17より前の原作Vega/stage16の同一objectとprevious_script原本を照合する。既存渡航を盲目的に移設/解除せず、正規回復との共存を最小差分で検証する。')
