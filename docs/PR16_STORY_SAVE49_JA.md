# 505番道路への通常南接続・Save49 限定受入

`PASS_ROUTE505_SOUTH_CONNECTION_SAVE49_SCOPED`。504番道路17,19南から1歩で505番道路map3/23・33,0南へ。戦闘/eventなし。通常Save49/独立Continueを限定受入。回復施設・ミュウツーPP回復は未完。

source `edaffdbc22212b8957b6c1b32cc1287f6a08cc54` / run `37141976146` / job `111258130792` 全8step成功。artifact `11280742739` / 191483bytes / SHA256 `13a6d9258c97e42bce86b289dd618d6b0ff38026e80f926c6899a68ba069699d`。全44member/29画面/47+cold13入力。12新controller成功原log継承、新34原本受入/拒否だけ。native2/record0/旧受入再走0/ROM変更0。

## 保存・全境界

0は504、1は505へ初接続。2〜6通常menu実cursor0→4、7保存確認、8上書き確認。9〜21書込中13種類。20最終Flash一時一致でもcounter48、21counter49で再差分。22〜25成功文言/安定Flash、26field。cold0/1は33,0南で全SaveRTC一致。42checksum/旧Save48bank57344byte/6894byte1700範囲。

party全600byte・HP/PP/EXP/Bag/15224円/全legacy flag/PC/S61E/story4071=9/4072=1・badge1不変。オノノクスHP294/294・PP[11,10,15,20]、ミュウツーHP314/354・PP0。親Save48の新パネル判定と残PP選択を継承。戦闘なしのため新判定/slot3選択のnative実証は追加0。Save47でのslot0実使用4回だけを継承し、原used0誤陰性を改作しない。

補助var4021=108→109/4022=3→4のowner未解決、全RAM ledger `9e4f38b66578ac978b454de0a9573e854c8449d017f5fd82ea4aa4c1ffb02606` 不変/最終cold一致。Save48途中ledger差/Save46party2byte/Save39cold差/Save44並替差のowner未解明と旧失敗履歴を保持。

保存済みmap3/23 map viewとmap3/44地形1440cellを再利用。新規追加読取は接続先33,0の1cellだけ、高度3/衝突0/behavior33。南接続は通常入力で確認済みだが33,0以南は未受入。

## 次checkpoint送信前の確認

AST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名、親artifact/run/source/SHA/counter/bank/member、ORIGINAL/ROM/親INPUT環境変数集合、送信tree/staged一覧、専用宛先/private/source guardと正確なunittest終端を照合。成功試験を記録器だけの失敗で再走しない。

次: Save49 artifact11280742739のstory-fast.srm（21374dbfbc9e38f0febf16304706b7f3b14feacf204d5956bd622dcf941b1a04、131088bytes）だけから再開。504南端17,19から通常南1入力で505番道路map3/23・33,0南/高度3へ接続、通常Save49/独立Continue全SaveRTC一致を限定受入。party4/RP0/15224円/badge1/story4071=9/4072=1、party600byte/HP/PP/Bag/legacy flags/PC/S61E不変。オノノクスPP[11,10,15,20]、ミュウツーHP314/354・全PP0で通常回復未完。次は既存map3/23 collision_gridの北端26〜33通路と南connection→map3/2を再利用し、33,0以南の新しい高度/ownerだけ追加読取して通常回復地点を目指す。最初の新戦闘/event/未通過境界/接続または正常回復地点で保存。未観測経路や回復を受入にしない。新classify/残PP選択はSave48の実装を継承、今回戦闘0で追加native実証0。20最終Flash一時一致でもcounter48/書込中、21counter49で再差分、22成功文言/安定Flash→26field。aux4021=108→109/4022=3→4はowner未解決、全RAMledger不変/最終cold一致。旧Save48途中ledger差/Save47raw used0誤陰性/Save46party2byte/Save39cold差/Save44並替差と旧失敗を保持。47+cold13入力/29画面/12controller34受入は無影響再走0。正規全国図鑑/全story/自然EXP・技習得・進化/LuckyEgg/12case/Lv100soak/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用、新artifactは新save/画面/textだけ。一般CI既知qol_production.c不一致とfinalHEAD action_requiredを全成功にしない。
