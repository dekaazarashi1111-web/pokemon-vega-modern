# 洞窟本区画南出口・Save37 限定受入

`PASS_CAVE_SOUTH_EXIT_ROOM_SAVE37_SCOPED`。Save36の6,13から南へ通常歩行し、4,19のwarpでmap1/38・6,4西の南出口部屋へ到達。通常Save37/独立Continueまで限定受入。西側開通/正規event/trainer360を含む本区画走破のmilestoneは完了した。出口部屋から外の503番道路への接続と全storyは未受入のまま保持する。

source `7e5bc03a76de3b99c4f999c05c9fcf48963b0044` / run `37126025449` / job `111211361589` 全8step成功。artifact `11275371718` / 186258bytes / SHA256 `4e846024bfa840a09459bc5b7c166f4cf170a1844d43f117e6be0c1bc36abc2d`。全48member、63/cold13入力、33画面。新12controllerと26原本受入/拒否試験、native2/記録native0。ROM/fixture/compile/既受入再走0。地形920cells/出口warp/接続部屋viewは保存原本再利用。

戦闘0・party600byte/HP320/PP[1,8,0,0]/全Bag/HM05/13576円/PC/S61E/story4071=8/4072=1・badge1不変。補助flag2056=0→1とvar4021=19→26/4022=0→2/404d=20→21のruntime ownerは未解決。42sector checksum/旧Save36bank57344byte/6917byte1753範囲差分/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400保持。

13〜23は部分write、24は書込中画面/counter36のまま最終Flash hashと一時一致し、25では再び異なる。単一hash一致を保存完了としない。26〜29でcounter37・安定全Flashと保存成功文言、30でfield復帰。独立Continue0/1も同じ南出口部屋。全sector checksum/全SaveRTC比較と画面の異なる意味を保つ。

次: Save37 artifact11275371718のstory-fast.srm（7942159bf82220a864a128c66f97aa3da6e2558b0f3e8181d410a925e145a301、131088bytes）だけから再開。map1/38・6,4西・party4/RP0・13576円・badge1・story4071=8/4072=1、ミュウツーHP320/354・PP[1,8,0,0]。Save36の正規event/trainer360完了地点から洞窟本区画4,19→南出口部屋1/38へ通常warpし、Save37/独立Continueを限定受入。本区画走破のmilestoneは完了。外の503番道路への接続/全storyはまだ未受入。次は部屋6,4→6,5→5,5→4,5→4,6の通常出口候補。保存済map1/38 warp0は4,6→map3/21 warp1。必要なら既存のmap3/21 warp1保存ownerを照合し、未保存のtargetだけ限定採取する。host回復/PP/flag/var注入は禁止。受入済の西側event・trainer360・洞窟本区画・今回63/cold13入力33画面/12controller26受入を無影響再走しない。party600byte/Bag/13576円/PC/S61E/story値は不変、補助flag2056=0→1とvar4021=19→26/4022=0→2/404d=20→21だけ。runtime owner未解決。24のFlash一時一致/counter36を保存完了にせず、25のhash再差分、26〜29成功文言/安定全Flash、30field復帰/cold全SaveRTC一致を区別。残件は出口部屋→外の通常接続とその先のstory、正規全国図鑑解禁、分離progressionの自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。trainer352は未受入だがこの正規出口経路を通るための追加勝利へ捏造せず、未実施のまま保持。HM05は所持のみで未習得/未使用、同じ拒否入力を反復しない。全story/一般CI全成功/製品releaseは未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断の境界を保持。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
