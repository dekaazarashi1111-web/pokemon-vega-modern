# Modernization引継ぎ

最終更新: 2026-09-08

この文書は`USER-MODERNIZATION-P01`からP08までの累積候補と、次工程が再利用する入力・未採用境界を固定する入口である。機械可読の候補identityは`config/modernization_candidate.json`、入力原本の固定台帳は`config/modernization_inputs.json`を正とする。

## 現在位置

- P01「ID・対象区分・共通処理の先行監査と根本修正」はローカル必須gateをPASSした。
- 累積候補はStage63 `build/stages/63_modernization_p01_identity_repair.gba`、SHA-256 `6642602d33e1e074c20afebfc649846f0aaf106c2455f2ca212a4f427ec74fbd`、CRC32 `FB09EF2D`。
- 現行プレイ基準はStage62のまま。Stage63をiPad、通常プレイsave、Codex対戦protocolへ採用していない。
- P02・P03はStage63を親候補として統合する。P04の公式情報・外部素材調査は並列準備できるが、ROMへの統合順はP02/P03の累積候補を継承する。

## P01で直したこと

旧取得資料は`canonical_id`だけで現行manifestへ結合していたため、現行のキャタピー649／内部タマゴ412に対して意味が逆転していた。中央identity契約は数値IDではなくstable keyを先に照合し、次を固定した。

- `SPECIES_KEY_CATERPIE`: 現行ID 649、通常対象、collection ledger bit 386。
- `SPECIES_KEY_EGG`: 現行ID 412、内部slot、収集対象外、ledgerなし。
- その他321件の入力`apply=false`: 一括解除しない。
- 復元監査候補194件: `REVIEW_ONLY_NOT_APPLIED`。能力・種族値・タイプをP01では採用しない。
- サイドチェンジ: 予約仕様ID 1063だが現行Move manifest/runtimeには未実装。P03の依存として扱う。

Stage63はStage62の取得runtime collection表2行だけを訂正した。変更は10 bytes、宣言外変更0で、既存Species ID、1,216 collection bits、完成対象数1,206、save配置、ROM allocationを維持する。Stage61 Wikiは履歴ファイルを削除せず、該当2種と決定的索引を同じkey resolverから再生成した。

Stage63 exact-ROMのmGBA identity gateは独立2 processでPASSした。Caterpie 649のbit 386登録／読戻し、内部Egg 412が登録されないこと、両者の分離、取得save layout、継承中の進化・野生表とhookを実ROM関数で確認した。Stage26の旧物理host addressはStage36以降のmap event所有者に置換済みなので、このP01 gateでは明示的に除外し、既存Stage26のstrict host gate自体は別途2 processでPASSして弱体化していないことを確認した。

## 入力と再生成

私有ZIP原本はGit管理外の`userfile/imports/modernization_p01/`に読み取り専用で置く。正確なfilename、size、SHA-256、採用境界は`config/modernization_inputs.json`にある。ZIPを展開してtracked領域へ丸ごと複製しない。

GitHub Actions用にはprivate Release tag `private-environment-v1`の`pokemon-vega-private-env-v1-modernization-inputs.zip`へ2原本だけを分離して保存した。assetは81,236,580 bytes、SHA-256 `bef64d08c470beb9b58321635d8f43d6d4e4fa657a2e5a26e4d081f097f5615e`で、remote再取得後のsize／hash／全memberを検査済み。公開repositoryやtracked GitへROM・ZIPを入れない。

```bash
make modernization-identity-check
make modernization-p01-capacity-audit
make modernization-p01-focused-test
make modernization-p01
make modernization-p01-check
make modernization-p01-mgba
```

`modernization-p01`はStage62とクリーンFireRed日本版Rev.0をそれぞれhash照合し、Stage63本体、Stage62差分BPS、clean ROM差分BPS、metadata、監査報告を決定的に作る。BPSは両起点からStage63へのbyte完全往復を検査する。

## 容量と次工程の制約

- allocator宣言空き: 1,915,916 bytes。未割当非FF byteは0。
- Species 1,621、Move 1,063、Ability 312、Item 999は現行ID枠の空き0。追加前に中央manifestと全consumerの上限拡張が必要。
- 進化表: 1種16 slot、使用856、空き25,080。表自体のslotには余裕がある。
- TM/HM catalog 128、教え技runtime 64、form resolution 509は現行枠の空き0。未到達bitや未追跡RAM/saveを空きとして流用しない。
- save ABIの未追跡領域は利用可能と仮定しない。追加時はowner付きlayoutと移行方針を先に固定する。

## 次工程への入口

P02は現行ROMの全進化行をspecies/form keyへ正規化し、通常進化と一時フォーム変化を分離する。レビュー候補を自動採用せず、ベガ独自進化を保持する。P03の新しい技が条件になる経路は依存として明示する。

P03は提出ZIPの採用基準を維持し、原本を変更せず訂正レイヤーから基本1,025種・採用1,300 recordの集合を再生成する。レベル、進化時、思い出し、TM/TR、教え、タマゴ、共有タマゴ、進化前持越し、姿変更を別経路としてcompileし、対象外のベガ種を保持する。

P04で公式値が未確定の特性は、ユーザー指定により仮値を許可する。ただしstable species/form key、`TEMPORARY_REPLACEABLE`、採用理由、出典、差替えキーを機械可読に保持し、後から1か所の更新で差し替えられる形にする。画像・palette等は外部repositoryのlicenseとcommitを固定し、現行repoにない素材だけを再現可能なimporter経由で取り込む。
