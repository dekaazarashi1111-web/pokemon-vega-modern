# 第5ディグダ配置変更・Save81限定受入

`PASS_FIFTH_DIGLETT_EVENT_SAVE81_SCOPED`。Save80のジム10/16・3,9西から新東3歩、東/北2旋回、local10/6,8への通常A。台詞2本、local10消失/local9復帰、4376 set・4375 clearを確認。6,9北で通常Save81/独立Continue。新戦闘0、ジム突破は未受入。

source `2b152a0e2e63717ded440febee87a6bb277744bd` / run `37175514324` / job `111357194355`全8step成功。artifact `11293356282` / 147423bytes / SHA256 `d2d31d0bcb762100120c1dec319055ab1c843b05894ab7eb9632b5c6be1b4f5a`。48member/33画面/58+cold13入力。新controller31/新受入56。native2/record0/旧成功再走0/ROM変更0。

## 第5ownerと観測

保存済gym graphの39命令/2台詞を再利用。4372/4373/4374=false・4375=true分岐はset4376/remove10・clear4375/add9。全域再scanなし。0開始、1東旋回、2〜4東3歩、5北旋回、6話しかけた台詞、7配置変更、8field。local10除去/local9復帰は5/8原画と保存flagで照合。9〜13menu0→4、14確認/15上書き、16〜25保存中、25最終hashでもcounter80/保存中文言、26counter81/成功文言、30field。最終hashだけで完了としない。

全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持。physical flags全保持、S61E payload258:135→7・259:164→165の2flagsだけ。aux4021:107→110・4022:4→2のruntime ownerは未解明。42checksum/7126byte1827範囲、旧Save80bank57344byte保持。

全SaveRTCとprogress30/cold0/cold1全pixel一致。今回はprogress/coldの全RAM台帳も保持。過去Save77/78/80等RAM差分owner解明とは区別。後続開始定数はSave81のcold0と一致。

## 次

[local1/trainer132への新北2歩とowner](../content/modernization/pr16_story_save81_next_route.json)。開いたlocal10跡から6,7へ。local1/3,7の視線距離3を静的確認した新event候補であり、native戦闘は未受入。第6ディグダを無目的に押さない。

Save81 artifact11293356282のstory-fast.srm（131088bytes/SHA256 3beb00ee134983ae76b2e41bdc9d5cdbf76e2d031d3f42d3a07fadb164a07633）だけから再開。ミルジム10/16・6,9北。第5local10通常Aで4376 set/remove10・4375 clear/add9を受入。次は開いたlocal10跡6,8を通って新北2歩6,7へ。local1/3,7のtrainer132・視線距離3・movement10の新event候補で、最初の新戦闘/新境界の後だけ通常保存。発火しなければ6,7で縮小停止し画面確認。旧switchの入力再走0。全party600byte/HP288/294・PP9,10,15,2/Bag19416円/紙274一個/PC保持、S61E2flagsだけ。58+cold13入力33画面48member/native2、新controller31/新受入56。25最終hashでも保存中/counter80→26counter81/成功文言→30field。全SaveRTC/field全pixel/RAM台帳保持。過去Save77/78/80等RAM差分と今回aux4021:107→110・4022:4→2のruntime owner未解明。紙consumerは博物館2階local2・badge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
