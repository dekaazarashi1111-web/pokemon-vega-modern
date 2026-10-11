# 洞窟西高台・Save29 限定受入

`PASS_CAVE_WEST_HIGH_WILD_SAVE29_SCOPED`。Save28の27,7南から西高台を通り17,4西へ。野生ディグダ♂Lv8をれいとうビーム1回で倒し、通常Save29/独立Continueを受入。13,5岩階段、trainer352/353、西側story解禁は未到達。

source `33e1b9337469170adfca8af14ec4b3f298135b75` / run `37118447519` / job `111189690507` 全8step成功。artifact `11271899477` / 232451bytes / SHA256 `bb04e57ceb77be61b068e30e9dc88a343feb9754a7dec7c5066182ff4501f22f`。全55member、88/cold13入力、39画面を照合。遭遇遷移16、戦闘17〜27、勝利/解錠28、保存成功文言35、安定field36。warmのfield:false残留はcallback/lockで区別し、cold0/1ではtrue。

Save29 `780c27a138bc0795e2f30c328f69a77ded3569a9960318a61f0dc3d431f56a83` / 131088bytes。party600byte差分はれいとうビームPP5→4のみ。HP/EXP/種族/4技/道具/OT、Bag/HM05、12712円、全trainer/story flagsを保持。補助var4021だけ68→81、runtime ownerは未解決。旧Save28bank57344bytes、PC/S61E全payload、42stock checksums/S61E CRC、全国図鑑magic0/404e0/flag8400、story4071=6/4072=1/badge1。全Save/RTCはcoldと同一、6949byte/1760範囲差分。

正規owner0x08214656のsetflag4367/setvar4071=7を照合。末尾opcodeは0x6b。初回run37118280803は0x6dと推測したpreflightがnative0で失敗した原本を保持。変更4owner試験を追加し、旧16controllerは再走0。20受入/拒否試験は初回recordの成功gateから再利用（個別stderrは未保存）。旧guide書込みはguardでpush前に拒否され、新2記録先試験を追加。次の記録で絶対path引用をprivate guardがpush前に拒否。行番号/errorだけのreceiptへ修正し、新2receipt試験だけ実行。record native0、旧ゲーム受入再走0、ROM/compile/fixture0。Save28記録run37117631601全10step終端を固定JSONへ反映。一般CI全成功/releaseは主張しない。

次: Save29 artifact11271899477のstory-fast.srm（780c27a138bc0795e2f30c328f69a77ded3569a9960318a61f0dc3d431f56a83、131088bytes）だけから再開。map1/73・17,4西・party4/RP0・12712円・badge1・story4071=6/4072=1。西高台の通常移動、野生ディグダ♂Lv8の通常1勝、Save29/独立Continueは完了。次は17,4から西4歩で13,4、南の正規岩階段13,5→13,6へ進み、低地/橋からcoord11〜16,14のownerへ向かう。root0x08214656はsetflag4367/var4071=7の正規owner。先頭0x69・末尾0x6b/endを実byte観測。flag4367は未設定で8,10枝は未解禁。ミュウツーHP324/PP[1,14,0,4]、オノノクスHP294/PP[15,10,15,20]。火炎放射PP0を使わず、host回復/flag/var解禁は禁止。trainer352/353は未対戦。既存ROM/runnerはSave24 artifact11263343138、runtime11263910704をhash固定してActions入力のみ再利用。新公開artifactは新save/画面/textだけ。88/cold13入力・39画面・16controller+4owner/新20受入試験、Save1〜28は無影響再走しない。初回native0失敗を保持。13,5岩階段/洞窟走破/HM05原因/全国図鑑/自然成長進化/全storyは未完。
