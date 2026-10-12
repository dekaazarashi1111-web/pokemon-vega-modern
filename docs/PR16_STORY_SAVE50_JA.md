# 505番道路の通常迂回・セナラナ戦・Save50限定受入

`PASS_ROUTE505_SENA_RANA_SAVE50_SCOPED`。33,0から西側へ57歩/18方向転換、22,20階段を通過して高度4の22,18北へ。センパイとコウハイのセナとラナのダブル戦1勝と通常Save50/独立Continueだけを受入。南接続/正常回復は未完。

source `68c53dd8bbd74ce07d71f32a21d657e80cd1457e` / run `37143645467` / job `111263061326`全8step成功。artifact `11281112264` / 853577bytes / SHA256 `96d1c619b2d219f23ad2904bffae9288cc254326374a5afced2fa166868f0c4c`。全168member、153画面、296+cold13入力。20新controller原log継承、44新受入/拒否試験。native2/record0/旧入力再走0/ROM変更0。

## ダブル戦と通常入力の限界

79〜125でココガラ/タマンチュラ/クヌギダマ/ビッパと戦い、122勝利、125賞金416円、126field。party4/RP0、15224→15640円。trainer1054は同候補remapでphysicalflag1406へ対応し、保存差はその1bitだけ。

実技panelは86/87/88でcursor0→2→3。89/103/117は相手確定のため同じpanelが残る。raw controllerのused6を改作せず、選択3+target3と実PP消費2に分離する。つばめがえしは2回、PP20→18。3回目はミュウツーが先に最後の相手を倒し未実行。slot1/全4技native受入ではない。次の戦闘前にtargetを別計数し、Save50の実PPへ再束縛する。

ミュウツーは全PP0。通常わるあがき3回、反動でHP314→226→138→50。オノノクスHP294/294・PP[11,10,15,18]。ミュウHP342/342、メタモンHP300/300は技欄4つ0。PP持ち2体への単なる並替では解決しない。回復は未完、任意戦を避けて実回復を優先する。

## 全保存境界

party差はbyte41=43→44（24の歩行中、runtime owner未解明）、byte55=20→18（PP2）、186/187=58,1→50,0（HP314→50）。party phase全6hashを原本へ結合。全Bag/所持品/PC/S61E/badge1/story4071=9/4072=1は不変。aux4021=109→37/4022=4→0とRAMledger39/85/106/126のownerは未解明。最終coldでは全RAMledgerも一致。

127〜131通常menu cursor0→4、132確認、133上書き、134〜145は12種類の書込中Flash。146安定Flash/counter50でも成功文言はまだ未表示、147〜149成功文言、150field。cold0/1は22,18北で全SaveRTC一致。42sector checksum、旧Save49bank57344byte保全、6948byte/1728差分範囲。

## 再利用と未踏範囲

Save49の1cellとSave44の505collision viewを再利用。read-only run37143096088で未読東側322cell/13script、run37143284932で西8〜20行187cell/12script、診断0。東側のみ/西20行まででは南へ通じる候補なし。今回さらに21行12cellと南接続先1cell/map3/2を追加読取して104歩の候補を得た。実通過は先頭57歩だけ、残47歩と南connectionは未受入。新しいread-only原本から再開し、再採取しない。

旧Save47誤陰性/Save48途中ledger/Save46party2byte/Save39cold/Save44並替差と旧失敗を保持。正規全国図鑑/自然EXP・技習得・進化/全story/研究施設自然到達/releaseは未完。一般CI既知source不一致とaction_requiredを全green扱いしない。

次: Save50 artifact11281112264のstory-fast.srm（131088bytes/SHA256 b586055a74bd6b826d7ea8150e25954a9452718ad5b46e4926f0d01f9088022e）だけから再開。505番道路33,0→西側迂回57歩→22,18北/高度4でセナラナのダブル戦1勝、通常Save50/独立Continue全SaveRTC一致を限定受入。party4/RP0/15640円/badge1/story4071=9/4072=1。オノノクスHP294/294・PP[11,10,15,18]、ミュウツーHP50/354・PP全0、ミュウHP342/342とメタモンHP300/300はいずれも技4枠0。PP持ちは1体だけで、並替だけで2体にはできない。次は保存済み候補routeのindex57から残47歩を使い、任意戦を避けて南connection→map3/2の28,0/正常回復を優先。最初の新戦闘/event/未通過境界/接続または実回復で保存。戦闘前にはダブル戦の技選択/相手確定を別計数し、現在PPへ再束縛する。今回raw used6は選択3+target3で実PP消費2、3回目は相方が先に倒して未実行。ミュウツーのわるあがき3回反動264HPを回復扱いしない。新classifierはslot0/2/3表示とslot3実使用2だけをnative確認、slot1/全4技は未完。歩行中party byte41=43→44と途中RAMledger4差・aux4021=109→37/4022=4→0はowner未解明。146安定Flash/counter50→147成功文言→150fieldを分離。原本296+cold13入力153画面/20controller44受入/168memberを無影響再走0。旧失敗と旧party/ledger不明差を保持。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。ROM/host補充/故意全滅/merge/release/baseline切替なし。既存ROM/runtime/inputはActions入力専用。一般CI既知qol_production.c source不一致/finalHEAD action_requiredを全成功にしない。
