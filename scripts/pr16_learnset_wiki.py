#!/usr/bin/env python3
"""Issue19候補の技習得Wiki。保存採用行の読取projectionでありROM生成器ではない。"""
from __future__ import annotations
from collections import Counter, defaultdict
import csv
import hashlib
import html
import json
from pathlib import Path
import posixpath
import re
import struct

CONSUMERS = ('egg', 'evolution', 'form_change', 'level_up', 'machine',
             'pre_evolution_carry', 'reminder', 'shared_egg', 'tutor')
LABELS = {'egg':'タマゴ', 'evolution':'進化時', 'form_change':'姿変更から持越し',
          'level_up':'レベル', 'machine':'技マシン', 'pre_evolution_carry':'進化前から持越し',
          'reminder':'専用思い出し', 'shared_egg':'共有タマゴ', 'tutor':'教え技'}
LAYERS = {'official_baseline':'公式基準', 'vega_original_baseline':'原作Vega基準',
          'explicit_distinct_owner_clone':'受入済み別owner複製', 'explicit_identity_repair':'受入済みidentity修復'}
CARRY = {'pre_evolution_carry', 'form_change'}
OLD_ROUTES = {**{c:c for c in CONSUMERS if c not in CARRY}, 'machine_archive':'machine',
              'tutor_archive':'tutor', 'move_memory_reminder':'reminder'}
SCOPE = 'CANDIDATE_LEARNSET_WIKI_NOT_GAMEPLAY_OR_RELEASE_ACCEPTANCE'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def encode(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def identity(raw):
    return {'size':len(raw), 'sha256':hashlib.sha256(raw).hexdigest()}


def source_hash(row):
    # 受入済みtools.pr16_learnset_successor.encodeと同一。元rowを変更しない。
    return identity(encode(row))['sha256']


def rows(path):
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            need(bool(line.strip()), '空JSONL行')
            yield json.loads(line)


def unique(items, key):
    out = {}
    for item in items:
        value = key(item)
        need(value not in out, '重複identity: '+str(value))
        out[value] = item
    return out


def read_registry(path, key, count):
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        result = {int(r['id']):dict(r, id=int(r['id'])) for r in csv.DictReader(stream)}
    need(set(result)==set(range(count)) and len({r[key] for r in result.values()})==count,
         'manifest ID/key集合不一致')
    return result


def route_key(row):
    return row['species_id'], row['consumer'], row['source_id']


def meaning(row):
    if row['consumer'] in CARRY:
        return 'CARRY_REFERENCE_NOT_DIRECT_GRANT'
    if row['consumer']=='egg' and row['conditional_egg']:
        return 'CONDITIONAL_BREEDING_NOT_FLAT_EGG'
    return 'BASELINE_DATA_NOT_PHYSICAL_SUPPLY_ACCEPTANCE'


def project(row, conditions):
    """条件を捨てずに共有辞書へ分離。古いruntime_adoptionは現役判定に使わない。"""
    source = row['provenance']['source_route']
    metadata_keys = {'source_url','source_file','source_line','source_offset','source_raw_token',
                     'source_game','source_kind','order','route_id','name_ja','move_name_ja',
                     'move_id','project_move_id','existing_vega_move_id','official_move_id'}
    condition = {k:v for k,v in source.items() if k not in metadata_keys and v not in ('',None,[],{})}
    cond = source_hash(condition)
    need(cond not in conditions or conditions[cond]==condition, '条件hash衝突')
    conditions[cond] = condition
    origin = {k:source[k] for k in sorted(metadata_keys) if k in source and source[k] not in ('',None)}
    for k in ('source_kind','source_identity','source_decision','reference_id','vega_id','dex_no','binding'):
        if k in row['provenance']:
            origin[k] = row['provenance'][k]
    return {k:row[k] for k in ('species_id','species_key','consumer','move_id','move_key','layer',
                               'source_id','source_order','conditional_egg')} | {
        'condition_id':cond, 'source_row_sha256':source_hash(row), 'source':origin,
        'meaning':meaning(row), 'binding_origin':row.get('binding_origin'), 'physical_supply_verified':False}


def join_sources(tables, parent, floette, species, moves):
    """保存128352行ledgerと37追加行を、元行hash・owner・consumerで一対一結合する。"""
    source = {}
    for family in CONSUMERS:
        blocks = list(rows(tables/(family+'.jsonl')))
        need([r['species_id'] for r in blocks]==list(species), 'consumer owner順序/集合')
        for block in blocks:
            need(block['species_key']==species[block['species_id']]['species_key'], '表owner key')
            for row in block['routes']:
                need(row['consumer']==family and row['species_id']==block['species_id'], '表consumer/owner')
                k=route_key(row); need(k not in source, 'source identity重複'); source[k]=row
    for row in rows(parent/'binding-routes.jsonl'):
        k=route_key(row); need(k not in source, '明示binding衝突'); source[k]=row
    result=[]; conditions={}; seen=set()
    for entry in rows(parent/'route-ledger.jsonl'):
        k=route_key(entry); need(k in source and k not in seen, 'ledger欠落/重複')
        row=source[k]; seen.add(k)
        need(entry['route_sha256']==source_hash(row) and entry['runtime_applied'] is False,
             '保存ledger原本hash/scope')
        result.append(row)
    need(seen==set(source), 'ledgerに未結合の採用行')
    for row in rows(floette/'floette-routes.jsonl'):
        k=route_key(row)
        need(row['species_id']==1029 and k not in seen, 'Floette追加owner/重複')
        seen.add(k);result.append(row)
    for row in result:
        sid,mid=row['species_id'],row['move_id']
        need(type(mid) is int and 1<=mid<=1062 and mid in moves and row['move_key']==moves[mid]['move_key'],
             'active Move ID/key/Side Change')
        need(sid in species and row['species_key']==species[sid]['species_key'], 'active species key')
        need(row['layer'] in LAYERS and row['disposition']==('EXPLICIT_BINDING_SELECTED' if row['layer']=='explicit_identity_repair' else 'BASELINE_SELECTED'), '基準外overlay/placeholder')
    projected=[project(row,conditions) for row in result]
    return result,projected,conditions


def span(folder, metadata):
    name=metadata['file']; start=metadata['offset']; size=metadata['size']
    need(Path(name).name==name and type(start) is int and type(size) is int and start>=0 and size>=0,
         'payload span path/size')
    data=(folder/name).read_bytes()
    need(start+size<=len(data), 'payload span切詰め')
    return data[start:start+size]


def words(raw):
    need(len(raw)%2==0, 'U16 stride')
    values=[r[0] for r in struct.iter_unpack('<H',raw)]
    need(all(1<=m<=1062 for m in values), 'payload move範囲')
    return values


def supply_projection(parent, floette, species):
    """元payload spanを表示へ投影。既存のPLA1/PLC2/C decoder回帰は呼ばない。"""
    policies=(floette/'owner-policies.bin').read_bytes()
    need(len(policies)==len(species) and all(p in range(1,8) for p in policies), 'owner policy')
    index=unique(rows(floette/'consumer-index.jsonl'), lambda r:(r['species_id'],r['consumer']))
    need(set(index)=={(sid,c) for sid in species for c in CONSUMERS}, '9 consumer集合')
    catalogs=json.loads((parent/'catalogs.json').read_bytes())
    result={}
    for sid in species:
        record={'species_id':sid,'policy':policies[sid],'learning_owner':policies[sid]==1,
                'preserve_stored_four_moves_and_pp':True,'machine_slots':[], 'tutor_slots':[],
                'machine_archive':[], 'tutor_archive':[], 'direct_levels':[], 'direct_egg':[],
                'evolution':[], 'reminder':[], 'shared_egg':[], 'physical_supply_verified':False}
        folder=floette if sid==1029 else parent
        for family in CONSUMERS:
            item=index[sid,family]
            need(item['species_key']==species[sid]['species_key'], 'payload species key')
            if policies[sid]!=1:
                need(item['status']=='IDENTITY_ONLY_NO_REPLACEMENT' and item['payload'] is None,
                     '非学習ownerへの表付与')
                continue
            need(item['status']=='PAYLOAD_PREPARED_NOT_INSTALLED', '未知payload由来状態')
            if family in CARRY:
                need(item['payload'] is None, 'carryを直接表へ平坦化')
                continue
            data=span(folder,item['payload'])
            if family in ('machine','tutor'):
                need(len(data)==16 and (family!='tutor' or data[8:]==b'\0'*8), 'compatibility幅')
                bits=[i for i in range(128) if data[i//8]>>(i%8)&1]
                catalog=unique(catalogs[family]['slots'],lambda r:r['bit_index'])
                need(all(bit in catalog for bit in bits), '未知catalog bit')
                record[family+'_slots']=[catalog[bit] for bit in bits]
                sequence=words(span(folder,item['archive']))
                need(len(sequence)==len(set(sequence)), 'archive重複')
                record[family+'_archive']=[{'move_id':mid,'raw_index':i,
                    'raw_page_one_based':i//40+1 if family=='machine' else 1,
                    'mode':3+i//40 if family=='machine' else 7,
                    'requires_hall_of_fame_flag':'0x082C',
                    'physical_supply_verified':False} for i,mid in enumerate(sequence)]
            elif family=='level_up':
                need(len(data)%3==0 and data.endswith(b'\0\0\xff'), 'level終端/stride')
                record['direct_levels']=[{'move_id':mid,'level':lv} for mid,lv in struct.iter_unpack('<HB',data[:-3])]
                need(all(1<=r['move_id']<=1062 and 1<=r['level']<=100 for r in record['direct_levels']), 'level範囲')
            elif family=='egg':
                need(len(data)>=2 and struct.unpack_from('<H',data)[0]==20000+sid, 'egg owner')
                if sid==1029:
                    need(data==struct.pack('<HH',21029,65535) and item['routes']==0, 'Floette空egg終端')
                    record['direct_egg']=[]
                else:
                    record['direct_egg']=words(data[2:])
            else:
                record[family]=words(data)
        result[sid]=record
    return result


def audit_projection(original, supply):
    """新Wikiに表示するsourceと保存spanの整合性。生成/ARM/旧単体試験なし。"""
    grouped=defaultdict(list)
    for row in original:
        grouped[row['species_id'],row['consumer']].append(row)
    for sid,block in supply.items():
        if not block['learning_owner']:
            need(not any(grouped[sid,c] for c in CONSUMERS), '非学習ownerの採用row')
            continue
        for c in CONSUMERS:
            source=grouped[sid,c]
            mids=[r['move_id'] for r in source]
            if c=='level_up':
                levels=[]
                for r in source:
                    raw=r['provenance']['source_route']
                    lv=raw.get('target_learning_level',raw.get('learning_level',raw.get('level')))
                    levels.append({'move_id':r['move_id'],'level':lv})
                need(levels==block['direct_levels'], '新Wiki level source/span順序不一致')
            elif c in ('machine','tutor'):
                available={r['move_id'] for r in block[c+'_slots']}
                archive=[r['move_id'] for r in block[c+'_archive']]
                need(available|set(archive)==set(mids) and not available&set(archive), '新Wiki bit/archive membership')
                need(archive==list(dict.fromkeys(m for m in mids if m not in available)), 'archive raw順序')
            elif c=='egg':
                need([r['move_id'] for r in source if not r['conditional_egg']]==block['direct_egg'], 'conditional egg混入')
            elif c not in CARRY:
                need(list(dict.fromkeys(mids))==block[c], '新Wiki専用consumer順序')
    return {'source_span_pairs':len(supply)*7,'projection_only':True,'native_runs':0}


def diff_membership(old, current, policy):
    before={(OLD_ROUTES[r['old_route']],r['move_id']) for r in old if r['old_route'] in OLD_ROUTES}
    after={(r['consumer'],r['move_id']) for r in current if r['consumer'] not in CARRY and not r['conditional_egg']}
    def values(items):return [{'consumer':c,'move_id':m} for c,m in sorted(items)]
    return {'old_direct_memberships':len(before),'new_direct_memberships':len(after),
            'common':values(before&after),'old_only':values(before-after),'new_only':values(after-before),
            'old_historical_or_conditional_rows':[r for r in old if r['old_route'] not in OLD_ROUTES],
            'owner_policy':policy,'comparison':'UNIQUE_CONSUMER_MOVE_MEMBERSHIP_NOT_LEVEL_SEQUENCE_OR_SUPPLY',
            'stored_four_moves_deleted':False}


def escape(value):
    if isinstance(value,(dict,list)):
        value=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    return html.escape(str(value),quote=False).replace('|','&#124;').replace('[','&#91;').replace(']','&#93;').replace('`','&#96;').replace('\n','<br>')


def tree_hash(files):
    return hashlib.sha256(''.join(n+'\0'+identity(b)['sha256']+'\n' for n,b in sorted(files.items())).encode()).hexdigest()


def check_links(files):
    count=0
    anchors={n:set(re.findall(r'<a id="([^"]+)">',b.decode())) for n,b in files.items() if n.endswith('.md')}
    for name,data in files.items():
        need(not name.startswith('/') and '..' not in name.split('/') and '\\' not in name, 'output path')
        if not name.endswith('.md'):continue
        text=re.sub(r'```.*?```','',data.decode(),flags=re.S)
        for target in re.findall(r'\]\(([^)]+)\)',text):
            page,_,anchor=target.partition('#')
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),page)) if page else name
            need(resolved in files and not re.match(r'^[a-zA-Z]+:',target), 'Wikiリンク切れ: '+name+' -> '+target)
            if anchor:need(anchor in anchors.get(resolved,set()), '条件anchor欠落')
            count+=1
    return count


def render(model, species, moves, old_blocks):
    """全owner/全Move IDを生成。旧Wikiファイル・受入証拠には書き込まない。"""
    files={}; by_owner=defaultdict(list); by_move=defaultdict(list)
    for row in model['routes']:
        by_owner[row['species_id']].append(row);by_move[row['move_id']].append(row)
    candidate=model['candidate']; identity_line='候補 SHA-256 `'+candidate['sha256']+'` / '+str(candidate['size'])+' bytes / CRC32 `'+candidate['crc32']+'`。\n'
    def put(path,title,body):
        parent='../' if '/' in path else ''
        files[path]=('# '+escape(title)+'\n\n'+identity_line+'\n[Wiki入口]('+parent+'README.md)\n\n'+body.rstrip()+'\n').encode()
    def move_link(mid,prefix='../'):
        return '['+str(mid)+': '+escape(moves[mid].get('display_name',moves[mid]['move_key']))+']('+prefix+'moves/'+str(mid)+'.md)'
    diffs=[]
    for sid,sp in species.items():
        active=by_owner[sid];supply=model['supply'][sid]
        diff=diff_membership(old_blocks[sid]['old_entries'],active,supply['policy']);diffs.append(dict(species_id=sid,**diff))
        body='stable key: `'+sp['species_key']+'`。owner policy: `'+str(supply['policy'])+'`。\n\n'
        body+=('採用元の習得データを表示します。通常操作・物理供給の受入ではありません。\n' if supply['learning_owner'] else
               '**非学習identity。新規習得表へフォールバックしません。保存済み4技とPPの保持は別契約です。**\n')
        body+='\n[供給条件と受入境界](../SUPPLY_CONDITIONS.md) / [履歴差分](../DIFF_INDEX.md)\n'
        body+='\n旧候補からの直接membership: 共通 '+str(len(diff['common']))+'、旧のみ '+str(len(diff['old_only']))+'、新のみ '+str(len(diff['new_only']))+'。レベル順序比較ではありません。\n'
        body+='\n## 基準の全経路（元順序保持）\n\n| # | 方法 | 技 | 基準 | 条件・持越し元 | 原本source ID |\n|---|---|---|---|---|---|\n'
        for i,r in enumerate(active):
            cond=r['condition_id'];source=r['source'];level=model['conditions'][cond].get('level',model['conditions'][cond].get('learning_level'))
            label=LABELS[r['consumer']]+(' Lv'+str(level) if r['consumer']=='level_up' and level is not None else '')
            body+='| '+str(i)+' | '+label+' | '+move_link(r['move_id'])+' | '+LAYERS[r['layer']]+' | [条件](../conditions/'+cond[:2]+'.md#'+cond+')'+(' 持越し参照・直接付与なし' if r['consumer'] in CARRY else ' 条件付き繁殖' if r['conditional_egg'] else '')+' | '+escape(r['source_id'])+' |\n'
        for family in ('machine','tutor'):
            body+='\n## '+LABELS[family]+'の実装表projection\n\n'
            slots=supply[family+'_slots'];archive=supply[family+'_archive']
            body+='既存slot（bitは0始まり、Wiki番号は1始まり）。適合bitだけでは道具の入手・使用成功を意味しません。\n\n'
            body+='、'.join(move_link(r['move_id'])+' (bit '+str(r['bit_index'])+', 番号 '+str(r['wiki_ordinal'])+')' for r in slots) or 'なし'
            body+='\n\n追加archive（殿堂入り0x082C必須、既習得除外より前のraw順序）。\n\n| raw位置 | ページ | mode | 技 |\n|---|---|---|---|\n'
            for r in archive:
                body+='| '+str(r['raw_index'])+' | '+str(r['raw_page_one_based'])+' | '+str(r['mode'])+' | '+move_link(r['move_id'])+' |\n'
        put('pokemon/'+str(sid)+'.md',str(sid)+' '+sp.get('display_name',sp['species_key']),body)
    for mid,mv in moves.items():
        entries=by_move[mid];counts=Counter(r['meaning'] for r in entries)
        body='stable key: `'+mv['move_key']+'`。経路数 '+str(len(entries))+'。\n\n直接データと持越し参照を合算して「直接習得可能種数」にしません。\n\n'
        body+='| 種族 | 方法 | 基準 | 意味 |\n|---|---|---|---|\n'
        # 同一種族・方法・意味の重複sourceは種族ページで全件保持し、逆引きは集合にする。
        keys=sorted({(r['species_id'],r['consumer'],r['layer'],r['meaning']) for r in entries})
        for sid,c,layer,kind in keys:
            body+='| ['+str(sid)+': '+escape(species[sid].get('display_name',species[sid]['species_key']))+'](../pokemon/'+str(sid)+'.md) | '+LABELS[c]+' | '+LAYERS[layer]+' | '+kind+' |\n'
        put('moves/'+str(mid)+'.md',str(mid)+' '+mv.get('display_name',mv['move_key']),body)
    pages=defaultdict(list)
    for key,value in sorted(model['conditions'].items()):
        pages[key[:2]].append('<a id="'+key+'"></a>\n\n## 条件 '+key+'\n\n```json\n'+json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2).replace('```','\\u0060\\u0060\\u0060')+'\n```\n')
    for prefix,entries in pages.items():put('conditions/'+prefix+'.md','原本の習得条件 '+prefix,'\n'.join(entries))
    put('POKEMON_INDEX.md','全種族・フォーム1671 owner' if len(species)==1671 else '全種族・フォーム',
        '\n\n'.join('['+str(sid)+': '+escape(r.get('display_name',r['species_key']))+'](pokemon/'+str(sid)+'.md)' for sid,r in species.items()))
    put('MOVE_INDEX.md','全技ID逆引き', '\n\n'.join(move_link(mid,'') for mid in moves))
    put('DIFF_INDEX.md','旧候補46487d98との直接membership差分',
        '旧Wikiは `docs/wiki/p08-candidate-46487d98` の保存履歴です。次表は技×consumer集合差分で、順序・習得レベル・供給受入の差分ではありません。旧のみでも保存済み4技を削除しません。carry、conditional egg、build preservationは直接付与と分離しています。\n\n'
        '| 種族 | 共通 | 旧のみ | 新のみ |\n|---|---|---|---|\n'+''.join('| ['+str(d['species_id'])+'](pokemon/'+str(d['species_id'])+'.md) | '+str(len(d['common']))+' | '+str(len(d['old_only']))+' | '+str(len(d['new_only']))+' |\n' for d in diffs))
    put('SUPPLY_CONDITIONS.md','実装表・原本条件・未受入範囲',
        '基準行は公式1299件とVega181種の保存原本、および明示owner binding/Floette差分から投影しました。原本の再採取はしていません。\n\n'
        'machine/tutorの適合bitは入手可能性を意味しません。追加archiveは殿堂入りflag0x082Cが必要です。machineは**既習得4技を除く前に40行ずつ**区切り、mode3..6、tutor追加はmode7です。mode0/1は既存経路へ委譲、mode2はprobeです。特殊Tutor152..160は通常slot0..63ではなく、従来の個別条件を保持します。\n\n'
        '**直接ROM4hook/28owner/独立2processの受入を継承していますが、このWiki生成はnative再受入ではありません。** Bag通常入口、殿堂入り前後、ページ選択/取消、習得選択、戦闘、通常Save/fresh Continue、Floette12追加技の実供給は未完です。初期fixtureやsource/span照合を通常操作へ読み替えません。\n\n'
        '進化前/姿変更からの持越し参照は直接習得表ではありません。非直接Vegaタマゴ2394行も直接・共有付与へ変換しません。Side Change159経路103種は非採用原本を保持しactiveから除外します。placeholder0、owner_approved_overlay0です。\n\n'
        'このWikiは**Issue19の技習得に限定した調整用スナップショット**です。種族値・特性・技効果・道具供給・Issue18残監査は旧Wiki/各正本を参照し、このWikiで再受入したとは扱いません。製品全体、clean-ROM2生成、release、baseline切替、mergeは未承認です。')
    put('README.md','Issue19 後継候補の技習得基準Wiki',
        '**現候補の採用基準・consumer表projectionです。最終バランスや通常操作の受入ではありません。**\n\n'
        '[全種族・フォーム](POKEMON_INDEX.md) / [全技逆引き](MOVE_INDEX.md) / [旧候補との集合差分](DIFF_INDEX.md) / [条件と限界](SUPPLY_CONDITIONS.md)\n\n'
        '[機械可読manifest](data/index.json) / [全経路索引](data/routes_index.json) / [owner・供給表](data/supply.jsonl) / [条件辞書索引](data/conditions_index.json) / [非採用Side Change履歴](data/excluded_routes.jsonl) / [Vega非直接タマゴ履歴](data/vega_hatch_links.jsonl)\n\n'
        '旧 `p08-candidate-46487d98` は上書きしていません。公式基準・原作Vega基準・空の所有者overlayを分離しています。各原本行はsource_id、source_order、source_row_sha256と固定artifact/member hashへ結合します。`runtime_adoption`等の採取時ラベルを現在の受入へ改作していません。\n\n'
        '再生成は `python3 -B scripts/pr16_learnset_wiki_actions.py build`、読取専用検査は `python3 -B scripts/pr16_learnset_wiki_actions.py check`。保存入力がない場合はfail-closedで、旧原本の再採取やARM再compileは行いません。')
    route_index=[]
    for sid in species:
        name='data/routes/'+str(sid)+'.jsonl'
        files[name]=b''.join(encode(r) for r in by_owner[sid])
        route_index.append({'species_id':sid,'path':name,'rows':len(by_owner[sid]),**identity(files[name])})
    files['data/routes_index.json']=encode(route_index)
    files['data/supply.jsonl']=b''.join(encode(v) for v in model['supply'].values())
    condition_index=[]
    for prefix in sorted(pages):
        subset={k:v for k,v in model['conditions'].items() if k.startswith(prefix)}
        name='data/conditions/'+prefix+'.json';files[name]=encode(subset)
        condition_index.append({'prefix':prefix,'path':name,'rows':len(subset),**identity(files[name])})
    files['data/conditions_index.json']=encode(condition_index)
    files['data/membership_diff.jsonl']=b''.join(encode(r) for r in diffs)
    files['data/species.jsonl']=b''.join(encode(r) for r in species.values())
    files['data/moves.jsonl']=b''.join(encode(r) for r in moves.values())
    for name in ('excluded_routes.jsonl','vega_hatch_links.jsonl','owner_approved_overlay.json'):
        files['data/'+name]=model['history'][name]
    manifest={n:identity(b) for n,b in sorted(files.items())}
    files['data/index.json']=encode({'schema_version':1,'scope':SCOPE,'candidate':candidate,
        'counts':model['counts'],'source_bindings':model['source_bindings'],'files':manifest,
        'payload_tree_sha256':tree_hash(files),'new_native_runs':0,'accepted_tests_rerun':0,
        'physical_supply_verified':False,'gameplay_e2e_accepted':False,'issue19_complete':False,
        'release_ready':False,'active_baseline_changed':False,'self_hash_policy':'index以外をmanifestへ記録'})
    check_links(files)
    return files


def write_new(folder, files):
    need(not folder.exists() and not any(p.is_symlink() for p in (folder,*folder.parents)), '新Wiki上書き/symlink禁止')
    for name,data in sorted(files.items()):
        p=folder/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)


def check_tree(folder, expected):
    """書込を行わず、余分なファイル/symlink/byte差分も拒否する。"""
    need(folder.is_dir() and not folder.is_symlink(), 'Wiki directory不正')
    actual={}
    for p in folder.rglob('*'):
        need(not p.is_symlink(), 'Wiki symlink禁止')
        if p.is_dir():continue
        need(p.is_file(), 'Wiki regular file限定')
        actual[p.relative_to(folder).as_posix()]=p.read_bytes()
    need(actual==expected, 'Wiki path集合/byte不一致')
    return tree_hash(actual)
