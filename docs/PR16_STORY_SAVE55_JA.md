# ミルシティ通常レンジャー戦・がくしゅうそうち・Save55限定受入

`PASS_MIRU_RANGER_GIFT_SAVE55_SCOPED`。回復済Save54からPC出口4歩/warp、市内26歩でレンジャー東隣16,20。通常Aの会話から6体撃破し、864円・がくしゅうそうち1個・像の裏の紙を調べる依頼・NPC離脱・Save55と独立Continueを受入。

source `3439daa92e993a3edb89f89d3a37a9bcbdba3e99` / run `37151051768` / job `111284855297`全8step成功。artifact `11284146293` / 639742bytes / SHA256 `7c57c180c20427639f4dac4b3bd6302090f18a56a3d8416206803c2b16315804`。154member/139画面/268+cold13入力、21controller原log/47新受入拒否試験。native2/record0/旧再走0/ROM変更0。

## 必須ownerと実戦

未読45node/38cell/1mapだけ採取、既読scriptを復元して再decodeしない。静的candidateの暫定gym欄map39/0はTM21民家と判明し、必須導線から除外。未入館。実際はtown local10(15,20)/script149023660、保存starter4031=0→trainer331、同候補のphysical1611。new setflag4381をS61E payload259のbit5から独立照合。

観測36〜45の会話→46戦闘開始。つばめがえし6回選択/実PP20→14、5回交代拒否。ダブルtarget確定0。オノノクスHP294→293→288/294。ミュウツー354/354と全PP保持。94勝利/96報酬864円/102〜103がくしゅうそうち/104〜111像の裏の紙の依頼/112NPC離脱とfield。主力Lv100によるstory短縮であり自然育成・難易度受入ではない。

## 保存と限定差分

113〜117通常menu0→4、118確認/119上書き、120〜131部分write。131counter55でも部分write、132最終Flashでも保存中、133〜135成功文言、136field。cold0/1は全SaveRTC同一、勝利残留を追加勝利にしない。

party5byte差分だけ。PP6/HP6と仲間offset41三件。歩行時の3byteとRAM台帳41/63/83/103のownerは未解明。Bagは空items先頭へ182を1個追加だけ、17040→17904円。legacy1611とexpanded4381だけ。vars4021=114→16/4022=1→0/40ac=0→16はruntime owner未解明。story4071=9/4072=1、badge1、全国図鑑未解禁。旧bank57344byte、PC全byte、S61E CRC/残payload保持。42checksum、6999byte/1764範囲。

がくしゅうそうちは装備していない。回復を繰り返していない。こころのやかた入館・像の調査は次工程。旧Save52 cold差/Save54回復台帳owner未解明も保持。

次: Save55 artifact11284146293のstory-fast.srm（131088bytes/SHA256 f9f9638a49aa4b0f0553c3bfcbaeb736f49d4ae42e5b5ca2509c8aaad9f515a2）だけから再開。map3/2・16,20南、こころのやかた前。通常出口/市内30歩、レンジャー331の6体へ1勝/864円/がくしゅうそうち182を1個通常取得、離脱flag4381、Save55/独立Continue全SaveRTC一致を限定受入。オノノクス288/294・PP[15,10,15,14]、ミュウツー354/354・PP[10,20,15,10]、所持金17904円/RP0/badge1/story4071=9/4072=1。次はNPC実台詞「こころのやかた奥のどうぞうの裏の紙」を調べる必須導線。保存済town warp15,19→map1/59・warp1から、未読室内owner/必要地形だけ調査し通常入力で入館・最初の新event/戦闘/未通過境界を保存する。任意TM21民家map39/0をgymと誤認しない。がくしゅうそうちは取得のみ、装備/自然成長受入なし。RAM台帳4差分/仲間offset41三件/aux2件と40ac=16のowner未解明を保持。最終/cold台帳77ccaa1d7ceee4a641d1094ab5b8f5caf44668ea125287542f3e2bed65a80e57。Save55counter131は部分write、132安定でも保存中→133成功→136field。268+cold13入力139画面21controller47受入154memberを無影響再走0。全国図鑑/全story/自然育成・進化/LuckyEgg/研究施設自然到達未完、doubletarget分離native未実証。既存ROM/runtime/input非再配布、host補充/回復再走/故意全滅/merge/release/baseline切替なし。一般CI既知不一致/action_requiredを全成功にしない。
