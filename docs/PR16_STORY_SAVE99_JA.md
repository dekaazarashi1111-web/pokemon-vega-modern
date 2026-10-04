# Ranger接近・Save99限定受入

`PASS_RANGER_APPROACH_SAVE99_SCOPED`。Save98から新61歩/15旋回で505番道路18,28西まで接近。通常Save99と独立Continue。会話/新戦闘/warpは0。

source `625a1e1aecfa41860a2018e854114c15d246905a` / run `37197174924` / job `111421350168` 全8step成功。artifact `11301562515` / 606235bytes / SHA256 `33b59f66e11a2db147def8160de679dc2b7363fc05fa13b531deaeaa584db509`。119member/104画面/197+cold13入力。40controller/67新受入。成功native2/失敗0/記録native0/旧成功再走0。

## ROCK_STAIRSと歩行owner

behavior0x2aは固定上流/ROMのROCK_STAIRS。0x8059d1cの判定、0x805b368の北=現在tile/南=1tile南、0x805b348の通常歩行slow分岐をbinding。warp/一方向ledgeではない。32,15→32,14→32,13を北入力、22,19→22,20→22,21を南入力で実通過。全tile単位/15旋回、blocked0/自動歩行0。

歩数4021は30→91、4022は0→1。61歩でfriendship周期128には届かず、status0の4体は毒ダメージなし。party600byte全保持、HP277/294とPP3,9,8,2保持。次friendship周期まで37歩。RAMledgerは観測53で変化しowner未解明、以後/coldは保持。過去RAM42/physical2056等は未解決のまま。

## 保存・動的Ranger

77〜81menu0→4、82/83確認、84〜96保存中。96counter99でも途中hash、97最終hash/成功文言、101clearfield。全SaveRTC131088byte/PC/S61E/旧bank57344byte保持、7160byte/1788範囲/42checksum。

最終画面の主人公18,28西に対しRangerは2tile東の20,28。cold0も20,28、無入力120frame後cold1は20,29。位置は16px/tileの実画面比較で確認し、RAMobject配列は未採取。progress/cold0差132px、progress/cold1差410px、cold間差376pxは矩形145,67〜158,102のNPCだけ。全pixel一致ではない。静的初期18,27への北Aや回復を仮定しない。

## 次

Save99 artifact11301562515のstory-fast.srm（131088bytes/SHA256 18de364bd911a9470965cf571e10aab899e8f4236bcaef327586e965b3a02b6b）だけから再開。505番道路3/23・18,28西。61歩/15旋回・ROCK_STAIRS2か所・通常Save99/独立Continueを限定受入。草地を通ったが戦闘0、wild controllerはnative未使用。主人公のRanger正面隣接は未達。実画面のRangerは20,28、cold120frame後20,29へ動く。静的18,27へ北Aを盲送しない。次は実NPC位置・正面隣接を画面またはread-only object観測で確定して通常A。4382=true/4380=falseの固定scriptは4072=2/4352clear/町3,2へのwarp5,16。これは未測定、回復台詞は別分岐なのでHP/PP回復を仮定しない。最初の新field→通常Save100/独立Continueで止める。接近61歩/町/博物館/封書/受付再走なし。HP277/294/PP3,9,8,2/ミュウツー全HP/PP/23114円/4061=1/紙274=0/4382/4383/バッジ2/全party600byte/PC/S61E保持。4021=(30+61)%128=91/4022=(0+61)%5=1、次friendship周期まで37歩。今回RAM53差分と過去RAM42/2056等のowner未解明は残す。104画面/197+cold13入力、96counter99は途中hash/保存中、97最終hash/成功文言、101clearfield。cold間376pixelはRanger移動、全SaveRTC一致と全pixel一致を混同しない。40新controller/67新受入、成功native2/失敗0/記録native0/旧成功再走0。Save98記録run37196489863の全11stepを終端同期。旧失敗原本不変、ROM/runtime非再配布、ROM変更/host補充/merge/release/baseline変更0。全国図鑑/自然成長進化/全story/release未受入。一般CI既知qol_production.c不一致を全成功にしない。warp-tableの座標だけで発火可能と判断しない。毎回固定ROMのtile behaviorと必要方向を確認し、通常着地/矢印/方向階段/境界connectionを区別する。実画面の出口は裏付け。無入力自動歩行は実測まで未確認。
