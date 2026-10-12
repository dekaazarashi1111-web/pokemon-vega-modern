# 初ディグダ配置変更・Save77限定受入

`PASS_FIRST_DIGLETT_EVENT_SAVE77_SCOPED`。Save76のジム10/16・6,18北から北3歩、local5/6,14への通常A。台詞2本、4372/4378 set、local5消失を確認。6,15北で通常Save77/独立Continue。新戦闘0、ジム突破は未受入。

source `4f11ebcc0481013051cf83c092fabc7737915b2f` / run `37172406819` / job `111347883827`全8step成功。artifact `11291697564` / 145360bytes / SHA256 `89e54745a9599cc5f81ae8bca48dcb5f0e30da85e4dd7536121bd8bced5fb321`。46member/31画面/54+cold13入力。新controller26/新受入51。native2/record0/旧成功再走0/ROM変更0。

## 初回ownerと観測

保存済gym graphの29命令を再利用。4378未set分岐はset4378/set4372/removeobject5。2台詞のROM byteも固定。全域再scanなし。4「めのまえのディグダにはなしかけた」、5「ディグダのはいちがへんかした」、6field/北通路が開く。7〜11通常menu0→4、12確認/13上書き、14〜24保存中。23最終hash先行counter76、24counter77でも別一時hash/未完、25〜27成功、28field。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持。physical flags全保持、S61E payload258:7→23/259:160→164の2flagだけ。aux4021:85→88/4022:2→0のruntime ownerは未解明。42checksum/7112byte1787範囲、旧Save76bank57344byte保持。

全SaveRTCとprogress28/cold0/cold1全pixel一致。progress/cold0のRAM台帳は6270e896、cold1の120frame待機後だけ60276271へ変化。原因ownerは未解明。保存と画面の一致を全RAM不変へ読み替えない。

## 次

[local6への新4歩とowner](../content/modernization/pr16_story_save77_next_route.json)。旧初ディグダを再走しない。

Save77 artifact11291697564のstory-fast.srm（131088bytes/SHA256 11632f541a4c8b6a7782c32b5e30b0c4c9414a8cc4323da0e263e6454cc867e6）だけから再開。ミルジム10/16・6,15北。新北3歩と初ディグダlocal5への通常Aで4372/4378 set・local5消失、2台詞と通常Save77/独立Continueを受入。次は保存next-routeの開いた6,14へ北2歩→左2歩4,13→北旋回を確認→local6/4,12へA。4372=true分岐は4375 set/remove9→4372 clear/add5。最初の新event/battle後通常保存。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持、S61E payload258:7→23/259:160→164の2flagだけ。54+cold13入力31画面46member/native2、26新controller/51新受入。23最終hash先行counter76→24counter77/別一時hashでも保存中→25成功→28field。全SaveRTC/field全pixel一致。progressとcold0のRAM台帳6270e896保持、cold1だけ60276271へ変化しruntime owner未解明。全RAM不変としない。aux4021:85→88/4022:2→0のowner未解明。紙consumerは博物館2階local2・badge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャーは未完。全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達も未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
