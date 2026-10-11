# 第3ディグダ配置変更・Save79限定受入

`PASS_THIRD_DIGLETT_EVENT_SAVE79_SCOPED`。Save78のジム10/16・4,13北から東5歩、東/北2旋回、local8/9,12への通常A。台詞2本とlocal5/8消失・local9再出現、4372/4374 set・4375 clearを確認。9,13北で通常Save79/独立Continue。新戦闘0、ジム突破は未受入。

source `3a728e7cee7fd19ec21a86264b6e211c7bbe55a1` / run `37174296972` / job `111353581646`全8step成功。artifact `11292333576` / 160894bytes / SHA256 `9c0aeb948cc228dd0da14c7b45194a677a0c680110857bdcf1e7463ee35a776b`。50member/35画面/62+cold13入力。新controller29/新受入56。native2/record0/旧成功再走0/ROM変更0。

## 第3ownerと観測

保存済gym graphの43命令/2台詞を再利用。4372/4373=false・4375=true・4376=false分岐はset4372/remove5・set4374/remove8・clear4375/add9。全域再scanなし。0開始、1東旋回、2〜6東5歩、7北旋回、8「めのまえのディグダにはなしかけた」、9「ディグダのはいちがへんかした」、10field。7/10原画で3個体の配置差を確認。11〜15通常menu0→4、16確認/17上書き、18〜27保存中、27最終hash先行、28counter79/成功文言、28〜31成功、32field。27のhashだけで完了としない。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持。physical flags全保持、S61E payload258:135→87の3flagだけ。aux4021:92→97のruntime ownerは未解明。42checksum/7068byte1804範囲、旧Save78bank57344byte保持。

全SaveRTCとprogress32/cold0/cold1全pixel一致。今回全progress/coldのRAM台帳60276271保持。Save77 cold/Save78 progressなど過去RAM差分ownerは未解明のまま。後続開始定数はSave79のcold0と一致する。

## 次

[local9への新10歩とowner](../content/modernization/pr16_story_save79_next_route.json)。local5/6/8の旧入力は再走しない。

Save79 artifact11292333576のstory-fast.srm（131088bytes/SHA256 88040caadde36a1cbad95bb8e558650089d868d742bba16809a3a32f8ae7553b）だけから再開。ミルジム10/16・9,13北。local8通常Aで4372/4374 set・4375 clear、local5/8消失・local9再出現を全画面/保存ownerで受入。次は保存next-routeの9,12→9,11→3,11→3,9へ新10歩、西旋回→local9/2,9へA。4372/4374=true分岐は4375 set/remove9・4372 clear/add5・4374 clear/add8。最初の新event/battle後通常保存。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持、S61E payload258:135→87の3flagだけ。62+cold13入力35画面50member/native2、29新controller/56新受入。27最終hashでもcounter78/保存中→28counter79/成功文言→32field。全SaveRTC/field全pixel/今回RAM台帳60276271保持。aux4021:92→97のowner未解明、過去Save77 cold/Save78 progress RAM差分ownerも未解明。紙consumerは博物館2階local2・badge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャーは未完。全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達も未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
