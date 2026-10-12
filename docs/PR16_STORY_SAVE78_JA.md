# 第2ディグダ配置変更・Save78限定受入

`PASS_SECOND_DIGLETT_EVENT_SAVE78_SCOPED`。Save77のジム10/16・6,15北から北2/左2歩、左/北2旋回、local6/4,12への通常A。台詞2本とlocal5再出現、4372 clear/4375 setを確認。local9は画面外のため除去を固定ownerと保存flagで照合。4,13北で通常Save78/独立Continue。新戦闘0、ジム突破は未受入。

source `de1b52a458cb1acc6f7729052e80f000cab46716` / run `37173461220` / job `111351067311`全8step成功。artifact `11292531569` / 161328bytes / SHA256 `b4f001281468afc2cf2f1ece1ee22a99b9d3565775ca42f0cb0f4b3ef4fb39a5`。49member/34画面/60+cold13入力。新controller29/新受入56。native2/record0/旧成功再走0/ROM変更0。

## 第2ownerと観測

保存済gym graphの43命令を再利用。4372=true・4374/4376=false分岐はset4375/removeobject9/clear4372/addobject5。2台詞byteも固定。全域再scanなし。0開始、1〜2北歩、3左旋回、4〜5左歩、6北旋回、7「めのまえのディグダにはなしかけた」、8「ディグダのはいちがへんかした」、9field。10〜14通常menu0→4、15確認/16上書き、17〜26保存中、27counter78/最終hash/成功文言、27〜30成功、31field。counter/最終hashだけでfield完了としない。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持。physical flags全保持、S61E payload258:23→135の2flagだけ。aux4021:88→92/4022:0→4のruntime ownerは未解明。42checksum/7121byte1798範囲、旧Save77bank57344byte保持。

全SaveRTCとprogress31/cold0/cold1全pixel一致。progress0/1のRAM台帳6270e896→progress2以後60276271。Save78 cold0/1も60276271で安定。原因ownerは未解明。今回cold安定から過去cold差分や全progress RAM不変を主張しない。後続開始定数はSave78のcold0を使う。

## 次

[local8への東5歩とowner](../content/modernization/pr16_story_save78_next_route.json)。local5/6の旧入力は再走しない。

Save78 artifact11292531569のstory-fast.srm（131088bytes/SHA256 ae2385e5668d3ce9af954fe473c55881960c43dc98857afd93892209bfaffa1b）だけから再開。ミルジム10/16・4,13北。新北2/左2歩と左/北2旋回、local6通常Aで4372 clear/local5再出現・4375 set/local9除去ownerを受入。次は保存next-routeの東5歩9,13→北旋回→local8/9,12へA。4372/4373=false・4375=true・4376=false分岐は4372 set/remove5・4374 set/remove8・4375 clear/add9。最初の新event/battle後通常保存。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持、S61E payload258:23→135の2flagだけ。60+cold13入力34画面49member/native2、29新controller/56新受入。17〜26保存中→27counter78/最終hash/成功表示→31field。全SaveRTC/field全pixel一致。progress2でRAM台帳6270e896→60276271、以後/cold0/1保持、runtime owner未解明。次開始COLD_LEDGERは60276271で旧Save77のcold0とは異なる。aux4021:88→92/4022:0→4のowner未解明。紙consumerは博物館2階local2・badge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャーは未完。全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達も未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
