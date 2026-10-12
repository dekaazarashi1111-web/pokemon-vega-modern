# 第4ディグダ配置変更・Save80限定受入

`PASS_FOURTH_DIGLETT_EVENT_SAVE80_SCOPED`。Save79のジム10/16・9,13北から北2/西6/北2の新10歩、西/北/西3旋回、local9/2,9への通常A。台詞2本とlocal9消失・local5/8再出現、4375 set・4372/4374 clearを確認。3,9西で通常Save80/独立Continue。新戦闘0、ジム突破は未受入。

source `f508187e5b698a598eaffe0916a9d83c2a21753c` / run `37174872497` / job `111355311681`全8step成功。artifact `11292349565` / 176497bytes / SHA256 `e433d24c51758611f085eae80814a727740ceab682efabd1d6398dc7c70f83fb`。56member/41画面/74+cold13入力。新controller31/新受入56。初回run37174805490は30成功/1失敗でnative未起動、期待入力数4→6を訂正して失敗1件だけ成功。計32実行、成功30件再走0。native2/record0/旧成功再走0/ROM変更0。

## 第4ownerと観測

保存済gym graphの47命令/2台詞を再利用。4372/4374=true分岐はset4375/remove9・clear4372/add5・clear4374/add8。全域再scanなし。0開始、1〜2北2歩、3西旋回、4〜9西6歩、10北旋回、11〜12北2歩、13西旋回。14話しかけた台詞、15配置変更、16field。local9除去/local8復帰は13/16原画、local5は下端で頭部のみなので全体目視を主張せず保存flagとownerで照合。17〜21通常menu0→4、22確認/23上書き、24〜34保存中、34counter80でも最終hash未達、35最終hash/成功文言、38field。counterだけで完了としない。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持。physical flags全保持、S61E payload258:87→135の3flagだけ。aux4021:97→107のruntime ownerは未解明。42checksum/7132byte1831範囲、旧Save79bank57344byte保持。

全SaveRTCとprogress38/cold0/cold1全pixel一致。progress19menu中のRAM台帳60276271→e9f829d5を明示、以後/coldでは保持。今回/過去RAM差分owner未解明。後続開始定数はSave80のcold0と一致。

## 次

[local10への新東3歩とowner](../content/modernization/pr16_story_save80_next_route.json)。local5/6/8/9の旧入力は再走しない。

Save80 artifact11292349565のstory-fast.srm（131088bytes/SHA256 6083038273bdf89de7563800c91a215c861552e7fc4da71af7c4a3c3237580dc）だけから再開。ミルジム10/16・3,9西。local9通常Aで4375 set・4372/4374 clear、local9消失・local5/8復帰を保存ownerで受入。local5全体は画面下端で見えない。次は保存next-routeの東3歩で6,9、北旋回→local10/6,8へA。4372/4373/4374=false・4375=true分岐は4376 set/remove10・4375 clear/add9。最初の新event/battle後通常保存。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持、S61E payload258:87→135の3flagだけ。74+cold13入力41画面56member/native2、新controller31（初回30成功/1失敗、修正1のみ成功。計32実行）/56新受入。34counter80でも保存中/最終hash未達→35最終hash/成功文言→38field。全SaveRTC/field全pixel一致。progress19menuでRAM台帳60276271→e9f829d5、以後/cold保持。今回/過去RAMとaux4021:97→107のowner未解明。紙consumerは博物館2階local2・badge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
