# 洞窟岩階段・Save27 限定受入

`PASS_CAVE_ROCK_STAIRS_WILD_SAVE27_SCOPED`。Save26の32,15西から23,15、岩階段23,14→23,13を通常移動し高台19,13へ。野生ダンゴロ♂Lv7を火炎放射1回で倒し、通常Save27/独立Continueを受入。trainer352/353やteleportは未到達。

source `77b229ce45d6dc8140c8f8f75ad91652492fad85` / run `37116043940` / job `111182955509` 全8step成功。artifact `11271451341` / 240649bytes / SHA256 `e394284e2e9bcfa26cbbd357d44d7ce65ba218c89a00e5aeffdd4a3d86925b64`。全52member、86/cold13入力、38画面を照合。遭遇遷移17、戦闘18〜26、勝利/解錠27、保存成功文言34、安定field35。warmのfield:false残留はcallback/lockで区別し、cold0/1ではtrue。追加勝利へ計上しない。

Save27 `fb3c41c4178a04cee89301c74ecf2a646dc4d5633eefa8086664ca0057d7b1d4` / 131088bytes。party600byte差分は火炎放射PP1→0のみ。HP/EXP/種族/4技/道具/OT、全Bag/HM05、所持金12712、全trainer/story flagsを保持。補助var4021だけ53→68、runtime ownerは未解決。旧Save26bank57344bytes、PC/S61E全payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6952byte/1755範囲差分。

新12controller試験成功原本を再利用し、新20受入/拒否試験のみ実行。record native0、旧受入再走0、ROM変更/compile/fixture0。新artifactは新save/画面/textだけ。Save26記録run37115447922全10step成功を終端照合して固定JSONへ反映。一般CI全成功/releaseは主張しない。

次: Save27 artifact11271451341のstory-fast.srm（fb3c41c4178a04cee89301c74ecf2a646dc4d5633eefa8086664ca0057d7b1d4、131088bytes）だけから再開。map1/73・19,13西・party4/RP0・12712円・badge1・story4071=6/4072=1。岩階段23,14→23,13、高台西行と野生ダンゴロ♂Lv7の通常1勝、Save27/独立Continueは完了。次は19,13から南を向いて19,14の正規coord teleportを通常入力で確認。候補destination27,7または8,10を静的候補と実観測で区別し、最初の新境界で保存する。trainer352/353は未対戦。ミュウツーPP[1,14,0,5]/HP324、オノノクスPP[15,10,15,20]/HP294。火炎放射PP0を使わず実技UIで残PPを扱う。host回復/flag/var解禁は禁止。既存ROM/runnerはSave24 artifact11263343138、runtime11263910704をhash固定しActions入力のみ再利用。新公開artifactは新save/画面/textだけ。86/cold13入力・12controller/新20受入試験・Save1〜26は無影響再走しない。teleport/洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。
