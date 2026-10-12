# 洞窟正規teleport・Save28 限定受入

`PASS_CAVE_COORD19_TO27_SAVE28_SCOPED`。Save27の19,13で南を向き19,14へ。flag4367=0の正規scriptで27,7へteleportし通常Save28/独立Continueを受入。8,10行き・trainer352/353・洞窟走破は未受入。

source `1cc88ec763b69ada00bc4f5da4b5c632c5ccd9c8` / run `37117145212` / job `111186021028` 全8step成功。artifact `11271154923` / 127600bytes / SHA256 `43f98cdb2823fce7c34fbb76f439b3ffd26a900ddf9cee8c394567129a1b95ed`。全36member、40/cold13入力、17画面を照合。trigger2、暗転3、到着4、解錠6、保存成功文言13、安定field14。戦闘0。warm ledger hashは保存最終解錠14で更新しcoldと一致、途中値と混同しない。

Save28 `a5cfc5714bcc447550d78ff45f42c74109f12d607bad1d94dbf61fe96b06f4a4` / 131088bytes。party600bytes/PP[1,14,0,5]、Bag/HM05、所持金12712、全trainer/story flags・vars、PC/S61E全payload不変。旧Save27bank57344bytes、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6916byte/1743範囲差分。

実root0x08214661は先頭lock→checkflag4367→goto_if1。未設定側27,7・設定側8,10を独立ROM byteで照合。開発計測器の先頭lock漏れでrun37116752441/37116959565は各native0で停止、失敗原本を保持。最初の12+追加4試験と修正影響16再検査を区別し、今回は新20受入/拒否試験だけ。record native0、旧ゲーム受入再走0、ROM/compile/fixture0。一般CI全成功/releaseは主張しない。

条件比較の補助参照: https://raw.githubusercontent.com/pret/pokefirered/master/src/scrcmd.c （ScrCmd_checkflag・ScrCmd_goto_if・sScriptConditionTable）。実Vega候補のbyteと保存flagを受入の正本にする。

次: Save28 artifact11271154923のstory-fast.srm（a5cfc5714bcc447550d78ff45f42c74109f12d607bad1d94dbf61fe96b06f4a4、131088bytes）だけから再開。map1/73・27,7南・party4/RP0・12712円・badge1・story4071=6/4072=1。19,14→27,7の正規teleport（flag4367=0）、Save28/独立Continueは完了。次は27,7高台から西側の正規通路/橋/coord11〜16,14（var4071=6）とflag4367のstory ownerを追い、新しい通常入力を進める。8,10行きはflag4367=1の未解禁枝。27,7へのteleport成功を洞窟走破へ昇格せず、19,14を無目的に周回しない。trainer352/353も未対戦。ミュウツーPP[1,14,0,5]/HP324、オノノクスPP[15,10,15,20]/HP294。火炎放射PP0を使わず、host回復/flag/var解禁は禁止。既存ROM/runnerはSave24 artifact11263343138、runtime11263910704をhash固定してActions入力のみ再利用。新公開artifactは新save/画面/textだけ。40/cold13入力・17画面・20新受入試験とSave1〜27は無影響再走しない。旧preflight2回はnative0失敗のまま保持。洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。
