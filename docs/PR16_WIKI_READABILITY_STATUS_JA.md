# Wiki R0.1 閲覧改善の固定引継ぎ

生成・限定検証済み。固定公開commitと実物レビュー・提示・完了Actionsの受領はまだ。

[閲覧入口](wiki/r0.1-6e88a021/README.md) / [ベガ比較](wiki/r0.1-6e88a021/VEGA_BALANCE_INDEX.md) / [全種族](wiki/r0.1-6e88a021/POKEMON_INDEX.md) / [技](wiki/r0.1-6e88a021/MOVE_INDEX.md) / [特性](wiki/r0.1-6e88a021/ABILITY_INDEX.md)。

[検証](../content/modernization/pr16_wiki_readability_verification.json) / [全member manifest](wiki/r0.1-6e88a021/data/index.json) / [固定状態JSON](../content/modernization/pr16_wiki_first_execution_plan.json)。

役割候補は全種族の判断用表示から除外。リーテイルLv46こうごうせいを含む全習得/逆引き/条件byteとゲーム情報は不変。技術JSONは詳細へ折り畳み、4主要一覧を人向けに整理。

ファイル数 4517、展開size 177464001、検証リンク 592544。ZIP `wiki-r0.1-6e88a021.zip`、size 33950355、SHA-256 `abd887f241fbfdcc454bfc13abf9fa3b7c7c2025943c40ec3880dc2a66f1268e`。資料限定、展開/全member hash/内部リンク/決定性を確認済み。

入力R0 commit `473aca371dbfd1d8a041d2ead4326a54759dcda4`、生成source `4e3d869f2a13f4fbea78bfe4b137a18fe7bd82c6`、公開commit `提示受領時に束縛`。Actions run 38104885843 の `pr16-wiki-readability-package` artifactを使うか、READMEの限定packageコマンドで再現する。外側artifact ZIPには内側の閲覧ZIPが含まれる。

参考JSON内の旧repository pathは来歴で、旧機械読取原本/実行環境を資料ZIPへ同梱しない。全習得のMarkdown閲覧導線は内部完結。説明は完全な実効果仕様ではない。

旧R0/原本/受入証拠は不変。全クリ対象外（PASSではない）、保存安全性は未完。正式788分類/86未知・選定残7・安全容量0を保持。全体private guardの既存違反や無関係なCI失敗は解消と主張しない。未承認バランス変更、merge、release、baseline切替なし。
