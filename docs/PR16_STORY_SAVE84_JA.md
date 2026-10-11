# ミルジム第6ディグダ配置変更・Save84限定受入

`PASS_SIXTH_DIGLETT_EVENT_SAVE84_SCOPED`。Save83のジム10/16・11,7東から新北4歩11,3、西のlocal11/10,3へ通常A。4374 set/remove8、4376 clear/add10を保存byteと限定39命令ownerで照合。local11自体は残る。通常Save84/独立Continue、新戦闘0。

source `ca2b55818b9ebd8b936b912b30c6ae1d2c4cd6b4` / run `37178451752` / job `111365910830`全8step成功。artifact `11294830074` / 146258bytes / SHA256 `0ed33bdf10932f62481ccbc22ce7e976bc08cf83073b6213423c43d2f68d545f`。49member/34画面/60+cold13入力。新controller31/新受入59。native2/record0/旧成功再走0/ROM変更0。

## 通常配置変更と保存境界

0開始11,7東→1北旋回→2〜5北4歩11,3→6西旋回→7話しかけた台詞→8配置変更文言→9field。local8は画面外、local10は下端のため全変更objectの直接視認は主張しない。保存flagsと固定ownerを照合し、local11は画面に残る。

10〜14menu0→4、15確認/16上書き、17〜26保存中。26は最終hashでもcounter83、27でcounter84/成功文言、31field。全party600byte/HP287/294・PP4,10,12,2/EXP/持物/控え保持。全Bag・20664円・紙274一個保持、physical trainer132/160含む全flags保持、PC保持。S61E payload2byteで4374 set/4376 clear、CRC確認。42checksum/7162byte1849範囲、旧Save83bank57344byte保持。

progress31/cold0/1全pixelと全SaveRTC一致、今回progress/coldRAM台帳全保持。aux4021:115→119/4022:0→4と過去RAM差分runtime ownerは未解明のまま。

## 次

[第7local10の新branchと限定39命令owner](../content/modernization/pr16_story_save84_next_route.json)。南4/西5の9歩6,7、南向きA。4374trueから4372set/remove5・4374clear/add8。旧第5local10の4375true branchは再走しない。

保存後の別stateで同じlocal10へ第8入力すれば4373/4377set/remove6/11・4372clear/add5となり、東側からleader前へ進む静的候補を見つけた。未入力であり、ジム攻略/leader到達・勝利へ昇格しない。毎回通常保存と新stateを照合する。

Save84 artifact11294830074のstory-fast.srm（131088bytes/SHA256 882a52243dfb4d0faf4fa7d1e828197cf198b135c07c7698b3cfaaede360b8ac）だけから再開。ミルジム10/16・11,3西。第6local11の通常Aで4374set/remove8・4376clear/add10、local11保持。次は南4/西5の9歩6,7へ、南のlocal10/6,8へ通常A。4374trueの新branchで4372set/remove5・4374clear/add8。旧Save81の4375true branchとは別の第7相互作用。最初の新event後通常保存、予期しないNPC/境界は縮小停止。第7保存後の第8local10候補は4372trueから4373/4377set/remove6/11・4372clear/add5でleader前経路を開く静的予測、今回未入力。旧switch/勝利trainer132/160再走0。HP287/294・PP4,10,12,2、Bag20664円・紙274一個/PC保持、S61Eは4374/4376だけ。60+cold13入力34画面49member/native2、新controller31/新受入59。26最終hashでも保存中/counter83→27counter84/成功→31field。全SaveRTC/field全pixel/今回RAM全保持。aux4021:115→119/4022:0→4と過去RAM差分runtime owner未解明。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
