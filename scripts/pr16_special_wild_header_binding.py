#!/usr/bin/env python3
"""特殊野生fixture: header全体の一意性を仮定せず、一意な実mapだけを選ぶ。"""
from collections import defaultdict
import struct
from pr16_special_wild import need, identity


def select_fixture(rom, anchors, declared):
    packed=b''.join(struct.pack('<BBH8B',*row['fields']) for row in declared)
    begin,end=anchors['qol_start']-0x08000000,anchors['qol_end']-0x08000000
    need(0<=begin<end<=len(rom),'QOL bounds')
    table=rom.find(packed,begin,end)
    need(table>=0 and rom.find(packed,table+1,end)<0,'exact effective846/QOL binary table')
    bymap=defaultdict(list)
    for row in declared:
        pair=tuple(row['fields'][:2])
        if row['region']=='TOHOKU' and row['fields'][9]<=8 and pair not in ((3,19),(255,255),(11,3)):
            bymap[pair].append(row)
    need(len(rom)>=0x82580,'wild root literal bounds')
    root=struct.unpack_from('<I',rom,0x8257C)[0]-0x08000000
    need(0<=root<len(rom)-20,'bounded wild header root')
    inventory=defaultdict(list);terminated=False
    for i in range(1024):
        offset=root+20*i
        need(offset+20<=len(rom),'bounded wild table scan')
        group,map_id=rom[offset:offset+2]
        if (group,map_id)==(255,255):terminated=True;break
        info=struct.unpack_from('<I',rom,offset+16)[0]
        inventory[(group,map_id)].append({'offset':offset,'info':info,'identity':identity(rom[offset:offset+20])})
    need(terminated,'terminated wild table')
    candidates=[];excluded=[]
    for pair,headers in sorted(inventory.items()):
        if pair not in bymap:continue
        # 同一byteの重複も選ばない。first/last優先の推測をしない。
        if len(headers)!=1:
            excluded.append({'map':list(pair),'reason':'DUPLICATE_MAP','headers':headers});continue
        header=headers[0];info=header['info'];info_offset=info-0x08000000
        if not 0<=info_offset<=len(rom)-8:
            excluded.append({'map':list(pair),'reason':'NO_VALID_FISHING_INFO','headers':headers});continue
        pointer=struct.unpack_from('<I',rom,info_offset+4)[0];slots=pointer-0x08000000
        if not 0<=slots<=len(rom)-40:
            excluded.append({'map':list(pair),'reason':'NO_VALID_FISHING_SLOTS','headers':headers});continue
        candidates.append({'map':list(pair),'info':info,'header_offset':header['offset'],
            'header':header['identity'],'rows':bymap[pair],
            'info_identity':identity(rom[info_offset:info_offset+8]),'slots_identity':identity(rom[slots:slots+40])})
    need(candidates,'unique research/fishing intersection')
    candidates.sort(key=lambda item:(len(item['rows']),item['map']))
    need((3,63) in bymap,'hidden existing ecology fixture bound')
    duplicates=[{'map':list(pair),'headers':headers} for pair,headers in sorted(inventory.items()) if len(headers)>1]
    return {'fishing':candidates[0],'hidden':{'map':[3,63],'rows':bymap[(3,63)]},
        'candidates':[{k:c[k] for k in ('map','info')} for c in candidates],
        'research_table':{'offset':table,**identity(packed)},'root':root,'header_count':i,
        'header_inventory':identity(rom[root:root+20*(i+1)]),'duplicate_maps_excluded':duplicates,
        'excluded_research_headers':excluded,'old_unbound_map':[11,3],
        'selection_policy':'UNIQUE_HEADER_ONLY_NO_FIRST_OR_LAST_PRECEDENCE'}
