# ミルジムtrainer132通常1勝・Save82限定受入

`PASS_GYM_TRAINER132_SAVE82_SCOPED`。Save81のジム10/16・6,9北から新北2歩6,7、local1/trainer132視線発火。やまおとこヤスハルの4体を通常撃破し864円獲得、physical1412だけset。通常Save82/独立Continue。ジムleader/第6switchは未入力。

source `e98ad40624e04de8842dc19f5601ce28f125749e` / run `37176546268` / job `111360218777`全8step成功。artifact `11292834696` / 288486bytes / SHA256 `b48fdb05b06fa6bfcd90b0921ca8b3db2574c1e214563170831f4fbdc5fa7208`。78member/63画面/118+cold13入力。新controller36/新受入66。native2/record0/旧成功再走0/ROM変更0。

## 通常戦闘と保存境界

0開始6,9北→1/6,8→2/6,7視線、3/4NPC西隣からの台詞。5〜37新戦闘。サイホーンLv22♂、ゴビットLv23、コジオLv23♀、ワンリキーLv24♂。ドラゴンクロー3回、かわらわり1回、交代取消3。35勝利/37賞金864円。PP予約は選択ごと最大3PPで、3回後にslot2へ切替。実消費は保存party2byteから別途確認。

38field、39〜43menu0→4、44確認/45上書き、46〜55保存中。55counter82でも部分write、56最終hashと成功文言、60field。全party598byte保持、PP9→6/15→14の2byteだけ。HP288/294・全EXP/持物/控え保持。全Bag保持と19416→20280円。physical1412だけ、PC/S61E/紙274一個/flag4383保持。42checksum/7172byte1846範囲、旧Save81bank57344byte保持。

progress38/60/cold0/1全pixelと全SaveRTC一致。progressRAM13/34変化・aux4021:110→111/4022:2→0はruntime owner未解明。coldRAMは保存直前と同一で120frame後も保持。過去RAM差分owner解明とは別。local1元位置3,7/trainer132は静的ownerと勝利bitで照合し、西隣5,7は画面上の位置。runtime object IDの確定とは区別。

## 次

[第6local11への新東5/北4歩と限定39命令owner](../content/modernization/pr16_story_save82_next_route.json)。4372/4373/4374/4375=false、4376=trueから4374set/remove8・4376clear/add10。local11自体は残る。未測定の次候補であり、ジム突破には昇格しない。

Save82 artifact11292834696のstory-fast.srm（131088bytes/SHA256 ba090d0e6efe1f7d3effba4991973bd956574f18780fa7843ccf4910748ec8e9）だけから再開。ミルジム10/16・6,7北。新北2歩でlocal1/trainer132ヤスハルに通常1勝、敵4体/賞金864円/physical1412set。次は東5歩11,7・北4歩11,3の新9歩、local11/10,3へ西旋回して通常A。4376=true分岐は4374set/remove8・4376clear/add10、local11自体は残る。最初の新event/battle後通常保存、予期しない境界は縮小停止。旧5switch/勝利trainer132再走0。HP288/294・PP6,10,14,2、Bag20280円・紙274一個/PC/S61E保持。118+cold13入力63画面78member/native2、新controller36/新受入66。55counter82でも保存中/部分write→56最終hash/成功→60field。全SaveRTC/field全pixel/coldRAM保持。今回RAM13/34変化・aux4021:110→111/4022:2→0と過去RAM差分のruntime owner未解明。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
