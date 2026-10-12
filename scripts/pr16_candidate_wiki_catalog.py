#!/usr/bin/env python3
"""Wiki用のID結合・供給の証拠分離・Stage61意味差分。ゲームデータは編集しない。"""
from __future__ import annotations
from collections import Counter, defaultdict
import json
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, STATE, need, stable

TYPES = {0:'ノーマル',1:'かくとう',2:'ひこう',3:'どく',4:'じめん',5:'いわ',6:'むし',7:'ゴースト',8:'はがね',9:'？？？',10:'ほのお',11:'みず',12:'くさ',13:'でんき',14:'エスパー',15:'こおり',16:'ドラゴン',17:'あく',23:'フェアリー',24:'ステラ'}
CATEGORIES = {0:'物理',1:'特殊',2:'変化'}
GROWTH = {0:'中',1:'不規則',2:'変動',3:'やや遅い',4:'早い',5:'遅い'}
EGGS = {0:'なし',1:'怪獣',2:'水中1',3:'虫',4:'飛行',5:'陸上',6:'妖精',7:'植物',8:'人型',9:'水中3',10:'鉱物',11:'不定形',12:'水中2',13:'メタモン',14:'ドラゴン',15:'未発見'}
SLOTS = ('通常1','通常2','隠れ')
DIRECT = {'level_up','egg','machine','tutor','shared_egg','move_memory_reminder','machine_archive','tutor_archive','conditional_egg'}
SUPPLY_UNKNOWN = 'SUPPLY_NOT_FOUND_IN_CURRENT_SOURCES'
DEFERRED = 'DEFERRED_AUDIT'
IMPLEMENTED = 'IMPLEMENTED_NOT_NATIVE_ACCEPTED'
CANONICAL = 'GENERATED_CANONICAL'
EXACT = 'EXACT_CANDIDATE_ROM'
INHERITED = 'INHERITED_ACCEPTED'
ROUTES = {'level_up':'レベルアップ','egg':'タマゴ','machine':'TM/HM互換','tutor':'教え技互換','shared_egg':'共有タマゴ技','move_memory_reminder':'わざメモリー','machine_archive':'TMアーカイブ','tutor_archive':'教え技アーカイブ','build_learnable_preservation':'保持履歴（直接習得ではない）','conditional_egg':'条件付きタマゴ','wild_initial':'野生初期技','fixed_gift':'固定配布・イベント','form_specific':'フォーム固有'}
STATS = ('hp','attack','defense','sp_attack','sp_defense','speed','total')


def indexed(rows: list[dict], domain: str) -> dict[int, dict]:
    result = {r['id']:r for r in rows}
    need(len(result)==len(rows) and sorted(result)==list(range(len(rows))), domain+' ID不連続/重複')
    need(len({r['key'] for r in rows})==len(rows), domain+' key重複')
    return result


def subset(row: dict, *keys: str) -> dict:
    return {k:row[k] for k in keys if k in row}


def known_route(row: dict, source: str) -> dict:
    return dict(row, source_path=source, evidence=CANONICAL,
                current_route_native_acceptance=DEFERRED)


def history_rows(history: dict, learnsets: dict[int, dict]) -> list[dict]:
    """原本全行を保持。元routeのlevel/slotまで一致しない場合は同等としない。"""
    result = []
    for group, rows in sorted(history['groups'].items()):
        for source in rows:
            routes = learnsets[source['species_id']]['routes']
            candidates = [r for r in routes if r['move_id']==source['move_id']]
            same_route = [r for r in candidates if r['route']==source['route']]
            params = source['source_parameters']
            exact = [r for r in same_route if
                     (source['route']!='level_up' or r.get('level')==int(params['level'])) and
                     (source['route'] not in ('machine','tutor') or r.get('slot')==int(params['slot_no']))]
            result.append(dict(source, group=group, same_move_present=bool(candidates),
                original_route_present=bool(same_route), original_parameters_present=bool(exact),
                current_teaching_routes=sorted({r['route'] for r in candidates if r['route'] in DIRECT}),
                preservation_history_present=any(r['route']=='build_learnable_preservation' for r in candidates),
                evidence=CANONICAL, comparison_evidence=EXACT))
    return result


def normal_learnset(routes: list[dict]) -> Counter:
    # Stage61のmachine/tutor一覧はslot番号を保存していないので技IDの多重集合だけを比較。
    return Counter((r['route'],r['move_id'],r.get('level') if r['route']=='level_up' else None)
                   for r in routes if r['route'] in {'level_up','egg','machine','tutor'})


def old_routes(species: dict) -> list[dict]:
    result = []
    for route, rows in species['learnsets'].items():
        mapped = {'machine_runtime':'machine','tutor_runtime':'tutor'}.get(route,route)
        for row in rows:
            result.append(dict(row,route=mapped) if isinstance(row,dict) else {'route':mapped,'move_id':row})
    return result


def counter_rows(counter: Counter) -> list[dict]:
    return [dict(route=key[0],move_id=key[1],level=key[2],occurrences=count)
            for key,count in sorted(counter.items(),key=lambda item: (item[0][0],item[0][1],-1 if item[0][2] is None else item[0][2]))]


def performance_diff(species: list[dict], moves: list[dict], abilities: list[dict], items: list[dict],
                     learnsets: dict, evolutions: list[dict], megas: list[dict], old: dict, baseline: dict) -> dict:
    current = {'species':species,'moves':moves,'abilities':abilities,'items':items}
    result = {'baseline':baseline['active_rom'],'identity_policy':'数値IDとstable keyを検査。pointer移動を性能変更に数えない。',
              'id_changes':{},'species':[],'moves':[],'learnsets':[],'evolutions':[], 'megas':[],
              'exclusive_z_mapping':{'status':'BASELINE_FIELD_NOT_RECORDED','evidence':DEFERRED},
              'not_comparable_fields':['Stage61に未収録のZ mapping','Stage61に未収録のarchive/共有タマゴ/保持履歴','Stage61に未収録のZ/Max詳細とconsumer証拠'],
              'pointer_layout_is_not_performance_change':True}
    for domain, rows in current.items():
        before={r['id']:r for r in old[domain]}; after={r['id']:r for r in rows}
        common=set(before)&set(after)
        need(all(before[i]['key']==after[i]['key'] for i in common),domain+'同じIDでstable keyが変わっている')
        result['id_changes'][domain]={'added':[subset(after[i],'id','key','name') for i in sorted(set(after)-set(before))],
                                     'removed':[subset(before[i],'id','key','name') for i in sorted(set(before)-set(after))]}
    for row in species:
        if row['id']>=len(old['species']):continue
        before=old['species'][row['id']]
        fields={}
        for key, a,b in [('base_stats',before['base_stats'],row['base_stats']),
                        ('types',[r['id'] for r in before['types']],row['types']),
                        ('ability_ids',[r['id'] for r in before['abilities']],row['ability_ids']),
                        ('ev_yield',before['ev_yield'],row['ev_yield']),
                        ('capture_rate',before['capture_rate'],row['capture_rate']),
                        ('exp_yield',before['exp_yield'],row['exp_yield']),
                        ('gender_ratio',before['gender_ratio'],row['gender_ratio'])]:
            if a!=b: fields[key]={'before':a,'after':b}
        if fields:result['species'].append({'id':row['id'],'key':row['key'],'fields':fields})
        a=normal_learnset(old_routes(before));b=normal_learnset(learnsets[row['id']]['routes'])
        if a!=b:result['learnsets'].append({'species_id':row['id'],'species_key':row['key'],
                                          'added':counter_rows(b-a),'removed':counter_rows(a-b),
                                          'machine_tutor_slot_comparison':'BASELINE_SLOT_NOT_RECORDED'})
    old_effects={r['effect_id'] for r in old['moves']}
    for row in moves:
        row['effect_novelty']='EXISTING_EFFECT_ID_REUSED' if row['effect_id'] in old_effects else 'EFFECT_ID_NOT_IN_STAGE61_MOVE_ROWS'
        row['new_handler_verified']=False
        if row['id']>=len(old['moves']):continue
        before=old['moves'][row['id']]; fields={}
        pairs=[(k,before[k],row[k]) for k in ('power','accuracy','pp','priority','effect_id','flags','target_id')]
        pairs += [('type_id',before['type']['id'],row['type_id']),('category',before['category'],row['category']),
                  ('secondary_percent',before.get('secondary_percent',before.get('secondary')),row['secondary_percent'])]
        for key,a,b in pairs:
            if a is not None and a!=b:fields[key]={'before':a,'after':b}
        if fields:result['moves'].append({'id':row['id'],'key':row['key'],'fields':fields})
    def evo_key(r): return (r['species_id'],r['method_id'],r['parameter'],r['target_id'],r.get('extra',0))
    a=Counter(evo_key(dict(r,species_id=s['id'])) for s in old['species'] for r in s['evolutions'])
    b=Counter(evo_key(r) for r in evolutions)
    for label,changes in [('added',b-a),('removed',a-b)]:
        for key,count in sorted(changes.items()):
            result['evolutions'].append(dict(change=label,species_id=key[0],method_id=key[1],parameter=key[2],target_id=key[3],extra=key[4],occurrences=count))
    old_megas={(key[0],key[2],key[3],key[4]) for key in a if key[1]==254 and key[2]}
    for row in megas:
        key=(row['base_species_id'],row['item_id'],row['mega_species_id'],row['variant'])
        if key not in old_megas:
            result['megas'].append(dict(change='MAPPING_NOT_IN_STAGE61',**subset(row,'base_species_id','mega_species_id','item_id','variant')))
    return result


def assemble(d: dict, inputs: Inputs) -> dict:
    """ROM由来の値と、canonical供給・履歴・限定native証拠を別fieldで結合する。"""
    ids=d['registries']; species=d['species']; moves=d['moves']; abilities=d['abilities']; items=d['items']
    by={k:indexed(v,k) for k,v in [('species',species),('moves',moves),('abilities',abilities),('items',items)]}
    need(d['counts']=={'species':len(species),'move':len(moves),'ability':len(abilities),'item':len(items)},'projection件数不一致')
    canonical=d['canonical']; supply=canonical['content/collection_supply_v1/canonical_model.json']
    acquisition_path='vendor/vega_acquisition/content/species_acquisition_routes.csv'
    acquisition=defaultdict(list)
    for r in canonical[acquisition_path]:acquisition[r['species_key']].append(known_route(r,acquisition_path))
    for name,key in [('forms','species_key'),('pool_entries','species_key')]:
        for r in supply[name]:acquisition[r[key]].append(known_route(r,'content/collection_supply_v1/canonical_model.json#'+name))
    for r in supply['gifts']:
        if 'form_index' in r:
            form=supply['forms'][r['form_index']]
            acquisition[form['species_key']].append(known_route(r,'content/collection_supply_v1/canonical_model.json#gifts'))
    for r in canonical['vendor/vega_acquisition/content/acquisition_events.csv']:
        for key in r['target_species_keys'].split('|'):
            acquisition[key].append(known_route(r,'vendor/vega_acquisition/content/acquisition_events.csv'))
    requirements={(r['from_species_key'],r['to_species_key']):r for r in canonical['vendor/vega_acquisition/content/evolution_requirements_553.csv']}
    evos=d['evolutions']; outs=defaultdict(list); ins=defaultdict(list)
    for row in evos:
        need(row['species_id'] in by['species'] and row['target_id'] in by['species'],'進化参照不正')
        condition = requirements.get((row['species_key'],row['target_key']),{}).get('integrated_condition')
        row['condition']=('Lv.'+str(row['parameter']) if row['method_id']==4 else condition or 'method='+str(row['method_id'])+' / parameter='+str(row['parameter'])+' / extra='+str(row['extra']))
        row['condition_evidence']=EXACT if row['method_id']==4 else CANONICAL if condition else DEFERRED
        outs[row['species_id']].append(row);ins[row['target_id']].append(row)
    form_base={r['target_species']:r['base_species'] for r in supply['forms']}
    for m in d['megas']:form_base[m['mega_species_id']]=m['base_species_id']
    rock=canonical['config/modernization_rockruff_own_tempo_stage75.json'];form_base[rock['identity']['species_id']]=rock['identity']['normal_species_id']
    owners=defaultdict(list); hidden=[]; ve_ids=set()
    for row in species:
        sid=row['id']; registry=ids['species'][sid]
        row.update({k:registry.get(k,'') for k in ('classification','form_key','national_no')})
        row['base_species_id']=registry.get('base_species_id',form_base.get(sid,sid))
        row['base_species_key']=by['species'][row['base_species_id']]['key']
        row['form_status']='MEGA_BATTLE_ONLY' if any(r['mega_species_id']==sid for r in d['megas']) else row['classification']
        row['type_names']=[TYPES.get(t,'TYPE_'+str(t)) for t in row['types']]
        row['growth']=GROWTH.get(row['growth_id'],'UNKNOWN');row['egg_groups']=[EGGS.get(t,'EGG_'+str(t)) for t in row['egg_group_ids']]
        row['evolutions']=outs[sid];row['pre_evolutions']=ins[sid]
        row['final_evolution']=not any(r['method_id'] not in (252,253,254) for r in outs[sid])
        row['acquisition']=acquisition[row['key']]
        row['wild_initial_moves']={'status':DEFERRED,'reason':'現候補の全野生header/生成level/固定movesetを未抽出。一般レベル技から野生の実初期技を断定しない。'}
        row['fixed_gift_moves']={'status':DEFERRED,'reason':'canonical入手経路は併記するが、固定配布の実movesetを未抽出。'}
        row['abilities']=[]
        for slot,aid in zip(SLOTS,row['ability_ids']):
            need(aid in by['abilities'],'特性ID参照不正')
            ability=by['abilities'][aid]
            row['abilities'].append(dict(subset(ability,'id','key','name','description'),slot=slot,evidence=EXACT))
            if aid:owners[aid].append({'species_id':sid,'species_key':row['key'],'slot':slot})
        row['hidden_ability']={'species_id':sid,'species_key':row['key'],'ability_id':row['ability_ids'][2],
            'slot_evidence':EXACT,'assigned':row['ability_ids'][2]!=0,
            'first_supply':SUPPLY_UNKNOWN if row['ability_ids'][2] else 'NOT_ASSIGNED',
            'wild_probability':DEFERRED,'fixed_gift':DEFERRED,'raid':DEFERRED,'patch':DEFERRED,'breeding':DEFERRED,
            'reason':'隠れslotと初回供給の証拠は別。通常入手表にあるだけでは隠れslot供給と扱わない。'}
        hidden.append(row['hidden_ability'])
        if row['classification']=='VEGA_ORIGINAL':ve_ids.add(sid)
    # オリジナルの関連formだけを閉包追加。公式と同じ進化先に接続するだけで公式全系統をVega化しない。
    changed=True
    while changed:
        extra={r['id'] for r in species if r['base_species_id'] in ve_ids}-ve_ids
        changed=bool(extra);ve_ids.update(extra)
    item_supply={r['item_id']:known_route(r,'content/collection_supply_v1/canonical_model.json#items') for r in supply['items']}
    shop=canonical['content/modernization/mega_shop_catalog.json']
    for r in shop['entries']:
        item_supply[r['item_id']]=dict(subset(r,'item_id','item_key','price_bp','quantity','claim_flag'),
            source='MEGA_BP_SHOP',unlock=shop['unlock'],repeatability='ONCE_PER_CLAIM_FLAG',evidence=CANONICAL,
            source_path='content/modernization/mega_shop_catalog.json',current_route_native_acceptance=INHERITED,
            acceptance_scope='catalog・通常UI購入経路の限定受入。全品の独立native試験を意味しない。')
    for row in items:row['supply']=item_supply.get(row['id'],{'status':SUPPLY_UNKNOWN})
    runtime=canonical['config/modernization_p05_ability_runtime.json']
    added={r['canonical_id']:r for r in runtime['ability_allocation']['rows']}
    for row in abilities:
        row['owners']=owners[row['id']];row['project_added']=row['id'] in added
        row['implementation']= {'battle_core':IMPLEMENTED,'ai':DEFERRED,'circus_suppression':DEFERRED,
            'native_scope':'全所有種族・全routeの受入を意味しない。'}
        if row['id'] in added:
            entry=added[row['id']];row['allocation']=entry
            row['integration_hooks']=[r for r in runtime['integration_hooks'] if entry['ability_key'] in r.get('ability_keys',[])]
            row['runtime_profile']=runtime['runtime_profile']['abilities'].get(entry['ability_key'],{})
            row['implementation']['battle_core']=INHERITED
            row['implementation']['native_evidence']='content/modernization/p08_native_mega_acceptance.json'
    learns={r['species_id']:r for r in d['learnsets']};move_owners=defaultdict(set);historical_owners=defaultdict(set)
    for sid,row in learns.items():
        for r in row['routes']:
            mid=r['move_id'];need(mid in by['moves'] and r['move_key']==by['moves'][mid]['key'],'習得技key参照不正')
            (move_owners if r['route'] in DIRECT else historical_owners)[mid].add(sid)
    effects=defaultdict(list)
    for key,value in d['source_model']['effect_ids'].items():effects[value].append(key)
    for row in moves:
        mid=row['id'];row['type_name']=TYPES.get(row['type_id'],'TYPE_'+str(row['type_id']));row['category']=CATEGORIES.get(row['category_id'],'UNKNOWN')
        row['effect_keys']=sorted(effects[row['effect_id']])
        row['canonical_fields']=d['source_model']['cfru_battle_fields'].get(str(mid),{})
        row['canonical_fields_evidence']=CANONICAL
        row['category_tables']=[dict(table=name,**subset(value,'evidence','consumer_proof','matches')) for name,value in d['move_categories'].items() if mid in value['move_ids']]
        row['learner_species_ids']=sorted(move_owners[mid]);row['learner_count']=len(move_owners[mid]);row['vega_learner_species_ids']=sorted(move_owners[mid]&ve_ids)
        row['preservation_only_species_ids']=sorted(historical_owners[mid]-move_owners[mid])
        row['max_conversion']={'canonical_power':d['source_model']['max_powers'].get(str(mid)),'evidence':CANONICAL,'consumer_proof':DEFERRED}
        row['generic_z']={'power':row['z_power'],'status_effect_id':row['z_effect'],'evidence':EXACT,'target_mapping_audit':DEFERRED}
    mega_by_species=defaultdict(list)
    for m in d['megas']:
        need(m['item_id'] in by['items'],'mega道具参照不正')
        m['stone']=subset(by['items'][m['item_id']],'id','key','name','supply')
        m['abilities']=[subset(by['abilities'][i],'id','key','name','project_added') for i in m['ability_ids']]
        inherited=any(i in added for i in m['ability_ids'])
        m['native_status']=INHERITED if inherited else IMPLEMENTED
        m['native_scope']={'turn_revert_cold_save':INHERITED if inherited else IMPLEMENTED,
                          'switch':DEFERRED,'faint':DEFERRED,'battle_end':DEFERRED,
                          'source':'content/modernization/p08_native_mega_acceptance.json' if inherited else None,
                          'warning':'限定6特性の過去原本と現P08移送記録を継承。全77形態の個別受入ではない。'}
        m['policy']={'ring_item_id':shop['unlock']['item_id'],'once_per_battle':CANONICAL,'circus':'mode policyに従う。形態別独立試験はDEFERRED_AUDIT。'}
        for sid in (m['base_species_id'],m['mega_species_id']):mega_by_species[sid].append(m['mega_species_id'])
    zs=[];z_by_species=defaultdict(list)
    for source in d['special_z_moves']['rows']:
        sid,iid,base,zid=(source[k] for k in ('species_id','item_id','base_move_id','z_move_id'))
        need(sid in by['species'] and iid in by['items'] and base in by['moves'] and zid in by['moves'],'専用Z参照不正')
        row=dict(source,species_key=by['species'][sid]['key'],item_key=by['items'][iid]['key'],base_move_key=by['moves'][base]['key'],z_move_key=by['moves'][zid]['key'],
                 z_move=subset(by['moves'][zid],'id','key','name','type_id','type_name','category','power','accuracy','target_id','effect_id','effect_keys'),
                 item=subset(by['items'][iid],'id','key','name','supply'),mapping_proof=d['special_z_moves']['proof'],
                 native_e2e=IMPLEMENTED,handler_proof=DEFERRED,
                 battle_policy={'once_per_battle':CANONICAL,'species_form_match':'表のSpecies IDが対象。別formへ自動拡張しない。','consumer_runtime_audit':DEFERRED})
        zs.append(row);z_by_species[sid].append(len(zs)-1)
    for row in species:row['mega_forms']=mega_by_species[row['id']];row['special_z_rows']=z_by_species[row['id']]
    baseline=inputs.json('docs/wiki/stage61/data/index.json')
    old={k:inputs.jsonl('docs/wiki/stage61/data/'+k+'.jsonl') for k in ('species','moves','abilities','items')}
    diff=performance_diff(species,moves,abilities,items,learns,evos,d['megas'],old,baseline)
    species_changed={r['id'] for r in diff['species']}|{r['species_id'] for r in diff['learnsets']}
    move_changes={r['id']:r['fields'] for r in diff['moves']}
    for row in moves:row['stage61_changes']=move_changes.get(row['id'],{})
    historical=history_rows(d['p07_source_rows'],learns)
    vega=[]
    for sid in sorted(ve_ids):
        row=by['species'][sid];unique={r['move_id'] for r in learns[sid]['routes'] if r['route'] in DIRECT}
        roles={'stab':[],'priority':[],'healing':[],'setup':[],'disruption':[]}
        for mid in sorted(unique):
            move=by['moves'][mid];labels=' '.join(move['effect_keys'])
            if move['type_id'] in row['types'] and move['category_id']!=2:roles['stab'].append(mid)
            if move['priority']>0 and move['category_id']!=2:roles['priority'].append(mid)
            if any(k in labels for k in ('HEAL','RECOVER','ABSORB','REST','WISH')):roles['healing'].append(mid)
            if move['category_id']==2 and any(k in labels for k in ('UP','DEFENSE_CURL','GROWTH','QUIVER','DRAGON_DANCE','CALM_MIND')):roles['setup'].append(mid)
            if move['category_id']==2 and any(k in labels for k in ('SLEEP','POISON','PARALY','BURN','CONFUS','TAUNT','ENCORE','LEECH','SPIKES','TRAP','DISABLE')):roles['disruption'].append(mid)
        vega.append(dict(subset(row,'id','key','name','form_key','base_stats','type_names','abilities','final_evolution'),
            bst_band=(row['base_stats']['total']//50)*50,speed_band=(row['base_stats']['speed']//20)*20,
            attack_bias=row['base_stats']['attack']-row['base_stats']['sp_attack'],roles=roles,
            role_classification='effect keyによる検索補助。威力・対象・実動作は技ページを参照。',
            stage61_changed=sid in species_changed or sid>=len(old['species'])))
    bindings=dict(d['source_bindings']);bindings.update({k:v for k,v in inputs.bindings.items() if k!=STATE})
    return dict(candidate=d['candidate'],counts=d['counts'],species=species,moves=moves,abilities=abilities,items=items,
        hidden_abilities=hidden,learnsets=list(learns.values()),evolutions=evos,megas=d['megas'],z_moves=zs,
        vega_balance=vega,p07_history=historical,balance_diff_stage61=diff,source_bindings=bindings,
        roots=d['roots'],tables=d['tables'],source_model=d['source_model'],
        move_categories=d['move_categories'],selection_check=d['selection_check'],
        native_evidence=canonical['content/modernization/p08_native_mega_acceptance.json'],
        transfer_evidence=canonical['content/modernization/pr16_p08_candidate_transfer.json'],
        new_native_runs=0,rom_changes=0)
