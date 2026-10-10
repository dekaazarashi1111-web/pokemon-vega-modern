# ポケモンベガ Modern 調整基準Wiki R0

**固定レビュー版 R0** — SHA-256 `6e88a021785bfa7cf00e26d7f2433c380602d830e94e1d2fc31e3198cda31df2` / 33554432 bytes / CRC32 `00F31AF7`。

[入口](README.md) · [証拠区分と制限](LIMITATIONS.md) · [提案記入](OWNER_PROPOSALS.md)

ROM数値・文字列は旧候補読取＋5段階非変更範囲の継承。全機能の新native受入ではありません。

**性能比較・調整案の参照用です。試遊版・配布版の完成宣言ではありません。**

| 読む対象 | 入口 |
| --- | --- |
| ベガ206行の性能横比較 | [開く](VEGA_BALANCE_INDEX.md) |
| 全1671種族・フォームと全習得 | [開く](POKEMON_INDEX.md) |
| 1063技・直接/持越し逆引き | [開く](MOVE_INDEX.md) |
| 318特性とslot別逆引き | [開く](ABILITY_INDEX.md) |
| 隠れ特性と供給境界 | [開く](HIDDEN_ABILITY_INDEX.md) |
| 76メガと画像資源 | [開く](MEGA_INDEX.md) |
| 34キョダイマックス登録 | [開く](GMAX_INDEX.md) |
| 31専用Z・汎用Z/Max | [開く](Z_MOVE_INDEX.md) |
| 1044道具と供給 | [開く](ITEM_INDEX.md) |
| 入手・解禁と限定受入 | [開く](SUPPLY_CONDITIONS.md) |
| 旧基準からの意味差分 | [開く](DIFF_INDEX.md) |
| 証拠区分・保存/製品の未完 | [開く](LIMITATIONS.md) |
| 承認案の記入入口 | [開く](OWNER_PROPOSALS.md) |
| 機械可読データと検証 | [開く](CODEX_INDEX.md) |

旧P08数値を5段階・7,013範囲の非変更証明で後継候補へ結合し、現役128,389経路/109,659条件は後継の採用表だけを使います。持越し35,211行を直接習得数へ足しません。未承認調整0。

入力source HEAD: `c935d493c998bc62a6189381085fc9d2bb6c6803`。識別情報は[data/index.json](data/index.json)。
