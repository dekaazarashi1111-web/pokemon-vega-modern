# 503西端から504東端・Save39 限定受入

`PASS_ROUTE503_TO_504_SAVE39_SCOPED`。Save38の503番道路9,76から西へ進み、通常connectionでmap3/44（504番道路）・71,9西に到達。通常Save39/独立Continueまで限定受入。新戦闘0。洞窟走破は前Save38で達成済みであり、全story・全国図鑑・自然成長は未完。

source `442449ed7b8eb4453820de744aa938a22309f411` / run `37128394742` / job `111218333230` 全8step成功。artifact `11276165710` / 264597bytes / SHA256 `78fb4fd98f03cb822947f2361747c56bbfa945cfc30b6bef1a19a24e85180dcb`。全55member、67/cold13入力、39画面。新15controller（初回11/画像menu4）は原log継承、新26原本受入/拒否試験、成功native2/未保存停止1/記録native0。ROM/fixture/compile/既受入再走0。map3/44の保存済72×20地形viewを再採取せず利用。

party600byte/HP320/PP[1,5,0,0]/全Bag/HM05/13796円/PC/S61E/全legacy flag/story4071=8/4072=1・badge1不変。補助var4021=30→40だけ、runtime owner未解決。42sector checksum/旧Save38bank57344byte/6785byte1672範囲/cold全SaveRTC一致。全国図鑑magic0/404e0/flag8400保持。

12〜16で通常menuのcursor0→4を画像確認。19〜29は部分write、30はcounter38のまま最終Flashと一時一致、31でcounter39/再差分、32〜35は成功文言/安定Flash、36field復帰。cold0/1は同じ504東端に復帰。進行RAM ledger `a42b7de819dcb559b39e870697fd51b376d8955e5025164a64d3355f4b02af8c` とcold `95d109f9df4c120c3343661ca2c130f17047761f4ef8a01bc4b9e05456073a26` は異なる。owner未解決のまま保持し、全RAM不変とは主張しない。全Save/RTCはbyte一致。

初回run37128174890は504到達後に固定down4入力の1回が反映されずTrainerCardへ入った。90入力/56画面/native1、Save38全byte不変の未保存原本artifact11275619886を保持。通常menuを各行の実画像cursorで検証してからレポートだけに決定する修正を入れ、変更影響区間だけ再測定した。受入済みSave38以前は再走していない。

次: Save39 artifact11276165710のstory-fast.srm（2cc5e239b0e32951a9c5b68375b1b78318be6d5d11389a1e1a898f16b7bda720、131088bytes）だけから再開。map3/44（504番道路）・71,9西・party4/RP0・13796円・badge1・story4071=8/4072=1、HP320/354・PP[1,5,0,0]。503西端→504東端の通常connectionとSave39/独立Continueを限定受入、戦闘0。洞窟走破milestoneは前Save38で完了、全storyは未完。次は保存済72×20の504地形から先へ。70,9はcollision壁なので左を反復しない。71,9→71,10→70,10→69,10→68,10→67,10→66,10→65,10→64,10が静的候補。未読のelevation/behaviorと必要なownerだけ限定照合し、最初の新戦闘/新eventまたは通常回復地点で保存。PPをhost補充しない。Save39で改善した実画像menu_index/レポートcursor0→4確認を継承し、固定down4短間隔へ戻さない。67/cold13入力39画面/15controller26受入を無影響再走しない。初回90入力/56画面はTrainerCardに入り未保存で停止、原本artifact11275619886を保持。30Flash一時一致/counter38→31再差分/counter39→32安定/成功文言→36fieldを区別。cold RAM ledgerは進行時と異なりowner未解決、全Save/RTCは一致。Save36の227入力後parser失敗回復、Save37の24→25→26の区別、Save38のNPC103初戦/賞金220円/再戦1029未受入を保持。残件: 通常story、正規全国図鑑解禁、分離progression自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。trainer352未受入、HM05所持だけ・未習得/未使用。全story/一般CI全成功/製品release未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
