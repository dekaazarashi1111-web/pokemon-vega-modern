#!/usr/bin/env python3
"""受入済み数値系譜と現役習得を結合する固定R0。旧generator/nativeは再実行しない。"""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
from pathlib import Path, PurePosixPath
import posixpath
import re
from urllib.parse import unquote, urlsplit
import pr16_wiki_r0_reconcile as r

ROOT = r.ROOT
OUT = 'docs/wiki/r0-6e88a021'
INDEX = OUT+'/data/index.json'
TASK = 'USER-20261010-WIKI-R0-RENDER'
CODE = ('scripts/pr16_wiki_r0_build.py', 'scripts/pr16_wiki_r0_publish.py',
        'tests/test_pr16_wiki_r0_build.py', '.github/workflows/pr16-wiki-r0-build.yml')
CARRY = {'pre_evolution_carry', 'form_change'}
DIRECT = {'egg','evolution','level_up','machine','reminder','shared_egg','tutor'}
ROLES = {'stab':'一致攻撃','priority':'先制攻撃','healing':'回復候補','setup':'積み候補','disruption':'妨害候補'}
STATS = [('hp','HP'),('attack','攻撃'),('defense','防御'),('sp_attack','特攻'),('sp_defense','特防'),('speed','素早さ'),('total','BST')]
INHERIT = 'ROM数値・文字列は旧候補読取＋5段階非変更範囲の継承。全機能の新native受入ではありません。'
need = r.need


def compact(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)+'\n').encode()


def esc(value):
    return str(value).replace('&','&amp;').replace('<','&lt;').replace('>','&gt;').replace('|','&#124;').replace('\n','<br>').replace('[','&#91;').replace(']','&#93;').replace('`','&#96;')


def block(value):
    return '\n```json\n'+r.encode(value).decode().replace('```','\\u0060\\u0060\\u0060')+'```\n'


def output_bytes(name, text):
    raw=text.encode() if isinstance(text,str) else text
    return raw.rstrip(b'\r\n')+b'\n' if name.endswith('.md') else raw


def table(headers, rows):
    return '| '+' | '.join(headers)+' |\n| '+' | '.join(['---']*len(headers))+' |\n'+''.join('| '+' | '.join(map(str,row))+' |\n' for row in rows)+'\n'


def head(title, depth=0):
    prefix='../'*depth
    return '# '+title+'\n\n**固定レビュー版 R0** — SHA-256 `'+r.NEW_SHA+'` / 33554432 bytes / CRC32 `00F31AF7`。\n\n[入口]('+prefix+'README.md) · [証拠区分と制限]('+prefix+'LIMITATIONS.md) · [提案記入]('+prefix+'OWNER_PROPOSALS.md)\n\n'+INHERIT+'\n\n'


def link(kind, row, depth=0):
    return '['+str(row['id'])+': '+esc(row['name'])+']('+'../'*depth+kind+'/'+str(row['id'])+'.md)'


def move_roles(species, mids, moves):
    result={key:[] for key in ROLES}
    for mid in sorted(set(mids)):
        move=moves[mid]; effects=' '.join(move['effect_keys'])
        if move['type_id'] in species['types'] and move['category_id'] != 2: result['stab'].append(mid)
        if move['priority'] > 0 and move['category_id'] != 2: result['priority'].append(mid)
        if any(k in effects for k in ('HEAL','RECOVER','ABSORB','REST','WISH')): result['healing'].append(mid)
        if move['category_id']==2 and any(k in effects for k in ('UP','DEFENSE_CURL','GROWTH','QUIVER','DRAGON_DANCE','CALM_MIND')): result['setup'].append(mid)
        if move['category_id']==2 and any(k in effects for k in ('SLEEP','POISON','PARALY','BURN','CONFUS','TAUNT','ENCORE','LEECH','SPIKES','TRAP','DISABLE')): result['disruption'].append(mid)
    return result


def item_parameter(item):
    fields=[item[k] for k in ('hold_effect_param','hold_effect_parameter') if k in item]
    need(all(type(v) is int or isinstance(v,str) and re.fullmatch('[0-9]+',v) for v in fields),'持物引数型不正')
    values=[int(v) for v in fields]
    need(bool(values) and len(set(values))==1 and 0 <= values[0] <= 255,'持物引数のalias欠落/競合')
    return values[0]



def route_validate(row, sid, species, moves, conditions):
    mid=row['move_id']; cid=row['condition_id']; consumer=row['consumer']
    need(type(mid) is int and 0 < mid < len(moves), 'route技ID不正')
    need(row['species_id']==sid and row['species_key']==species[sid]['key'] and row['move_key']==moves[mid]['key'], 'route owner/key不一致')
    need(consumer in DIRECT|CARRY and cid in conditions, 'route consumer/条件欠落')
    expected='CARRY_REFERENCE_NOT_DIRECT_GRANT' if consumer in CARRY else ('CONDITIONAL_BREEDING_NOT_FLAT_EGG' if consumer=='egg' and row['conditional_egg'] else 'BASELINE_DATA_NOT_PHYSICAL_SUPPLY_ACCEPTANCE')
    need(row['meaning']==expected and row['physical_supply_verified'] is False, 'route意味/物理受入の混同')
    need(isinstance(row['source_id'],str) and row['source_id'] and re.fullmatch('[0-9a-f]{64}',row['source_row_sha256']), '原本参照欠落')
    return consumer, mid


class Inputs:
    def __init__(self, root):
        self.root=root;self.bindings={}
        self.rec=r.load(self.take(r.REPORT))
        need(self.rec['status']=='PASS_NUMERIC_LINEAGE_AND_REGISTRY_NOT_REVIEW_READY' and self.rec['candidate']['sha256']==r.NEW_SHA, '数値照合未完')
        # 受入済み監査を再実行せず、その入力byteを照合する。
        for name,binding in self.rec['input_bindings'].items():
            need(r.identity(self.take(name))==binding, '受入後の入力変更: '+name)
        self.indexes={folder:r.load(self.take(folder+'/data/index.json')) for folder in (r.OLD,r.NEW)}
    def take(self,name):
        raw=r.read(self.root,name);self.bindings[name]=r.identity(raw);return raw
    def bound(self,folder,name):
        raw=self.take(folder+'/'+name)
        need(r.identity(raw)==self.indexes[folder]['files'][name], '固定Wiki入力不一致: '+name)
        return raw
    def records(self,folder,name): return r.records(self.bound(folder,name))


def model(inputs):
    old={name:inputs.records(r.OLD,'data/'+name+'.jsonl') for name in ('species','moves','abilities','items','evolutions','megas','z_moves')}
    for name,count in r.COUNTS.items(): r.indexed(old[name],count)
    for name in ('species','moves'):
        need(r.successor_index(name,inputs.records(r.NEW,'data/'+name+'.jsonl'))==r.indexed(old[name],r.COUNTS[name]), '後継ID join不一致')
    conditions={}
    cindex=r.load(inputs.bound(r.NEW,'data/conditions_index.json'))
    need([x['prefix'] for x in cindex]==[f'{i:02x}' for i in range(256)], '条件prefix集合')
    for entry in cindex:
        data=inputs.bound(r.NEW,entry['path']);need(r.identity(data)=={k:entry[k] for k in ('sha256','size')},'条件index hash')
        values=r.load(data);need(len(values)==entry['rows'],'条件件数')
        for key,value in values.items():
            need(key.startswith(entry['prefix']) and key not in conditions and hashlib.sha256(compact(value)).hexdigest()==key,'条件のhash/重複')
            conditions[key]=value
    supply=inputs.records(r.NEW,'data/supply.jsonl');diff=inputs.records(r.NEW,'data/membership_diff.jsonl')
    need([x['species_id'] for x in supply]==list(range(1671)) and [x['species_id'] for x in diff]==list(range(1671)), 'supply/diff ID集合')
    route_index=r.load(inputs.bound(r.NEW,'data/routes_index.json'))
    need([x['species_id'] for x in route_index]==list(range(1671)), 'route index ID集合')
    direct=[set() for _ in old['species']]; carry=[set() for _ in old['species']]; conditional=[set() for _ in old['species']]
    inverse=[defaultdict(set) for _ in old['moves']];counts=Counter();layers=Counter();allkeys=set()
    for entry in route_index:
        sid=entry['species_id'];raw=inputs.bound(r.NEW,entry['path']);rows=r.records(raw)
        need(r.identity(raw)=={k:entry[k] for k in ('sha256','size')} and len(rows)==entry['rows'], 'route index不一致')
        for row in rows:
            consumer,mid=route_validate(row,sid,old['species'],old['moves'],conditions)
            key=(sid,consumer,row['source_id']);need(key not in allkeys,'route多重対応');allkeys.add(key)
            (carry if consumer in CARRY else conditional if row['conditional_egg'] else direct)[sid].add(mid)
            inverse[mid][sid].add('conditional_egg' if row['conditional_egg'] else consumer)
            counts[consumer]+=1;layers[row['layer']]+=1
        need(bool(supply[sid]['learning_owner']) == (supply[sid]['policy']==1), '学習owner判定不一致')
        need(supply[sid]['learning_owner'] or not rows, '非学習ownerへfallback')
        actual={(x['consumer'],x['move_id']) for x in rows if x['consumer'] not in CARRY and not x['conditional_egg']}
        d=diff[sid]; expected={(x['consumer'],x['move_id']) for x in d['common']+d['new_only']}
        need(actual==expected and len(actual)==d['new_direct_memberships'], '現役membershipと差分不一致')
    expect=inputs.indexes[r.NEW]['counts']
    need(dict(counts)==expect['consumers'] and dict(layers)==expect['layers'] and sum(counts.values())==expect['routes'] and len(conditions)==expect['conditions'], '現役経路の全件集計不一致')
    need(expect['active_side_change']==expect['owner_overlay_rows']==expect['placeholder_rows']==0,'未承認採用/placeholder')
    owners=[[] for _ in old['abilities']]
    for s in old['species']:
        need(len(s['ability_ids'])==3,'特性slot数')
        for slot,aid in zip(('通常1','通常2','隠れ'),s['ability_ids']):
            need(type(aid) is int and 0 <= aid < len(owners),'特性参照範囲')
            owners[aid].append({'species_id':s['id'],'slot':slot})
    vega=r.load(inputs.bound(r.OLD,'data/vega_balance.json'));vega_ids=[s['id'] for s in vega]
    need(len(vega_ids)==len(set(vega_ids))==206 and all(old['species'][v['id']]['key']==v['key'] for v in vega),'Vega比較対象不一致')
    gmax=[]
    for s in old['species']:
        if not s['form_key'].endswith('_GIGA'):continue
        reverse=[e for e in s['evolutions'] if e['method_id']==253]
        need(len(reverse)==1 and 0<=reverse[0]['target_id']<1671,'Gmax逆変換対応不明')
        gmax.append({'id':s['id'],'base_id':reverse[0]['target_id'],'reverse':reverse[0], 'resource_status':'POINTER_TABLE_INHERITED_ASSET_BODIES_NOT_AUDITED', 'native_status':'DEFERRED_AUDIT'})
    need(len(gmax)==34 and len(old['megas'])==76 and len(old['z_moves'])==31,'機構件数不一致')
    return dict(old, supply=supply,diff=diff,direct=direct,carry=carry,conditional=conditional,inverse=inverse,owners=owners,vega_ids=vega_ids,gmax=gmax,
                counts=expect,roles=[move_roles(s,direct[s['id']],old['moves']) for s in old['species']])


def learning_body(raw):
    text=raw.decode(); marker='\nstable key:'
    need(marker in text and r.NEW_SHA in text,'後継表示のidentity/形式不一致')
    return 'stable key:'+text.split(marker,1)[1]


def render(inputs, data, source_head):
    need(bool(re.fullmatch('[0-9a-f]{40}',source_head)), 'source HEAD不正')
    files={};sp=data['species'];moves=data['moves'];abilities=data['abilities'];items=data['items']
    def put(name,text):
        need(name not in files and '..' not in PurePosixPath(name).parts and not name.startswith('/'),'出力重複/path')
        files[name]=output_bytes(name,text)
    def numtable(s): return table([v for _,v in STATS],[[s['base_stats'][k] for k,_ in STATS]])
    def abilitylinks(s,depth): return ' / '.join(link('abilities',abilities[a],depth) for a in s['ability_ids'])
    def specieslinks(ids,depth): return '、'.join(link('pokemon',sp[i],depth) for i in sorted(set(ids))) or '該当なし'
    def evolutions(rows):
        return table(['入力ID','条件表示','変換先','方法/引数/extra','確認区分'],[(link('pokemon',sp[e['species_id']],1),esc(e['condition']),link('pokemon',sp[e['target_id']],1),f"{e['method_id']} / {e['parameter']} / {e['extra']}",esc(e['condition_evidence'])) for e in rows]) if rows else '該当する登録行なし。未発見の実行経路の不存在証明ではありません。\n\n'
    family=defaultdict(list)
    for s in sp:family[s['base_species_id']].append(s['id'])
    for s in sp:
        sid=s['id'];text=head(str(sid)+' '+esc(s['name']),1)
        text+='stable key: `'+s['key']+'` / form: `'+s['form_key']+'` / registry base: '+str(s['base_species_id'])+'。\n\n'
        text+='## 基本性能\n\nタイプ: '+esc(' / '.join(dict.fromkeys(s['type_names'])))+'。通常1 / 通常2 / 隠れ: '+abilitylinks(s,1)+'。\n\n'+numtable(s)
        text+='分類: '+esc(s['classification'])+' / 全国番号: '+str(s['national_no'])+' / 静的最終段階扱い: '+str(s['final_evolution'])+'。\n\n'
        text+='同じregistry baseを持つ行: '+specieslinks(family[s['base_species_id']],1)+'。registryのbase欄と戦闘終了時の変換先は別に表示します。\n\n'
        text+='## 進化・変換と前段階\n\nmethod253/254等の特殊変換を通常進化と断定しません。\n\n'+evolutions(s['evolutions'])+evolutions(s['pre_evolutions'])
        text+='## 現役の直接データからの検索補助\n\n直接表には追加archiveも含みます。条件付きタマゴと持越しは下の候補抽出から除外しました。今いる場所で習得できることや自然供給を意味しません。effect keyによる候補抽出で、強さ・効果のnative受入ではありません。\n\n'
        for role,label in ROLES.items():
            text+='**'+label+'**: '+('、'.join(link('moves',moves[mid],1) for mid in data['roles'][sid][role]) or '該当なし')+'。\n\n'
        text+='## 入手・解禁・隠れ特性の境界\n\n以下は旧正本の供給定義・限定継承scopeです。全routeの自然到達を新たに受入していません。隠れslotが0なら夢特性追加済みとはしません。\n'+block(s['acquisition'])
        text+='## 現役の全習得・元順序・供給条件\n\n'+learning_body(inputs.bound(r.NEW,'pokemon/'+str(sid)+'.md'))
        put('pokemon/'+str(sid)+'.md',text)
    for move in moves:
        mid=move['id'];text=head(str(mid)+' '+esc(move['name']),1)
        text+='stable key: `'+move['key']+'`。\n\n'+table(['タイプ','分類','威力','命中','PP','優先度','効果ID','対象ID'],[[esc(move['type_name']),esc(move['category']),move['power'],move['accuracy'],move['pp'],move['priority'],move['effect_id'],move['target_id']]])
        text+='説明: '+esc(move['description'])+'。0威力/命中等の特殊解釈は実装scopeを参照してください。\n\n'
        text+='## 効果由来・Z/Max変換・確認状態\n\nsource定義やhandler名の存在を全対象native受入へ昇格しません。\n'+block({k:move[k] for k in ('effect_keys','effect_origin','effect_novelty','new_handler_verified','canonical_fields_evidence','generic_z','max_conversion')})
        direct=[sid for sid,c in data['inverse'][mid].items() if c & DIRECT];carry=[sid for sid,c in data['inverse'][mid].items() if c & CARRY]
        text+='## 新しい逆引き集計\n\n直接データ '+str(len(direct))+'種/フォーム、持越し参照 '+str(len(carry))+'種/フォーム（重複対象あり。合算しません）。\n\n直接: '+specieslinks(direct,1)+'。\n\n持越しのみを含む参照集合: '+specieslinks(carry,1)+'。\n\n'
        text+='条件付き繁殖: '+specieslinks([sid for sid,c in data['inverse'][mid].items() if 'conditional_egg' in c],1)+'。直接種数には加算しません。\n\n'
        text+='## 全経路の逆引き（後継原本表示）\n\n'+learning_body(inputs.bound(r.NEW,'moves/'+str(mid)+'.md'))
        put('moves/'+str(mid)+'.md',text)
    for a in abilities:
        text=head(str(a['id'])+' '+esc(a['name']),1)+'stable key: `'+a['key']+'`。\n\n説明: '+esc(a['description'])+'。\n\n'
        text+='## 実装・効果と未確認\n'+block({k:a.get(k) for k in ('effect_key','runtime_binding','implementation','status','project_added','notes')})
        text+='## 全所持種族・フォーム（slot別）\n\n隠れslotの登録と現在地での通常取得は別です。\n\n'+table(['種族/フォーム','slot'],[(link('pokemon',sp[o['species_id']],1),o['slot']) for o in data['owners'][a['id']]])
        put('abilities/'+str(a['id'])+'.md',text)
    for item in items:
        text=head(str(item['id'])+' '+esc(item['name']),1)+'stable key: `'+item['key']+'`。\n\n説明: '+esc(item['description'])+'。\n\n'
        text+=table(['価格table値','ポケット','持物効果ID','持物効果引数'],[[item['price'],esc(item.get('pocket','旧投影に欄なし・未確認')),item['hold_effect_id'],item_parameter(item)]])
        text+='## 役割・効果定義\n\n数値継承とcallback/意味定義の証明範囲を分離します。\n'+block({k:item.get(k) for k in ('role','hold_effect_key','battle_effect_key','battle_effect_param','field_effect_key','field_effect_param','target_policy','consume_policy','runtime_binding')})
        text+='## 供給・解禁と受入範囲\n\nショップ価格等は以下のsource定義が上のtable価格と異なる場合があります。未監査を不存在へ読み替えません。\n'+block(item['supply'])
        put('items/'+str(item['id'])+'.md',text)
    for entry in data['megas']:
        sid=entry['mega_species_id'];text=head('メガ '+esc(sp[sid]['name'])+' / '+str(sid),1)
        text+=link('pokemon',sp[entry['base_species_id']],1)+' → '+link('pokemon',sp[sid],1)+' / 必要石: '+link('items',items[entry['item_id']],1)+'。\n\n'
        text+='## 性能差・タイプ・特性\n'+block({k:entry[k] for k in ('stat_delta','types_before','types_after','ability_ids')})
        text+='## 発動・終了・併用・入手条件\n\n登録対応と自然入手/各終了経路の実測は別です。併用の未監査を許可へ変換しません。\n'+block({k:entry[k] for k in ('policy','stone','native_scope','native_status','reverse_entries','reverse_verified')})
        text+='## 画像資源の固定byte確認\n\n保存したfront/back/icon/paletteの範囲hashを数値系譜と同じ非変更証明で継承。全画面を新たに目視確認したものではありません。\n'+block(entry['assets'])
        put('mega/'+str(entry['base_species_id'])+'-'+str(sid)+'.md',text)
    for entry in data['gmax']:
        s=sp[entry['id']];base=sp[entry['base_id']]
        text=head('キョダイマックス登録 '+esc(s['name'])+' / '+str(s['id']),1)+link('pokemon',base,1)+' ↔ '+link('pokemon',s,1)+'。\n\n'
        text+='元種族はROMのmethod253逆変換行から対応付けました。registry baseが自分自身を指す欄を通常形態IDと誤読しません。\n\n'+numtable(s)
        text+='## 発動・終了・専用技・併用\n\n通常戦闘の発動条件/専用Max技/解除全経路/他機構との併用はこの候補の同scope native未監査です。登録だけで発動可能とはしません。技ごとの一般Max投影は技ページでsource定義として区別します。\n'+block(entry)
        text+='## 因子・道具・解禁source\n\nGMAX_FACTOR_ONLY等は正本の定義であって、現時点の自然取得を証明しません。必要道具がこの資料で確定しない場合も「不要」とはしません。\n'+block(s['acquisition'])
        text+='## 画像資源\n\n種族画像pointer tableは非変更継承済み。個別画像body/寸法/palette組合せの監査は未完です。メガ76件の資源照合結果を転用しません。\n'
        put('gmax/'+str(s['id'])+'.md',text)
    for i,z in enumerate(data['z_moves']):
        text=head('専用Z登録 '+str(i)+' / '+esc(moves[z['z_move_id']]['name']),1)
        text+=link('pokemon',sp[z['species_id']],1)+' + '+link('items',items[z['item_id']],1)+' + '+link('moves',moves[z['base_move_id']],1)+' → '+link('moves',moves[z['z_move_id']],1)+'。\n\n'
        text+='## 対応・発動・終了・併用・供給\n\nexact IDのみ。別フォームへの自動拡張や全handler/自然供給の受入は行いません。アニメーション/個別画像資源と終了状態の同scope監査は未完です。\n'+block(z)
        put('z/'+str(i)+'.md',text)
    # 元条件のanchorを保ったまま固定後継表示を再利用する。
    for i in range(256):put(f'conditions/{i:02x}.md',inputs.bound(r.NEW,f'conditions/{i:02x}.md'))
    put('SUPPLY_CONDITIONS.md',head('入手・供給・解禁の索引')+'[全道具と供給](ITEM_INDEX.md) / [全種族の供給定義](POKEMON_INDEX.md) / [隠れ特性](HIDDEN_ABILITY_INDEX.md)\n\n以下はIssue19習得原本の限定scopeをそのまま掲示します。「このWiki」は以下の引用区間では旧習得Wikiを指します。R0の数値継承は別途証明済みです。\n\n---\n\n'+inputs.bound(r.NEW,'SUPPLY_CONDITIONS.md').decode())
    put('DIFF_INDEX.md',head('旧候補との差分と非採用')+'種族値・タイプ・特性slot・技数値・進化登録・機構登録は5段の非変更範囲により継承。数値を調整した新ROMではありません。習得は後継ownerの現役表を採用し、旧表のままではありません。\n\n**持越し参照は直接付与と別、Side Change非採用、所有者承認overlay0。** membership差分はlevel順序・自然供給・実動作の差分ではありません。\n\n'+inputs.bound(r.NEW,'DIFF_INDEX.md').decode())
    def comparison(ids):
        return table(['ID/名称','stable key / form','静的段階','タイプ',*[v for _,v in STATS],'通常1 / 通常2 / 隠れ','一致/先制/回復/積み/妨害'],[(link('pokemon',sp[sid]),esc(sp[sid]['key']+' / '+sp[sid]['form_key']),'最終扱い' if sp[sid]['final_evolution'] else '進化行あり',esc('/'.join(dict.fromkeys(sp[sid]['type_names']))),*[sp[sid]['base_stats'][k] for k,_ in STATS],abilitylinks(sp[sid],0),'/'.join(str(len(data['roles'][sid][k])) for k in ROLES)) for sid in ids])
    put('VEGA_BALANCE_INDEX.md',head('ベガと関連フォーム206行の横比較')+'元比較表の対象IDを保ち、検索補助を後継の直接習得データから再計算しました。列の件数は強さ評価ではありません。ブラウザ内検索でID/key/タイプ/特性を絞れます。\n\n'+comparison(data['vega_ids']))
    put('POKEMON_INDEX.md',head('全1671種族・フォーム')+'[ベガ横比較](VEGA_BALANCE_INDEX.md)。ID0や非学習ownerも識別のため収録。収集対象数や自然入手可能数ではありません。\n\n'+comparison(range(1671)))
    put('MOVE_INDEX.md',head('全1063技と直接/持越し逆引き')+table(['技','key','タイプ','分類','威力','命中','PP','優先度','直接種数','持越し種数'],[(link('moves',m),m['key'],esc(m['type_name']),esc(m['category']),m['power'],m['accuracy'],m['pp'],m['priority'],sum(bool(c&DIRECT) for c in data['inverse'][m['id']].values()),sum(bool(c&CARRY) for c in data['inverse'][m['id']].values())) for m in moves]))
    put('ABILITY_INDEX.md',head('全318特性と所持slot逆引き')+table(['特性','key','説明','所持slot数','handler/native区分'],[(link('abilities',a),a['key'],esc(a['description']),len(data['owners'][a['id']]),esc(a['implementation'])) for a in abilities]))
    put('HIDDEN_ABILITY_INDEX.md',head('隠れ特性と供給条件')+'隠れslot0は未割当です。登録、パッチ適用条件、自然供給、全route受入を分離します。種族ページの供給定義と道具ページのscopeを参照してください。\n\n'+table(['種族/フォーム','隠れslot'],[(link('pokemon',s),link('abilities',abilities[s['ability_ids'][2]])) for s in sp]))
    put('ITEM_INDEX.md',head('全1044道具・供給')+table(['道具','key','table価格','役割','供給定義'],[(link('items',i),i['key'],i['price'],esc(i.get('role','未投影 / '+i['classification'])),esc(i['supply'].get('source','未確認')) if isinstance(i['supply'],dict) else '個別参照') for i in items]))
    put('MEGA_INDEX.md',head('メガ76件・個別資源・条件')+'登録77行中、逆対応を確認した76対応行（変換先は75フォーム）。2つの元IDが同じ変換先を持つ対応も個別保持し、旧自己参照登録を新メガと数えません。\n\n'+table(['元種族','変換先と個別証拠','石'],[(link('pokemon',sp[x['base_species_id']]),'['+esc(sp[x['mega_species_id']]['name'])+'](mega/'+str(x['base_species_id'])+'-'+str(x['mega_species_id'])+'.md)',link('items',items[x['item_id']])) for x in data['megas']]))
    put('GMAX_INDEX.md',head('キョダイマックス34登録・未監査範囲')+'FORM_KEY_*_GIGAを34件収録。対応はmethod253の逆変換登録に結合し、因子/入手sourceと同scope native未確認を分離します。\n\n'+table(['通常側（逆変換登録）','Gmax側の個別証拠','資源/native'],[(link('pokemon',sp[x['base_id']]),'['+str(x['id'])+': '+esc(sp[x['id']]['name'])+'](gmax/'+str(x['id'])+'.md)','pointer table継承 / 個別body・native未監査') for x in data['gmax']]))
    put('Z_MOVE_INDEX.md',head('専用Z31登録と汎用Z/Max')+'汎用Zと一般Maxの数値・source投影は各[技ページ](MOVE_INDEX.md)に全件掲載。専用Zの対応byteと効果handler/併用/解除受入を分離します。\n\n'+table(['対象種族ID','道具','元技','専用Zと個別証拠'],[(link('pokemon',sp[z['species_id']]),link('items',items[z['item_id']]),link('moves',moves[z['base_move_id']]),'['+esc(moves[z['z_move_id']]['name'])+'](z/'+str(i)+'.md)') for i,z in enumerate(data['z_moves'])]))
    put('LIMITATIONS.md',head('証拠区分・未確認・保存安全性')+'''| 区分 | R0で意味すること |
| --- | --- |
| ROM数値の継承 | 旧46487d98の読取と受入済み5段の宣言差分非交差。新候補ROMの再構成/再測定ではない。 |
| GENERATED_CANONICAL / source定義 | 入手、効果、policyの定義。自然到達/全handler動作の証明ではない。 |
| INHERITED_ACCEPTED | 原本に書かれた限定scopeだけ継承。別種族/解除/Saveへ自動拡張しない。 |
| 同scope新native | このR0作業では0件。存在しない成功を追加しない。 |
| DEFERRED_AUDIT / 未確認 | 必要な実装や供給が不存在という意味ではない。 |
| 未実装 | 原本が明示する場合だけ使用。未監査と区別する。 |
| 所有者検討 | 承認0、性能/特性/技/新形態の変更0。 |

全クリ走破は所有者により対象外（PASSではない）。Save101と原本を保全し、保存制御統合・容量/owner移管・高ID幅・失敗復旧・必要な局所Save/fresh Continueは未完です。容量分類784/未知90、安全容量0。R0は試遊・製品完成・release承認ではありません。

メガ資源bodyの証拠をGmaxへ転用せず、専用Z対応を別フォームへ拡張しません。習得表のmembership、archive選択、自然供給、戦闘、保存は別ゲートです。持越し・条件付き繁殖は直接付与と区別します。

全体private guardの既存違反と無関係なCI障害は別台帳に残し、新出力の範囲検査を全体PASSと呼びません。baseline/merge/releaseは不変です。
''')
    put('OWNER_PROPOSALS.md',head('承認案との結合入口')+'''この版を基準に、対象ID/stable key/form、現在値、提案後の値、理由、対象ページ、R0の意味hashを指定できます。提出や記入は実装承認ではありません。

`owner_approved_overlay=[]`、承認済みbatch0を保持。次の情報を所有者の明示指示から記録し、依存条件と保存互換を確認してから限定実装します。

```json
{"reference_revision":"R0","reference_semantic_sha256":"data/index.jsonを参照","target_id":null,"stable_key":null,"form_key":null,"before":null,"after":null,"rationale":null,"approval_status":"NOT_APPROVED"}
```

自動の役割タグから採用案や対象種を創作しません。所有者の案待ちだけで後続の保存基盤作業を止めません。
''')
    put('CODEX_INDEX.md',head('機械可読データと再生成')+'[data/index.json](data/index.json) に入力HEAD・候補・全入力hash・意味hash・出力hashを固定。[種族要約](data/species.jsonl)、[技逆引き](data/moves.jsonl)、[特性逆引き](data/abilities.jsonl)、[機構](data/mechanics.json)、[現役経路参照](data/active_sources.json) を提供します。全経路・条件の元JSONは候補固定のIssue19ディレクトリに保持し、R0 manifestでbyteを束縛します。\n\n```bash\npython3 -B scripts/pr16_wiki_r0_build.py check\n```\n\ncheckは入力・全生成byte・ファイル集合・リンク・mtimeを照合し、書き込みません。buildは別R0出力だけを生成し、同一内容の再書込みをしません。公開後のR0を調整版へ上書きせず次のreview revisionを別途作ります。\n')
    navigation=[('VEGA_BALANCE_INDEX.md','ベガ206行の性能横比較'),('POKEMON_INDEX.md','全1671種族・フォームと全習得'),('MOVE_INDEX.md','1063技・直接/持越し逆引き'),('ABILITY_INDEX.md','318特性とslot別逆引き'),('HIDDEN_ABILITY_INDEX.md','隠れ特性と供給境界'),('MEGA_INDEX.md','76メガと画像資源'),('GMAX_INDEX.md','34キョダイマックス登録'),('Z_MOVE_INDEX.md','31専用Z・汎用Z/Max'),('ITEM_INDEX.md','1044道具と供給'),('SUPPLY_CONDITIONS.md','入手・解禁と限定受入'),('DIFF_INDEX.md','旧基準からの意味差分'),('LIMITATIONS.md','証拠区分・保存/製品の未完'),('OWNER_PROPOSALS.md','承認案の記入入口'),('CODEX_INDEX.md','機械可読データと検証')]
    put('README.md',head('ポケモンベガ Modern 調整基準Wiki R0')+'**性能比較・調整案の参照用です。試遊版・配布版の完成宣言ではありません。**\n\n'+table(['読む対象','入口'],[(label,'[開く]('+path+')') for path,label in navigation])+'旧P08数値を5段階・7,013範囲の非変更証明で後継候補へ結合し、現役128,389経路/109,659条件は後継の採用表だけを使います。持越し35,211行を直接習得数へ足しません。未承認調整0。\n\n入力source HEAD: `'+source_head+'`。識別情報は[data/index.json](data/index.json)。\n')
    species_data=[{'id':s['id'],'key':s['key'],'name':s['name'],'form_key':s['form_key'],'registry_base_id':s['base_species_id'],'types':s['types'],'type_names':s['type_names'],'base_stats':s['base_stats'],'ability_ids':s['ability_ids'],'evolutions':s['evolutions'],'numeric_evidence':'INHERITED_ROM_RANGE_PROOF','direct_move_ids':sorted(data['direct'][s['id']]),'carry_move_ids':sorted(data['carry'][s['id']]),'conditional_egg_move_ids':sorted(data['conditional'][s['id']]),'role_search_hints':data['roles'][s['id']]} for s in sp]
    move_data=[{k:m[k] for k in ('id','key','name','power','accuracy','pp','priority','type_id','type_name','category','effect_id','effect_keys')}|{'numeric_evidence':'INHERITED_ROM_RANGE_PROOF','owners':[{'species_id':sid,'consumers':sorted(c)} for sid,c in sorted(data['inverse'][m['id']].items())]} for m in moves]
    ability_data=[{'id':a['id'],'key':a['key'],'name':a['name'],'description':a['description'],'owners':data['owners'][a['id']]} for a in abilities]
    for name,values in [('species',species_data),('moves',move_data),('abilities',ability_data)]:put('data/'+name+'.jsonl',b''.join(compact(v) for v in values))
    mechanics={'megas':data['megas'],'gmax':data['gmax'],'z_moves':data['z_moves'],'owner_approved_overlay':[]}
    put('data/mechanics.json',r.encode(mechanics))
    active={name:{'path':r.NEW+'/data/'+name,'binding':r.identity(inputs.bound(r.NEW,'data/'+name))} for name in ('routes_index.json','conditions_index.json','supply.jsonl','membership_diff.jsonl')}
    put('data/active_sources.json',r.encode(active))
    semantic=r.identity(compact({'species':species_data,'moves':move_data,'abilities':ability_data,'mechanics':mechanics,'active':active,'items':items,'vega_ids':data['vega_ids'],'catalogue_semantics':{name:[{k:v for k,v in row.items() if k not in {'learner_count','learner_species_ids','vega_learner_species_ids','preservation_only_species_ids','fixed_gift_moves','wild_initial_moves'}} for row in data[name]] for name in ('species','moves','abilities','evolutions')}}))['sha256']
    for name in CODE: inputs.take(name)
    manifest={'schema_version':1,'task':TASK,'review_revision':'R0','source_head':source_head,'candidate':inputs.rec['candidate'],'numeric_reconciliation':r.REPORT,'input_bindings':dict(sorted(inputs.bindings.items())),'semantic_sha256':semantic,'counts':data['counts']|{'vega_comparison_rows':206,'abilities':318,'items':1044,'megas':76,'mega_mapping_rows':76,'mega_distinct_forms':75,'gmax_registered':34,'z_special':31},'files':{n:r.identity(b) for n,b in sorted(files.items())},'accepted_tests_rerun':0,'new_native_processes':0,'rom_reconstructions':0,'release_ready':False,'active_baseline_changed':False}
    manifest['tree_sha256']=r.identity(compact(manifest['files']))['sha256']
    put('data/index.json',r.encode(manifest))
    return files,manifest


LINK=re.compile(r'(?<!!)\[[^\]\n]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)')
ANCHOR=re.compile(r'<a\s+id="([^"]+)"\s*>')


def validate_links(files):
    """新R0内部だけを検証。外部/旧候補への誤リンクは許可しない。"""
    anchors={n:set(ANCHOR.findall(b.decode())) for n,b in files.items() if n.endswith('.md')}
    count=0
    for name,body in files.items():
        if not name.endswith('.md'):continue
        text=re.sub(r'```.*?```','',body.decode(),flags=re.S)
        for target in LINK.findall(text):
            url=urlsplit(html.unescape(target));need(not url.scheme and not url.netloc and not url.query,'外部リンク禁止: '+name)
            path=unquote(url.path);need(not path.startswith('/') and '\\' not in path,'link絶対path')
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),path)) if path else name
            need(resolved in files,'リンク先欠落: '+name+' -> '+target)
            if url.fragment:need(unquote(url.fragment) in anchors.get(resolved,set()),'anchor欠落: '+target)
            count+=1
    return count


def generate(root, source_head):
    inputs=Inputs(root);data=model(inputs);files,manifest=render(inputs,data,source_head)
    links=validate_links(files)
    return files,manifest,links


def write_outputs(root,files):
    folder=root/OUT
    for name in files:
        rel=PurePosixPath(name)
        need(name==rel.as_posix() and not rel.is_absolute() and '..' not in rel.parts and '\\' not in name,'出力相対path不正')
        current=root
        for part in PurePosixPath(OUT+'/'+name).parts:
            current/=part;need(not current.is_symlink(),'出力経路symlink禁止')
    if folder.exists():
        actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
        need(actual<=set(files),'stale出力は無断削除しない')
    for name,raw in files.items():
        path=folder/name;need(not path.is_symlink(),'出力symlink禁止');path.parent.mkdir(parents=True,exist_ok=True)
        if not path.exists() or path.read_bytes()!=raw:path.write_bytes(raw)


def check(root):
    stored=r.load(r.read(root,INDEX));folder=root/OUT
    names=set(stored['input_bindings'])|{OUT+'/'+n for n in stored['files']}|{INDEX}
    before={n:(r.identity(r.read(root,n)),(root/n).stat().st_mtime_ns) for n in names}
    files,manifest,links=generate(root,stored['source_head'])
    actual={p.relative_to(folder).as_posix() for p in folder.rglob('*') if p.is_file()}
    need(actual==set(files),'R0ファイル集合不一致')
    for name,raw in files.items():need(r.read(root,OUT+'/'+name)==raw,'出力byte不一致: '+name)
    after={n:(r.identity(r.read(root,n)),(root/n).stat().st_mtime_ns) for n in names}
    need(before==after,'checkの書込み副作用')
    return {'status':'PASS','files':len(files),'links':links,'read_only_byte_mtime':True,'deterministic_output':True,'semantic_sha256':manifest['semantic_sha256'],'tree_sha256':manifest['tree_sha256']}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['build','check']);parser.add_argument('--source-head')
    args=parser.parse_args()
    if args.command=='check':print(json.dumps(check(ROOT)));return
    files,manifest,links=generate(ROOT,args.source_head);write_outputs(ROOT,files)
    print(json.dumps({'status':'BUILT_NOT_PUBLISHED','files':len(files),'links':links,'semantic_sha256':manifest['semantic_sha256']}))


if __name__=='__main__':main()
