# 洞窟南段差・正規story owner・Save31 限定受入

`PASS_CAVE_SOUTH_OWNER_SAVE31_SCOPED`。Save30の13,6南から下層を進み、14,9/14,13の南段差を通常通過。14,14の正規owner0x08214656でflag4367が0→1/var4071が6→7となった通常Save31/独立Continueを受入。戦闘0。洞窟出口は未完。

source `accd52953d20245894396a0444d39f56b8d78a35` / run `37120372607` / job `111195148880` 全8step成功。artifact `11273187310` / 166942bytes / SHA256 `d5a5857b3fb520f5b12cd6825bf7d1760ac136dc35cc6d3cc021d3fd9a9938f3`。全37member、52/cold13入力、22画面。最初の段差6、次の段差/owner座標9、保存成功文言18、安定field19。観測17はcounter31でもFlash部分書込み/保存中画面のまま。独立Continue0/1でも14,14南。

Save31 `f0d2c1afb303390fb415e52090379a234a813f1bd7854ea77d92f5cb7b50ac2f` / 131088bytes。party全600byte、HP/PP/EXP/種族/4技/道具/OT、Bag/HM05、12712円、legacy全flagsを保持。S61E payload差分はoffset257の65→193だけでflag4367の1bit。CRC/complement8byte更新と他payload不変を独立照合。var4071は正規ownerと一致して6→7、補助var4021は87→93/4022は1→2で補助2件のruntime ownerは未解決。旧Save30bank57344bytes、PC payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4072=1/badge1を保持。全Save/RTCはcold同一、6960byte/1775範囲差分。

新12controller原logを保持して再走0。初回record37120815549は入力環境名誤りでsetUpClass停止、Ran0/native0。失敗stderr原本artifact11273570337を保持し名前だけ修正。未実行だった新24受入/拒否試験を今回だけ実行し全stderr保存。flag欠落、別flag追加と再計算済CRC、CRC破損を拒否。既存失敗原本と試験証拠を改作しない。record native0/ROM変更0/compile0/fixture0/既受入再走0。Save30記録run37120155157全11step終端を固定JSONへ反映。一般CI全成功/releaseは主張しない。

次: Save31 artifact11273187310のstory-fast.srm（f0d2c1afb303390fb415e52090379a234a813f1bd7854ea77d92f5cb7b50ac2f、131088bytes）だけから再開。map1/73・14,14南・party4/RP0・12712円・badge1・story4071=7/4072=1。南段差14,9/14,13を通常通過し、14,14のowner0x08214656でflag4367=1/var4071=7になった通常Save31と独立Continueを受入。次は14,14から南側通路を進み、洞窟全地形/obj/warpと新しいstory状態を固定ROMから照合して出口へ向かう。既存静的ownerでは19,14のteleport分岐はflag4367=1で8,10へ変わり、7,5のcoordはvar4071=7が発火条件。これらへの到達/発火/出口は未観測。保存済みlower_corridor_terrainはx8〜19/y4〜16だけ。範囲外を推測せず未読地形だけを採取して通常経路を決める。ミュウツーHP324/PP[1,14,0,4]、オノノクスHP294/PP[15,10,15,20]は不変。今回戦闘0。火炎放射PP0を使わずhost回復/flag/var解禁は禁止。既存ROM/runnerはSave24 artifact11263343138、runtime11263910704をActions入力だけ再利用し、新公開artifactは新save/画面/textだけ。52/cold13入力・22画面・新12controller/24受入試験、Save1〜30は無影響再走しない。補助var4021=93/4022=2のruntime ownerは未解決。trainer352/353、分岐先への実warp、洞窟走破、HM05原因、全国図鑑、自然成長進化、全storyは未完。
