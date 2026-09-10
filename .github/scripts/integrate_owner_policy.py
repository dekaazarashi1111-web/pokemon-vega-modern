"""Preimage-checked source integration for the explicit 2026-09-10 owner decision."""
from pathlib import Path
import hashlib
import json
import os
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT/'tools'))
sys.path.insert(0, str(ROOT/'scripts'))
import modernization_owner_policy as policy

MARKER = '## 2026-09-10 現行の所有者承認'
NOTICE = '''## 2026-09-10 現行の所有者承認

正本は `content/modernization/p08_owner_approved_policy.json`。追加技アーカイブは
**殿堂入り後・Bagのわざメモリーから無料**を正式採用。通常思い出し・技忘れ等に
新しい殿堂入り制限を追加しない。固定Stage74設定の暫定ラベルは履歴として不変。

**publicは所有者自身が選んだ正しい現行設定**。本文に残るprivate repository／private
Releaseの表現は過去の構成名・説明であり、非公開性の根拠でも現行の必須条件でもない。
非公開化や既存追跡原本の移動・削除を完成条件にしない。過去の全index guard失敗を
PASSへ改称せず、秘密情報・新規の意図しない資材混入を防ぐ検査も無効化しない。
Stage62・実プレイsave・原本・履歴・PR未マージは保持する。

この承認はP03/P05/P06/P07の未受入経路や製品全体の完成を意味しない。

'''
HELPER = '''\ndef current_remaining_work(root, forgetting):
    # Compose current adoption only after validating immutable historical evidence.
    overview = remaining_work(root, forgetting)
    receipt = root/'content/modernization/p08_final_candidate_acceptance.json'
    need(not receipt.is_symlink(), 'symlink final receipt')
    if receipt.exists():
        import record_modernization_final_acceptance as integration
        overview = integration.project_overview(overview, root)
    sys.path.insert(0, str(root/'tools'))
    from modernization_owner_policy import project
    return project(overview, root)

'''


def replace_once(text, before, after):
    policy.need(text.count(before) == 1, 'source anchor absent or ambiguous')
    return text.replace(before, after, 1)


def pinned_edit(name, expected_blob, transform, marker):
    path=ROOT/name
    raw=policy.read(ROOT,name)
    text=raw.decode('utf-8')
    if marker in text:
        return
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    policy.need(blob==expected_blob, 'concurrent source drift: '+name)
    path.write_text(transform(text),encoding='utf-8')


def integrate():
    policy.load(ROOT)
    def forgetting(text):
        text=replace_once(text,'\ndef main():\n',HELPER+'\ndef main():\n')
        return replace_once(text,'result=build();overview=remaining_work(ROOT,result);','result=build();overview=current_remaining_work(ROOT,result);')
    pinned_edit('scripts/record_modernization_p03_forgetting.py','fc55815656a825d04235223b3f70a185b21d893f',forgetting,'def current_remaining_work(')
    def final(text):
        return replace_once(text,"    current['source_bindings'][RECEIPT]=identity(read(root,RECEIPT))\n    return current\n",
                            "    current['source_bindings'][RECEIPT]=identity(read(root,RECEIPT))\n    from modernization_owner_policy import project\n    return project(current, root)\n")
    pinned_edit('scripts/record_modernization_final_acceptance.py','ffa3a4012417dc6adb144be1e69142ce708c070b',final,'from modernization_owner_policy import project')
    for name in ('docs/CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md','docs/FINAL_INTEGRATION_HANDOFF_JA.md'):
        path=ROOT/name;text=policy.read(ROOT,name).decode('utf-8')
        if MARKER not in text:
            first,rest=text.split('\n',1)
            if name.endswith('CHATGPT_WEB_GITHUB_ENVIRONMENT_JA.md'):
                first=first.replace('private GitHub','GitHub')
            text=first+'\n'+rest.rstrip()+'\n\n'+NOTICE
            if name.endswith('FINAL_INTEGRATION_HANDOFF_JA.md'):
                start=text.index('### archive economy\n')
                end=text.index('P06の監査194行',start)
                text=text[:start]+'''### archive economy（正式採用済み）

2026-09-10 13:18:32 UTCの所有者指示により、現行の「殿堂入り後・Bagのわざメモリー・無料」を正式採用した。
`config/modernization_p03_stage74_supply.json` の `runtime.unlock` / `runtime.economy` は固定履歴として変更せず、
`content/modernization/p08_owner_approved_policy.json` を現在の受入判断として接続する。
価格・解禁・供給場所のROM変更は不要。通常思い出し・技忘れ等の既存条件は変えない。
残件一覧の再生成もこの判断を読むため、「料金未承認」へ戻らない。

'''+text[end:]
                text=text.replace('P07採用行、archive economy、clean ROMからの最終再生成、公開済み原本の保護問題が残る。','P07採用行、clean ROMからの最終再生成が残る。archive economyとpublic設定の所有者判断は確定済み。')
                text=text.replace('対応方法は所有者の明示承認が必要。','publicは所有者が意図して設定した。非公開化・原本移動の承認待ちを残件にしない。')
                text=text.replace('P07/料金の未決判断に依存しない。','P07の未決判断に依存しない。料金は無料として正式採用済み。')
            path.write_text(text,encoding='utf-8')
    import record_modernization_p03_forgetting as record
    overview=record.current_remaining_work(ROOT,record.build())
    (ROOT/record.OVERVIEW).write_text(json.dumps(overview,ensure_ascii=False,sort_keys=True,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'status':'OWNER_DECISIONS_COMPOSED_NOT_PRODUCT_COMPLETION','decision_id':policy.DECISION_ID,
                      'remaining_conditions':[r['id'] for r in overview['remaining_conditions']],
                      'rom_changes':0,'new_emulator_runs':0,'release_ready':overview['release_ready']}))


if __name__=='__main__':integrate()
