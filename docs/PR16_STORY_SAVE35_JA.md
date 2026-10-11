# 戻り転送・野生戦・Save35 限定受入

`PASS_CAVE_RETURN_WILD_SAVE35_SCOPED`。Save34から8,10→27,7の戻り転送を通常入力で通り、16,5で野生バルキー♂Lv6に通常勝利。西階段手前で通常Save35/独立Continueへ区切った。西階段/8,5/7,5eventへ到達したとは主張しない。

source `95edb59bcf19a560f81355aa446c3cf57bf95a62` / run `37124732153` / job `111207625688` 全8step成功。artifact `11274735081` / 365141bytes / SHA256 `df1e104b934c21c0577822e864eac2c42e67e38f7cb78e953f432b357215162b`。全77member、115/cold13入力、60画面。23/24のfield移行/黒画面初期化は無入力で有限待機。25〜37で野生戦、32でひるんだため、はどうだんの2選択と実PP消費1を区別する。HP322→320、PP14→13。38でfield callback/lock0へ復帰し、wire field:falseは残留戦闘値によるため追加戦闘/未復帰としない。

42〜53は部分Flash write12状態、53はcounter35先行、54で全Flash完成と保存成功文言。54〜56の成功文言を目視確認、57でfield復帰。全Save/RTC独立Continue一致と42sector checksumを別途検証。旧Save34bank57344bytes・全Bag/HM05/13128円/PC/S61E・全legacy/storyflags/badge1維持。party差分4byteのうちoffset41/241の+1はruntime owner未解決、補助var4021=119→7/4022=1→0も別記する。自然成長を受入にしない。

最初のrun37124366728（f98a120a）は56入力/24画面/native1、次のrun37124554654（f1f7817a）は57入力/25画面/native1。両者とも野生戦開始callbackの検査器停止・Flash未変更・新保存なし。失敗の原本を保持した上で有限no-input待機だけを修正し、未受入区間をSave34から回復した。成功測定native2、合計開発native4。旧19controller/4transition成功stepは再実行せず、最新5wait-onlyと26独立受入/拒否試験を追加。ROM/compile/fixture/既受入ゲーム再走0。

次: Save35 artifact11274735081のstory-fast.srm（df15c94737ee6511a80173215ab0edbfb3927161c7b6dbb59f9c403b4a197d98、131088bytes）だけから再開。map1/73・16,5西・party4/RP0・13128円・badge1・story4071=7/4072=1・flag4367=1。戻り転送8,10→27,7と野生バルキー1勝、通常Save35/独立Continueまで限定受入。ミュウツーHP320/354・PP[1,13,0,0]。はどうだん選択2回のうち初回はひるみ、実PP消費1。host回復/PP/flag/var注入禁止。次は16,5→16,4→15,4→14,4→13,4→13,5西岩階段→13,6→12,6→11,6→10,6→9,6→8,6→8,5→7,5候補。失敗辺9,7→9,6は反復せず、戻り転送の今回完了prefixも再走しない。保存済920cells/map-load3node14命令/7,5event6nodeを再採取しない。8,5はflag4367により開く静的ownerを継承するが、西階段/実8,5/7,5event/trainer360は未受入。本成功115/cold13入力・60画面・全77member、旧controller19+4成功step継承/新5wait-only/新26受入。失敗run37124366728の56入力24画面、37124554654の57入力25画面はいずれも未保存native1で保持。party offset41/241の各+1と補助var4021=119→7/4022=1→0のruntime ownerは未解決で、自然成長受入へ昇格しない。保存成功文言54〜56/全Flash完成54/field復帰57/cold全SaveRTC一致。trainer352/360、洞窟出口4,19→map1/38、全国図鑑、自然成長進化、全storyは未完。既存ROM/runtime/inputはActionsだけ、新公開artifactは新save/画面/textのみ。
