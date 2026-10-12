# 洞窟南通路・Save26 限定受入

`PASS_CAVE_SOUTH_WILD_SAVE26_SCOPED`。31,7南から東南を迂回し32,15西へ通常進行。野生ディグダ♀Lv6を火炎放射1回で倒し、通常Save26/独立Continueを受入。trainer352/353やteleportは未到達。

source `3fde7851bff63efd661b0e5b9f6c6b488272fbb5` / run `37114774344` / job `111179348370` 全8step成功。artifact `11270502866` / 212283bytes / SHA256 `c2e3f92164eb2034e7647c46c8a672d1606b3979b4a058037e4549d753e7f1f3`。全51member、84/cold13入力、37画面を照合。遭遇遷移16、戦闘17〜25、勝利/解錠26、保存成功文言33、安定field34。warmのfield:false残留はcallback/lockで区別し、cold0/1ではtrue。追加勝利には数えない。

Save26 `e65fc5bb2c76d7cfcdd144c1a69451ad8508ff73ad82e4c7f24595d75200624d` / 131088bytes。party600byte差分は火炎放射PP2→1のみ。HP/EXP/種族/4技/道具/OT、全Bag/HM05、所持金12712、全trainer/story flags保持。補助var4021だけ40→53、runtime ownerは未解決。旧Save25bank57344bytes、PC/S61E全payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6906byte/1743範囲差分。

15controller試験成功原本を再利用し、新20受入/拒否試験だけを実行。record native0、旧受入再走0、ROM変更/compile/fixture0。新artifactは新save/画面/textだけ。一般CI全成功やreleaseは主張しない。

次: Save26 artifact11270502866のstory-fast.srm（e65fc5bb2c76d7cfcdd144c1a69451ad8508ff73ad82e4c7f24595d75200624d、131088bytes）だけから再開。map1/73・32,15西・party4/RP0・12712円・badge1・story4071=6/4072=1。野生ディグダLv6の通常1勝、Save26/独立Continueは完了。次は32,15から西へ23,15、岩階段23,14→23,13、19,13→19,14の正規coord teleportを通常入力で確認する。trainer352（30,13）/353（21,17）は未対戦、残り経路は静的候補だけ。ミュウツーPP[1,14,1,5]/HP324、オノノクスPP[15,10,15,20]/HP294。残PPを実技UIで扱い、host回復/flag/var解禁は禁止。既存候補ROM/runnerはSave24 artifact11263343138、runtimeは11263910704をhash固定してActions入力のみ再利用。新公開artifactは新save/画面/textだけ。84/cold13入力・15controller/新20受入試験・Save1〜25は無影響再走しない。teleport/洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。
