# PR16 ストーリー分離fixture checkpoint

## 受入範囲

run `36500700863` / source HEAD `5243a6000755bd5596f994f322b1587f33fc2484` / artifact `11005890195`。
`PASS_SPLIT_PREPARATION_WITH_PROGRESSION_BLOCKED`。Actions完了はrunの最終conclusionを別途照会する。

- `story-fast.srm`: 自己OT Lv100のMewtwo/Haxorus/Mew/Bibarel、空きparty2枠。Mewtwo通常技選択→サイコブレイク→勝利→field→通常Save counter14→15→独立fresh Continue。
- `progression.srm`: 自己OT Axew Lv37/EXP68589、持ち物なし。戦闘前状態のまま通常Save counter14→15→独立fresh Continue。次の進化試験の再開用であり進化成功saveではない。
- 原本2体のPC格納はnative80-byte BoxPokemonを保持。party100-byte原像はartifactへ別保存。PCが100-byte party structを保存するとは主張しない。RAM再配置後も全80byteを再同定。

両コピーの全hash、原本hash、各caseのstdout/stderr、画面、fixture前後全RAM・全変更byte台帳はartifactと`content/modernization/pr16_story_acceleration_checkpoint.json`を参照する。Save14原本artifact10999218544は不変。コピーのcounter15を自然進行Save15へ昇格しない。

## 実装上の訂正

計画の暫定species数値8件は実台帳より1大きかった。実manifest/現候補ROMは直接一致し、runtime offsetではない。Mewtwo150、Haxorus850、Mew151、Bibarel690、Axew848、Audino788、Chansey365、Blissey366へstable keyで解決した。計画の技symbol区切り差だけを一意性検査付きで解決し、数値fallbackを禁止。

現ROM headerから32byte種族表、12byte技表、40byte道具表を再解決。道具8件のID・名称・pocket・held-effect ABIを照合したが、Lucky Egg倍率の対照は未実施。支援Bag用品も未追加。field utility技は未解禁のため初期4枠を空にした。

## progressionの実停止原因

Axew848の閾値はnative CreateMonでLv38/EXP68590、進化先849を確認した。別の診断processで通常Caterpie Lv2戦を直接開始し、通常入力のみで勝利、EXP68589→68590、Lv37→38、進化画面へ入る。しかしnational dex=0、target849>151のnative gateが自動取消state17/stopped=1へ遷移させる。B取消入力や戦闘後host writeによる結果ではない。

実候補の`0x080CFA20`からのbranchはIsNationalPokedexEnabled `0x0806DA51`を呼び、state8/target>0x97でstate17へ移す。同系branchは`0x080D067C`にも残る。code範囲hashをcheckpointへ固定した。旧P02 acceptance runnerの`p02s_enable_national_dex`は全国図鑑をfixture解禁しており、旧成功を自然Save14条件の進化成功へ流用しない。

診断はexit3 / `BLOCKED_NATIONAL_DEX_EVOLUTION_GUARD`のまま記録する。全国図鑑flagの注入、ROMの閾値緩和、進化結果の強制書込みをしていない。今回のActions成功はこの限定診断の再現・保存までであり、進化受入ではない。

## 次の未完作業

story-fast保存コピーからマオリ以降の通常storyを進める。原本Save14や今回のsmokeを無影響に再生しない。field技は自然なHM/key item/badge authorization後に別fixture境界で投入する。

成長側は、全国図鑑の正規取得条件と現候補の進化gateの設計ownerを先に照合する。Save14のflagを注入して成功扱いせず、必要なら正規story解禁後の別境界、または影響台帳付きsource修正・後継候補として扱う。Lucky Eggなし/あり対照、12境界ケース、Lv100 soakは未着手/未受入のまま。

## 検証と境界

新規19 focused tests、7host-write拒否、host compile1、新規native3 process/5 fresh cores、通常Save2。開発時13 process/15 coresは正式3件と分けて履歴化。Save1〜14の既受入scenario再実行0、ROM変更0。戦闘開始後の7write APIを拒否し、fixture前後SaveBlock1/2不変を検査。自然難易度・自然入手・全story・release/merge/baseline切替は主張しない。

## 完了照会と全Save差分

run36500700863はcompleted/success、記録commit c2d3cf659d4122555842d2a31eaf7c7647c0cf51の非force反映を確認。75 evidence hashを再照合し、15画面を目視確認した。全Save差分2本は再構成一致し、追加artifact 11005935534 へ保存。詳細は `content/modernization/pr16_story_acceleration_completion.json`。今回の追加native/compile/受入再実行は0。進化未受入を保持。
