#!/usr/bin/env python3
"""生のmethod254登録行と、正逆対応が成立したメガ形態を区別する。"""
from __future__ import annotations
import json
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import need, stable
from pr16_candidate_wiki_render import table, link, jsonblock


def partition(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    verified=[]; anomalies=[]
    for row in rows:
        self_reference=row['base_species_id']==row['mega_species_id']
        if row['reverse_verified'] and not self_reference:
            verified.append(row)
        else:
            # 新しい不一致を黙って許容しない。既存self-referenceだけを未確認として保存する。
            need(self_reference and not row['reverse_verified'] and row['mapping_scope']=='LEGACY',
                 'unexpected mega forward/reverse mapping')
            anomalies.append(dict(row,classification='LEGACY_SELF_REFERENCE_WITHOUT_REVERSE',
                native_status='DEFERRED_AUDIT',is_accepted_mega_form=False,
                interpretation='method254のraw登録行。別Speciesへの変化・逆変換を示さず、メガ形態の件数から除外。',
                consumer_behavior='DEFERRED_AUDIT'))
    return verified,anomalies


def normalize(model: dict) -> dict:
    """catalogのraw行は監査dataへ退避し、通常SpeciesをMEGA_BATTLE_ONLYにしない。"""
    verified,anomalies=partition(model['megas'])
    model['megas']=verified
    model['mega_mapping_anomalies']=anomalies
    valid_targets={r['mega_species_id'] for r in verified}
    for row in model['species']:
        row['mega_forms']=sorted(set(row['mega_forms']) & valid_targets)
        if row['form_status']=='MEGA_BATTLE_ONLY' and row['id'] not in valid_targets:
            row['form_status']=row['classification']
        row['mega_mapping_anomalies']=[{'classification':r['classification'],
            'base_species_id':r['base_species_id'],'target_species_id':r['mega_species_id'],
            'item_id':r['item_id'],'item_key':r['item_key'],'reverse_verified':False,
            'evidence':'EXACT_CANDIDATE_ROM','consumer_behavior':'DEFERRED_AUDIT'}
            for r in anomalies if row['id']==r['base_species_id']]
    model['mega_mapping_summary']={'raw_rows':len(verified)+len(anomalies),
        'forward_reverse_verified':len(verified),'unverified_legacy_rows':len(anomalies),
        'game_data_changed':False}
    return model


def append_audit(files: dict[str,bytes], model: dict) -> None:
    """manifestの再計算前に、件数・個別ページ・索引へ監査結果を追加する。"""
    anomalies=model['mega_mapping_anomalies'];summary=model['mega_mapping_summary']
    # raw行数を形態数と混同した固定文言を残さない。
    for name in list(files):
        if name.endswith('.md'):
            files[name]=files[name].decode().replace('全77形態','全形態').replace('全77メガ','全メガ').encode()
    notice=(f"\n\n## メガ登録行の監査\n\nraw登録{summary['raw_rows']}行のうち、正逆対応を確認できたメガは{summary['forward_reverse_verified']}行です。"
            f"自己参照・逆変換なしの旧登録{summary['unverified_legacy_rows']}行はメガ形態として数えず、[登録行監査](MEGA_MAPPING_AUDIT.md) に分離しました。ゲームデータは修正していません。\n")
    for name in ('README.md','MEGA_INDEX.md','CODEX_INDEX.md'):
        files[name]+=notice.encode()
    body='# メガ登録行の監査\n\n候補 SHA-256 `'+model['candidate']['sha256']+'`。\n\n[Wiki入口](README.md) / [正逆対応済みメガ](MEGA_INDEX.md)\n\n'
    body+='method254 + itemの存在だけで、別メガ形態や正逆対応を受入しません。次の自己参照行は候補に存在する事実を保持しつつ、メガ一覧・メガ資産一覧・形態数から除外します。consumerの実挙動は未監査です。\n\n'
    body+=table(['base / target','raw item','区分','逆変換','native'],[
        (link('pokemon',model['species'][r['base_species_id']]),
         link('items',model['items'][r['item_id']]),r['classification'],False,'DEFERRED_AUDIT') for r in anomalies])
    body+='\n'+jsonblock(summary)+'\n[raw監査データ](data/mega_mapping_anomalies.json) に元の登録・asset hashを保存します。\n'
    files['MEGA_MAPPING_AUDIT.md']=body.encode()
    files['data/mega_mapping_anomalies.json']=stable({'summary':summary,'rows':anomalies})
    for row in model['species']:
        if row['mega_mapping_anomalies']:
            files[f"pokemon/{row['id']}.md"]+=('\n## メガとは区別する未確認登録\n\n[メガ登録行監査](../MEGA_MAPPING_AUDIT.md)\n\n'+jsonblock(row['mega_mapping_anomalies'])).encode()
