# ミルジムtrainer160通常1勝・Save83限定受入

`PASS_GYM_TRAINER160_SAVE83_SCOPED`。Save82のジム10/16・6,7北から新東5歩11,7でlocal3/trainer160視線発火。たんぱんこぞうトラジの4体を通常撃破し384円獲得、physical1440だけset。通常Save83/独立Continue。残り北4歩/第6switchは未入力。

source `73ed1d12284202767179653e77e642a92c2dbaf6` / run `37177597798` / job `111363381549`全8step成功。artifact `11293763616` / 306071bytes / SHA256 `587f00bf6078a0e022171ddc8bf20282601c456e533165e1bfe76a70911780f5`。85member/70画面/132+cold13入力。新controller31/新受入67。native2/record0/旧成功再走0/ROM変更0。

## 通常戦闘と保存境界

0開始6,7北→1東旋回→2〜6東5歩11,7視線、7/8NPC南隣からの台詞。9〜44新戦闘。ライノス♀Lv22、レクオレ♂Lv23、ファイマー♂Lv23、リーティン♂Lv24。ドラゴンクロー2回/かわらわり2回/交代取消3。23でHP288→287、42勝利/44賞金384円。PP予約は選択ごと最大3PPで、2回後にslot2へ切替。実消費は保存party byteから別途確認。

45field、46〜50menu0→4、51確認/52上書き、53〜62保存中。62counter83でも部分write、63最終hashと成功文言、67field。全party597byte保持、PP6→4/14→12・HP288→287の3byteだけ。全EXP/持物/控え保持。全Bag保持と20280→20664円。physical1440だけ、PC/S61E/紙274一個/flag4383保持。42checksum/7168byte1847範囲、旧Save82bank57344byte保持。

progress45/67/cold0/1全pixelと全SaveRTC一致。progressRAM17/38変化・aux4021:111→115はruntime owner未解明。coldRAMは保存直前と同一で120frame後も保持。過去RAM差分owner解明とは別。local3元位置11,9/trainer160は静的ownerと勝利bitで照合し、南隣11,8は画面上の位置。runtime object IDの確定とは区別。

## 次

[第6local11への残り新北4歩と限定39命令owner](../content/modernization/pr16_story_save83_next_route.json)。4372/4373/4374/4375=false、4376=trueから4374set/remove8・4376clear/add10。local11自体は残る。今回は未入力のため静的予測のままであり、ジム突破には昇格しない。

Save83 artifact11293763616のstory-fast.srm（131088bytes/SHA256 157a945e7bdb3287b519c235ef95c12ddcefb14a62d479cf3a5f753e4f009523）だけから再開。ミルジム10/16・11,7東。新東5歩でlocal3/trainer160トラジに通常1勝、敵4体/賞金384円/physical1440set。次は新北4歩11,3、西のlocal11/10,3へ旋回して通常A。4376=true分岐は4374set/remove8・4376clear/add10、local11自体は残る。最初の新event/battle後通常保存、予期しない境界は縮小停止。旧5switch/勝利trainer132/160再走0。HP287/294・PP4,10,12,2、Bag20664円・紙274一個/PC/S61E保持。132+cold13入力70画面85member/native2、新controller31/新受入67。62counter83でも保存中/部分write→63最終hash/成功→67field。全SaveRTC/field全pixel/coldRAM保持。今回RAM17/38変化・aux4021:111→115と過去RAM差分のruntime owner未解明。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
