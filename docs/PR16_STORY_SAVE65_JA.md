# 上階の隣接カケル1勝・Save65限定受入

`PASS_MANSION_ADJACENT_TRAINER155_SAVE65_SCOPED`。Save64の26,6西からA1回で西隣NPCと会話。りかけいのおとこカケル（trainer155）に新1勝、通常保存・独立Continue。歩行0、穴と像の紙は未到達。

source `edc783a132db676ca3ddda135b6cc570e1340a20` / run `37161669046` / job `111316205366`全8step成功。artifact `11287846702` / 220212bytes / SHA256 `3ff9d889180cded9202f5e1cfda7cff67a571bb7cc5577de135440cf9a419915`。70member/55画面/99+cold13入力。新controller27case、58新受入拒否試験（初回56成功・誤mutation2件、観測indexを訂正して2件だけ成功。成功56件の再走0、計60実行）。native2/record0/旧受入再走0/ROM変更0。訂正2case成功後の記録runはraw失敗log内の絶対pathをguardが拒否。raw原本は元artifactに保持し、tracked証拠は検査行/終端の要約へ限定した。再検査0で成功58件を継承する。

## 会話・trainer戦と保存

0開始、1会話「ひとりごとのじゃましないでよ」、2導入、3りかけいのおとこのカケル。4コイキング♀Lv12、13ウパー♀Lv14、19クヌギダマ♂Lv15。9/15/21つばめがえし選択、実PP5→4→3→2、12/18交代拒否。24勝利、25降参台詞、26賞金360円、27field。敵3体撃破はtrainer1勝だけ。

28〜32menu0→4、33確認/34上書き、35〜47保存中。47counter65でも部分write、48〜51成功文言、52field。progress27/52/cold0/cold1全画面byte一致、全SaveRTC一致。

## 保存差分と次の新経路

party600byte中PP55の5→2だけ、残り599byte/HP288/294・ミュウツー全HP/PP・EXP/持物・全Bag/RP0・全legacy vars・PC/S61E全payload・旧Save64bank57344byte保持。所持金18744→19104、physical1435:0→1だけ。保存済local7のtrainer155命令と固定remap155+0x500→1435をROM byte照合。ただしruntime object IDは直接捕捉していない。RAM台帳は6と27で変化、owner未解明。42checksum/6856byte1665範囲。

[次の静的経路](../content/modernization/pr16_story_save65_evidence/next-route.json)はNPC占有25,6を除いた28歩。26,6から北へ26,5→25,5→24,5→23,5→23,6と未通過床を進み、穴31,21へ向かう。旧候補のNPC tileを無理に反復しない。実通行/穴/南東階段/紙側接続は未受入。つばめがえし残2PP、通常技の残量を守りhost補充しない。Flash未使用/がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。一般CI既知不一致/action_requiredを成功にしない。

次: Save65 artifact11287846702のstory-fast.srm（131088bytes/SHA256 c3d67760ba4c452c48abddbf423ea9bd5a052e38227fee85e47e299a60a45dda）だけから再開。上階map1/60・26,6西。A1回で隣接カケル/りかけい155に新1勝、敵3体・つばめがえし3選択/実PP5→2・交代拒否2・賞金360円/physical1435を限定受入。歩行0、通常Save65/独立Continue。HP288/294・PP15,10,15,2、party残り599byte/Bag/RP0/badge1/story4071=9/4072=1/全legacy vars/PC保持、19104円。次はNPC25,6を避ける保存済静的28歩候補:26,6→26,5→25,5→24,5→23,5→23,6→23,11→25,11→25,16→31,16→穴31,21。最初の新event/戦闘/不通境界で保存。穴→入口31,22/南東階段→紙側は未実測。つばめがえし残2PP、host補充なし、残量に応じて通常技を選ぶ。27新controller/58新受入（56継承+訂正2、計60実行、成功例再走0）、99+cold13入力55画面70member/native2。47counter65部分write、48成功→52field、全SaveRTC/field画面同一。RAM台帳6/27変化のruntime owner未解明。旧offset41/2056/aux/40ac未解明保持。Flash未使用/がくしゅうそうち未装備。既受入階段/経路/野生戦/隣接会話trainer戦/保存は無影響再走しない。全国図鑑/全story/自然成長・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
