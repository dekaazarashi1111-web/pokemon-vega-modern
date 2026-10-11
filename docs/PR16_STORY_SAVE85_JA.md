# ミルジム第7ディグダ配置変更・Save85限定受入

`PASS_SEVENTH_DIGLETT_EVENT_SAVE85_SCOPED`。Save84のジム10/16・11,3西から新南4/西5歩6,7へ。南のlocal10/6,8に通常A、4374trueの未入力branchで4372 set/remove5・4374 clear/add8。local10自体は残る。通常Save85/独立Continue、新戦闘0。

source `82233207e0a0d5c3ac4939bd0167f3ca2af20417` / run `37179458924` / job `111368877918`全8step成功。artifact `11294671228` / 188776bytes / SHA256 `38be22318e6505767f44799730956c14dc93f38a12370427a8866012de032149`。55member/40画面/72+cold13入力。新controller31/新受入63。native2/record0/旧成功再走0/ROM変更0。

## 通常配置変更と保存境界

0開始11,3西→1南旋回→2〜5南4歩→6西旋回→7〜11西5歩6,7→12南旋回→13話しかけた台詞→14配置変更文言→15field。local10保持。local5除去/local8復帰を保存flagsと限定39命令ownerで照合し、全変更object画面内とは主張しない。

16〜20menu0→4、21確認/22上書き、23〜33保存中。33でcounter85だが部分hash/保存中、34で最終hashと成功文言、37field。partyは598/600byte保持、raw241:108→109/341:61→62（控え2体のraw offset41）が観測11で変化、RAM台帳も同時変化。runtime ownerは未解明。主力HP287/294・PP4,10,12,2/EXP/持物/全Bag・20664円・紙274一個・PC・physical flags保持。S61E payload258:71→23で4372 set/4374 clear、CRC確認。42checksum/7171byte1847範囲、旧Save84bank57344byte保持。

progress37/cold0/1全pixelと全SaveRTC一致、cold RAM台帳保持。aux4021:119→0/4022:4→3と過去RAM差分runtime ownerは未解明のまま。party/RAMの全保持とは記録しない。

## 次

[第8local10の未入力4372true branchと限定43命令owner](../content/modernization/pr16_story_save85_next_route.json)。移動せず同じ南向きAで4373/4377set/remove6/11・4372clear/add5。別stateの新eventとして通常保存する。

その保存後にleader前7,3へ東5/北4/西4の13歩を進む静的候補がある。第8/leader到達・勝利/ジム攻略は未入力・未受入。

Save85 artifact11294671228のstory-fast.srm（131088bytes/SHA256 0001f6a52812526ea52a9f2bcca8055e934379830214a8507867b10e3c2e00e0）だけから再開。ミルジム10/16・6,7南。第7local10の4374true branchで4372set/remove5・4374clear/add8、local10保持。次は移動せず南のlocal10/6,8へ通常A。4372trueの未入力第8branchで4373/4377set/remove6/11・4372clear/add5を予測。最初の新event後通常保存し、別stateとして独立Continue。第8後の東5/北4/西4の13歩leader前7,3は静的候補のみ、今回未入力。旧第5/第7branch、勝利trainer132/160再走0。HP287/294・PP4,10,12,2/Bag20664円・紙274一個/PC保持。party598/600byte保持、raw241:108→109と341:61→62が進行観測11で変化、RAM台帳も11で変化。これら/aux4021:119→0・4022:4→3と過去差分runtime ownerは未解明。72+cold13入力40画面55member/native2、新controller31/新受入63。33counter85でも保存中/部分hash→34最終hash/成功→37field。全SaveRTC/field全pixel/coldRAM保持。紙consumer博物館2階local2はbadge0x823必須、現badge1で引渡し未解禁。ジム突破→紙引渡し→505道路レンジャー、全story/全国図鑑/自然成長進化/LuckyEgg/研究施設自然到達は未完。Flash未使用/がくしゅうそうち未装備、host補充/ROM変更/入力ROMruntime再配布/故意全滅/merge/release/baseline変更なし。一般CI既知qol_production.c不一致/action_requiredを全成功にしない。
