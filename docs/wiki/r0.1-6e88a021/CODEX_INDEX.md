# 参考JSONと固定入力

**R0.1（閲覧改善版）** — 固定R0と同じゲーム情報。ゲーム投入用ではありません。

[入口](README.md) · [制限](LIMITATIONS.md) · [識別情報](data/index.json)

[版/全member manifest](data/index.json)、[種族](data/species.jsonl)、[技](data/moves.jsonl)、[特性](data/abilities.jsonl)、[機構](data/mechanics.json)、[分類の原本値](data/classification.json)を提供します。ID/stable key/原本証拠は削除せず、主要MDから分離しました。

非網羅な旧役割抽出は [履歴専用JSON](data/legacy_role_hints.jsonl) へ隔離しています。空抽出は技の不存在を意味せず、判断用タグとして使用しないでください。

[固定R0入力manifest](data/r0_input_manifest.json) と [現役原本参照](data/active_sources.json) 内のrepository pathは由来の記録です。旧候補/Issue19の全機械読取原本や実行コードはこのZIPに含みません。それらが必要な監査は固定リポジトリを参照してください。通常閲覧用の全習得・条件・逆引きMarkdownは同梱済みで、そのリンクに外部依存はありません。

`check` は再生成byte・集合・リンク・mtimeを照合する読取専用コマンドです。`package` は既存版を検査し明示したZIPだけを書きます。ゲーム情報の意味hashと表示用tree hashを別々に記録します。
