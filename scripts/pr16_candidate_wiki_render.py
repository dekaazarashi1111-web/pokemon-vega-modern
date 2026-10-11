#!/usr/bin/env python3
"""候補Wikiの決定的なMarkdown/JSON生成。I/Oを持たず、書込はCLIへ分離する。"""
from __future__ import annotations
from collections import Counter
import hashlib
import html
import json
import posixpath
import re
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import digest, need, stable
from pr16_candidate_wiki_catalog import STATS, ROUTES, SLOTS, SUPPLY_UNKNOWN, subset

INDEXES = {
    'CODEX_INDEX':'読み方と機械可読索引','VEGA_BALANCE_INDEX':'ベガ性能比較','POKEMON_INDEX':'全種族・フォーム',
    'MOVE_INDEX':'全技','ABILITY_INDEX':'全特性','HIDDEN_ABILITY_INDEX':'隠れ特性と供給',
    'LEARNSET_INDEX':'習得経路とP07履歴','MEGA_INDEX':'全メガ','Z_MOVE_INDEX':'汎用・専用Z',
    'ITEM_INDEX':'全道具と供給','BALANCE_DIFF_STAGE61':'Stage61意味差分','RUNTIME_LIMITATIONS':'証拠と未監査範囲',
}


class Link(str):
    """この型だけはtable内で作成済みMarkdownとして扱う。"""


def cell(value) -> str:
    if isinstance(value,Link):return str(value)
    if isinstance(value,(dict,list,tuple)):value=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))
    if value is None:value='—'
    return html.escape(str(value),quote=False).replace('|','&#124;').replace('[','&#91;').replace(']','&#93;').replace('`','&#96;').replace('\n','<br>')


def table(headers, rows) -> str:
    return '\n'.join(['| '+' | '.join(map(cell,headers))+' |','| '+' | '.join('---' for _ in headers)+' |']+
                      ['| '+' | '.join(map(cell,row))+' |' for row in rows])+'\n'


def jsonblock(value) -> str:
    return '```json\n'+json.dumps(value,ensure_ascii=False,sort_keys=True,indent=2).replace('```','\\u0060\\u0060\\u0060')+'\n```\n'


def link(folder: str, row: dict, prefix: str='') -> Link:
    return Link(f'[{row["id"]}: {cell(row["name"])}]({prefix}{folder}/{row["id"]}.md)')


def tree_hash(files: dict[str,bytes]) -> str:
    return digest(''.join(name+'\0'+digest(data)+'\n' for name,data in sorted(files.items())).encode())


def validate_links(files: dict[str,bytes]) -> int:
    count=0
    for name,raw in files.items():
        need(not name.startswith('/') and '..' not in name.split('/') and '\\' not in name,'生成path不正')
        if not name.endswith('.md'):continue
        text=re.sub(r'```.*?```','',raw.decode(),flags=re.S)
        for target in re.findall(r'\]\(([^)]+)\)',text):
            need(not re.match(r'^[a-zA-Z]+:',target),'外部リンクは生成物内に持たない')
            page,sep,anchor=target.partition('#')
            resolved=posixpath.normpath(posixpath.join(posixpath.dirname(name),page)) if page else name
            need(resolved in files,'内部リンク切れ: '+name+' -> '+target)
            if sep:
                need(f'id="{anchor}"' in files[resolved].decode(),'anchor欠落: '+target)
            count+=1
    return count


def render(model: dict) -> dict[str,bytes]:
    files={}; candidate=model['candidate']; sp=model['species']; moves=model['moves']; abilities=model['abilities']; items=model['items']
    by={'pokemon':sp,'moves':moves,'abilities':abilities,'items':items}
    learns={r['species_id']:r for r in model['learnsets']}
    mega={r['mega_species_id']:r for r in model['megas']}
    source_text=('候補 SHA-256 `'+candidate['sha256']+'` / '+str(candidate['size'])+' bytes / CRC32 `'+candidate['crc32']+'`。')
    def put(name,title,body,child=False):
        back='[Wiki入口](../README.md)' if child else '[Wiki入口](README.md)'
        files[name]=('# '+title+'\n\n'+source_text+'\n\n'+back+'\n\n'+body.rstrip()+'\n').encode()
    def ref(folder,identifier,child=False):return link(folder,by[folder][identifier],'../' if child else '')
    def mlist(ids,child=False):return Link('、'.join(str(ref('moves',mid,child)) for mid in ids) or '—')
    def slist(ids,child=False):return Link('、'.join(str(ref('pokemon',sid,child)) for sid in ids) or '—')
    def evolutions(rows,child=False):
        return table(['元','先','method / parameter / extra','条件','条件の証拠'],[
            (ref('pokemon',r['species_id'],child),ref('pokemon',r['target_id'],child),f'{r["method_id"]} / {r["parameter"]} / {r["extra"]}',r['condition'],r['condition_evidence']) for r in rows])
    for row in sp:
        sid=row['id']; stats=row['base_stats']
        body=table(['ID','stable key','表示名','ROM内名','form','base','全国図鑑','区分'],[(sid,row['key'],row['name'],row.get('rom_name'),row['form_key'],ref('pokemon',row['base_species_id'],True),row['national_no'],row['form_status'])])
        body+='\n## 基礎性能 — EXACT_CANDIDATE_ROM\n\n'
        body+=table(['タイプ1 / 2','HP','攻撃','防御','特攻','特防','素早さ','BST'],[(' / '.join(row['type_names']),*[stats[k] for k in STATS])])
        body+='\n'+table(['EV','捕獲率','基礎経験値','成長率','性別比byte','タマゴグループ','孵化cycle','なつき度'],[(row['ev_yield'],row['capture_rate'],row['exp_yield'],row['growth'],row['gender_ratio'],row['egg_groups'],row['egg_cycles'],row['friendship'])])
        body+='\n## 特性slotと隠れ特性供給\n\n'+table(['slot','特性','stable key','説明','証拠'],[(a['slot'],ref('abilities',a['id'],True),a['key'],a['description'],a['evidence']) for a in row['abilities']])
        body+='\n隠れslotの値と、隠れslot個体の初回供給は別です。供給記録がないことだけで到達不能とは断定しません。\n\n'+jsonblock(row['hidden_ability'])
        body+='\n## 進化元・進化先\n\n'+evolutions(row['pre_evolutions']+row['evolutions'],True)
        body+='\n## 全習得経路\n\nTM/HM・教え技は互換と道具供給を区別します。保持履歴は直接習得経路ではありません。同じ技の複数経路・重複行も保持します。\n\n'
        body+=table(['経路','技','stable move key','条件 / 順序','証拠','利用区分'],[
            (ROUTES.get(r['route'],r['route']),ref('moves',r['move_id'],True),r['move_key'],subset(r,'level','slot','order','owner_species_id'),r['evidence'],r.get('availability','RECORDED_ROUTE')) for r in learns[sid]['routes']])
        body+='\n## 野生初期技・固定配布・フォーム固有\n\n'+jsonblock({'wild_initial':row['wild_initial_moves'],'fixed_gift':row['fixed_gift_moves'],'form_specific':'上記Species IDの実tableを参照。baseからの推測コピーはしない。'})
        body+='\n## メガ・専用Z\n\n'+table(['メガフォーム'],[(ref('pokemon',mid,True),) for mid in row['mega_forms']])
        for zindex in row['special_z_rows']:
            z=model['z_moves'][zindex]
            body+='\n'+table(['クリスタル','元技','Z技','native'],[(ref('items',z['item_id'],True),ref('moves',z['base_move_id'],True),ref('moves',z['z_move_id'],True),z['native_e2e'])])
        if sid in mega:
            body+='\n### メガ登録・資産manifest（素材byteなし）\n\n'+jsonblock(mega[sid])
        body+='\n## 入手経路・解禁条件 — GENERATED_CANONICAL\n\n'
        body+=jsonblock(row['acquisition']) if row['acquisition'] else SUPPLY_UNKNOWN+'\n'
        body+='\n## 参照\n\n[習得履歴の読み方](../LEARNSET_INDEX.md) / [証拠の限界](../RUNTIME_LIMITATIONS.md) / [Stage61との差分](../BALANCE_DIFF_STAGE61.md)\n'
        put(f'pokemon/{sid}.md',f'{sid}: {row["name"]}',body,True)
    for row in moves:
        mid=row['id'];body=table(['ID','stable key','名前','タイプ','分類','威力','命中','PP','優先度','対象ID'],[(mid,row['key'],row['name'],row['type_name'],row['category'],row['power'],row['accuracy'],row['pp'],row['priority'],row['target_id'])])
        body+='\n## 説明とeffect\n\n'+cell(row['description'])+'\n\n'+jsonblock(subset(row,'effect_id','effect_keys','secondary_percent','flags','category_tables','canonical_fields','canonical_fields_evidence','effect_novelty','new_handler_verified'))
        body+='\nflags byteは実候補値、symbolic flagsは固定上流の意味情報です。tableのbyte一致だけでconsumer実行済みとは扱いません。\n'
        body+='\n## Z・Max関係\n\n'+jsonblock(subset(row,'generic_z','max_conversion'))
        relations=[z for z in model['z_moves'] if mid in (z['base_move_id'],z['z_move_id'])]
        body+='\n'+table(['対象','クリスタル','元技','Z技'],[(ref('pokemon',z['species_id'],True),ref('items',z['item_id'],True),ref('moves',z['base_move_id'],True),ref('moves',z['z_move_id'],True)) for z in relations])
        body+='\n## 習得Species\n\n'+str(row['learner_count'])+' Species。道具供給・ゲーム進行上の到達可能性を一括受入した数ではありません。\n\n'+str(slist(row['learner_species_ids'],True))+'\n'
        body+='\n### ベガオリジナル\n\n'+str(slist(row['vega_learner_species_ids'],True))+'\n'
        body+='\n### 保持履歴にだけ存在\n\n'+str(slist(row['preservation_only_species_ids'],True))+'\n'
        body+='\n## Stage61からの技性能差分\n\n'+jsonblock(row['stage61_changes'])
        put(f'moves/{mid}.md',f'{mid}: {row["name"]}',body,True)
    for row in abilities:
        body=table(['ID','stable key','名前','本プロジェクト追加'],[(row['id'],row['key'],row['name'],row['project_added'])])
        body+='\n'+cell(row['description'])+'\n\n## 実装・受入範囲\n\n'+jsonblock(subset(row,'implementation','allocation','integration_hooks','runtime_profile'))
        body+='\n## 所有Species/Formとslot\n\n'+table(['Species','stable key','slot'],[(ref('pokemon',o['species_id'],True),o['species_key'],o['slot']) for o in row['owners']])
        put(f'abilities/{row["id"]}.md',f'{row["id"]}: {row["name"]}',body,True)
    for row in items:
        body=table(['ID','stable key','名前','ROM価格','持ち物効果ID','parameter'],[(row['id'],row['key'],row['name'],row['price'],row['hold_effect_id'],row['hold_effect_parameter'])])
        body+='\n'+cell(row['description'])+'\n\n## 供給・解禁・反復性\n\n'+jsonblock(row['supply'])
        put(f'items/{row["id"]}.md',f'{row["id"]}: {row["name"]}',body,True)
    overview=table(['分類','件数'],[(k,v) for k,v in model['counts'].items()]+[('メガ',len(model['megas'])),('専用Z対応',len(model['z_moves'])),('P07原本行',len(model['p07_history']))])
    nav='\n'.join(f'- [{title}]({name}.md)' for name,title in INDEXES.items())+'\n'
    put('README.md','P08調整前候補Wiki',
        '**開発中の調整前スナップショットです。配布版・release承認ではありません。**\n\n'+overview+'\n'+nav+
        '\n数値は現候補の読取結果、意味・供給は正本、native証拠は限定scopeとして分離します。Stage61履歴は変更しません。性能調整・夢特性追加・追加メガ・追加専用Zの採否は所有者の別指示で決めます。\n\n'
        '## 再生成と検査\n\n```bash\npython3 -B scripts/build_pr16_candidate_wiki.py build\npython3 -B scripts/build_pr16_candidate_wiki.py check\n```\n\n'
        'checkは候補・正本・全生成byte・リンク・stale fileを再照合し、一切書き込みません。新しいROM生成・ARM build・mGBA・受入再実行は行いません。\n')
    put('POKEMON_INDEX.md','全Species/Form',table(['ID / 名前','stable key','form','区分','タイプ','BST','特性1 / 2 / 隠れ'],[(ref('pokemon',r['id']),r['key'],r['form_key'],r['form_status'],' / '.join(r['type_names']),r['base_stats']['total'],' / '.join(a['name'] for a in r['abilities'])) for r in sp]))
    put('MOVE_INDEX.md','全技',table(['ID / 名前','stable key','タイプ','分類','威力','命中','PP','優先度','effect','習得種数','Vega種数','Stage61変更'],[(ref('moves',r['id']),r['key'],r['type_name'],r['category'],r['power'],r['accuracy'],r['pp'],r['priority'],r['effect_keys'],r['learner_count'],len(r['vega_learner_species_ids']),bool(r['stage61_changes'])) for r in moves]))
    put('ABILITY_INDEX.md','全特性',table(['ID / 名前','stable key','説明','project追加','所有slot数','battle core / AI / Circus'],[(ref('abilities',r['id']),r['key'],r['description'],r['project_added'],len(r['owners']),r['implementation']) for r in abilities]))
    put('ITEM_INDEX.md','全道具・供給',table(['ID / 名前','stable key','説明','供給'],[(ref('items',r['id']),r['key'],r['description'],r['supply']) for r in items]))
    hidden=model['hidden_abilities'];assigned=[r for r in hidden if r['assigned']]
    missing=[r for r in model['vega_balance'] if not sp[r['id']]['hidden_ability']['assigned']]
    body='**隠れslotの有無と、その個体を初めて供給できることは別です。未発見は到達不能の断定ではありません。**\n\n'
    body+='## 隠れ特性が設定されているSpecies\n\n'+table(['Species','隠れ特性','初回供給'],[(ref('pokemon',r['species_id']),ref('abilities',r['ability_id']),r['first_supply']) for r in assigned])
    body+='\n## 夢特性未設定のベガオリジナル\n\n'+table(['Species','stable key'],[(ref('pokemon',r['id']),r['key']) for r in missing])
    body+='\n## 初回供給記録未発見\n\n'+table(['Species','状態'],[(ref('pokemon',r['species_id']),SUPPLY_UNKNOWN) for r in assigned if r['first_supply']==SUPPLY_UNKNOWN])
    put('HIDDEN_ABILITY_INDEX.md','隠れ特性と供給監査',body)
    body='役割欄はeffect keyを用いた検索補助です。回復対象・妨害内容・実効威力の評価は各技ページを確認してください。\n\n'
    body+=table(['Species / form','タイプ','HP','攻撃','防御','特攻','特防','素早さ','BST','特性1 / 2 / 隠れ','最終進化','Stage61変更'],[(ref('pokemon',r['id']),sp[r['id']]['type_names'],*[r['base_stats'][k] for k in STATS],' / '.join(a['name'] for a in r['abilities']),r['final_evolution'],r['stage61_changed']) for r in model['vega_balance']])
    body+='\n## 技の横比較\n\n'+table(['Species','一致技','先制技','回復候補','積み候補','妨害候補'],[(ref('pokemon',r['id']),*[mlist(r['roles'][key]) for key in ('stab','priority','healing','setup','disruption')]) for r in model['vega_balance']])
    body+='\n[並び替え用JSON](data/vega_balance.json) にBST帯・素早さ帯・攻撃−特攻・type・roleを保存します。\n'
    put('VEGA_BALANCE_INDEX.md','ベガオリジナル性能比較',body)
    history=model['p07_history']; groups=sorted({r['group'] for r in history})
    body='同じ技の複数経路を保持します。build_learnable_preservationは保持履歴であり、その経路から直接教えられるという意味ではありません。\n\n'
    body+=table(['経路','行数'],[(ROUTES.get(k,k),v) for k,v in sorted(Counter(r['route'] for s in model['learnsets'] for r in s['routes']).items())])
    body+='\n## P07原本行の現在候補照合\n\nlevelは同じlevel、machine/tutorは同じslotまで一致した場合だけ原条件ありとします。履歴側のorderは記録しつつ、level技の表示順移動を習得条件変更と混同しません。\n\n'
    body+=table(['group','原本行','同じ技あり','元routeあり','元条件あり','保持履歴あり'],[(g,len(rows),sum(r['same_move_present'] for r in rows),sum(r['original_route_present'] for r in rows),sum(r['original_parameters_present'] for r in rows),sum(r['preservation_history_present'] for r in rows)) for g in groups for rows in [[r for r in history if r['group']==g]]])
    body+='\n'+table(['group','Species','技','元route / 条件','元CSV / 行','元条件一致','現在のteaching route','保持履歴'],[(r['group'],ref('pokemon',r['species_id']),ref('moves',r['move_id']),{'route':r['route'],**r['source_parameters']},f'{r["source_member"]}:{r["source_csv_line"]}',r['original_parameters_present'],r['current_teaching_routes'],r['preservation_history_present']) for r in history])
    body+='\n## Species別全経路\n\n'+table(['Species','経路別件数'],[(ref('pokemon',r['species_id']),dict(sorted(Counter(x['route'] for x in r['routes']).items()))) for r in model['learnsets']])
    put('LEARNSET_INDEX.md','習得経路・P07履歴照合',body)
    body='メガは実候補の進化表method254・石・逆方向と正本mappingから収集します。native_statusは形態ごとに分け、6追加特性の限定受入を全77形態へ拡大しません。\n\n'
    body+=table(['base','mega','石','type before / after','6値・BST差分','特性','正逆一致','native'],[(ref('pokemon',r['base_species_id']),ref('pokemon',r['mega_species_id']),ref('items',r['item_id']),{'before':r['types_before'],'after':r['types_after']},r['stat_delta'],Link(' / '.join(str(ref('abilities',a)) for a in r['ability_ids'])),r['reverse_verified'],r['native_status']) for r in model['megas']])
    body+='\n各メガ個別ページにfront/back/icon/palette/shinyのpointer・寸法・SHAを記録します。画像byteは保存しません。\n\n[資産manifest](data/mega_assets.json) / [全メガJSONL](data/megas.jsonl)\n'
    put('MEGA_INDEX.md','全メガ・石・資産・受入scope',body)
    body='## 汎用Z\n\n各技の実候補z_powerとz_effectを機械可読データに保持します。汎用変換先consumerの全組合せ監査はDEFERRED_AUDITであり、専用Zの対応表受入と混同しません。\n\n'
    body+=table(['元技','type','分類','Z威力','Z変化effect','Max canonical威力'],[(ref('moves',r['id']),r['type_name'],r['category'],r['z_power'],r['z_effect'],r['max_conversion']['canonical_power']) for r in moves if r['z_power'] or r['z_effect']])
    body+='\n## 専用Z — 実mapping\n\nSpecies + Item + base Move → Z Move の表を候補byteと照合しています。表示名の部分一致ではありません。別form・皮剥がれ形態は別Species行として示します。全組合せのnative E2Eは未受入です。\n\n'
    body+=table(['Species/Form','クリスタル','元技','Z技','type / 分類','威力 / 命中 / 対象','effect','供給 / 解禁 / 反復','native E2E'],[(ref('pokemon',r['species_id']),ref('items',r['item_id']),ref('moves',r['base_move_id']),ref('moves',r['z_move_id']),r['z_move']['type_name']+' / '+r['z_move']['category'],subset(r['z_move'],'power','accuracy','target_id'),r['z_move']['effect_keys'],r['item']['supply'],r['native_e2e']) for r in model['z_moves']])
    body+='\n1戦1回・mode制約はcanonical policyの情報です。表のbyte一致のみから、その候補の全caller・全handler・全modeで実行済みとは扱いません。\n'
    put('Z_MOVE_INDEX.md','汎用Z・専用Z対応',body)
    diff=model['balance_diff_stage61'];body='Stage61固定データと数値ID・stable keyで比較します。pointer移動、元資料にないfield、保持履歴だけの存在は性能差分へ混ぜません。\n\n'
    body+=table(['domain','追加ID','削除ID'],[(k,len(v['added']),len(v['removed'])) for k,v in diff['id_changes'].items()])
    for domain,folder in [('species','pokemon'),('moves','moves'),('abilities','abilities'),('items','items')]:
        body+='\n## '+domain+' ID追加\n\n'+table(['ID / 名前','stable key'],[(ref(folder,r['id']),r['key']) for r in diff['id_changes'][domain]['added']])
    body+='\n## 種族性能の変更\n\n'+table(['Species','変更field'],[(ref('pokemon',r['id']),r['fields']) for r in diff['species']])
    body+='\n## 技性能の変更\n\n'+table(['技','変更field'],[(ref('moves',r['id']),r['fields']) for r in diff['moves']])
    body+='\n## 習得経路の意味差分\n\nTM/tutorの旧Wikiはslotを保存していないため技ID多重集合で比較します。元levelの変更は削除＋追加として残します。\n\n'
    body+=table(['Species','追加','削除'],[(ref('pokemon',r['species_id']),r['added'],r['removed']) for r in diff['learnsets']])
    body+='\n## 進化・メガmapping\n\n'+jsonblock({'evolutions':diff['evolutions'],'megas':diff['megas']})
    body+='\n## 比較不能なfield\n\n'+jsonblock(subset(diff,'not_comparable_fields','exclusive_z_mapping','pointer_layout_is_not_performance_change'))
    put('BALANCE_DIFF_STAGE61.md','Stage61からの意味差分',body)
    evidence={'EXACT_CANDIDATE_ROM':'選択候補から読取またはbyte照合。動作の全経路受入ではない。','GENERATED_CANONICAL':'tracked正本・固定上流に由来。実配布や実callerの全面受入ではない。','INHERITED_ACCEPTED':'旧候補の限定native原本をP08移送根拠に従って継承。再実行なし。','NATIVE_ACCEPTED':'同一候補・同一scopeの実行原本がある場合のみ。今回のWiki生成では新規付与しない。','IMPLEMENTED_NOT_NATIVE_ACCEPTED':'候補table/実装はあるが対象全体の独立native受入はない。',SUPPLY_UNKNOWN:'隠れslotや仕様値の存在とは別に、初回供給根拠を現在の入力から特定できない。','DEFERRED_AUDIT':'今回の読取スコープでは未監査。'}
    body=table(['証拠ラベル','意味'],list(evidence.items()))
    body+='\n## 明示的な未監査範囲\n\n野生初期技と固定配布の全実moveset、隠れ特性の種族別初回供給率・継承・patch、汎用Z変換先の全consumer、専用Z全組合せのnative E2E、全77メガの交代・ひんし・終了・Save/Continue個別受入、全特性のAIとCircus抑制組合せは今回追加実行していません。各ページのDEFERRED_AUDIT/IMPLEMENTED_NOT_NATIVE_ACCEPTEDを参照してください。\n\n'
    body+='専用handlerの完全新規追加か既存流用かはeffect IDだけで断定しません。effect_noveltyはStage61の技行に同じeffect IDが存在したかであり、handler新設の証拠ではありません。役割候補は自動検索補助で、強さの採否判断ではありません。\n\n'
    body+='## 受入済み原本の再利用\n\n'+jsonblock({'original_native':subset(model['native_evidence'],'candidate_rom_sha256','native_mega_turn_revert_cold_save_cases','accepted_original_processes','accepted_original_core_instances','limits','closed_scope'),
        'transfer':subset(model['transfer_evidence'],'candidate','candidate_crc32','final_native_acceptance_complete','completed_actions','domain_transfers'),
        'new_native_runs':0,'rom_changes':0,'active_baseline_changed':False,'release_approved':False})
    body+='\n## 読取rootと資産\n\n'+jsonblock(model['roots'])+'\nsource bindingとtable hashは [data/index.json](data/index.json) / [data/provenance.json](data/provenance.json) に保存します。\n'
    put('RUNTIME_LIMITATIONS.md','証拠区分・runtime限界',body)
    body=nav+'\n## データ入口\n\n'+table(['データ','内容'],[(Link('[index.json](data/index.json)'),'候補・入力hash・全ファイルmanifest'),(Link('[provenance.json](data/provenance.json)'),'table・source binding・固定上流'),(Link('[balance_diff_stage61.json](data/balance_diff_stage61.json)'),'意味差分'),(Link('[p07_history.jsonl](data/p07_history.jsonl)'),'原本1572行と元route/条件の現在照合')])
    body+='\n名前だけでjoinしないでください。数値IDとstable keyを併用します。JSONLの1行が1種族・1技・1履歴recordです。個別ページはpokemon/moves/abilities/itemsの数値ID名です。\n'
    put('CODEX_INDEX.md','Codex・調整判断の入口',body)
    for name in ('species','moves','abilities','items','hidden_abilities','learnsets','megas','z_moves','p07_history','evolutions'):
        files['data/'+name+'.jsonl']=b''.join((json.dumps(r,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode() for r in model[name])
    for name in ('vega_balance','balance_diff_stage61'):
        files['data/'+name+'.json']=stable(model[name])
    files['data/mega_assets.json']=stable([{'mega_species_id':r['mega_species_id'],'mega_species_key':r['mega_species_key'],'assets':r['assets']} for r in model['megas']])
    files['data/provenance.json']=stable(subset(model,'candidate','source_bindings','roots','tables','selection_check','source_model','move_categories','new_native_runs','rom_changes'))
    manifest={name:{'size':len(data),'sha256':digest(data)} for name,data in sorted(files.items())}
    files['data/index.json']=stable({'schema_version':1,'candidate':candidate,'counts':model['counts'],
        'record_counts':{name:len(model[name]) for name in ('species','moves','abilities','items','hidden_abilities','learnsets','megas','z_moves','p07_history','vega_balance')},
        'source_bindings':model['source_bindings'],'files':manifest,'payload_tree_sha256':tree_hash(files),
        'self_hash_policy':'index.json自身をpayload manifestから除外。全tree hashは検証reportに記録。',
        'new_native_runs':0,'rom_changes':0,'release_approved':False})
    validate_links(files)
    return files
