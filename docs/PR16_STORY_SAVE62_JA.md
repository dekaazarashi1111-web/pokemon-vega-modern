# 館のコレクター210新1勝・Save62限定受入

`PASS_MANSION_COLLECTOR210_SAVE62_SCOPED`。Save61の25,6東から新1歩で26,6東へ進み、ヒサテルに発見され新trainer戦。敵3体を倒して1勝、通常保存・独立Continue。上階/有効階段/像の紙は未到達。

source `ec04bdcf827896ce22d2d0d39aaa9e3f63d88d20` / run `37159791919` / job `111310675760`全8step成功。artifact `11286961947` / 219383bytes / SHA256 `9ed808bfc02e6531bcc2c4df59089f18e70154a82b4a0ff6f807630d76fb9364`。71member/56画面/101+cold13入力。新controller27case、58新受入拒否試験。native2/record0/旧受入再走0/ROM変更0。

## コレクター新1勝と保存

0開始、1新1歩/接近、2勧誘台詞、3導入、4ポケモンコレクターのヒサテル。5イシズマイ♂Lv11、15ビッパ♂Lv12、21コフキムシ♀Lv14。10/16/22でslot3つばめがえし選択、実PP9→8→7→6。13/19の交代確認を2回拒否し先頭維持。25勝利、26降参台詞、27実賞金840円、28field。3体撃破を3勝とせずtrainer1勝だけ。

29〜33menu0→4、34確認/35上書き、36〜48保存中。48counter62でも部分write、49〜52成功文言、53field。progress28/53/cold0/cold1の全画面byte一致、全SaveRTCも一致。今回trainer戦後はwire field=trueへ戻る。残留flags12/outcome1を追加勝利にしない。

## 差分・静的owner・次の経路

party600bytes中slot3 PPの1byteだけ変化し残り599byte保持。保存partyからPP8/7/6各段階の全600byte hashも独立再構成。HP288/294・PP15,10,15,6、ミュウツー全HP/PP、EXP/held item・全Bag/RP0・全legacy vars・PC/S61E全payload・旧Save61bank57344byte保持。所持金17904→18744。legacy flag唯一の差分はphysical1490=0→1。保存済map1/59 local9/初期26,4/script154591088のtrainerbattle210命令と固定remap210+0x500→1490をROM byte照合。ただしruntime object IDの直接捕捉とは主張しない。

42checksum、6975byte/1716範囲。RAM台帳は観測17の2体目撃破で変化しruntime owner未解明。過去のRAM台帳/offset41/2056/aux/40ac未解明を保持。

保存済み二階層の静的床/warp ownerから、[紙までの静的候補](../content/modernization/pr16_story_save62_evidence/route-plan.json)を新規整理。26,6から89tile移動+3層間接続の92edges。上階32,10の領域は紙16,28側と非連結で、上階31,21のbehavior102穴→入口階31,22→入口階30,29階段→上階33,29の南側領域→紙背面16,27が候補。新ROM採取0、動的NPC/戦闘/穴作動/階段作動は未受入。まず未通過8歩の北東階段30,10へ進み最初の新境界で保存する。

全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達は未受入。Flash未使用/未習得、がくしゅうそうち未装備。一般CI既知不一致/action_requiredを成功にしない。

次: Save62 artifact11286961947のstory-fast.srm（131088bytes/SHA256 6526b5a8cf179800096fda0721f2e1770818170c83e9b76da39957166d86e356）だけから再開。map1/59・26,6東。Save61から新1歩でヒサテル/コレクター210の新1勝、敵3体・つばめがえし3選択/実PP9→6・交代拒否2回・賞金840円、physical1490=0→1を限定受入。HP288/294・PP15,10,15,6、ミュウツー全HP/PP、party残り599byte/Bag/RP0/badge1/story4071=9/4072=1/全legacy vars保持、所持金18744。次は未通過8歩26,6→27,6→28,6→28,7→28,8→28,9→28,10→29,10→30,10（behavior108階段）からmap1/60warp2へ。最初の新event/戦闘/不通境界で保存。上階/紙未到達。紙までの静的候補は専用route-plan.jsonの89tile+3層間接続（92edges）。上階32,10側から紙16,28側へ直接歩けず、上階31,21のbehavior102穴→入口階31,22→入口階30,29の階段→上階33,29→紙背面16,27が候補。穴/階段/動的通行は未実測、旧20,24着地点不発は再走しない。27新controller/58新受入、101+cold13入力56画面71member/native2。48counter62でも部分write、49成功→53field。全SaveRTC/field画面同一。RAM台帳は観測17の2体目撃破で変化しowner未解明。旧offset41/2056/aux4021/4022/404d/40ac未解明保持。Flash未使用/未習得、がくしゅうそうち未装備。旧迂回/野生戦/本trainer戦/保存を無影響再走しない。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
