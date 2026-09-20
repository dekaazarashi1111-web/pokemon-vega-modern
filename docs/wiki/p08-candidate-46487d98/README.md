# P08調整前候補Wiki

候補 SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38` / 33554432 bytes / CRC32 `CC068B4A`。

[Wiki入口](README.md)

**開発中の調整前スナップショットです。配布版・release承認ではありません。**

| 分類 | 件数 |
| --- | --- |
| ability | 318 |
| item | 1044 |
| move | 1063 |
| species | 1671 |
| メガ | 76 |
| 専用Z対応 | 31 |
| P07原本行 | 1572 |

- [読み方と機械可読索引](CODEX_INDEX.md)
- [ベガ性能比較](VEGA_BALANCE_INDEX.md)
- [全種族・フォーム](POKEMON_INDEX.md)
- [全技](MOVE_INDEX.md)
- [全特性](ABILITY_INDEX.md)
- [隠れ特性と供給](HIDDEN_ABILITY_INDEX.md)
- [習得経路とP07履歴](LEARNSET_INDEX.md)
- [全メガ](MEGA_INDEX.md)
- [汎用・専用Z](Z_MOVE_INDEX.md)
- [全道具と供給](ITEM_INDEX.md)
- [Stage61意味差分](BALANCE_DIFF_STAGE61.md)
- [証拠と未監査範囲](RUNTIME_LIMITATIONS.md)

数値は現候補の読取結果、意味・供給は正本、native証拠は限定scopeとして分離します。Stage61履歴は変更しません。性能調整・夢特性追加・追加メガ・追加専用Zの採否は所有者の別指示で決めます。

## 生成・検証と残件

このスナップショットは .github/workflows/pr16-candidate-wiki.yml が詳細読取→結合→描画を実行して作成します。同じ入力で2プロセスの生成byteを比較し、全ファイル・source hash・内部リンクを照合します。

Issue #18全体は未完です。専用build/check CLIとMakefile入口は未反映（追加要求がツールの安全確認でブロックされたため、別経路で同じファイルを作成していません）。野生初期技・固定配布の全実moveset、汎用Z変換先、種族別の夢特性初回供給は明示的な監査残件です。既存native受入の再実行やゲーム性能変更はしていません。


## メガ登録行の監査

raw登録77行のうち、正逆対応を確認できたメガは76行です。自己参照・逆変換なしの旧登録1行はメガ形態として数えず、[登録行監査](MEGA_MAPPING_AUDIT.md) に分離しました。ゲームデータは修正していません。
