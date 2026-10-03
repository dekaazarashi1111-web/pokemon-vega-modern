# 503新5勝・ちえのどうくつ北入口・Save22 限定受入

`PASS_ROUTE503_FIVE_TRAINERS_CHIE_ENTRANCE_SAVE22_SCOPED`。Save21後の新しい通常trainer5戦と北入口へのwarp、通常Save22・独立Continueだけを受入。洞窟内部/階段/走破、HM05習得/使用、自然育成/進化、全国図鑑、研究施設自然到達、全storyは未受入。

## 原本と実行会計

測定source `8c6f51827d3d51a1f2f25b4444f6103496d2ecba`、run `36668710078`、job `109738877587`、upload/postを含む全8step成功。artifact `11076499444`、17940588bytes、SHA256 `43a9676c164ba2716366dd351ef1f2a973a115e92cce183ac14a8a8f6f1dcbb5`、期限 `2026-12-29T04:24:40Z`。全121member/93画面を全byte検証し、開発57anchorと追加cold4/5の計59anchorを目視。

397/cold35入力、41557/cold3464frames。開発2・正式2native成功、compile/ROM変更/旧受入case再走0。新58受入試験+10転送試験=68を開発/正式で二重計上しない。今回の記録は原本読取のみでnative/受入試験再走0、別の記録拒否22試験。開発cold30入力はcard終端で未受入。正式は固定prefixの後だけ退出入力を追加し、cold4のmenu/lock1とcold5のfield/lock0を区別した。

測定jobが再構成したexpected.json全27997bytesを、事前宣言SHA256 `9104b9aa1b3fc654193932c48cbbf2863ff8610c6bfd466675a42cb79f66b4b7` と一致する場合だけ追跡へ回収する。未知出力から期待値を再生成しない。

## 新5戦と到達範囲

アミカtrainer102/240円、コウガ108/132円、アイク94/2600円、ルチア1362/2600円、ヘイスケ97/468円。賞金計6040円、6256→12296円。5戦の連続性と個別の勝利/賞金画面、保存physical bitを結合。観測8は同一戦闘の交代UI取消、観測37は次trainer接近中のlock1で、全5回のidle復帰を主張しない。残留battle_flags12/outcome1を追加勝利と数えず、野生勝利/逃走/捕獲/敗北/通常回復は0。

map3/21のwarp15,56から、観測80でmap1/36・4,6北へ通常移動。固定ROMの相互warp表と洞窟onloadの世界地図flag2217直接ownerを照合。新trainer5roots/30nodes・洞窟1node、diagnostics0。洞窟奥、帰りwarp実行、rematchは未受入。

## Saveと保全境界

Save22 `bb3b6159ab12358fd051b88a592c99807b2bc14b1f9f41e952daf7a4d1a4529e`、131088bytesは独立Continue後も全Save/RTC不変。party4/RP0・12296円・badge1、var4071=6/4072=1。ミュウツーHP324/354、技PP[1,14,5,5]、他3体HP満タン。全員Lv100でEXP/種族/技/装備は保持。600partybytesの差分はPP4bytes、HP1byte、slot1/3のoffset41各1byteのみ。offset41の因果owner/全なつき度の受入にしない。Mew/Bibarelの4技/PPは空のまま、全Bag slot/HM05保持。

全Save差分6895bytes/1836範囲。旧Save21 bank57344bytes、PC、未使用party200bytesを保持。sector checksum42件とS61E全payload/CRC/反転値を検証。legacy差分はtrainer5bitと2056/2217、vars4021:92→23/4022:2→3/404d:8→20だけ。flag2056と補助varのruntime ownerは未解決のまま、推測で受入範囲を広げない。NationalDex magic0/var404e0/flag840=0、分離progression/grant ownerを保持。

観測84/85は書込途中、86でSave22/Flash/field安定。保存成功文言frameは未採取。ROM/Save/全差分hex/画像はartifactだけ、tracked text原本は `content/modernization/pr16_story_save22_evidence`。

## CI・旧受入との分離

前回Save21記録run36663051577/job109721759017のpush/upload/postを含む全11step成功を別APIで照合、反映HEAD98052e7fの祖先関係を確認。Save1〜21/旧BP/P08は再走しない。一般CIのP03 capacity段階failureと後続skip/artifact failureは専用成功と別scopeで保持し、全CI成功を主張しない。PR merge/release/active baseline切替なし。

## 次の唯一の開始点

story-fastの唯一の開始点はartifact11076499444のstory-fast.srm（Save22、131088bytes、SHA256 bb3b6159ab12358fd051b88a592c99807b2bc14b1f9f41e952daf7a4d1a4529e）。ちえのどうくつ北入口map1/36・4,6北・party4/RP0、12296円・badge1・var4071=6/4072=1。ミュウツーHP324/354・PP[1,14,5,5]、他3体HP満タン。503新5勝/6040円・北入口warp・通常Save22/独立Continueは完了。洞窟内部/階段/走破は未到達。現在地から通常storyの未完区間だけをSave/cold境界で進める。397/cold35入力・68試験・Save1〜21/旧BP/P08は無影響に再走しない。HM05は所持だけで未習得/未使用・原因未解決。Save21の同一拒否入力は繰り返さず、必要時は固定ROMの互換性判定ownerを限定照合し、承認済みfield-utility分離fixtureの自然取得条件を確認する。基準外習得を盲追加しない。分離progression原本Axew Lv37/EXP68589とNationalDex magic0・grant ownerを保全し、flag/var注入で解禁しない。正規全国図鑑解禁、自然育成/進化、Lucky Egg対照・12成長ケース・Lv100soak・研究施設自然到達・全storyは未完。

記録source `216ccc6302104238f446230818151552f02b1944`、run `36672864966`。記録自身のpush/upload/postは自己予測せず、別API・record-head.txt・record.zipで読戻し確認する。
