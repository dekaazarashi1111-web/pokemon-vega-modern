# 503番道路の電話イベント・Save21 限定受入

`PASS_ROUTE503_PHONE_SAVE21_SCOPED`。支援story-fastのSave20後だけを進め、トシヒデ通常1勝、電話イベント/自動移動、通常Save21と独立Continueを受入。HM05は通常UIで拒否を確認しただけで、習得/使用・原因修正を合格にしない。自然育成/進化、全国図鑑、研究施設自然到達、全storyは未受入。

## 完了原本と実行会計

測定source `b58a6356c9b100a9180a9af955d25e1c6be48d0c`、run `36662466133`、job `109719980409`、upload/postを含む全8step成功。artifact `11073849807`、17794173bytes、SHA256 `2ed9efdd23374911bcb23e5092147231ba0af5f06f9280e84ee6a091868e2b05`、期限 `2026-12-29T03:00:49Z`。全86member/61画面を全byte検証。開発38anchorと正式pixelを結び、追加cold5を目視して計39anchor。

181/cold33入力、16528/cold2760frames。開発2・正式2native成功、compile/ROM変更/旧受入case再走0。新62試験を開発と正式で別124件へ水増ししない。記録は原本読取のみでnative/受入62試験再走0、別の記録拒否12試験。開発coldはcard後menuで終了し未受入。正式coldは原本prefixを全保持した後に待機/B/待機を追加し、observe5でfield=true/lock0を確認した。

## 通常操作で確定した範囲

HM05ケース→4体とも「おぼえられない」→ミュウ選択で相性拒否→field復帰。観測5/7/8/10とparty全byte不変を結合。ミュウ/ビーダルの4技/PPは空のまま。表示だけから互換性判定の原因を断定せず、基準外の習得や移動用fixtureを追加していない。HM05取得自体はSave20の既受入原本を継承する。

アヤメ南側から503番道路へ。map3/21 object3・13,12の通常trainer101トシヒデに1勝、賞金240円で6016→6256円。観測19で戦闘開始、24は同戦闘内の交代menuを取消、35で勝利、37で賞金、38でfield復帰。残るbattle_flags12/outcome1を追加勝利と数えない。野生勝利/離脱/捕獲/敗北/通常回復0、rematch1027は未実行。

map3/21 coord表のx21〜24/y17・var4071=5を実ROM headerから照合。今回の到達はx23のrootだけで、電話会話「ニューアイランド」「メア」等と自動移動を観測40〜47に結合した。var4071=6更新owner、非表示flag4366のownerを2nodes/診断0で照合。他3coordの実到達や全storyの完了を証明しない。

## Save差分と安全境界

Save21 `c9cb14fa73a38e105a0e6553f7fc1dc82c9bdd182e0409e28022c8ffe44b3d20`、131088bytesを独立Continue後も全保持。map3/21・24,17西、party4/RP0、6256円・badge1・var4071=6/4072=1。ミュウツーHP349/354、サイコブレイクPP10→5。他3体HP満タン。600partybytes中HP/PP各1byteと2体EV欄各1byteだけ変化し、EXP/種族/Lv100/4技/装備は不変。これは自然育成/進化/全EV因果ケースの受入ではない。

通常ケースを開いた際にmachines先頭2slotがTM15/HM05→HM05/TM15へ整列した。全item/countと他Bag slotは不変。ローカル検証は当初の「Bag全slot不変」という誤仮定を拒否し、この具体的な順序交換だけを許可した。nativeを再実行して都合のよい結果を採り直していない。

全Save差分6988bytes/1783範囲。旧Save20 bank57344bytes、boxed PC、未使用party200bytes保持。ROM宣言checksum42件、S61E CRC/反転値を検証。legacy差分はtrainer physical1381のみ、変数4021=24→92/4022=0→2/4071=5→6だけ。S61E payloadのoffset257:1→65は拡張flag4366/index2062のbit6。NationalDex magic0/var404e0/flag840=0と分離progression/grant owner不変。全差分hex/ROM/Save/画像はartifactのみ。tracked text原本は `content/modernization/pr16_story_save21_evidence`。

電話中7枚だけSave y20とlive y17の同期遅れを、正確なframe/座標/callback/hash/lock付きで区別した。旧判定器は変更せず、会話中をfield到達にしない。47で座標一致/解錠。51/52は書込途中、53/54でcounter21/Flash/field安定。保存成功文言frameは採取していない。

## 既存結果・CIとの切分け

旧Save20記録run36573749814/source556e4b21はpush/upload/postを含む全11step成功、反映HEAD e517baa4を別APIで照合した。旧受入Save1〜20/旧BP/P08/自然成長原本を再走しない。一般CIのP03 capacity既知source不一致とaction_requiredは専用成功と別scope。全CI成功、PR merge、release、active baseline切替は主張しない。

## 次の唯一の開始点

story-fastの唯一の開始点はartifact11073849807のstory-fast.srm（Save21、131088bytes、SHA256 c9cb14fa73a38e105a0e6553f7fc1dc82c9bdd182e0409e28022c8ffe44b3d20）。503番道路map3/21・24,17西・party4/RP0、6256円・badge1、var4071=6/4072=1。ミュウツーHP349/354・サイコブレイクPP5、他3体HP満タン。トシヒデ1勝/240円・電話会話/自動移動・通常Save21/独立Continueは完了。HM05所持、通常UIで4体とも非適合表示・ミュウ選択拒否。習得/使用/原因解決は未完。同じ拒否入力を繰り返さず、必要時は固定ROMの互換性判定ownerを限定照合し、自然取得条件を満たす承認済みfield-utility分離fixtureの適用条件を読む。基準外の習得を盲追加しない。現在地から通常storyの未完区間だけをSave/cold境界で進める。181/cold33入力・62試験・Save1〜20/旧BP/P08は無影響に再走しない。分離progression原本Axew Lv37/EXP68589とNationalDex magic0・grant ownerを保全し、flag/var注入で解禁しない。正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。

記録source `dd00a9d0a585849c4395645ee0384944526d2272`、run `36663051577`。記録自身のpush/uploadは自己予測せず、別API・record-head.txt・record.zipで読戻し確認する。
