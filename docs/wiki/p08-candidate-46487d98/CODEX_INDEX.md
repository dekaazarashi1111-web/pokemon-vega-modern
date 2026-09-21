# Codex・調整判断の入口

候補 SHA-256 `46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38` / 33554432 bytes / CRC32 `CC068B4A`。

[Wiki入口](README.md)

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

## データ入口

| データ | 内容 |
| --- | --- |
| [index.json](data/index.json) | 候補・入力hash・全ファイルmanifest |
| [provenance.json](data/provenance.json) | table・source binding・固定上流 |
| [balance_diff_stage61.json](data/balance_diff_stage61.json) | 意味差分 |
| [p07_history.jsonl](data/p07_history.jsonl) | 原本1572行と元route/条件の現在照合 |

名前だけでjoinしないでください。数値IDとstable keyを併用します。JSONLの1行が1種族・1技・1履歴recordです。個別ページはpokemon/moves/abilities/itemsの数値ID名です。


## メガ登録行の監査

raw登録77行のうち、正逆対応を確認できたメガは76行です。自己参照・逆変換なしの旧登録1行はメガ形態として数えず、[登録行監査](MEGA_MAPPING_AUDIT.md) に分離しました。ゲームデータは修正していません。

[今回追加の固定consumer監査・正確な残件](CONSUMER_AUDIT.md)

[汎用Zの実行時split・候補table監査](RUNTIME_Z_AUDIT.md)

[技effectのsource由来・残件](EFFECT_ORIGIN_AUDIT.md)

[夢特性パッチ：種族別適用条件・供給source・未受入範囲](HIDDEN_PATCH_AUDIT.md)

[野生・配布・raid初期技のsource規則と残件](CREATION_MOVESET_AUDIT.md)
