# 館内通常13歩・野生1勝・Save57限定受入

`PASS_MANSION_WILD_SAVE57_SCOPED`。Save56から西1歩/北12歩、19,13でバーニン♀Lv9に遭遇。オノノクスLv100のつばめがえし1回で通常撃破し、Save57と独立Continue。HP288/294・PP[15,10,15,13]。上階/像/紙は未到達。

source `c246f9c79b3513f01f1dbe5a987b685f8653fddc` / run `37154941204` / job `111296302107`全8step成功。artifact `11284919827` / 164504bytes / SHA256 `dd16a6b510145b130ed5a0632373b7ee972b30732234ce9a6351e46c1d3f22c8`。69member/53画面/93+cold13入力。controller27case（初回25、影響1+新規2の計28実行、未影響24件原log継承）、51新受入拒否試験。成功native2/失敗native1/record0/旧受入再走0/ROM変更0。

## 着地点warpと発火床の訂正

旧引継ぎの20,24warp8はmap1/60側から戻る着地点。実床behavior8であり、通常北入力では発火しない。初回run37154589799/source79ad87e8223c84f0cb781667e54ab85a395fcddd/job111295266609/artifact11285188296は20,25→20,24→20,23の16入力3画面/native1でguard停止。全Save56不変・未保存。原本を改作せず、有効behavior108の30,10階段への別経路を実装した。同じ不発北歩行を繰り返さない。

新階層1/60は15node/1444cell/1mapだけ採取。像16,28/script149012422にitem274「だいじなふうしょ」/flag4383を静的確認。native未到達・未取得であり、その受入とは区別する。

## 野生戦と保存

0〜14暗所の通常移動、15野生遷移/16暗転/17battle。18バーニン♀Lv9、19オノノクスLv100。21slot0/22slot2/23slot3の実技UI、つばめがえしPP14、24撃破/実PP13。25callback field/lock0へ復帰。battle_flags4/outcome1とwire field:falseの残留を未復帰や追加勝利にしない。

26〜30通常menu0→4、31確認/32上書き、33〜45保存中。45counter57でも部分write、46〜49成功文言/安定Flash、50field。cold0/1の120frame後まで全SaveRTC/人物と床の暗所field全byte一致。

## 限定差分と未完

全party600bytesの差分はslot3 PPの1byteだけ。HP/EXP/held item/残partyを保持。全Bag/17904円/RP0、全legacy flags、PC/S61E全payloadと旧Save56bank57344byte保持。42checksum、7030byte/1731範囲。aux4021=25→38/4022=4→0のruntime owner未解明。RAMledgerは向きを北に変えた観測3で変化し、その後coldまで939b183a...を保持するがowner未解明。過去台帳/offset41/2056/aux/40ac未解明も保持。

全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CIの既知不一致/action_requiredを成功にしない。

次: Save57 artifact11284919827のstory-fast.srm（131088bytes/SHA256 082a6789ed90223995bd007efaa43337c8aca352d85f1a33068a6fae11b1b9ca）だけから再開。map1/59・19,13北。通常13歩と野生バーニンLv9へ1勝、つばめがえし1回/PP14→13、HP288/294・ミュウツー全HP/PP・Bag/17904円/RP0/badge1/story4071=9/4072=1保持、Save57/独立Continueを限定受入。上階/像の紙は未到達。旧次工程20,24のwarp8は床behavior8上の着地点であり、通常北入力では発火しない。未保存失敗16入力3画面/native1/Save56全byte不変を保持し、同じ北歩行を繰り返さない。次は保存済pr16_story_save57_measure.ROUTEの19,13からの接尾辞を使い、北19,12→西7,12→南7,16→西5,16→北5,6→東28,6→南28,10→東30,10のbehavior108階段warp5→map1/60warp2へ通常入力。最初の新event/戦闘/未通過境界で保存する。到着候補32,10/33,10は未測定。像の紙ownerはmap1/60背景16,28/script149012422・item274だいじなふうしょ/setflag4383と静的照合済みだが取得は未受入。次階層warp31,21→map1/59の31,22は逆向き着地点と区別。27controller計28実行と51新受入、93+cold13入力53画面69memberを無影響再走0。RAMledgerは観測3で939b183a3db45a9fedd87e87814bbb94e1cd42a8510dc3d3083d0ce96d9ff1d4へ変化しowner未解明、全coldSaveRTC/全暗所field画面同一。45counter57でも部分write、46成功→50field。旧RAM/offset41/2056/aux4021/4022/404d/40acのowner未解明を保持。Flash未使用/未習得、がくしゅうそうち未装備。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
