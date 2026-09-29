# アヤメ前提・カチヌキ3兄弟 — 開発checkpoint

Task: USER-20260929-STORY-AYAME-GATE。2026-09-29、開始remote HEAD c0e997047b61ed0c2c405c8949a32d6b44299610。

固定Save17 artifact11008723945（全144memberと外側hash一致）を読み取り専用で回収した。bootstrap source e7e91000395c5412e802e5c4081eb3926700977c と開始HEADとの差分は旧未保存WIP 1ファイルのみ。実行中Actionsは0を確認。HEADのPR CIはforgetting成功、source-validation失敗であり全greenとは扱わない。

旧 `pr16_story_ayame_gate_development/wip_20260929_0308.json` は保存終端も完了processも無い履歴であり、Save18ではない。唯一の保存済み開始点Save17から新しい通常入力を行った。町→ゲート上階の初回訪問だけでは連戦は始まらず、ジム前NPCとの通常会話後に再入場すると正規イベントが発火した。現在は第1戦の賞金200円まで観測、通常Save/coldは未完。

`pr16_story_ayame_chain.py` と専用25試験を追加し、ローカルで25 PASS。交代用party UIからBATTLEへ戻る遷移、KO、field残留outcome1を新しい勝利や別戦に数えない。中間2戦はlock1を許容し、各戦のoutcome0リセット→battle上の勝利→field復帰と連戦全体の最終解錠を別々に要求する。未知callback、欠測、早期解錠、4戦目、敗北/逃走/捕獲を拒否する。

これは実装途中のcheckpointであり、Save18・3連勝・自然育成・進化・全国図鑑・全storyを受入しない。ROM/原本Save/既受入BP/P08/Save1〜17/全国図鑑owner/active baselineは変更しない。終了前に通常Saveと独立Continue、影響範囲の検証、固定再開MD/JSONと両ログを更新する。
