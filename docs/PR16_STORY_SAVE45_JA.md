# 西上段・下り階段・Save45 限定受入

`PASS_ROUTE504_WEST_DESCENT_SAVE45_SCOPED`。504番道路39,12西の上段から西へ進み、26,10→26,11の下り階段→26,12下段へ。19歩/7方向転換・戦闘0、通常Save45と独立Continueを限定受入。回復地点到達とPP回復は未完。

source `cc2be073d7a914bad7c077b8f16d4e6ea61988bb` / run `37136050485` / job `111240684827` 全8step成功。artifact `11278563389` / 455477bytes / SHA256 `e41256ac2b00d0024a0a6d834283faa7a522082884d4a79f7500ee34a8cc0d44`。全70member/55画面/98+cold13入力。20controller成功原logを継承、新32原本受入/拒否試験だけ。native2/record0/旧受入再走0/ROM変更0。

先頭オノノクスHP294/294・PP[15,10,15,20]、2番目ミュウツーHP314/354・PP[0,0,0,0]、全party600byte不変。費用/道具消費0。バッグの道具/きのみは空のまま。控えの既存PPを回復済みと混同しない。

0〜26通常西進と階段を通過。27〜31通常menu cursor0→4。34〜45部分write12状態。46最終Flashに一致するがcounter44/書込み中、47counter45もまだ書込み文言。48〜51成功文言、52field。cold0/1は26,12南の下段。全55画面を目視。

全Bag/14264円/legacy flags/PC/S61E/story4071=9/4072=1/badge1不変。補助var4021=104→123/4022=0→4はruntime owner未解明。42sector checksum/旧Save44bank57344byte/6890byte1706範囲/cold全SaveRTC一致。全観測RAM ledger `4bc47968c1071a65f115cc64d8aa48dc2a37fcf75718360dd375f3dc7e8dfa0a` も不変。Save44の並替時変化とSave39旧cold差owner未解明を保持。

保存済504地形1440cell/既存owner再採取0。高度4から階段0を経て下段3へ通常通過した範囲だけを受入。共通PPラベル/arrowの新classifierは20controller試験を通過したが、今回は戦闘0で実オノノクス技UI未観測。次の新戦闘で独立照合する。

## 次checkpoint送信前の確認

新counterのAST/import/CP/GUIDE/EVIDENCE/VISUAL/OUT/CODE/workflow名を照合。新counter ORIGINAL/ROMと親counter INPUTのenv集合、親artifact/run/source/save SHA/counter/bank世代/全member数を確認。送信treeとstaged一覧を明示し旧正本と交差0。専用宛先/private/source guardを維持。unittestはreturncode/全成功行/正確な終端で判定し、試験名skippedへのsubstring判定を禁止。成功試験は記録器だけの失敗で再走しない。

次: Save45 artifact11278563389のstory-fast.srm（e356f82361d9c0cccf984a7113b91324d42d6c3c15acf22b42a4fea3ce21927d、131088bytes）だけから再開。map3/44・26,12南/下段elevation3・party4/RP0・14264円・badge1・story4071=9/4072=1。西上段39,12から26,10→26,11下り階段→26,12下段を通常通過、19歩/7方向転換/戦闘0。全party600byte不変。先頭オノノクスHP294/294・PP[15,10,15,20]、2番目ミュウツーHP314/354・PP[0,0,0,0]のまま。道具/きのみ空、回復地点はまだ未到達。次は保存済み1440地形から26,12→25,12→24,12→23,12→22,12→22,11→22,10→9,10方面の下段西通路を有限候補にする。最初の新戦闘/event/未通過境界で通常Save。先頭オノノクスの新classifierは共通PPラベル/arrowに変更し20controller試験済みだが今回戦闘0で実技UIは未観測。新戦闘では実cursorと技名/残PPを画面と保存partyから照合。旧ミュウツー技名依存classifierやPP0入力loopを使わない。南側map3/23→3/2は静的接続候補であり回復施設の位置/到達は未受入。host補充/ROM編集/故意の全滅なし。98+cold13入力・55画面・20controller32受入試験を無影響再走しない。46最終Flashでもcounter44/書込中、47counter45、48成功文言→52field。全SaveRTC/cold RAM ledger一致、補助var4021=104→123/4022=0→4のowner未解明。Save44並替RAM ledger差、Save39旧差、Save40/41/42失敗回収履歴を保持。通常story/正規全国図鑑/自然EXP・技習得・進化/Lucky Egg/12ケース/Lv100soak/研究施設自然到達未完。全story/一般CI全成功/製品release未完。cleanROM二重生成/BPS固定/merge/release/baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
