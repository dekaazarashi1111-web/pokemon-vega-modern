# 洞窟南出口から503番道路・Save38 限定受入

`PASS_CAVE_OUTSIDE_ROUTE503_TRAINER103_SAVE38_SCOPED`。Save37の南出口部屋6,4から6,5→5,5→4,5→4,6へ歩き、出口矢印から南へ追加通常入力して屋外map3/21・9,76南へ到達。出口trainer103に正規勝利・賞金220円の後、通常Save38/独立Continueまで限定受入。洞窟本区画・南出口部屋・外503番道路の接続milestoneは完了。全story・全国図鑑・自然成長は未完。

source `1d3504839f4c1a86b054d3529f2c98a19ac40236` / run `37127609831` / job `111216024409` 全8step成功。artifact `11275249543` / 347936bytes / SHA256 `1d35ef01905047e71d8777cd491b3209e9dfc5f83508e23fd09f48e352915c6a`。全81member、122/cold13入力、62画面。新16controller（初回10/矢印修正3/NPC修正3）は原log継承、新28原本受入/拒否試験、成功native2/未保存停止2/記録native0。ROM/fixture/compile/既受入再走0。失敗原本で採取したmap3/21を再採取せず再利用。NPC10のscript graph6nodeを新規採取し、trainer103初戦/1029再戦を分離。measurementのnew_script_nodes=0は継承値の誤記であり、保存graph6nodeを正としてcheckpointで明示訂正。原本は改作しない。

party600byte差分はPP8→5の1byteだけ、HP320/354保持。Bag/HM05/PC/S61E不変、13576→13796円（賞金220円）。legacyflag1383=0→1（trainer103）と2056=1→0、補助var4021=26→30/4022=2→0/40ae=79→91、補助runtime owner未解決。story4071=8/4072=1・badge1・全国図鑑magic0/404e0/flag8400保持。42sector checksum/旧bank57344byte/6840byte1710範囲/cold全SaveRTC一致。

43〜54は書込中12画面/11Flash状態（53/54同じ）。55でcounter38/安定全Flashだが台詞移行中、56〜58保存成功文言、59field復帰。Save37の24一時一致→25再差分→26安定とは異なる。

初回run37127113183は出口矢印tile4,6で待機上限となった。Save37全byte不変/未保存の原本artifact11275422186を保持。待機を増やす代わりに実画面の下矢印から通常南入力1回を追加し、変更影響区間だけ検証した。第二native run37127420854は屋外到達したがNPC会話で未保存停止、artifact11275593672を保持。会話/戦闘を含む影響区間だけ修正。中間run37127280308はguardの変更集合基準不一致でnative0。既受入Save37以前は再走していない。

次: Save38 artifact11275249543のstory-fast.srm（ca6b332ff001f757bde9d82baab19d4b6b8547488afefe62dc6ea408ced8b074、131088bytes）だけから再開。map3/21・9,76南・party4/RP0・13796円・badge1・story4071=8/4072=1、HP320/354・PP[1,5,0,0]。洞窟本区画→南出口部屋→外503番道路の通常接続とSave38/独立Continueを限定受入。洞窟走破milestone完了。出口trainer103（じゅくがえり・モトナリ）のココガラLv7/ポッポLv11/ビッパLv9に3手で勝利、賞金220円。全storyは未完。次は保存済503番道路南部viewから西側のmap3/44接続を通常進行し、最初の新event/新戦闘または回復地点で限定checkpoint。必要な未読隣接mapだけ採取。host回復/PP/flag/var注入は禁止。既受入の西側event・trainer360・洞窟本区画・Save38入力は無影響再走しない。Save38初回は矢印tile4,6で追加南入力がなく待機停止。未保存原本/失敗を保持し、変更影響区間だけ回復した。Save36の227完走入力後parser失敗回復とSave37の24一時Flash一致→25再差分→26安定→30fieldを保持。残件: 通常story継続、正規全国図鑑解禁、分離progressionの自然EXP/技習得/進化、Lucky Egg/12ケース/Lv100soak、研究施設自然到達。trainer352未受入。HM05は所持だけ・未習得/未使用。全story/一般CI全成功/製品releaseは未完。clean-ROM二重生成/BPS固定、merge・release・baseline切替は別途所有者判断。既存ROM/runtime/inputはActions内入力のみ、新公開artifactは新save/画面/textだけ。
