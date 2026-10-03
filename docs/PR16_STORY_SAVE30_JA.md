# 洞窟西岩階段・Save30 限定受入

`PASS_CAVE_WEST_STAIRS_SAVE30_SCOPED`。Save29の17,4西から13,4まで進み、13,5岩階段を通常通過し下層13,6南で通常Save30/独立Continueを受入。戦闘0、story解禁/洞窟走破は未完。

source `5518bc514b00151d4bd55dbd1baf66b3ca05dd04` / run `37119699930` / job `111193264460` 全8step成功。artifact `11273101471` / 134841bytes / SHA256 `da0f5a7b78f25be478e9b63cb8e9ad7fb2f0f7d8ef6431240af6073ad6388563`。全33member、46/cold13入力、18画面を照合。南へ向き直り5、階段6、下層7、保存成功文言14、安定field15。独立Continue0/1でも同じ13,6南。

Save30 `cb22ab0344990a51ef40d01e4049e8976a65340e629eaef2b390b6ce5f80d70b` / 131088bytes。party全600byte、HP/PP/EXP/種族/4技/道具/OT、Bag/HM05、12712円、全trainer/story flagsを保持。補助var4021だけ81→87、4022は0→1。これらのruntime ownerは未解決。旧Save29bank57344bytes、PC/S61E全payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6941byte/1761範囲差分。

新12controller試験は測定runの原logを保持して再走0。新20受入/拒否試験は今回だけ実行し全stderrを保存。既存Save29の失敗原本と試験証拠を改作しない。record native0/ROM変更0/compile0/fixture0/既受入再走0。Save29記録run37119219773全10step終端を固定JSONへ反映。一般CI全成功/releaseは主張しない。

次: Save30 artifact11273101471のstory-fast.srm（cb22ab0344990a51ef40d01e4049e8976a65340e629eaef2b390b6ce5f80d70b、131088bytes）だけから再開。map1/73・13,6南・party4/RP0・12712円・badge1・story4071=6/4072=1。正規岩階段13,5を通常通過し下層13,6のSave30/独立Continueを受入。次は下層から南のcoord11〜16,14へ進み、正規owner0x08214656によるflag4367/var4071=7を通常入力で観測する。保存済みlower_corridor_terrainでは13,6→13,7→14,7→14,8の南にbehavior59境界14,9がある。衝突bitだけで到達不能と断定せず、通常入力と画面で境界を確認する。ミュウツーHP324/PP[1,14,0,4]、オノノクスHP294/PP[15,10,15,20]は不変。今回戦闘0。火炎放射PP0を使わずhost回復/flag/var解禁は禁止。既存ROM/runnerはSave24 artifact11263343138、runtime11263910704をActions入力だけ再利用し、新公開artifactは新save/画面/textだけ。46/cold13入力・18画面・新12controller/20受入試験、Save1〜29は無影響再走しない。補助var4021=87/4022=1のruntime ownerは未解決。trainer352/353、story flag4367、洞窟走破、HM05原因、全国図鑑、自然成長進化、全storyは未完。
