# ポケモンベガ Modern 閲覧資料

**R0.1（閲覧改善版）** — 固定R0と同じゲーム情報。ゲーム投入用ではありません。

[入口](README.md) · [制限](LIMITATIONS.md) · [識別情報](data/index.json)

まず[ベガ比較](VEGA_BALANCE_INDEX.md)を開き、必要な場合だけ[全種族](POKEMON_INDEX.md)へ進みます。気になる名前から個別ページの「全習得」を読み、関連する[技](MOVE_INDEX.md)・[特性](ABILITY_INDEX.md)の詳細へ移ってください。資料全体を一括でAIへ渡す必要はありません。

基本性能・全習得経路/条件・機構対応は固定R0から不変です。役割要約の取りこぼしを判断根拠から外し、表示だけを改善しました。バランス変更案や実装承認は含みません。

[道具](ITEM_INDEX.md) · [メガ](MEGA_INDEX.md) · [Gmax](GMAX_INDEX.md) · [専用Z](Z_MOVE_INDEX.md) · [供給条件](SUPPLY_CONDITIONS.md) · [隠れ特性](HIDDEN_ABILITY_INDEX.md) · [旧基準との差分](DIFF_INDEX.md)

## ローカル保存と別AIへの渡し方

閲覧用ZIP `wiki-r0.1-6e88a021.zip` を展開し、`r0.1-6e88a021/README.md` をMarkdown対応エディタで開きます。主要一覧と全詳細を同梱し、Markdownの相対リンクは展開後も内部で完結します。ZIPと全memberのsize/SHA-256は同時提供の検証記録にあります。

リポジトリからの再現は `python3 -B scripts/pr16_wiki_readability.py package --output .local/wiki-r0.1-6e88a021.zip`。完成済み閲覧版のhashを照合して資料だけをZIP化します。ROM/save/private入力/.git/実行環境は含みません。公開Releaseは作りません。

別AIには「この固定版のベガ比較→指定した系統の全習得→関連する技/特性詳細だけを読み、検討に使ってください。原本やゲームは編集せず、習得・自然供給・効果の未確認を区別してください」と伝えます。

[参考JSONの読み方](CODEX_INDEX.md)は必要時だけ参照。これはゲームへ直接投入するデータではありません。保存安全性・配布受入の完了宣言でもありません。
