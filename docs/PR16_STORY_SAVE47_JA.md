# 北迂回・ジュネ勝利・Save47 限定受入

`PASS_ROUTE504_JUNE_SAVE47_SCOPED`。504番道路3,12西から11,5東へ下段19歩/8方向転換。だいすきクラブのジュネの4体に通常勝利し、Save47/独立Continueを限定受入。回復施設・ミュウツーPP回復は未完。

source `eabbb96a80487644d4a873eaea0a7b3a1a6a03b3` / run `37138339081` / job `111247375971` 全8step成功。artifact `11279895650` / 518854bytes / SHA256 `16992156ad670c7b385c5391506af7f6d1c54217166b5d1cfc5cc88db29d5efc`。全105member/90画面/170+cold13入力。12新controller成功原log継承、新44原本受入/拒否だけ。native2/record0/旧受入再走0/ROM変更0。

## オノノクスの初実技UIと原controllerの誤陰性

全90原画を確認。35/42/49/57はドラゴンクローslot0、PP15/14/13/12、36/43/50/58実使用。ココガラ/アクタシ/ビッパ/ファマー4体を撃破、60勝利文言、62賞金960円、63field。HP294/294、最終PP[11,10,15,20]。ミュウツーHP314/354・PP0。party差は600byte中52=15→11だけ、599byte不変。

旧PP_LABELの矩形は現行UIのタイプ/物理アイコンを含み、4技画面ともotherへ誤分類した。原receiptのused[0,0,0,0]とkeep_current3件を改作せず保持。有限通常A入力がslot0を実使用したことをraw画面/4段階party hash/保存PP差で独立検証し、controller集計の0を採用しない。

`classify_panel` は技名/種族/PP数値に依存しないパネル上枠と実cursorを用い、原88進行画面で実技4/交代3だけ検知する。新44試験にsynthetic4cursor/曖昧拒否/全実画像を含む。nativeでの4slot選択や他技使用を受入れたとはしない。次はこの判定を使い、PP上限を親[11,10,15,20]へ束縛。既存measurement sourceは不変。

## 保存・境界

64〜68通常menu cursor0→4、71〜82部分Flash12種類、83counter47/安定Flash/文言遷移、84〜86成功文言、87field。cold0/1は11,5東で全SaveRTC一致。42checksum/旧Save46bank57344byte/6902byte1708範囲。

physicalflag1402のみ0→1、14264→15224円、全Bag/HP/EXP/PC/S61E/story4071=9/4072=1・badge1不変。trainer数値IDは本checkpointでscript owner独立照合していない。補助var4021=22→40/4022=1→0、RAM ledger31/51差のowner未解決、最終/cold `9893bcce967f221d81a398053ea137368a84aae2486afc8b9a082703bbfcc344` 一致。Save46旧party2byte/途中ledger、Save39旧cold差/Save44並替差のowner未解明と旧失敗履歴を保持。

地形1440cell/既存owner再採取0。88vertex候補のうち20vertex/19歩で最初の新trainer戦へ区切った。残りの到達/回復は未証明。

## 次checkpoint送信前の確認

AST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名、親artifact/run/source/SHA/counter/bank/member、ORIGINAL/ROM/親INPUT環境変数集合、送信tree/staged一覧、専用宛先/private/source guardと正確なunittest終端を照合。成功試験を記録器だけの失敗で再走しない。

次: Save47 artifact11279895650のstory-fast.srm（0ffabf8d049f74edaabdaf32a54872a267d9ea4c04f02845612295a9f30c6431、131088bytes）だけから再開。map3/44・11,5東/下段3・party4/RP0・15224円・badge1・story4071=9/4072=1。3,12から北迂回19歩/8方向転換→だいすきクラブのジュネ4体に勝利、通常Save47/cold同一。オノノクスHP294/294・PP[11,10,15,20]、ミュウツーHP314/354・全PP0で回復未完。初の実技UI35/42/49/57はslot0ドラゴンクローPP15/14/13/12、36/43/50/58通常使用、party全600byteの差は52=15→11だけ。原controllerはPPlabel矩形がタイプ/物理アイコン化した実UIをotherと誤陰性、raw used[0,0,0,0]を改作せず実4回と区別。次のcontrollerは新pr16_story_save47_accept.classify_panel（技名/種族/PP数値非依存のパネル上枠+実cursor、原90画面の4技/3交代を照合済）を使い、selectは親実PP[11,10,15,20]で上限を再束縛する。旧PPlabel/used0/古いPP15のclosureを流用しない。native4slot選択/他技使用は未受入。以後は11,5→12,5→13,5→13,4→14,4→14,3→18,3→18,4から東へ、34,13下段→34,16→25,17→25,15→17,15→17,19の保存地形迂回候補の未通過続きだけ。最初の新戦闘/event/未通過境界または正常回復地点で次Save。南接続map3/23→3/2は候補、回復施設未同定。今回170+cold13入力/90画面/12controller44受入を無影響再走しない。71〜82部分write、83counter47/最終Flash→84成功文言→87field。physicalflag1402だけ0→1、賞金960円、Bag/HP/EXP/PC/S61E/story不変。auxvar4021=22→40/4022=1→0とRAMledger31/51差のowner未解決、最終/cold一致。Save46 party2byte/途中ledger、Save39旧cold差/Save44並替差と旧失敗を保持。正規全国図鑑/通常story/自然EXP・技習得・進化/LuckyEgg/12case/Lv100soak/研究施設自然到達未完。一般CIqol_production.c source不一致とfinalHEAD action_requiredは全成功としない。ROM/host補充/故意の全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用、新artifactは新save/画面/textだけ。
